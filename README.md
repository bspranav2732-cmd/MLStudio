# SolvoSys — Machine Learning Research Workbench

SolvoSys is an end-to-end Machine Learning research and experimentation platform designed for tabular datasets. It provides intuitive model configuration, robust automated preprocessing, hyperparameter optimization, model comparison, residual analysis, and seamless execution on both **local workstations** and **remote Supercomputer / HPC clusters (SLURM)**.

---

## Architecture Overview

```
                          +-------------------------+
                          |      User / Browser     |
                          +-------------------------+
                                       |
                                       v
                          +-------------------------+
                          |    SolvoSys Frontend    | (Next.js 14, React, Tailwind)
                          |  http://localhost:3000  |
                          +-------------------------+
                                       |
                                       v REST API
                          +-------------------------+
                          |     FastAPI Backend     | (Uvicorn, Python 3.10+)
                          |  http://127.0.0.1:8000  |
                          +-------------------------+
                                  /         \
            [Local Mode]         /           \  [Supercomputer Mode]
                                v             v
        +-------------------------+     +-------------------------+
        |  Local Multi-Core Engine|     |  SSH Key Authentication |
        |  (Scikit-learn, Pandas) |     +-------------------------+
        +-------------------------+                   |
                                                      v
                                        +-------------------------+
                                        |     DGX Login Node      | (SFTP Package Transfer)
                                        +-------------------------+
                                                      |
                                                      v sbatch
                                        +-------------------------+
                                        |     SLURM Scheduler     | (Partition: cpu_student)
                                        +-------------------------+
                                                      |
                                                      v
                                        +-------------------------+
                                        |    Compute Node (dgxa)  |
                                        |  (Non-blocking batch)   |
                                        +-------------------------+
                                                      |
                                                      v results.json (SFTP download)
                                        +-------------------------+
                                        |   SolvoSys Evaluation   |
                                        +-------------------------+
```

---

## Core Features

- **Dataset Ingestion & Inspection**: CSV upload, automated datatype inference, missing value detection, summary statistics, and target/feature selection.
- **Automated Preprocessing**: Imputation strategies (Mean, Median, Constant, Drop), Categorical Encoding (One-Hot, Ordinal), and Feature Scaling (StandardScaler, MinMaxScaler, RobustScaler).
- **Tabular ML Algorithms**: Random Forest, Linear / Logistic Regression, Decision Trees, SVR / SVC, Ridge, Lasso, ElasticNet, and optional gradient boosted trees (local).
- **Hyperparameter Optimization**: Grid Search and Randomized Search with cross-validation and best-parameter telemetry.
- **Evaluation & Diagnostics**: Metrics calculation ($R^2$, RMSE, MAE, MAPE, Accuracy, F1, ROC-AUC), interactive residual distribution plots, actual vs predicted analysis, and feature importances.
- **Model Comparison Workbench**: Side-by-side leaderboard across multiple runs, tracking train/test $R^2$, training times, execution mode badges (`Local` vs `HPC`), and artifact exports.
- **Supercomputer (HPC) Execution**:
  - Encrypted SSH key authentication (Ed25519 / RSA) with transient in-memory passphrase handling.
  - Automated experiment packaging (`dataset.csv`, `config.json`, `experiment.py`, `run.slurm`).
  - SFTP package transfer and non-privileged `sbatch` job dispatch.
  - Real-time SLURM lifecycle tracking (`PENDING` -> `RUNNING` -> `COMPLETED`).
  - Automated result retrieval and guaranteed workspace cleanup post-execution.

---

## Local Development & Setup

### Prerequisites
- **Python**: Version 3.10 or higher.
- **Node.js**: Version 18.x or higher (with `npm`).
- **Operating System**: Windows, macOS, or Linux.

### 1. Backend Installation & Startup
Open a terminal in the project directory:

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI server on localhost:8000
python -m uvicorn server:app --host 127.0.0.1 --port 8000
```

### 2. Frontend Installation & Startup
In a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server on localhost:3000
npm run dev
```

### 3. One-Click Unified Launcher (Windows)
Alternatively, start both backend and frontend together using the included launcher:
```powershell
python start_solvosys.py
```
*(Or double-click `start_solvosys.bat`)*

---

## Supercomputer (HPC) Documentation

For full guides, administrator references, security audits, and operational boundaries:

- **[User HPC Setup Guide](USER_HPC_SETUP_GUIDE.md)**: Step-by-step instructions for Windows users, PowerShell Ed25519 key generation, passphrase security, public key registration, host verification, and troubleshooting.
- **[HPC Administrator One-Pager](HPC_ADMIN_ONE_PAGER.md)**: Architectural summary, authentication model, minimal SFTP operations, tested SLURM directives, live verification results on Mahindra DGX, and governance questions for cluster operators.
- **[Current HPC Limitations](HPC_LIMITATIONS.md)**: Supported single-node CPU boundaries, compute-node package availability, memory ceilings, and institutional policy dependencies.
- **[Security & Deployment Checklist](HPC_SECURITY_CHECKLIST.md)**: Client-side private key retention, credential ephemerality, anonymous workspace naming, loopback localhost binding, sanitized error messages, and orphan job prevention.

---

## Default HPC Resource Constraints (Tested)

```bash
#SBATCH --job-name=solvosys_ml
#SBATCH --partition=cpu_student
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=00:10:00
```

---

## Security Policy

- **No Passwords Stored**: SolvoSys exclusively uses public key authentication and never requests or stores your HPC account password.
- **Local Private Keys**: Private key files (`~/.ssh/id_ed25519`) remain on your local computer and are never transmitted over APIs or uploaded to clusters.
- **Transient Passphrases**: Passphrases decrypt keys in-memory for the active session and are never written to disk or logged.
- **Clean Disconnection**: Workspaces on the cluster are isolated under `~/solvosys_hpc_exp_<uuid>/` and removed upon job completion.

---

## License

Developed for Machine Learning research and experimentation at Mahindra University.
