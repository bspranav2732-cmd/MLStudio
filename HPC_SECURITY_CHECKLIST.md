# SolvoSys — HPC Security & Deployment Readiness Checklist

This document details the security safeguards, credential handling policies, and deployment verifications implemented in the SolvoSys Supercomputer (HPC) module.

---

## 1. Security & Credential Handling

| Check | Requirement | Status | Verification Detail |
| :--- | :--- | :---: | :--- |
| **Private Key Protection** | Private keys must remain on the user's local workstation. | **PASS** | Private key files (`~/.ssh/id_ed25519`) are never transmitted via API, never uploaded to the cluster, and never copied. |
| **Passphrase Ephemerality** | SSH passphrases must not be logged or persisted to disk. | **PASS** | Passphrases are held in-memory only for key decryption in Paramiko and are never logged, printed, or saved in configuration files. |
| **Zero Password Storage** | Institutional account passwords must never be stored. | **PASS** | SolvoSys exclusively uses public key authentication (`Ed25519` / `RSA`) and never prompts for or stores HPC account passwords. |
| **No Secrets in Bundles** | Upload packages must contain zero credentials. | **PASS** | Experiment packages contain only `dataset.csv`, `config.json`, `experiment.py`, and `run.slurm`. No keys, tokens, or environment secrets are included. |
| **Anonymous Workspace Naming** | Remote directories must not expose usernames or credentials. | **PASS** | Remote workspace directories use randomized UUIDs: `~/solvosys_hpc_exp_<uuid>/`. |
| **Host Verification Integrity** | Host key validation must prevent MITM attacks. | **PASS** | Paramiko uses the user's local `~/.ssh/known_hosts` file and checks host key authenticity before establishing sessions. |

---

## 2. Server & Deployment Architecture

| Check | Requirement | Status | Verification Detail |
| :--- | :--- | :---: | :--- |
| **Localhost Binding** | Backend must bind strictly to loopback interface. | **PASS** | FastAPI server binds exclusively to `127.0.0.1:8000` (`uvicorn.run(app, host="127.0.0.1", port=8000)`), preventing unauthorized remote network access. |
| **UI Workflow Decoupling** | Developer diagnostics must not clutter standard UI. | **PASS** | Testing and diagnostic buttons (*Test File Transfer*, *Test SLURM*, *Verify Env*, *Benchmark*) are sequestered inside an expandable `<StExpander title="🛠️ Advanced / HPC Diagnostics">`. |
| **Error Sanitization** | Exceptions must not leak stack traces or internal paths. | **PASS** | Frontend displays friendly, sanitized alerts (e.g. *"The HPC job exceeded its allocated memory limit (2 GB)"*) without raw stack traces. |

---

## 3. Remote Cluster Hygiene & Resource Safety

| Check | Requirement | Status | Verification Detail |
| :--- | :--- | :---: | :--- |
| **Workspace Lifecycle Safety** | Remote directories must never be deleted while jobs run. | **PASS** | `HPCExperimentExecutor` strictly verifies `SlurmJobState.is_terminal(state)`. The remote workspace remains completely intact throughout `PENDING`, `CONFIGURING`, and `RUNNING` states. |
| **Guaranteed Cleanup** | Remote directories must be removed after job termination. | **PASS** | A non-blocking `rm -rf ~/solvosys_hpc_exp_<uuid>/` is executed via SSH immediately after downloading results for terminal jobs (`COMPLETED`, `FAILED`, `CANCELLED`). |
| **Orphan Job Prevention** | User cancellations must terminate running remote jobs. | **PASS** | Clicking `STOP TRAINING` triggers `scancel <slurm_job_id>` immediately over SSH, ensuring no orphan jobs remain on compute nodes. |
| **Adaptive Polling Cadence** | Scheduler inquiries must not overload cluster control daemon. | **PASS** | Backend polls `squeue` on an adaptive schedule (3.0s while queued, 2.0s while running) and terminates polling immediately upon terminal state. |
| **Conservative Allocations** | Default resource requests must respect cluster etiquette. | **PASS** | Fixed defaults: `--cpus-per-task=2`, `--mem=2G`, `--time=00:10:00`, `--partition=cpu_student`. |
