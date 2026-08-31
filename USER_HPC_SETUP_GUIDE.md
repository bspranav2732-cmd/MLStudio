# SolvoSys HPC User Setup Guide (Windows)

This guide walks you through configuring **SolvoSys** to connect to the **Mahindra University DGX Supercomputer** cluster via SSH and submit machine learning training jobs using SLURM.

---

## 1. Prerequisites

Before connecting SolvoSys to the supercomputer, ensure you have:
1. **A valid Mahindra University HPC account** (e.g., student / faculty credentials).
2. **Access permission** to the university DGX cluster and target SLURM partition (default: `cpu_student`).
3. **Network access** to the cluster login node (`dgxa_login01` / `dgx-login01.mahindrauniversity.edu.in` via campus network or university VPN).
4. **An SSH key pair** generated on your local Windows PC.

---

## 2. Generating an SSH Key Pair on Windows

SolvoSys uses secure **SSH key-based authentication** (`Ed25519`). SolvoSys **never asks for or stores your university account password**.

1. Open **PowerShell** on your Windows computer:
   ```powershell
   ssh-keygen -t ed25519 -C "your_username@mahindrauniversity.edu.in"
   ```
2. When prompted:
   - **File destination**: Press `Enter` to accept the default path (`C:\Users\<username>\.ssh\id_ed25519`).
   - **Passphrase**: Enter a strong passphrase to encrypt your local private key.
3. Your key pair is now created:
   - **Private Key**: `~/.ssh/id_ed25519` (**STRICTLY CONFIDENTIAL** — never share, email, or upload this file).
   - **Public Key**: `~/.ssh/id_ed25519.pub` (This is the key authorized on the cluster).

---

## 3. Understanding the SSH Key Passphrase

- **Local Protection**: The passphrase encrypts your private key on your Windows machine.
- **Not Your Cluster Password**: This passphrase is set by you to protect your local file; it is **not** your university portal/HPC password.
- **In-Memory Only**: When you enter the passphrase in SolvoSys, it is used strictly in-memory by the local SSH agent to unlock the private key for the session. SolvoSys never writes your passphrase to disk or sends it across the network.

---

## 4. Authorizing Your Public Key on the Supercomputer

Your public key (`id_ed25519.pub`) must be registered on your HPC account before you can log in.

### Option A: If Your Account Permits User-Managed SSH Keys
1. View and copy your public key in PowerShell:
   ```powershell
   Get-Content "$HOME\.ssh\id_ed25519.pub"
   ```
2. Connect to the DGX cluster using your terminal:
   ```powershell
   ssh your_username@dgx-login01.mahindrauniversity.edu.in
   ```
3. Append your public key to your `~/.ssh/authorized_keys` file:
   ```bash
   mkdir -p ~/.ssh && chmod 700 ~/.ssh
   echo "PASTE_YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

### Option B: If Your University Requires Administrator-Managed Keys
- Send your **public key file** (`id_ed25519.pub`) to the Mahindra University HPC System Administrator / IT Helpdesk.
- **Never send your private key (`id_ed25519`)**.

---

## 5. First-Time Host Key Verification (`known_hosts`)

When connecting to the DGX cluster for the first time, verify the host fingerprint against official university documentation:
1. Open PowerShell and initiate a test connection:
   ```powershell
   ssh your_username@dgx-login01.mahindrauniversity.edu.in
   ```
2. Check the fingerprint displayed by SSH against the official fingerprint provided by the HPC administrator.
3. Type `yes` to store the host in your local `~/.ssh/known_hosts` file.
4. Verify you can successfully log in and exit:
   ```bash
   exit
   ```

---

## 6. Configuring SolvoSys

In the SolvoSys user interface:
1. Navigate to the **Current Experiment** tab.
2. Under **Execution Mode**, select **Supercomputer**.
3. Fill in your connection details:
   - **Host**: `dgx-login01.mahindrauniversity.edu.in` (or your assigned login node)
   - **Username**: Your university HPC username
   - **Port**: `22`
   - **SSH Key Passphrase**: The passphrase protecting your local `id_ed25519` key.
4. Click **Connect**.
5. Once connected, the interface displays:
   - **Host**: `dgx-login01.mahindrauniversity.edu.in`
   - **Login Node**: `dgx-login01`
   - **Authentication**: `SSH Key`
   - **SLURM Partition**: `cpu_student` (default)

---

## 7. Running a Supercomputer Experiment

1. **Upload Dataset**: Drag and drop your dataset CSV.
2. **Configure Experiment**: Select Target column, Features, Algorithm (e.g., Random Forest), and Hyperparameters.
3. **Execution Mode**: Select **Supercomputer**.
4. **SLURM Partition**: Verify `cpu_student` is selected (or enter your assigned partition).
5. **Click Train Model**:
   - SolvoSys automatically bundles your dataset and experiment script.
   - Uploads the package to your temporary workspace on the cluster (`~/solvosys_hpc_exp_<uuid>/`).
   - Submits a batch job via SLURM `sbatch`.
   - Displays real-time progress and SLURM Job ID.
   - Downloads evaluation metrics and predictions upon completion.
   - Safely cleans up the temporary workspace directory on the cluster.

---

## 8. SLURM Job Status Explanations

| Status Banner | Meaning |
| :--- | :--- |
| **Packaging** | Local dataset preparation and SLURM batch script generation. |
| **Uploading** | Securely transferring files to your cluster directory via SFTP. |
| **Submitting** | Dispatching the job to the SLURM scheduler (`sbatch`). |
| **Job Queued (`PENDING`)** | The job is waiting in the partition queue for an available compute node. |
| **Running on compute node (`RUNNING`)** | The compute node (e.g. `dgxa`) is actively executing model training. |
| **Downloading** | Training finished; SolvoSys is retrieving `results.json` from the cluster. |
| **Completed** | Results are loaded into SolvoSys with full metrics, residual plots, and export capabilities. |
| **Cancelled** | The job was stopped by the user via the `STOP TRAINING` button. |
| **Timeout (`TIMEOUT`)** | The job exceeded the maximum walltime limit (default: 10 minutes). |
| **Out of Memory (`OUT_OF_MEMORY`)** | The job exceeded its RAM limit (default: 2 GB). |

---

## 9. Troubleshooting & FAQ

### "Host key verification failed"
- **Cause**: The cluster host key is missing from `~/.ssh/known_hosts` or changed.
- **Fix**: Connect once via PowerShell (`ssh your_username@dgx-login01.mahindrauniversity.edu.in`) and confirm the host key fingerprint.

### "Authentication failed / Permission denied (publickey)"
- **Cause**: Your public key is not registered in `~/.ssh/authorized_keys` on the DGX, or your username is incorrect.
- **Fix**: Ensure your public key (`id_ed25519.pub`) is authorized by the HPC administrator or placed in `~/.ssh/authorized_keys`.

### "Incorrect key passphrase"
- **Cause**: The passphrase entered in SolvoSys does not match the passphrase used when creating your local SSH key.
- **Fix**: Re-enter your local private key passphrase. If forgotten, generate a new key pair using `ssh-keygen -t ed25519`.

### "Job remains Queued for a long time"
- **Cause**: High cluster utilization on the selected partition.
- **Fix**: The job will automatically execute as soon as a node frees up. You can safely let it wait or click **STOP TRAINING** to cancel.

### "SLURM error: invalid partition specified"
- **Cause**: You entered a partition name that does not exist or that your account cannot access.
- **Fix**: Check with your administrator and ensure `cpu_student` (lowercase) is entered.

### "Python / Package unavailable on compute node"
- **Cause**: The compute node's Python environment lacks a specific optional library (e.g., XGBoost / CatBoost).
- **Fix**: Use verified built-in models (such as Random Forest, Linear Regression, Decision Trees) supported by the cluster's base Scikit-learn environment.
