"""
Solvosys HPC Subsystem
======================
Clean abstraction layer for Supercomputer (HPC/SLURM) experiment execution.
Provides local mock execution for offline testing and an extensible SSH/SFTP/SLURM layer.
"""

from hpc.connection import HPCConnection, SSHConnection, MockHPCConnection
from hpc.slurm import SlurmExecutor, RealSlurmExecutor, MockSlurmExecutor, SlurmJobState
from hpc.packaging import package_experiment
from hpc.executor import HPCExperimentExecutor
from hpc.agent import LocalHPCAgent, get_hpc_agent

__all__ = [
    "HPCConnection",
    "SSHConnection",
    "MockHPCConnection",
    "SlurmExecutor",
    "RealSlurmExecutor",
    "MockSlurmExecutor",
    "SlurmJobState",
    "package_experiment",
    "HPCExperimentExecutor",
    "LocalHPCAgent",
    "get_hpc_agent",
]
