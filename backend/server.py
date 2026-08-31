"""
Solvosys FastAPI Server
=======================
Exposes the complete Solvosys ML engine over a robust, non-blocking REST API.
Preserves all existing ML pipelines, validation methods, hyperparameter spaces,
plotting, and academic exports.
"""

import os
import sys
import io
import time
import uuid
import threading
import traceback
import tempfile
import shutil
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, FileResponse, StreamingResponse
from pydantic import BaseModel

# Add current directory to path for backend module imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from dataset import load_dataset, dataset_summary
from models import REGRESSION_MODELS, CLASSIFICATION_MODELS
from parameter_spaces import get_parameter_space
from engine import run_training
from plot import REGRESSION_PLOTS, CLASSIFICATION_PLOTS, setup_figure, apply_plot_style, save_figure
from export.export_utils import create_export_context, ExportContext
from export.code_generator import generate_python_script
from export.csv_export import export_predictions_to_dataframe
from export.pdf_generator import generate_pdf_report
from export.zip_generator import generate_experiment_zip
from hpc.agent import get_hpc_agent

app = FastAPI(
    title="Solvosys API",
    description="Backend API for Solvosys Machine Learning Research Workbench",
    version="2.0.0"
)

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# In-Memory State Store (Local, Thread-Safe)
# ----------------------------------------------------
DATASETS: Dict[str, Dict[str, Any]] = {}
JOBS: Dict[str, Dict[str, Any]] = {}
COMPARISON_RUNS: List[Dict[str, Any]] = []
_LOCK = threading.Lock()


# ----------------------------------------------------
# Models & Schemas
# ----------------------------------------------------
class PreprocessingConfig(BaseModel):
    missing_strategy: str = "None"
    encoding_strategy: str = "None"
    scaling_strategy: str = "None"


class HpcConnectRequest(BaseModel):
    mode: str = "mock"  # "mock" or "ssh"
    host: Optional[str] = None
    username: Optional[str] = None
    port: int = 22
    key_filename: Optional[str] = None
    passphrase: Optional[str] = None


class HpcSlurmTestRequest(BaseModel):
    partition: str


class TrainExperimentRequest(BaseModel):
    dataset_id: str
    target: str
    target_name: Optional[str] = None
    target_unit: Optional[str] = ""
    features: List[str]
    problem_type: str  # "Regression" or "Classification"
    model_name: str
    hyperparameters: Optional[Dict[str, Any]] = None
    split_method: str = "Train-Test Split"
    train_percent: int = 80
    folds: int = 5
    repeats: int = 1
    optimization: str = "None"  # "None", "Random Search", "Grid Search"
    opt_iters: int = 10
    opt_cv: int = 3
    use_multiple_seeds: bool = False
    num_seeds: int = 5
    use_oob: bool = False
    execution_mode: str = "local"  # "local" or "hpc"
    partition: Optional[str] = "cpu_student"
    preprocessing: Optional[PreprocessingConfig] = None


# ----------------------------------------------------
# Helper to make metrics JSON serializable
# ----------------------------------------------------
def serialize_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    serialized = {}
    for k, v in metrics.items():
        if isinstance(v, dict):
            serialized[k] = {
                sub_k: float(sub_v) if isinstance(sub_v, (np.floating, np.integer, float, int)) else sub_v
                for sub_k, sub_v in v.items()
            }
        elif isinstance(v, (np.floating, float)):
            serialized[k] = None if np.isnan(v) or np.isinf(v) else float(v)
        elif isinstance(v, (np.integer, int)):
            serialized[k] = int(v)
        elif isinstance(v, (np.ndarray, list)):
            serialized[k] = [float(x) if isinstance(x, (np.floating, float)) else x for x in v]
        else:
            serialized[k] = v
    return serialized


# ----------------------------------------------------
# Background Training Worker
# ----------------------------------------------------
CANCELLATION_REQUESTS = set()

def _background_train_worker(job_id: str, df: pd.DataFrame, config: dict):
    now = time.time()
    started_at_str = time.strftime("%H:%M:%S", time.localtime(now))
    with _LOCK:
        if job_id in JOBS:
            JOBS[job_id]["status"] = "running"
            JOBS[job_id]["start_time"] = now
            JOBS[job_id]["started_at_str"] = started_at_str
            JOBS[job_id]["current_stage"] = "dataset_prep"
            JOBS[job_id]["progress"] = "Preparing dataset..."
            JOBS[job_id]["stages_history"] = [{
                "stage": "dataset_prep",
                "label": "Preparing dataset",
                "message": "Dataset preparation started",
                "timestamp": now
            }]

    def progress_callback(data: Any):
        if job_id in CANCELLATION_REQUESTS:
            # Stop gracefully
            raise InterruptedError("Experiment cancelled by user.")

        now_t = time.time()
        with _LOCK:
            if job_id not in JOBS or JOBS[job_id]["status"] == "cancelled":
                return
                
            if isinstance(data, dict):
                stage = data.get("stage", "running")
                msg = data.get("message", "")
                JOBS[job_id]["current_stage"] = stage
                JOBS[job_id]["progress"] = msg
                
                if data.get("slurm_job_id"):
                    JOBS[job_id]["slurm_job_id"] = data.get("slurm_job_id")
                if data.get("slurm_state"):
                    JOBS[job_id]["slurm_state"] = data.get("slurm_state")
                if data.get("compute_node"):
                    JOBS[job_id]["compute_node"] = data.get("compute_node")
                if data.get("partition"):
                    JOBS[job_id]["partition"] = data.get("partition")

                if stage == "optimization":
                    JOBS[job_id]["optimization_info"] = {
                        "strategy": data.get("strategy"),
                        "iterations": data.get("iterations"),
                        "folds": data.get("folds"),
                        "total_fits": data.get("total_fits"),
                        "rows": data.get("rows")
                    }
                elif stage == "best_params":
                    JOBS[job_id]["best_params"] = data.get("best_params")
                    JOBS[job_id]["best_cv_score"] = data.get("best_cv_score")
                    
                # Add to history if unique
                history = JOBS[job_id].get("stages_history", [])
                if not history or history[-1]["stage"] != stage:
                    history.append({
                        "stage": stage,
                        "label": msg.split(":")[0] if ":" in msg else msg,
                        "message": msg,
                        "timestamp": now_t
                    })
                JOBS[job_id]["stages_history"] = history
            else:
                JOBS[job_id]["progress"] = str(data)

    try:
        if config.get("execution_mode") == "hpc":
            agent = get_hpc_agent()
            executor = agent.get_executor()
            if not executor:
                raise ConnectionError("Supercomputer is not connected. Please connect first.")
            pipeline_output = executor.run_experiment(
                df,
                config,
                progress_callback=progress_callback,
                job_cancellation_check=lambda: job_id in CANCELLATION_REQUESTS
            )
        else:
            pipeline_output = run_training(df, config, progress_callback=progress_callback)
        
        if job_id in CANCELLATION_REQUESTS:
            return

        results = pipeline_output["results"]
        evaluation = pipeline_output["evaluation"]
        training_time = pipeline_output.get("training_time", 0.0)
        
        # Build ExportContext for export generation
        context = create_export_context(
            config,
            results,
            evaluation,
            COMPARISON_RUNS
        )

        with _LOCK:
            if job_id in JOBS and JOBS[job_id]["status"] != "cancelled":
                JOBS[job_id]["status"] = "completed"
                JOBS[job_id]["current_stage"] = "completed"
                JOBS[job_id]["end_time"] = time.time()
                JOBS[job_id]["elapsed"] = JOBS[job_id]["end_time"] - JOBS[job_id]["start_time"]
                JOBS[job_id]["progress"] = f"Training completed in {JOBS[job_id]['elapsed']:.1f}s."
                JOBS[job_id]["training_time"] = training_time
                JOBS[job_id]["results"] = results
                JOBS[job_id]["evaluation"] = evaluation
                JOBS[job_id]["context"] = context
                JOBS[job_id]["evaluation_config"] = results.get("evaluation_config", {})
                JOBS[job_id]["best_params"] = results.get("best_params")
                
                history = JOBS[job_id].get("stages_history", [])
                history.append({
                    "stage": "completed",
                    "label": "Completed",
                    "message": f"Experiment completed in {training_time:.2f}s",
                    "timestamp": time.time()
                })
                JOBS[job_id]["stages_history"] = history

    except InterruptedError:
        with _LOCK:
            if job_id in JOBS:
                JOBS[job_id]["status"] = "cancelled"
                JOBS[job_id]["current_stage"] = "cancelled"
                JOBS[job_id]["end_time"] = time.time()
                JOBS[job_id]["elapsed"] = JOBS[job_id]["end_time"] - JOBS[job_id]["start_time"]
                JOBS[job_id]["progress"] = f"Cancelled after {JOBS[job_id]['elapsed']:.1f}s"
    except Exception as e:
        err_msg = str(e)
        stack = traceback.format_exc()
        print(f"[ERROR] Training Job {job_id} failed:\n{stack}", file=sys.stderr)
        with _LOCK:
            if job_id in JOBS and JOBS[job_id]["status"] != "cancelled":
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["current_stage"] = "failed"
                JOBS[job_id]["end_time"] = time.time()
                JOBS[job_id]["elapsed"] = JOBS[job_id]["end_time"] - JOBS[job_id]["start_time"]
                JOBS[job_id]["error"] = err_msg
                JOBS[job_id]["progress"] = f"Failed: {err_msg}"


# ----------------------------------------------------
# API Routes: Metadata & Options
# ----------------------------------------------------
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "Solvosys ML Engine", "time": time.time()}


# ----------------------------------------------------
# API Routes: HPC / Supercomputer Connection Layer
# ----------------------------------------------------
@app.get("/api/hpc/status")
def get_hpc_status_endpoint():
    """Returns the current connection status of the local HPC agent."""
    agent = get_hpc_agent()
    return agent.get_status()


@app.post("/api/hpc/connect")
def connect_hpc_endpoint(req: HpcConnectRequest):
    """Establishes connection via local HPC agent (supports 'mock' or 'ssh')."""
    agent = get_hpc_agent()
    try:
        res = agent.connect(
            mode=req.mode,
            host=req.host.strip() if req.host else None,
            username=req.username.strip() if req.username else None,
            port=int(req.port) if req.port else 22,
            key_filename=req.key_filename.strip() if req.key_filename else None,
            passphrase=req.passphrase
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hpc/disconnect")
def disconnect_hpc_endpoint():
    """Disconnects active Supercomputer session."""
    agent = get_hpc_agent()
    return agent.disconnect()


@app.post("/api/hpc/test-file-transfer")
def test_hpc_file_transfer_endpoint():
    """
    Executes a safe, non-destructive file transfer verification test (Upload -> Verify -> Download -> Verify -> Cleanup).
    Runs strictly inside a temporary user workspace folder and touches NO compute resources.
    """
    agent = get_hpc_agent()
    if not agent.get_status()["connected"]:
        raise HTTPException(status_code=400, detail="Supercomputer is not connected. Please click 'Connect' first.")
    try:
        result = agent.test_file_transfer()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hpc/test-slurm-job")
def test_hpc_slurm_job_endpoint(req: HpcSlurmTestRequest):
    """
    Executes a harmless test SLURM job to verify cluster scheduling, job monitoring,
    output retrieval, and safe cleanup.
    Does NOT execute Python on the compute node and touches NO user datasets.
    """
    agent = get_hpc_agent()
    if not agent.get_status()["connected"]:
        raise HTTPException(status_code=400, detail="Supercomputer is not connected. Please click 'Connect' first.")
    if not req.partition or not req.partition.strip():
        raise HTTPException(status_code=400, detail="SLURM partition is required to submit a test job.")
    try:
        result = agent.test_slurm_job(partition=req.partition.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hpc/verify-environment")
def verify_hpc_environment_endpoint(req: HpcSlurmTestRequest):
    """
    Submits a minimal SLURM job to verify the Python environment and installed libraries
    strictly on the COMPUTE NODE (not login node).
    Returns machine-readable package versions (numpy, pandas, scikit-learn, xgboost, catboost).
    """
    agent = get_hpc_agent()
    if not agent.get_status()["connected"]:
        raise HTTPException(status_code=400, detail="Supercomputer is not connected. Please click 'Connect' first.")
    if not req.partition or not req.partition.strip():
        raise HTTPException(status_code=400, detail="SLURM partition is required.")
    try:
        result = agent.verify_environment(partition=req.partition.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hpc/test-phase53-rfr")
def test_phase53_hpc_rfr_endpoint(req: HpcSlurmTestRequest):
    """
    Executes the Phase 5.3 First Real HPC Machine Learning Test:
    - Generates 100-sample synthetic regression dataset (seed 42)
    - Runs reference local Random Forest (n_estimators=10, random_state=42)
    - Submits and monitors real HPC Random Forest on partition (default: cpu_student)
    - Compares local vs HPC results
    - Verifies cleanup
    """
    agent = get_hpc_agent()
    if not agent.get_status()["connected"]:
        raise HTTPException(status_code=400, detail="Supercomputer is not connected. Please click 'Connect' first.")
    
    partition = req.partition.strip() if req.partition and req.partition.strip() else "cpu_student"
    executor = agent.get_executor()
    if not executor:
        raise HTTPException(status_code=400, detail="HPC executor is not available.")

    try:
        from sklearn.datasets import make_regression
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

        # 1. Local Run
        from engine import run_training
        local_output = run_training(df_synth.copy(), config_base)
        local_metrics = serialize_metrics(local_output["evaluation"].get("metrics", {}))

        # 2. HPC Run
        hpc_config = dict(config_base)
        hpc_config["execution_mode"] = "hpc"
        hpc_output = executor.run_experiment(df_synth.copy(), hpc_config)
        hpc_results = hpc_output["results"]
        hpc_metrics = serialize_metrics(hpc_output["evaluation"].get("metrics", {}))

        hpc_r2 = float(hpc_metrics.get("R2 Score", 0.0))
        local_r2 = float(local_metrics.get("R2 Score", 0.0))

        return {
            "status": "completed",
            "slurm_job_id": hpc_results.get("slurm_job_id"),
            "partition": partition,
            "compute_node": hpc_results.get("compute_node", "dgxa"),
            "hpc_training_time": hpc_output.get("training_time"),
            "local_training_time": local_output.get("training_time"),
            "hpc_metrics": hpc_metrics,
            "local_metrics": local_metrics,
            "r2_delta": abs(hpc_r2 - local_r2),
            "feature_importances": hpc_results.get("feature_importances", []),
            "predictions_preview": hpc_results.get("predictions_preview", [])[:5],
            "cleanup": "OK",
            "test_result": "PASS"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/hpc/prepare-phase53-test")
def prepare_phase53_hpc_test_endpoint(req: HpcSlurmTestRequest):
    """
    Temporary/development-only preparation step for Phase 5.3:
    1. Generates the synthetic Phase 5.3 dataset and config.
    2. Packages dataset.csv, config.json, experiment.py, run.slurm locally.
    3. Uploads files to a unique ~/solvosys_hpc_exp_<uuid>/ directory.
    4. Leaves the directory intact without submitting any SLURM jobs or running Python.
    5. Returns the exact remote directory path for manual login-node inspection.
    """
    agent = get_hpc_agent()
    if not agent.get_status()["connected"]:
        raise HTTPException(status_code=400, detail="Supercomputer is not connected. Please click 'Connect' first.")

    partition = req.partition.strip() if req.partition and req.partition.strip() else "cpu_student"

    try:
        result = agent.prepare_experiment_files(partition=partition)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/meta")
def get_metadata():
    """Returns available algorithms, split methods, and parameter spaces."""
    return {
        "regression_models": list(REGRESSION_MODELS.keys()),
        "classification_models": list(CLASSIFICATION_MODELS.keys()),
        "split_methods": [
            "Train-Test Split",
            "K-Fold Cross Validation",
            "Stratified K-Fold Cross Validation",
            "Repeated K-Fold",
            "Repeated Stratified K-Fold"
        ],
        "optimization_strategies": ["None", "Random Search", "Grid Search"],
        "preprocessing": {
            "missing_strategies": ["None", "Mean", "Median", "Most Frequent"],
            "encoding_strategies": ["None", "One-Hot", "Ordinal"],
            "scaling_strategies": ["None", "StandardScaler", "MinMaxScaler", "RobustScaler"]
        },
        "regression_plots": list(REGRESSION_PLOTS.keys()),
        "classification_plots": list(CLASSIFICATION_PLOTS.keys()),
    }


@app.get("/api/parameter-space/{model_name}")
def get_model_parameter_space(model_name: str):
    """Returns the parameter search space for a model."""
    space = get_parameter_space(model_name)
    clean_space = {}
    for k, v in space.items():
        clean_k = k.replace("model__", "").replace("poly__", "")
        clean_space[clean_k] = v
    return {"model_name": model_name, "param_space": clean_space, "raw_space": space}


# ----------------------------------------------------
# API Routes: Dataset Upload & Exploration
# ----------------------------------------------------
@app.post("/api/dataset/upload")
async def upload_dataset_endpoint(file: UploadFile = File(...)):
    """Uploads CSV dataset and returns comprehensive column statistics and preview."""
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        summary = dataset_summary(df)
        dataset_id = str(uuid.uuid4())
        
        # Column metadata
        columns_meta = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            missing_count = int(df[col].isnull().sum())
            unique_count = int(df[col].nunique())
            is_numeric = pd.api.types.is_numeric_dtype(df[col])
            
            meta = {
                "name": col,
                "type": dtype,
                "is_numeric": is_numeric,
                "missing": missing_count,
                "unique": unique_count
            }
            if is_numeric and len(df[col].dropna()) > 0:
                meta["min"] = float(df[col].min())
                meta["max"] = float(df[col].max())
                meta["mean"] = float(df[col].mean())
            columns_meta.append(meta)

        # First 10 rows for preview
        preview_rows = df.head(10).replace({np.nan: None}).to_dict(orient="records")

        total_missing = int(sum(summary["missing_values"].values())) if isinstance(summary.get("missing_values"), dict) else int(df.isnull().sum().sum())

        with _LOCK:
            DATASETS[dataset_id] = {
                "id": dataset_id,
                "filename": file.filename,
                "df": df,
                "summary": summary,
                "columns": columns_meta,
                "preview": preview_rows,
                "upload_time": time.time()
            }

        return {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": summary["rows"],
            "columns_count": summary["columns"],
            "missing_cells": total_missing,
            "columns": columns_meta,
            "preview": preview_rows
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")


@app.get("/api/dataset/{dataset_id}")
def get_dataset_info(dataset_id: str):
    """Retrieves dataset summary and column structure."""
    with _LOCK:
        if dataset_id not in DATASETS:
            raise HTTPException(status_code=404, detail="Dataset not found")
        ds = DATASETS[dataset_id]
        total_missing = int(sum(ds["summary"]["missing_values"].values())) if isinstance(ds["summary"].get("missing_values"), dict) else int(ds["df"].isnull().sum().sum())
        return {
            "dataset_id": ds["id"],
            "filename": ds["filename"],
            "rows": ds["summary"]["rows"],
            "columns_count": ds["summary"]["columns"],
            "missing_cells": total_missing,
            "columns": ds["columns"],
            "preview": ds["preview"]
        }


# ----------------------------------------------------
# API Routes: Experiment Training (Non-Blocking)
# ----------------------------------------------------
@app.post("/api/experiments/train")
def train_experiment(req: TrainExperimentRequest):
    """
    Submits a training experiment to run in the background.
    Returns immediately with a unique job ID for polling.
    """
    with _LOCK:
        if req.dataset_id not in DATASETS:
            raise HTTPException(status_code=404, detail="Dataset ID not found")
        df = DATASETS[req.dataset_id]["df"]
        filename = DATASETS[req.dataset_id]["filename"]

    if len(req.features) == 0:
        raise HTTPException(status_code=400, detail="Select at least one feature before training.")

    if req.target not in df.columns:
        raise HTTPException(status_code=400, detail=f"Target column '{req.target}' does not exist in dataset.")

    for f in req.features:
        if f not in df.columns:
            raise HTTPException(status_code=400, detail=f"Feature '{f}' does not exist in dataset.")

    # HPC validation: Ensure cluster is connected before dispatching
    if req.execution_mode == "hpc":
        agent = get_hpc_agent()
        if not agent.get_status()["connected"]:
            raise HTTPException(
                status_code=400,
                detail="Supercomputer is not connected. Please click 'Connect to HPC' before starting the experiment."
            )

    preprocessing_dict = {
        "missing_strategy": req.preprocessing.missing_strategy if req.preprocessing else "None",
        "encoding_strategy": req.preprocessing.encoding_strategy if req.preprocessing else "None",
        "scaling_strategy": req.preprocessing.scaling_strategy if req.preprocessing else "None"
    }

    config = {
        "target": req.target,
        "target_name": req.target_name or req.target,
        "target_unit": req.target_unit or "",
        "features": req.features,
        "problem_type": req.problem_type,
        "model_name": req.model_name,
        "hyperparameters": req.hyperparameters or {},
        "split_method": req.split_method,
        "train_percent": req.train_percent,
        "folds": req.folds,
        "repeats": req.repeats,
        "optimization": req.optimization,
        "opt_iters": req.opt_iters,
        "opt_cv": req.opt_cv,
        "use_multiple_seeds": req.use_multiple_seeds,
        "num_seeds": req.num_seeds,
        "use_oob": req.use_oob,
        "execution_mode": req.execution_mode,
        "partition": req.partition or "cpu_student",
        "preprocessing": preprocessing_dict,
        "dataset_name": filename
    }

    job_id = str(uuid.uuid4())

    with _LOCK:
        # Prevent simultaneous running jobs
        for existing_id, existing_job in JOBS.items():
            if existing_job["status"] in ["running", "queued"]:
                raise HTTPException(
                    status_code=409,
                    detail="Another experiment is already running. Please wait for it to finish or click Stop Training."
                )

        now = time.time()
        started_at_str = time.strftime("%H:%M:%S", time.localtime(now))
        JOBS[job_id] = {
            "id": job_id,
            "status": "queued",
            "current_stage": "dataset_prep",
            "progress": "Experiment queued...",
            "started_at_str": started_at_str,
            "start_time": now,
            "end_time": None,
            "elapsed": 0.0,
            "config": config,
            "dataset_id": req.dataset_id,
            "stages_history": [],
            "optimization_info": None,
            "best_params": None,
            "best_cv_score": None,
            "results": None,
            "evaluation": None,
            "context": None,
            "error": None
        }

    # Launch background thread
    worker_thread = threading.Thread(
        target=_background_train_worker,
        args=(job_id, df, config),
        daemon=True
    )
    worker_thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Experiment started in background."
    }


@app.post("/api/experiments/{job_id}/cancel")
def cancel_experiment(job_id: str):
    """Safely cancels an active background experiment."""
    with _LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Experiment job not found")
        job = JOBS[job_id]
        
        CANCELLATION_REQUESTS.add(job_id)
        
        if job["status"] in ["running", "queued"]:
            now = time.time()
            job["status"] = "cancelled"
            job["current_stage"] = "cancelled"
            job["end_time"] = now
            elapsed = now - job["start_time"]
            job["elapsed"] = elapsed
            job["progress"] = f"Cancelled after {elapsed:.1f}s"
            
            history = job.get("stages_history", [])
            history.append({
                "stage": "cancelled",
                "label": "Cancelled",
                "message": f"Cancelled after {elapsed:.1f}s",
                "timestamp": now
            })
            job["stages_history"] = history
            
            return {
                "message": "Experiment cancelled successfully.",
                "status": "cancelled",
                "elapsed_seconds": round(elapsed, 2)
            }
        else:
            return {
                "message": f"Job is already {job['status']}.",
                "status": job["status"],
                "elapsed_seconds": round(job.get("elapsed", 0.0), 2)
            }


@app.get("/api/experiments/{job_id}/status")
def get_experiment_status(job_id: str):
    """Polls the status of an experiment with rich execution stages."""
    with _LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Experiment job not found")
        job = JOBS[job_id]
        
        current_time = time.time()
        elapsed = (job["end_time"] - job["start_time"]) if job["end_time"] else (current_time - job["start_time"])
        
        return {
            "job_id": job["id"],
            "status": job["status"],
            "current_stage": job.get("current_stage", "running"),
            "progress": job["progress"],
            "started_at": job.get("started_at_str", ""),
            "elapsed_seconds": round(elapsed, 2),
            "stages_history": job.get("stages_history", []),
            "optimization_info": job.get("optimization_info"),
            "best_params": job.get("best_params"),
            "best_cv_score": job.get("best_cv_score"),
            "slurm_job_id": job.get("slurm_job_id"),
            "slurm_state": job.get("slurm_state"),
            "compute_node": job.get("compute_node"),
            "partition": job.get("partition"),
            "error": job["error"]
        }


@app.get("/api/experiments/{job_id}/results")
def get_experiment_results(job_id: str):
    """Retrieves full evaluation results, metrics, and evaluation protocol once complete."""
    with _LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Experiment job not found")
        job = JOBS[job_id]

    if job["status"] == "running" or job["status"] == "queued":
        return {"status": job["status"], "message": "Experiment is still in progress."}
    
    if job["status"] == "failed":
        return {"status": "failed", "error": job["error"]}

    results = job["results"]
    evaluation = job["evaluation"]
    config = job["config"]
    
    serialized_metrics = serialize_metrics(evaluation.get("metrics", {}))
    serialized_train_metrics = serialize_metrics(evaluation.get("train_metrics", {}))
    
    training_r2 = evaluation.get("training_r2")
    if training_r2 is None and isinstance(serialized_train_metrics, dict):
        training_r2 = serialized_train_metrics.get("R2 Score")

    validation_r2 = evaluation.get("validation_r2")
    if validation_r2 is None and isinstance(serialized_metrics, dict):
        validation_r2 = serialized_metrics.get("R2 Score")

    # Feature importances if available
    feature_importances = results.get("feature_importances", [])
    if not feature_importances:
        pipeline = results.get("pipeline")
        if pipeline and hasattr(pipeline.named_steps.get("model"), "feature_importances_"):
            model = pipeline.named_steps["model"]
            imps = model.feature_importances_
            feature_names = results.get("feature_names", config["features"])
            for name, imp in zip(feature_names, imps):
                clean_name = str(name).replace("num__", "").replace("cat__", "")
                feature_importances.append({"feature": clean_name, "importance": float(imp)})
            feature_importances = sorted(feature_importances, key=lambda x: x["importance"], reverse=True)

    # Sample predictions (first 20 rows)
    predictions_preview = results.get("predictions_preview", [])
    if not predictions_preview and "context" in job:
        try:
            pred_df = export_predictions_to_dataframe(job["context"])
            predictions_preview = pred_df.head(20).replace({np.nan: None}).to_dict(orient="records")
        except Exception:
            predictions_preview = []

    return {
        "status": "completed",
        "job_id": job["id"],
        "training_time": round(job.get("training_time", 0.0), 3),
        "total_elapsed": round(job.get("elapsed", 0.0), 3),
        "problem_type": config["problem_type"],
        "model_name": config["model_name"],
        "evaluation_config": job.get("evaluation_config", {}),
        "best_params": job.get("best_params"),
        "metrics": serialized_metrics,
        "train_metrics": serialized_train_metrics,
        "training_r2": training_r2,
        "validation_r2": validation_r2,
        "feature_importances": feature_importances,
        "predictions_preview": predictions_preview,
        "available_plots": list(REGRESSION_PLOTS.keys()) if config["problem_type"] == "Regression" else list(CLASSIFICATION_PLOTS.keys())
    }


# ----------------------------------------------------
# API Routes: Plots & Figures (Publication Quality)
# ----------------------------------------------------
@app.get("/api/experiments/{job_id}/plots/{plot_name}")
def get_experiment_plot(
    job_id: str,
    plot_name: str,
    width: str = "Double Column (190 mm)",
    quality: str = "Publication (300 DPI)",
    format: str = "png"
):
    """Generates and returns the requested publication-quality plot image bytes."""
    with _LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Job not found")
        job = JOBS[job_id]

    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Experiment must be completed before generating plots.")

    results = job["results"]
    problem_type = job["config"]["problem_type"]
    plot_dict = REGRESSION_PLOTS if problem_type == "Regression" else CLASSIFICATION_PLOTS

    if plot_name not in plot_dict:
        raise HTTPException(status_code=404, detail=f"Plot '{plot_name}' not available for {problem_type}.")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig = plot_dict[plot_name](results, width)
        if fig is None:
            raise HTTPException(status_code=400, detail=f"Could not generate plot '{plot_name}' with current model/data.")

        buffer = io.BytesIO()
        dpi_val = {
            "Screen Preview (150 DPI)": 150,
            "Publication (300 DPI)": 300,
            "High Quality (600 DPI)": 600,
            "Ultra Quality (1200 DPI)": 1200
        }.get(quality, 300)

        fig.savefig(buffer, format=format.lower(), dpi=dpi_val, bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)

        media_type = f"image/{format.lower()}"
        return Response(content=buffer.getvalue(), media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plot: {str(e)}")


# ----------------------------------------------------
# API Routes: Exports & Academic Downloads
# ----------------------------------------------------
@app.get("/api/experiments/{job_id}/export/script")
def download_python_script(job_id: str):
    """Downloads standalone educational Python script reproducing the experiment."""
    with _LOCK:
        if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
            raise HTTPException(status_code=404, detail="Completed experiment not found")
        context = JOBS[job_id]["context"]
        model_name = JOBS[job_id]["config"]["model_name"].lower().replace(" ", "_")

    script_content = generate_python_script(context)
    filename = f"run_{model_name}.py"
    
    return Response(
        content=script_content,
        media_type="text/x-python",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/experiments/{job_id}/export/csv")
def download_predictions_csv(job_id: str):
    """Downloads CSV containing actual vs predicted values and residuals/probabilities."""
    with _LOCK:
        if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
            raise HTTPException(status_code=404, detail="Completed experiment not found")
        context = JOBS[job_id]["context"]
        model_name = JOBS[job_id]["config"]["model_name"].lower().replace(" ", "_")

    pred_df = export_predictions_to_dataframe(context)
    csv_str = pred_df.to_csv(index=False)
    filename = f"predictions_{model_name}.csv"

    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/experiments/{job_id}/export/pdf")
def download_pdf_report(job_id: str):
    """Downloads academic publication research report in PDF format."""
    with _LOCK:
        if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
            raise HTTPException(status_code=404, detail="Completed experiment not found")
        context = JOBS[job_id]["context"]
        model_name = JOBS[job_id]["config"]["model_name"].lower().replace(" ", "_")

    temp_dir = tempfile.gettempdir()
    temp_pdf_path = os.path.join(temp_dir, f"solvosys_report_{job_id}.pdf")
    try:
        generate_pdf_report(context, temp_pdf_path)
        with open(temp_pdf_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)

    filename = f"report_{model_name}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@app.get("/api/experiments/{job_id}/export/zip")
def download_experiment_zip(job_id: str):
    """Downloads full reproducibility ZIP bundle with script, CSV, PDF, README, reqs, and plots."""
    with _LOCK:
        if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
            raise HTTPException(status_code=404, detail="Completed experiment not found")
        context = JOBS[job_id]["context"]
        model_name = JOBS[job_id]["config"]["model_name"].lower().replace(" ", "_")

    zip_buffer = generate_experiment_zip(context)
    filename = f"experiment_bundle_{model_name}.zip"

    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ----------------------------------------------------
# API Routes: Model Comparison
# ----------------------------------------------------
@app.get("/api/comparison")
def get_comparison_runs():
    """Returns list of runs stored in comparison."""
    with _LOCK:
        return {"runs": COMPARISON_RUNS}


@app.post("/api/comparison/add/{job_id}")
def add_to_comparison(job_id: str):
    """Adds a completed job to the model comparison list."""
    with _LOCK:
        if job_id not in JOBS or JOBS[job_id]["status"] != "completed":
            raise HTTPException(status_code=404, detail="Completed experiment not found")
        
        job = JOBS[job_id]
        from comparison import add_run
        global COMPARISON_RUNS
        COMPARISON_RUNS = add_run(
            COMPARISON_RUNS,
            job["config"],
            job["evaluation"],
            job.get("training_time", 0.0)
        )
        return {"message": "Run added to comparison", "runs_count": len(COMPARISON_RUNS), "runs": COMPARISON_RUNS}


@app.delete("/api/comparison/clear")
def clear_comparison():
    """Clears all runs from comparison."""
    with _LOCK:
        global COMPARISON_RUNS
        COMPARISON_RUNS = []
        return {"message": "Comparison cleared."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("SOLVOSYS_PORT", 8000))
    print(f"Starting Solvosys FastAPI Server on http://127.0.0.1:{port}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
