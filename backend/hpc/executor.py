"""
HPC Experiment Executor
=======================
Coordinates the lifecycle of a remote HPC experiment:
Packaging -> Upload -> SLURM Submission -> Polling & Status Tracking -> Result Download & Integration.
"""

import os
import json
import time
import uuid
import shutil
import tempfile
import pandas as pd
from typing import Dict, Any, Optional, Callable
from hpc.connection import HPCConnection
from hpc.slurm import SlurmExecutor, SlurmJobState
from hpc.packaging import package_experiment


class HPCExperimentExecutor:
    """High-level orchestrator for HPC / Supercomputer experiments."""

    def __init__(self, connection: HPCConnection, slurm: SlurmExecutor):
        self.connection = connection
        self.slurm = slurm

    def run_experiment(
        self,
        df: pd.DataFrame,
        config: Dict[str, Any],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        job_cancellation_check: Optional[Callable[[], bool]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete HPC experiment lifecycle.
        Returns: {
            "results": Dict[str, Any],
            "evaluation": Dict[str, Any],
            "training_time": float,
            "cleanup": str
        }
        """
        if not self.connection.is_connected():
            raise ConnectionError("Supercomputer is not connected. Please connect first.")

        exp_uuid = uuid.uuid4().hex[:8]
        remote_home = self.connection.get_home_dir()
        remote_exp_dir = f"{remote_home.rstrip('/')}/solvosys_hpc_exp_{exp_uuid}"

        local_temp = tempfile.mkdtemp(prefix="solvosys_pkg_")
        slurm_job_id = None
        compute_node = "Unknown"
        cleanup_status = "pending"

        try:
            # 1. Package locally
            if progress_callback:
                progress_callback({
                    "stage": "packaging",
                    "message": f"Packaging experiment for HPC ({len(df)} rows × {len(config.get('features', []))} features)..."
                })

            partition = config.get("partition", "cpu_student")
            package_experiment(df, config, output_dir=local_temp, partition=partition)

            if job_cancellation_check and job_cancellation_check():
                raise InterruptedError("Experiment cancelled before upload.")

            # 2. Upload experiment bundle
            if progress_callback:
                progress_callback({
                    "stage": "uploading",
                    "message": "Uploading experiment files to Supercomputer workspace..."
                })

            self.connection.upload_dir(local_temp, remote_exp_dir)

            if job_cancellation_check and job_cancellation_check():
                raise InterruptedError("Experiment cancelled after upload.")

            # 3. Submit SLURM Job
            if progress_callback:
                progress_callback({
                    "stage": "submitting",
                    "message": "Submitting job to SLURM scheduler (sbatch)...",
                    "slurm_job_id": None,
                    "slurm_state": "SUBMITTING",
                    "compute_node": None,
                    "partition": partition
                })

            slurm_job_id = self.slurm.submit_job(remote_exp_dir, "run.slurm")

            if progress_callback:
                progress_callback({
                    "stage": "queued",
                    "message": f"Job queued (SLURM Job: #{slurm_job_id}). Waiting for an available compute node on '{partition}'...",
                    "slurm_job_id": slurm_job_id,
                    "slurm_state": "PENDING",
                    "compute_node": None,
                    "partition": partition
                })

            # 4. Monitor & Poll SLURM Job with cluster-friendly adaptive interval
            start_monitor = time.time()
            job_status = "queued"
            last_progress_time = time.time()

            while True:
                if job_cancellation_check and job_cancellation_check():
                    self.slurm.cancel_job(slurm_job_id)
                    raise InterruptedError(f"SLURM Job #{slurm_job_id} cancelled by user.")

                # Cluster-friendly polling: 3.0s while queued/pending, 2.0s while actively running
                poll_interval = 3.0 if job_status == "queued" else 2.0
                time.sleep(poll_interval)
                status_info = self.slurm.get_job_status(slurm_job_id)
                raw_state = str(status_info.get("state", "UNKNOWN")).upper()
                solvosys_state = status_info.get("solvosys_status", "running")
                nodes = status_info.get("nodes", "")
                if nodes and nodes not in ["None", "Unknown", ""]:
                    compute_node = nodes

                friendly_msg = SlurmJobState.get_friendly_message(raw_state, slurm_job_id, compute_node, partition)

                # Emit progress update on state change or periodically
                if solvosys_state != job_status or (time.time() - last_progress_time >= 2.0):
                    job_status = solvosys_state
                    last_progress_time = time.time()
                    if progress_callback:
                        progress_callback({
                            "stage": solvosys_state,
                            "message": friendly_msg,
                            "slurm_job_id": slurm_job_id,
                            "slurm_state": raw_state,
                            "compute_node": compute_node if compute_node != "Unknown" else None,
                            "partition": partition
                        })

                if solvosys_state == "completed":
                    break
                elif solvosys_state == "failed":
                    if "TIMEOUT" in raw_state:
                        raise TimeoutError(f"The HPC job #{slurm_job_id} exceeded its allocated time limit (10 minutes).")
                    elif "OUT_OF_MEMORY" in raw_state:
                        raise MemoryError(f"The HPC job #{slurm_job_id} exceeded its allocated memory limit (2 GB).")
                    elif any(k in raw_state for k in ["NODE", "BOOT_FAIL"]):
                        raise RuntimeError(f"The HPC compute node failed during execution of Job #{slurm_job_id}.")
                    
                    out_log, err_log = self.slurm.get_job_output(slurm_job_id, remote_exp_dir)
                    error_detail = err_log or out_log or status_info.get('error', 'SLURM job failed. Check job output for details.')
                    raise RuntimeError(f"SLURM Job #{slurm_job_id} failed: {error_detail}")
                elif solvosys_state == "cancelled":
                    raise InterruptedError(f"HPC Job #{slurm_job_id} was cancelled.")

            # 5. Retrieve results
            if progress_callback:
                progress_callback({
                    "stage": "downloading",
                    "message": f"Job #{slurm_job_id} finished. Retrieving results and metrics from cluster...",
                    "slurm_job_id": slurm_job_id,
                    "slurm_state": "COMPLETED",
                    "compute_node": compute_node if compute_node != "Unknown" else None,
                    "partition": partition
                })

            remote_results_file = f"{remote_exp_dir}/results.json"
            local_results_file = os.path.join(local_temp, "results.json")
            
            self.connection.download_file(remote_results_file, local_results_file)

            with open(local_results_file, "r", encoding="utf-8") as f:
                results_data = json.load(f)

            training_time = results_data.get("training_time", time.time() - start_monitor)
            results_data["slurm_job_id"] = slurm_job_id
            results_data["compute_node"] = compute_node
            results_data["partition"] = partition

            # Build Solvosys evaluation structure
            train_metrics = results_data.get("train_metrics", {})
            metrics = results_data.get("metrics", {})
            
            training_r2 = results_data.get("training_r2")
            if training_r2 is None and isinstance(train_metrics, dict):
                training_r2 = train_metrics.get("R2 Score")
                
            validation_r2 = results_data.get("validation_r2")
            if validation_r2 is None and isinstance(metrics, dict):
                validation_r2 = metrics.get("R2 Score")

            evaluation_data = {
                "metrics": metrics,
                "train_metrics": train_metrics,
                "training_r2": training_r2,
                "validation_r2": validation_r2,
                "model_name": config.get("model_name"),
                "problem_type": config.get("problem_type"),
                "execution_mode": "hpc",
                "slurm_job_id": slurm_job_id,
                "compute_node": compute_node,
                "partition": partition
            }

            return {
                "results": results_data,
                "evaluation": evaluation_data,
                "training_time": float(training_time)
            }

        finally:
            # 6. Strict Safe Cleanup of remote experiment directory
            # CRITICAL RULE: NEVER delete workspace while SLURM job is active (PENDING/RUNNING).
            if "solvosys_hpc_exp_" in remote_exp_dir:
                try:
                    if slurm_job_id:
                        # Check if job is still in a non-terminal state
                        try:
                            status_info = self.slurm.get_job_status(slurm_job_id)
                            slurm_state = status_info.get("slurm_state", "UNKNOWN")
                            
                            # If non-terminal, cancel job first and wait for terminal state before deleting files
                            if not SlurmJobState.is_terminal(slurm_state):
                                self.slurm.cancel_job(slurm_job_id)
                                for _ in range(6):
                                    time.sleep(0.5)
                                    cur_st = self.slurm.get_job_status(slurm_job_id).get("slurm_state", "")
                                    if SlurmJobState.is_terminal(cur_st):
                                        break
                        except Exception:
                            pass

                    self.connection.delete_dir(remote_exp_dir)
                    cleanup_status = "OK"
                except Exception as e:
                    cleanup_status = f"Warning: Cleanup failed: {str(e)}"
            
            # Clean local temp directory
            shutil.rmtree(local_temp, ignore_errors=True)
