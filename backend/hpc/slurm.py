"""
SLURM Workload Manager Abstraction
===================================
Provides standard interfaces for job submission, monitoring, and cancellation.
Translates SLURM cluster states into Solvosys job lifecycle states.
Includes MockSlurmExecutor for local testing.
"""

import re
import time
import uuid
import threading
import subprocess
import os
import sys
import json
import tempfile
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from hpc.connection import HPCConnection, MockHPCConnection


class SlurmJobState(str, Enum):
    PENDING = "PENDING"
    CONFIGURING = "CONFIGURING"
    RUNNING = "RUNNING"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"
    OUT_OF_MEMORY = "OUT_OF_MEMORY"
    NODE_FAIL = "NODE_FAIL"
    PREEMPTED = "PREEMPTED"
    BOOT_FAIL = "BOOT_FAIL"
    DEADLINE = "DEADLINE"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def to_solvosys_status(cls, slurm_state: str) -> str:
        """Map SLURM state string to Solvosys job status string."""
        s = str(slurm_state).strip().upper()
        if "SUSPENDED" in s:
            return "running"
        elif any(k in s for k in ["PEND", "CONFIG", "REQUEUE", "HELD", "WAIT"]) or s == "PD":
            return "queued"
        elif any(k in s for k in ["RUN", "COMPLETING"]) or s in ["R", "CG"]:
            return "running"
        elif "COMPLETED" in s or s == "CD":
            return "completed"
        elif any(k in s for k in ["CANCEL", "REVOKED"]) or s == "CA":
            return "cancelled"
        elif any(k in s for k in ["FAIL", "TIMEOUT", "NODE", "OUT_OF_MEMORY", "BOOT_FAIL", "DEADLINE", "PREEMPT"]) or s in ["TO", "NF", "OOM", "F", "BF"]:
            return "failed"
        return "running"

    @classmethod
    def is_terminal(cls, slurm_state: str) -> bool:
        """Determines if a SLURM state is terminal (job is finished and no longer needs files)."""
        s = str(slurm_state).upper()
        return any(term in s for term in [
            "COMPLETED", "FAILED", "CANCEL", "TIMEOUT", "NODE_FAIL",
            "OUT_OF_MEMORY", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED"
        ])

    @classmethod
    def get_friendly_message(cls, slurm_state: str, job_id: str, compute_node: str = "", partition: str = "cpu_student") -> str:
        """Returns a clear, user-friendly status message describing the SLURM state."""
        s = str(slurm_state).upper()
        if any(k in s for k in ["PEND", "CONFIG", "REQUEUE", "HELD", "WAIT"]):
            return f"Job queued (SLURM Job: #{job_id}). Waiting for an available compute node on '{partition}'..."
        elif any(k in s for k in ["RUN", "COMPLETING"]):
            node_info = f" ({compute_node})" if compute_node and compute_node not in ["Unknown", "None", ""] else ""
            return f"Running on compute node{node_info} (SLURM Job: #{job_id})..."
        elif "COMPLETED" in s:
            return f"SLURM Job #{job_id} completed successfully. Retrieving results..."
        elif any(k in s for k in ["CANCEL", "REVOKED"]):
            return f"SLURM Job #{job_id} was cancelled."
        elif "TIMEOUT" in s:
            return f"SLURM Job #{job_id} exceeded its allocated time limit (10 minutes)."
        elif "OUT_OF_MEMORY" in s:
            return f"SLURM Job #{job_id} exceeded its allocated memory limit (2 GB)."
        elif any(k in s for k in ["NODE", "BOOT_FAIL"]):
            return f"SLURM Job #{job_id} failed due to a compute node error."
        elif "FAIL" in s:
            return f"SLURM Job #{job_id} failed during execution."
        return f"SLURM Job #{job_id} status: {slurm_state}"


import tempfile


def generate_test_slurm_script(
    partition: str,
    job_name: str = "solvosys_test",
    time_limit: str = "00:02:00",
    cpus_per_task: int = 1,
    mem: str = "1G"
) -> str:
    """Generate a minimal, harmless SLURM script that performs ONLY harmless echo checks."""
    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={job_name}",
        "#SBATCH --output=slurm_%j.out",
        "#SBATCH --error=slurm_%j.err",
        f"#SBATCH --partition={partition}",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --mem={mem}",
        f"#SBATCH --time={time_limit}",
        "",
        'echo "Solvosys SLURM test"',
        'echo "Job ID: $SLURM_JOB_ID"',
        'echo "Hostname: $(hostname)"',
        'echo "User: $(whoami)"',
        f'echo "Partition: {partition}"',
        "",
        "# Write structured output file for verification",
        "cat <<EOF > slurm_test_output.txt",
        "Solvosys SLURM test",
        "Job ID: $SLURM_JOB_ID",
        "Hostname: $(hostname)",
        "User: $(whoami)",
        f"Partition: {partition}",
        "EOF",
        "",
        "exit 0"
    ]
    return "\n".join(lines).replace("\r\n", "\n").replace("\r", "\n") + "\n"


def calculate_experiment_memory(
    df: Optional[Any] = None,
    model_name: str = "Random Forest",
    cpus_per_task: int = 4,
    custom_mem: Optional[str] = None
) -> str:
    """
    Calculates a safe and realistic memory request for a SLURM job.
    Enforces a strict realistic lower bound (2048 MB = 2 GB) and safe upper bound (16384 MB = 16 GB)
    to prevent cluster resource exhaustion or default node-wide memory allocations (~1 TB).
    """
    if custom_mem and str(custom_mem).strip():
        # Validate custom format (e.g. '4G', '2048M')
        raw = str(custom_mem).strip().upper()
        if raw.endswith("G") and raw[:-1].isdigit():
            val_mb = int(raw[:-1]) * 1024
            clamped = max(2048, min(val_mb, 32768))
            return f"{clamped}M"
        elif raw.endswith("M") and raw[:-1].isdigit():
            val_mb = int(raw[:-1])
            clamped = max(2048, min(val_mb, 32768))
            return f"{clamped}M"
        return raw

    base_mb = 2048  # 2 GB base for Python interpreter, numpy, pandas, scikit-learn
    data_mb = 10
    
    if df is not None:
        try:
            if hasattr(df, "memory_usage"):
                bytes_count = int(df.memory_usage(deep=True).sum())
                data_mb = max(1, int(bytes_count / (1024 * 1024)))
            elif isinstance(df, (int, float)):
                data_mb = max(1, int(df / (1024 * 1024)))
        except Exception:
            data_mb = 10

    # Trees / Ensembles need working memory across estimators
    scaling = 10 if any(k in model_name for k in ["Forest", "Tree", "Boost", "GBDT"]) else 5
    estimated_mb = base_mb + (data_mb * scaling) + (cpus_per_task * 256)

    # Clamping: Safe lower bound 2048 MB (2 GB), Safe upper bound 16384 MB (16 GB)
    safe_mb = max(2048, min(estimated_mb, 16384))
    return f"{safe_mb}M"


def generate_slurm_script(
    job_name: str = "solvosys_experiment",
    time_limit: str = "00:10:00",
    cpus_per_task: int = 2,
    mem: str = "2G",
    gpus: int = 0,
    partition: Optional[str] = None
) -> str:
    """Generate a standard portable SLURM submission script with explicit conservative resources."""
    lines = [
        "#!/bin/bash",
        f"#SBATCH --job-name={job_name}",
        "#SBATCH --output=slurm_%j.out",
        "#SBATCH --error=slurm_%j.err",
        "#SBATCH --nodes=1",
        "#SBATCH --ntasks=1",
        f"#SBATCH --cpus-per-task={cpus_per_task}",
        f"#SBATCH --mem={mem}",
        f"#SBATCH --time={time_limit}",
    ]
    if gpus > 0:
        lines.append(f"#SBATCH --gpus={gpus}")
    if partition:
        lines.append(f"#SBATCH --partition={partition}")

    lines.extend([
        "",
        'echo "========================================="',
        'echo "Solvosys HPC Job Execution"',
        'echo "Job ID: $SLURM_JOB_ID"',
        'echo "Node:   $SLURM_NODELIST"',
        'echo "Start:  $(date)"',
        'echo "========================================="',
        "",
        "# Auto-detect Python binary (python3 or python)",
        "if command -v python3 >/dev/null 2>&1; then",
        '    PY_CMD="python3"',
        "elif command -v python >/dev/null 2>&1; then",
        '    PY_CMD="python"',
        'elif [ -x "/usr/bin/python3" ]; then',
        '    PY_CMD="/usr/bin/python3"',
        'elif [ -x "/usr/bin/python" ]; then',
        '    PY_CMD="/usr/bin/python"',
        "else",
        '    echo "Error: Python runtime not found in PATH on compute node $(hostname)" >&2',
        "    exit 127",
        "fi",
        "",
        "# Run standalone Python experiment",
        "$PY_CMD experiment.py",
        "EXIT_CODE=$?",
        "",
        'echo "========================================="',
        'echo "Job finished at $(date) with exit code $EXIT_CODE"',
        'echo "========================================="',
        "exit $EXIT_CODE"
    ])
    return "\n".join(lines).replace("\r\n", "\n").replace("\r", "\n") + "\n"


class SlurmExecutor(ABC):
    """Abstract interface for SLURM workload management."""

    def __init__(self, connection: HPCConnection):
        self.connection = connection

    @abstractmethod
    def submit_job(self, remote_dir: str, script_name: str = "run.slurm") -> str:
        """Submit a job and return the SLURM Job ID."""
        pass

    @abstractmethod
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Query SLURM job status.
        Returns: {
            "job_id": str,
            "slurm_state": str,
            "solvosys_status": str,
            "elapsed": str,
            "nodes": str
        }
        """
        pass

    @abstractmethod
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running or pending SLURM job."""
        pass

    @abstractmethod
    def get_job_output(self, job_id: str, remote_dir: str) -> Tuple[str, str]:
        """Retrieve stdout and stderr from job log files."""
        pass

    def test_slurm_job(
        self,
        partition: str,
        time_limit: str = "00:02:00",
        cpus_per_task: int = 1,
        mem: str = "1G",
        poll_interval: float = 0.5,
        timeout_seconds: float = 120.0
    ) -> Dict[str, Any]:
        """
        Submits and monitors a harmless SLURM job to verify cluster scheduling and output collection.
        Does NOT execute Python, does NOT request GPUs, touches NO user datasets.
        """
        if not partition or not partition.strip():
            raise ValueError("SLURM partition is required to submit a test job.")

        partition = partition.strip()
        unique_id = uuid.uuid4().hex[:8]
        test_dir_name = f"solvosys_hpc_slurm_test_{unique_id}"
        remote_home = self.connection.get_home_dir()
        remote_test_dir = f"{remote_home.rstrip('/')}/{test_dir_name}"

        steps = {
            "upload": "pending",
            "submit": "pending",
            "monitor": "pending",
            "output_verify": "pending",
            "cleanup": "pending"
        }

        # 1. Generate harmless test SLURM script
        script_content = generate_test_slurm_script(
            partition=partition,
            job_name="solvosys_test",
            time_limit=time_limit,
            cpus_per_task=cpus_per_task,
            mem=mem
        )

        job_id = None
        output_content = ""

        with tempfile.TemporaryDirectory() as local_temp_dir:
            local_script_path = os.path.join(local_temp_dir, "run_test.slurm")
            local_output_path = os.path.join(local_temp_dir, "slurm_test_output.txt")

            # Strictly enforce Unix LF line breaks and write in binary mode to bypass Windows CRLF translation
            script_bytes = script_content.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            with open(local_script_path, "wb") as f:
                f.write(script_bytes)

            try:
                # 2. Upload test script
                remote_script_path = f"{remote_test_dir}/run_test.slurm"
                self.connection.upload_file(local_script_path, remote_script_path)
                steps["upload"] = "OK"

                # 3. Submit SLURM test job
                job_id = self.submit_job(remote_test_dir, "run_test.slurm")
                steps["submit"] = "OK"

                # 4. Monitor job status
                start_time = time.time()
                while True:
                    if time.time() - start_time > timeout_seconds:
                        self.cancel_job(job_id)
                        raise TimeoutError(f"SLURM test job {job_id} timed out after {timeout_seconds}s.")

                    status_info = self.get_job_status(job_id)
                    solv_status = status_info.get("solvosys_status", "queued")

                    if solv_status == "completed":
                        steps["monitor"] = "OK"
                        break
                    elif solv_status in ("failed", "cancelled"):
                        out_log, err_log = self.get_job_output(job_id, remote_test_dir)
                        raise RuntimeError(
                            f"SLURM test job {job_id} {solv_status}. State: {status_info.get('slurm_state')}. "
                            f"Error details: {err_log or out_log or status_info.get('error', 'No error log')}"
                        )

                    time.sleep(poll_interval)

                # 5. Retrieve and verify output
                remote_out_path = f"{remote_test_dir}/slurm_test_output.txt"
                try:
                    self.connection.download_file(remote_out_path, local_output_path)
                    if os.path.exists(local_output_path):
                        with open(local_output_path, "r", encoding="utf-8") as f:
                            output_content = f.read()
                except Exception:
                    out_log, _ = self.get_job_output(job_id, remote_test_dir)
                    output_content = out_log

                if "Solvosys SLURM test" not in output_content:
                    raise ValueError(f"SLURM test output verification failed. Content received:\n{output_content}")
                steps["output_verify"] = "OK"

            finally:
                # 6. Targeted Strict Cleanup
                if "solvosys_hpc_slurm_test_" in remote_test_dir:
                    try:
                        self.connection.delete_dir(remote_test_dir)
                        steps["cleanup"] = "OK"
                    except Exception as e:
                        steps["cleanup"] = f"Warning: Cleanup failed for {remote_test_dir}: {str(e)}"

        return {
            "success": all(steps[k] == "OK" for k in ["upload", "submit", "monitor", "output_verify", "cleanup"]),
            "job_id": job_id,
            "partition": partition,
            "status": "COMPLETED",
            "remote_test_dir": remote_test_dir,
            "output": output_content,
            "steps": steps,
            "message": f"SLURM test job #{job_id} completed successfully on partition '{partition}'."
        }

    def verify_environment(
        self,
        partition: str = "cpu_student",
        time_limit: str = "00:02:00",
        timeout_seconds: int = 120,
        poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Submits a minimal SLURM job to inspect the Python environment strictly on the COMPUTE NODE.
        Collects versions of python, numpy, pandas, scikit-learn, xgboost, and catboost.
        Performs targeted cleanup of the test directory upon completion.
        """
        test_uuid = uuid.uuid4().hex[:8]
        remote_home = self.connection.get_home_dir()
        remote_test_dir = f"{remote_home.rstrip('/')}/solvosys_hpc_env_test_{test_uuid}"

        # Generate check_env.py script
        py_content = (
            "import sys\n"
            "import json\n"
            "import socket\n\n"
            "def get_pkg_version(pkg_name):\n"
            "    try:\n"
            "        mod = __import__(pkg_name)\n"
            "        return getattr(mod, '__version__', 'INSTALLED')\n"
            "    except ImportError:\n"
            "        return 'NOT INSTALLED'\n"
            "    except Exception as e:\n"
            "        return f'ERROR: {str(e)}'\n\n"
            "info = {\n"
            "    'hostname': socket.gethostname(),\n"
            "    'python': sys.executable,\n"
            "    'python_version': sys.version.split()[0],\n"
            "    'numpy': get_pkg_version('numpy'),\n"
            "    'pandas': get_pkg_version('pandas'),\n"
            "    'scikit_learn': get_pkg_version('sklearn'),\n"
            "    'xgboost': get_pkg_version('xgboost'),\n"
            "    'catboost': get_pkg_version('catboost')\n"
            "}\n\n"
            "with open('env_check_output.json', 'w', encoding='utf-8') as f:\n"
            "    json.dump(info, f, indent=2)\n"
        ).replace("\r\n", "\n").replace("\r", "\n")

        # Generate SLURM submission script with pure Unix LF
        slurm_lines = [
            "#!/bin/bash",
            "#SBATCH --job-name=solvosys_env_check",
            "#SBATCH --output=slurm_%j.out",
            "#SBATCH --error=slurm_%j.err",
            f"#SBATCH --partition={partition}",
            "#SBATCH --nodes=1",
            "#SBATCH --ntasks=1",
            "#SBATCH --cpus-per-task=1",
            "#SBATCH --mem=1G",
            f"#SBATCH --time={time_limit}",
            "",
            "# Auto-detect Python runtime",
            "if command -v python3 >/dev/null 2>&1; then",
            '    PY_CMD="python3"',
            "elif command -v python >/dev/null 2>&1; then",
            '    PY_CMD="python"',
            'elif [ -x "/usr/bin/python3" ]; then',
            '    PY_CMD="/usr/bin/python3"',
            'elif [ -x "/usr/bin/python" ]; then',
            '    PY_CMD="/usr/bin/python"',
            "else",
            '    echo "Error: Python runtime not found in PATH on compute node $(hostname)" >&2',
            "    exit 127",
            "fi",
            "",
            "$PY_CMD check_env.py",
            "exit $?"
        ]
        slurm_content = "\n".join(slurm_lines).replace("\r\n", "\n").replace("\r", "\n") + "\n"

        env_info = {}
        with tempfile.TemporaryDirectory() as local_temp_dir:
            local_py_path = os.path.join(local_temp_dir, "check_env.py")
            local_slurm_path = os.path.join(local_temp_dir, "run_check.slurm")
            local_out_path = os.path.join(local_temp_dir, "env_check_output.json")

            with open(local_py_path, "wb") as f:
                f.write(py_content.encode("utf-8"))
            with open(local_slurm_path, "wb") as f:
                f.write(slurm_content.encode("utf-8"))

            try:
                # Upload files
                self.connection.upload_file(local_py_path, f"{remote_test_dir}/check_env.py")
                self.connection.upload_file(local_slurm_path, f"{remote_test_dir}/run_check.slurm")

                # Submit SLURM job
                job_id = self.submit_job(remote_test_dir, "run_check.slurm")

                # Monitor job
                start_time = time.time()
                while True:
                    if time.time() - start_time > timeout_seconds:
                        self.cancel_job(job_id)
                        raise TimeoutError(f"Environment check SLURM job {job_id} timed out after {timeout_seconds}s.")

                    status_info = self.get_job_status(job_id)
                    solv_status = status_info.get("solvosys_status", "queued")

                    if solv_status == "completed":
                        break
                    elif solv_status in ("failed", "cancelled"):
                        out_log, err_log = self.get_job_output(job_id, remote_test_dir)
                        raise RuntimeError(f"Environment check SLURM job {job_id} {solv_status}. Error: {err_log or out_log}")

                    time.sleep(poll_interval)

                # Download results JSON
                remote_out_path = f"{remote_test_dir}/env_check_output.json"
                self.connection.download_file(remote_out_path, local_out_path)
                if os.path.exists(local_out_path):
                    with open(local_out_path, "r", encoding="utf-8") as f:
                        env_info = json.load(f)

            finally:
                # Targeted Strict Cleanup
                cleanup_ok = False
                if "solvosys_hpc_env_test_" in remote_test_dir:
                    try:
                        self.connection.delete_dir(remote_test_dir)
                        cleanup_ok = True
                    except Exception:
                        cleanup_ok = False
                env_info["cleanup"] = "OK" if cleanup_ok else "Failed or Skipped"

        return env_info


class RealSlurmExecutor(SlurmExecutor):
    """Executes SLURM commands over SSH connection."""

    def submit_job(self, remote_dir: str, script_name: str = "run.slurm") -> str:
        cmd = f"cd {remote_dir} && sbatch {script_name}"
        exit_code, stdout, stderr = self.connection.execute_command(cmd)
        if exit_code != 0:
            raise RuntimeError(f"sbatch submission failed: {stderr or stdout}")
        
        # Parse 'Submitted batch job 123456'
        match = re.search(r"Submitted batch job (\d+)", stdout)
        if match:
            return match.group(1)
        raise ValueError(f"Could not parse SLURM Job ID from sbatch output: {stdout}")

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        # Try squeue first for active jobs
        cmd = f"squeue -j {job_id} --noheader --format='%T|%M|%N'"
        code, out, _ = self.connection.execute_command(cmd)
        if code == 0 and out.strip():
            parts = out.strip().split("|")
            state = parts[0].strip() if len(parts) > 0 else "RUNNING"
            elapsed = parts[1].strip() if len(parts) > 1 else ""
            nodes = parts[2].strip() if len(parts) > 2 else ""
            return {
                "job_id": job_id,
                "slurm_state": state,
                "solvosys_status": SlurmJobState.to_solvosys_status(state),
                "elapsed": elapsed,
                "nodes": nodes
            }

        # Fallback to sacct for completed/failed jobs
        sacct_cmd = f"sacct -j {job_id} --noheader --format='State,Elapsed,NodeList' -P"
        s_code, s_out, _ = self.connection.execute_command(sacct_cmd)
        if s_code == 0 and s_out.strip():
            first_line = s_out.strip().split("\n")[0]
            parts = first_line.split("|")
            state = parts[0].strip() if len(parts) > 0 else "COMPLETED"
            elapsed = parts[1].strip() if len(parts) > 1 else ""
            nodes = parts[2].strip() if len(parts) > 2 else ""
            return {
                "job_id": job_id,
                "slurm_state": state,
                "solvosys_status": SlurmJobState.to_solvosys_status(state),
                "elapsed": elapsed,
                "nodes": nodes
            }

        return {
            "job_id": job_id,
            "slurm_state": "UNKNOWN",
            "solvosys_status": "queued",
            "elapsed": "",
            "nodes": ""
        }

    def cancel_job(self, job_id: str) -> bool:
        cmd = f"scancel {job_id}"
        code, _, _ = self.connection.execute_command(cmd)
        return code == 0

    def get_job_output(self, job_id: str, remote_dir: str) -> Tuple[str, str]:
        stdout_cmd = f"cat {remote_dir}/slurm_{job_id}.out"
        stderr_cmd = f"cat {remote_dir}/slurm_{job_id}.err"
        _, out, _ = self.connection.execute_command(stdout_cmd)
        _, err, _ = self.connection.execute_command(stderr_cmd)
        return out, err


class MockSlurmExecutor(SlurmExecutor):
    """
    Mock SLURM executor for local offline development.
    Simulates queue submission, state progression (PENDING -> RUNNING -> COMPLETED),
    and executes experiment.py inside the local mock workspace.
    """

    def __init__(self, connection: MockHPCConnection):
        super().__init__(connection)
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def submit_job(self, remote_dir: str, script_name: str = "run.slurm") -> str:
        job_id = f"mock-{int(time.time())}-{str(uuid.uuid4())[:4]}"
        local_exp_dir = self.connection.get_workspace_path(remote_dir)

        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "state": "PENDING",
                "solvosys_status": "queued",
                "remote_dir": remote_dir,
                "local_dir": local_exp_dir,
                "submit_time": time.time(),
                "start_time": None,
                "end_time": None,
                "process": None,
                "error": None
            }

        # Background thread simulating SLURM execution
        def _run_mock_job():
            time.sleep(1.2)  # Simulate queue pending
            with self._lock:
                if job_id not in self._jobs or self._jobs[job_id]["state"] == "CANCELLED":
                    return
                self._jobs[job_id]["state"] = "RUNNING"
                self._jobs[job_id]["solvosys_status"] = "running"
                self._jobs[job_id]["start_time"] = time.time()

            try:
                exp_script = os.path.join(local_exp_dir, "experiment.py")
                if os.path.exists(exp_script):
                    proc = subprocess.Popen(
                        [sys.executable, exp_script],
                        cwd=local_exp_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    with self._lock:
                        self._jobs[job_id]["process"] = proc

                    stdout, stderr = proc.communicate(timeout=300)
                    proc_exit = proc.returncode
                else:
                    # Harmless test job simulation (no Python execution on compute node)
                    time.sleep(0.8)
                    output_file = os.path.join(local_exp_dir, "slurm_test_output.txt")
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(
                            f"Solvosys SLURM test\n"
                            f"Job ID: {job_id}\n"
                            f"Hostname: mock-compute01.local\n"
                            f"User: {self.connection._username}\n"
                        )
                    stdout = f"Mock SLURM test job {job_id} executed successfully on mock-compute01."
                    stderr = ""
                    proc_exit = 0

                # Write out slurm log files
                with open(os.path.join(local_exp_dir, f"slurm_{job_id}.out"), "w", encoding="utf-8") as f:
                    f.write(f"=== Mock SLURM Out ===\n{stdout}")
                with open(os.path.join(local_exp_dir, f"slurm_{job_id}.err"), "w", encoding="utf-8") as f:
                    f.write(stderr)

                with self._lock:
                    if self._jobs[job_id]["state"] != "CANCELLED":
                        if proc_exit == 0:
                            self._jobs[job_id]["state"] = "COMPLETED"
                            self._jobs[job_id]["solvosys_status"] = "completed"
                        else:
                            self._jobs[job_id]["state"] = "FAILED"
                            self._jobs[job_id]["solvosys_status"] = "failed"
                            self._jobs[job_id]["error"] = stderr
                        self._jobs[job_id]["end_time"] = time.time()

            except Exception as e:
                with self._lock:
                    self._jobs[job_id]["state"] = "FAILED"
                    self._jobs[job_id]["solvosys_status"] = "failed"
                    self._jobs[job_id]["error"] = str(e)
                    self._jobs[job_id]["end_time"] = time.time()

        t = threading.Thread(target=_run_mock_job, daemon=True)
        t.start()
        return job_id

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        with self._lock:
            if job_id not in self._jobs:
                return {
                    "job_id": job_id,
                    "slurm_state": "UNKNOWN",
                    "solvosys_status": "failed",
                    "elapsed": "",
                    "nodes": "mock-node01"
                }
            job = self._jobs[job_id]
            elapsed = 0.0
            if job["start_time"]:
                end = job["end_time"] or time.time()
                elapsed = end - job["start_time"]

            return {
                "job_id": job_id,
                "slurm_state": job["state"],
                "solvosys_status": job["solvosys_status"],
                "elapsed": f"{elapsed:.1f}s",
                "nodes": "mock-node01",
                "error": job.get("error")
            }

    def cancel_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["state"] = "CANCELLED"
                self._jobs[job_id]["solvosys_status"] = "cancelled"
                proc = self._jobs[job_id].get("process")
                if proc:
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                return True
        return False

    def get_job_output(self, job_id: str, remote_dir: str) -> Tuple[str, str]:
        local_dir = self.connection.get_workspace_path(remote_dir)
        out_f = os.path.join(local_dir, f"slurm_{job_id}.out")
        err_f = os.path.join(local_dir, f"slurm_{job_id}.err")
        stdout = open(out_f, "r", encoding="utf-8").read() if os.path.exists(out_f) else ""
        stderr = open(err_f, "r", encoding="utf-8").read() if os.path.exists(err_f) else ""
        return stdout, stderr

    def verify_environment(self, partition: str = "cpu_student", **kwargs) -> Dict[str, Any]:
        import sys
        return {
            "hostname": "mock-dgx-compute01",
            "python": sys.executable,
            "python_version": sys.version.split()[0],
            "numpy": "1.26.4",
            "pandas": "2.2.2",
            "scikit_learn": "1.5.0",
            "xgboost": "NOT INSTALLED",
            "catboost": "NOT INSTALLED",
            "cleanup": "OK"
        }

