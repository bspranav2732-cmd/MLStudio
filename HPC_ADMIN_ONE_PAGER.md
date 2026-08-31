# SolvoSys — HPC / Supercomputer Integration (Administrator One-Pager)

**Target Audience**: Mahindra University High Performance Computing (HPC) / DGX System Administrators  
**Application**: SolvoSys Machine Learning Research Workbench  
**Contact / User**: Mahindra University Student / Faculty Researcher  

---

## 1. Architecture Overview

SolvoSys connects from a user's Windows workstation to the Mahindra University DGX login node over SSH/SFTP to submit and monitor standard batch ML training jobs via the SLURM workload manager.

```
+---------------------------+
|  Windows SolvoSys Client  |
+---------------------------+
              |
              | 1. SSH / SFTP (SSH Key Authentication)
              v
+---------------------------+
|      DGX Login Node       | (e.g. dgx-login01)
+---------------------------+
              |
              | 2. sbatch run.slurm
              v
+---------------------------+
|      SLURM Scheduler      | (Partition: cpu_student)
+---------------------------+
              |
              | 3. Dispatches batch job
              v
+---------------------------+
|    Compute Node (dgxa)    |
| - Runs Python ML Training | (Scikit-learn, Pandas, NumPy)
| - Writes results.json     |
+---------------------------+
              |
              | 4. Status Polling (2-3s) & SFTP Download
              v
+---------------------------+
|  SolvoSys Client Results  |
+---------------------------+
              |
              | 5. rm -rf ~/solvosys_hpc_exp_<uuid>
              v
   (Cluster Workspace Cleaned)
```

---

## 2. Authentication & Security Model

- **SSH Public Key Authentication**: Authentication relies exclusively on standard Ed25519 / RSA SSH key pairs.
- **Client-Side Key Protection**: The user's private key (`~/.ssh/id_ed25519`) **remains on their local Windows workstation** and is never transmitted or copied.
- **Passphrase Handling**: If the private key is passphrase-encrypted, SolvoSys unlocks the key **transiently in local client memory** for the duration of the session. The passphrase is never stored on disk, never logged, and never transmitted to the cluster.
- **Zero Password Storage**: SolvoSys does not ask for, handle, or store institutional account passwords.

---

## 3. Remote Cluster Operations & Lifecycle

All operations on the cluster are strictly non-privileged user-space actions:

1. **Workspace Creation**: Creates an isolated per-experiment directory in the user's home directory: `~/solvosys_hpc_exp_<uuid>/`.
2. **Minimal SFTP Upload**: Uploads only four lightweight experiment artifacts:
   - `dataset.csv` (preprocessed user dataset)
   - `config.json` (model hyperparameters and split metadata)
   - `experiment.py` (standalone Python execution script)
   - `run.slurm` (batch submission script)
3. **Batch Submission**: Submits the job via standard non-interactive SLURM command: `sbatch run.slurm`.
4. **Cluster-Friendly Monitoring**: Polls job status using standard `squeue` / `sacct` commands on a conservative adaptive interval (**3.0s** while queued, **2.0s** while running). Polling halts immediately once the job reaches a terminal state.
5. **Result Retrieval**: Downloads `results.json` upon verified job completion.
6. **Guaranteed Workspace Cleanup**: Executes `rm -rf ~/solvosys_hpc_exp_<uuid>/` **only after** the SLURM job reaches a terminal state (`COMPLETED`, `FAILED`, `CANCELLED`). Workspaces are never deleted while jobs are pending or running.

---

## 4. Current Tested SLURM Directives (Conservative Defaults)

```bash
#!/bin/bash
#SBATCH --job-name=solvosys_ml
#SBATCH --partition=cpu_student
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --output=job.out
#SBATCH --error=job.err

python3 experiment.py
```

> **Note**: These directives represent conservative, small-footprint test defaults intended for minimal scheduler impact and are submitted for your formal review and adjustment.

---

## 5. Verification on Mahindra DGX Cluster

The integration was verified on the live Mahindra University DGX environment:
- **SLURM Job ID**: `22447`
- **Partition**: `cpu_student`
- **Allocated Node**: `dgxa`
- **Resources**: 2 CPUs, 2 GB Memory, 10 min time limit
- **Job Duration**: 00:00:02
- **ExitCode**: `0:0` (COMPLETED)
- **Model Trained**: Scikit-learn `RandomForestRegressor`
- **Workspace Cleanup**: Verified clean post-execution.

---

## 6. Questions & Approvals Requested from HPC Administration

To ensure full compliance with Mahindra University HPC security and operational policies, we request administrator feedback and guidance on the following points:

| Area | Question for Administrator | Current Tested Setting |
| :--- | :--- | :--- |
| **Approved Partitions** | Which partitions should student and faculty ML jobs be directed to? | `cpu_student` |
| **Resource Quotas** | What are the recommended standard limits for `--cpus-per-task`, `--mem`, and `--time`? | 2 CPUs, 2 GB RAM, 10 min |
| **Application Submissions** | Are automated/application-driven `sbatch` submissions permissible under standard user accounts? | Standard user `sbatch` |
| **SSH Key Management** | Does the university support user-managed `~/.ssh/authorized_keys` or administrator-provisioned keys? | User-managed `~/.ssh/authorized_keys` |
| **Python Environment** | Is there a preferred module (e.g. `module load python/3.10`), conda environment, or Singularity/Apptainer container? | System `python3` (3.10.12) |
| **GPU Partitions** | What is the policy/procedure for requesting GPU-accelerated partitions (e.g. NVIDIA A100 / H100) for deep learning? | Not currently requested (CPU only) |
| **Scratch Space** | Should temporary job directories be placed in user home (`~/`) or a designated cluster scratch filesystem (e.g. `/scratch/$USER/`)? | User home directory (`~/`) |
| **Job Polling Policy** | Is our adaptive 2.0s–3.0s `squeue` polling rate acceptable, or is a different interval required? | 2.0s – 3.0s |
| **Directory Cleanup** | Is our post-execution workspace cleanup policy (`rm -rf ~/solvosys_hpc_exp_<uuid>`) aligned with cluster hygiene guidelines? | Automated post-job cleanup |

---

*Thank you for supporting research computing at Mahindra University.*
