# SolvoSys — Current HPC Limitations & Operational Boundaries

This document outlines the current operational boundaries, supported configurations, and known limitations of the SolvoSys Supercomputer (HPC) execution mode.

---

## 1. Compute & Resource Limits

- **CPU-Only Execution**: The verified HPC pipeline currently runs on CPU-based compute nodes (e.g. `dgxa` on the `cpu_student` partition).
- **Conservative Default Allocation**:
  - **CPUs**: 2 (`#SBATCH --cpus-per-task=2`)
  - **Memory**: 2 GB (`#SBATCH --mem=2G`)
  - **Time Limit**: 10 minutes (`#SBATCH --time=00:10:00`)
- **Single-Node Execution**: Jobs currently execute within a single compute node (`#SBATCH --nodes=1 --ntasks=1`). Distributed multi-node training (e.g., MPI / Ray / Dask) is not currently implemented.

---

## 2. Hardware Acceleration (GPU)

- **GPU Acceleration Unvalidated**: GPU partitions (e.g. NVIDIA A100 / H100) and CUDA-accelerated model training have **not** been validated on the cluster.
- **No GPU Directives**: SolvoSys does not currently request `#SBATCH --gres=gpu:...` or submit to GPU-designated partitions.

---

## 3. Compute-Node Python Environment & Model Support

Environment inspection on compute node `dgxa` confirmed the following package availability:

| Package | Compute Node Version | SolvoSys HPC Support |
| :--- | :--- | :--- |
| **Python** | 3.10.12 | Supported |
| **Scikit-learn** | 1.7.2 | **Full Support** (Random Forest, Linear Models, Decision Trees, SVR, etc.) |
| **NumPy** | 1.26.4 | Supported |
| **Pandas** | 2.3.3 | Supported |
| **XGBoost** | *Not Installed* | **Not Supported on HPC** (Local execution only) |
| **CatBoost** | *Not Installed* | **Not Supported on HPC** (Local execution only) |

> **Important**: Do not attempt to run XGBoost or CatBoost models on the Supercomputer until the university HPC administrator provides a Python module, conda environment, or container containing those libraries.

---

## 4. Dataset & Optimization Scope

- **Dataset Size**: Datasets up to typical tabular ML sizes (~hundreds of MBs / hundreds of thousands of rows) fit comfortably within the 2 GB memory ceiling. Multi-gigabyte datasets will trigger an `OUT_OF_MEMORY` SLURM termination unless higher memory limits are authorized by the HPC administrator.
- **Hyperparameter Tuning**: Extensive grid or random searches with large iteration counts may exceed the 10-minute walltime limit, triggering a `TIMEOUT` termination.

---

## 5. Institutional & Cluster Policies

- **Queue Waiting Times**: Job scheduling latency depends on cluster load and queue priority within the `cpu_student` partition. SolvoSys does not control SLURM queue wait times.
- **Administrative Permissions**: All HPC operations are subject to university IT and HPC administrator policies regarding allowed partitions, storage quotas, and SSH access rules.
