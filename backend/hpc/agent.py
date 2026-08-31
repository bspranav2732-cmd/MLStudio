"""
Local HPC Agent
===============
Localhost manager for Supercomputer connection state and execution.
Binds to localhost only. Stores NO plaintext passwords.
Provides mock and real connection management.
"""

from typing import Dict, Any, Optional
from hpc.connection import HPCConnection, MockHPCConnection, SSHConnection
from hpc.slurm import SlurmExecutor, MockSlurmExecutor, RealSlurmExecutor
from hpc.executor import HPCExperimentExecutor


class LocalHPCAgent:
    """Manages the local connection and execution adapter for HPC clusters."""

    def __init__(self):
        self._connection: Optional[HPCConnection] = None
        self._slurm: Optional[SlurmExecutor] = None
        self._executor: Optional[HPCExperimentExecutor] = None
        self._mode = "disconnected"
        self._host = None
        self._username = None

    def connect(
        self,
        mode: str = "mock",
        host: Optional[str] = None,
        username: Optional[str] = None,
        port: int = 22,
        key_filename: Optional[str] = None,
        passphrase: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Connects to either Mock HPC or real cluster via SSH keys.
        Never stores passwords, keys, or passphrases in state or logs.
        """
        if mode == "mock":
            conn = MockHPCConnection()
            conn.connect(host="mock-cluster.local", username="mock_user")
            slurm = MockSlurmExecutor(conn)
            self._connection = conn
            self._slurm = slurm
            self._executor = HPCExperimentExecutor(conn, slurm)
            self._mode = "mock"
            self._host = "mock-cluster.local"
            self._username = "mock_user"
            return {
                "status": "connected",
                "mode": "mock",
                "host": self._host,
                "username": self._username,
                "message": "Connected to Mock HPC Cluster (Local Simulation)"
            }
        elif mode == "ssh":
            if not host or not str(host).strip() or not username or not str(username).strip():
                raise ValueError("Host and username are required for SSH connection.")
            host = str(host).strip()
            username = str(username).strip()
            port = int(port) if port else 22
            conn = SSHConnection()
            conn.connect(
                host=host,
                username=username,
                port=port,
                key_filename=key_filename.strip() if key_filename else None,
                passphrase=passphrase
            )
            slurm = RealSlurmExecutor(conn)
            self._connection = conn
            self._slurm = slurm
            self._executor = HPCExperimentExecutor(conn, slurm)
            self._mode = "ssh"
            self._host = host
            self._username = username
            return {
                "status": "connected",
                "mode": "ssh",
                "host": self._host,
                "username": self._username,
                "message": f"Connected to Supercomputer ({username}@{host})"
            }
        else:
            raise ValueError(f"Unknown connection mode: {mode}")

    def disconnect(self) -> Dict[str, Any]:
        if self._connection:
            self._connection.disconnect()
        self._connection = None
        self._slurm = None
        self._executor = None
        self._mode = "disconnected"
        self._host = None
        self._username = None
        return {
            "status": "disconnected",
            "message": "Supercomputer session disconnected."
        }

    def get_status(self) -> Dict[str, Any]:
        is_conn = self._connection is not None and self._connection.is_connected()
        info = self._connection.get_info() if is_conn else {}
        return {
            "connected": is_conn,
            "mode": self._mode if is_conn else "disconnected",
            "host": info.get("host") or self._host if is_conn else None,
            "username": info.get("username") or self._username if is_conn else None,
            "node": info.get("node") if is_conn else None,
            "auth_type": info.get("auth_type", "SSH Key / Agent") if is_conn else None,
            "message": "Connected" if is_conn else "Not Connected"
        }

    def get_connection(self) -> Optional[HPCConnection]:
        if self._connection and self._connection.is_connected():
            return self._connection
        return None

    def get_executor(self) -> Optional[HPCExperimentExecutor]:
        if self._connection and self._connection.is_connected():
            return self._executor
        return None

    def test_file_transfer(self) -> Dict[str, Any]:
        """Runs the safe file transfer test over the active HPC connection."""
        if not self._connection or not self._connection.is_connected():
            raise ConnectionError("Supercomputer is not connected. Please connect before running the file transfer test.")
        return self._connection.test_file_transfer()

    def test_slurm_job(self, partition: str) -> Dict[str, Any]:
        """Runs the harmless SLURM job test (submit -> monitor -> retrieve output -> verify -> cleanup)."""
        if not self._connection or not self._connection.is_connected():
            raise ConnectionError("Supercomputer is not connected. Please connect before testing a SLURM job.")
        if not self._slurm:
            raise ConnectionError("SLURM manager is not initialized.")
        return self._slurm.test_slurm_job(partition=partition)

    def verify_environment(self, partition: str = "cpu_student") -> Dict[str, Any]:
        """Submits a minimal SLURM job to inspect Python & scientific libraries on the compute node."""
        if not self._connection or not self._connection.is_connected():
            raise ConnectionError("Supercomputer is not connected. Please connect before verifying the environment.")
        if not self._slurm:
            raise ConnectionError("SLURM manager is not initialized.")
        return self._slurm.verify_environment(partition=partition)

    def prepare_experiment_files(self, partition: str = "cpu_student") -> Dict[str, Any]:
        """
        Temporary/inspection helper:
        Packages and uploads the Phase 5.3 synthetic dataset and batch script,
        returning the remote directory path for manual login-node inspection without running sbatch.
        """
        if not self._connection or not self._connection.is_connected():
            raise ConnectionError("Supercomputer is not connected. Please connect first.")

        from sklearn.datasets import make_regression
        import pandas as pd
        import tempfile
        import shutil
        import uuid
        from hpc.packaging import package_experiment

        X, y = make_regression(n_samples=100, n_features=4, n_informative=3, noise=10.0, random_state=42)
        df_synth = pd.DataFrame(X, columns=["feat1", "feat2", "feat3", "feat4"])
        df_synth["target_val"] = y

        config_base = {
            "target": "target_val",
            "target_name": "target_val",
            "target_unit": "units",
            "features": ["feat1", "feat2", "feat3", "feat4"],
            "problem_type": "Regression",
            "model_name": "Random Forest",
            "hyperparameters": {"n_estimators": 10, "random_state": 42},
            "split_method": "Train-Test Split",
            "train_percent": 80,
            "folds": 5,
            "repeats": 1,
            "optimization": "None",
            "use_multiple_seeds": False,
            "use_oob": False,
            "partition": partition,
            "preprocessing": {
                "missing_strategy": "None",
                "encoding_strategy": "None",
                "scaling_strategy": "StandardScaler"
            }
        }

        exp_uuid = uuid.uuid4().hex[:8]
        remote_home = self._connection.get_home_dir()
        remote_exp_dir = f"{remote_home.rstrip('/')}/solvosys_hpc_exp_{exp_uuid}"

        local_temp = tempfile.mkdtemp(prefix="solvosys_pkg_prep_")
        try:
            package_experiment(
                df_synth,
                config_base,
                output_dir=local_temp,
                partition=partition,
                time_limit="00:10:00",
                cpus_per_task=2,
                mem="2G"
            )
            self._connection.upload_dir(local_temp, remote_exp_dir)
        finally:
            shutil.rmtree(local_temp, ignore_errors=True)

        return {
            "status": "prepared",
            "remote_workspace": remote_exp_dir,
            "files": ["dataset.csv", "config.json", "experiment.py", "run.slurm"],
            "partition": partition,
            "cpus_per_task": 2,
            "mem": "2G",
            "time_limit": "00:10:00",
            "message": f"HPC test experiment files successfully uploaded to {remote_exp_dir}. Ready for inspection."
        }


# Global singleton agent instance for Solvosys process
_GLOBAL_HPC_AGENT = LocalHPCAgent()

def get_hpc_agent() -> LocalHPCAgent:
    return _GLOBAL_HPC_AGENT
