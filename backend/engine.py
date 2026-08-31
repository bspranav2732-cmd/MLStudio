import time
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.base import clone

from models import get_model
from preprocessing import build_preprocessor
from evaluation import evaluate
from validation import get_validation_method
from parameter_spaces import get_parameter_space
from optimization import run_optimization

def _run_single_seed(df, config, seed, progress_callback=None):
    start_time = time.time()

    # 1. Prepare Dataset
    if progress_callback:
        progress_callback({
            "stage": "dataset_prep",
            "message": f"Preparing dataset ({len(df)} rows × {len(config['features'])} features)..."
        })

    X = df[config["features"]]
    y = df[config["target"]]
    
    problem_type = config["problem_type"]
    model_name = config["model_name"]
    hyperparameters = config["hyperparameters"].copy()
    
    hyperparameters["random_state"] = seed # Try to inject seed if supported
    
    if config.get("use_oob"):
        hyperparameters["bootstrap"] = True
        hyperparameters["oob_score"] = True

    # 2. Build Base Components
    model = get_model(problem_type, model_name, hyperparameters)
    preprocessor = build_preprocessor(
        X,
        config["preprocessing"]["missing_strategy"],
        config["preprocessing"]["encoding_strategy"],
        config["preprocessing"]["scaling_strategy"]
    )
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", model)
    ])
    
    best_params = None
    optimization_results = None
    split_method = config["split_method"]
    
    evaluation_config = {
        "validation": split_method,
        "optimization": config["optimization"],
        "random_state": seed,
        "oob": config.get("use_oob", False)
    }

    # 3. Train-Test Split or Cross-Validation
    if split_method == "Train-Test Split":
        evaluation_config["validation"] = f"Train-Test Split ({config['train_percent']}/{100-config['train_percent']})"
        
        # PREVENT LEAKAGE: Split data before optimization
        X_train, X_test, y_train, y_test = get_validation_method(
            split_method, X, y, train_size=config["train_percent"] / 100, problem_type=problem_type, random_state=seed
        )

        if progress_callback:
            progress_callback({
                "stage": "split",
                "message": f"Train/test split completed: {len(X_train)} training rows ({config['train_percent']}%), {len(X_test)} holdout test rows ({100-config['train_percent']}%)",
                "train_rows": len(X_train),
                "test_rows": len(X_test)
            })
        
        if config["optimization"] != "None":
            param_space = get_parameter_space(model_name)
            
            if param_space:
                opt_iters = config.get('opt_iters', 10)
                opt_cv_folds = config["opt_cv"]
                total_fits = opt_iters * opt_cv_folds if config["optimization"] == "Random Search" else len(param_space) * opt_cv_folds
                
                if progress_callback:
                    progress_callback({
                        "stage": "optimization",
                        "strategy": config["optimization"],
                        "iterations": opt_iters,
                        "folds": opt_cv_folds,
                        "total_fits": total_fits,
                        "rows": len(X_train),
                        "message": f"Running {config['optimization']}: {opt_iters} iterations × {opt_cv_folds} folds = {total_fits} fits on {len(X_train)} training rows..."
                    })
                
                evaluation_config["optimization"] = f"{config['optimization']} ({opt_iters} iterations)"
                opt_cv = get_validation_method(
                    "K-Fold Cross Validation", X_train, y_train, folds=opt_cv_folds, problem_type=problem_type, random_state=seed
                )
                optimization_results = run_optimization(
                    pipeline=pipeline,
                    param_space=param_space,
                    cv=opt_cv,
                    X=X_train, # Optimization runs ONLY on training data
                    y=y_train,
                    strategy=config["optimization"],
                    n_iter=opt_iters,
                    problem_type=problem_type
                )
                pipeline = optimization_results["best_estimator"]
                best_params = optimization_results["best_params"]
                best_cv_score = optimization_results.get("best_score")
                evaluation_config["best_params"] = best_params
                evaluation_config["best_cv_score"] = best_cv_score
                
                if progress_callback:
                    progress_callback({
                        "stage": "best_params",
                        "best_params": best_params,
                        "best_cv_score": best_cv_score,
                        "message": f"{config['optimization']} completed. Best CV score: {best_cv_score:.4f}"
                    })
                
        # Ensure OOB configuration is preserved on final pipeline estimator
        if config.get("use_oob") and model_name == "Random Forest":
            pipeline.named_steps["model"].set_params(bootstrap=True, oob_score=True)

        if progress_callback:
            progress_callback({
                "stage": "final_train",
                "message": f"Fitting final model on {len(X_train)} training samples..."
            })

        pipeline.fit(X_train, y_train)

        # Prominently trigger Holdout Testing Stage
        if progress_callback:
            progress_callback({
                "stage": "holdout_eval",
                "message": f"Testing model on holdout test set ({100-config['train_percent']}%, {len(X_test)} samples)..."
            })

        y_train_pred = pipeline.predict(X_train)
        y_test_pred = pipeline.predict(X_test)
        y_test_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline.named_steps["model"], "predict_proba") else None

        if progress_callback:
            progress_callback({
                "stage": "metrics",
                "message": "Holdout testing completed. Calculating final evaluation metrics..."
            })
        
        results = {
            "problem_type": problem_type,
            "model_name": model_name,
            "split_method": split_method,
            "model": pipeline,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "y_train_pred": y_train_pred,
            "y_test_pred": y_test_pred,
            "y_test_prob": y_test_prob,
            "pipeline": pipeline,
            "best_params": best_params,
            "evaluation_config": evaluation_config
        }
        
    else:
        # Cross Validation Manual Loop (Prevents double fitting penalty)
        evaluation_config["optimization"] = "Disabled"
        evaluation_config["validation"] = f"{config['folds']}-Fold Cross Validation"
        
        repeats = config.get("repeats", 1)
        num_folds = config["folds"]
        if split_method in ["Repeated K-Fold", "Repeated Stratified K-Fold"]:
            evaluation_config["validation"] = f"{config['folds']}-Fold CV ({repeats} Repeats)"
        else:
            repeats = 1
            
        cv = get_validation_method(
            split_method, X, y, folds=num_folds, repeats=repeats, problem_type=problem_type, random_state=seed
        )
        
        if progress_callback:
            progress_callback({
                "stage": "cv_eval",
                "message": f"Running {evaluation_config['validation']} across {len(X)} samples...",
                "folds": num_folds,
                "repeats": repeats,
                "total_folds": num_folds * repeats
            })
        
        # Store predictions by repeat to prevent overwriting
        y_preds_all = [np.empty(len(y), dtype=float) if problem_type == "Regression" else np.empty(len(y), dtype=y.dtype) for _ in range(repeats)]
        y_probs_all = [np.empty_like(y, dtype=float) if hasattr(pipeline.named_steps["model"], "predict_proba") else None for _ in range(repeats)]
        
        cv_res = {
            "test_r2": [], "test_rmse": [], "test_mae": [], "test_mape": [],
            "test_accuracy": [], "test_precision_weighted": [], "test_recall_weighted": [], "test_f1_weighted": []
        }
                  
        import sklearn.metrics as metrics_lib
                  
        for idx, (train_idx, test_idx) in enumerate(cv.split(X, y)):
            repeat_idx = idx // num_folds
            
            if progress_callback:
                progress_callback({
                    "stage": "cv_fold_progress",
                    "fold": idx + 1,
                    "total_folds": num_folds * repeats,
                    "message": f"Evaluating fold {idx + 1}/{num_folds * repeats}..."
                })

            X_train_f, y_train_f = X.iloc[train_idx], y.iloc[train_idx]
            X_test_f, y_test_f = X.iloc[test_idx], y.iloc[test_idx]
            
            fold_pipeline = clone(pipeline)
            fold_pipeline.fit(X_train_f, y_train_f)
            
            preds = fold_pipeline.predict(X_test_f)
            y_preds_all[repeat_idx][test_idx] = preds
            
            if y_probs_all[repeat_idx] is not None:
                y_probs_all[repeat_idx][test_idx] = fold_pipeline.predict_proba(X_test_f)[:, 1]
                
            if problem_type == "Regression":
                cv_res["test_r2"].append(metrics_lib.r2_score(y_test_f, preds))
                cv_res["test_rmse"].append(np.sqrt(metrics_lib.mean_squared_error(y_test_f, preds)))
                cv_res["test_mae"].append(metrics_lib.mean_absolute_error(y_test_f, preds))
                cv_res["test_mape"].append(metrics_lib.mean_absolute_percentage_error(y_test_f, preds))
            else:
                cv_res["test_accuracy"].append(metrics_lib.accuracy_score(y_test_f, preds))
                cv_res["test_precision_weighted"].append(metrics_lib.precision_score(y_test_f, preds, average="weighted", zero_division=0))
                cv_res["test_recall_weighted"].append(metrics_lib.recall_score(y_test_f, preds, average="weighted", zero_division=0))
                cv_res["test_f1_weighted"].append(metrics_lib.f1_score(y_test_f, preds, average="weighted", zero_division=0))
                
        # Clean up empty metrics
        for k in list(cv_res.keys()):
            if not cv_res[k]:
                del cv_res[k]
                
        if progress_callback:
            progress_callback({
                "stage": "final_train",
                "message": f"Fitting final model on entire dataset ({len(X)} samples)..."
            })

        # Ensure OOB settings are applied before fitting final model on entire dataset
        if config.get("use_oob") and model_name == "Random Forest":
            pipeline.named_steps["model"].set_params(bootstrap=True, oob_score=True)

        # Fit final model on entire dataset
        pipeline.fit(X, y)

        if progress_callback:
            progress_callback({
                "stage": "metrics",
                "message": "Cross-validation evaluation completed. Aggregating results..."
            })
        
        results = {
            "problem_type": problem_type,
            "model_name": model_name,
            "split_method": split_method,
            "model": pipeline,
            "pipeline": pipeline,
            "X": X,
            "y": y,
            "y_test": y,
            "y_test_pred": y_preds_all[0], # Primary prediction output uses first repeat
            "y_test_prob": y_probs_all[0] if y_probs_all[0] is not None else None,
            "best_params": best_params,
            "cv_res": cv_res,
            "evaluation_config": evaluation_config
        }
        
    # Attempt to extract feature names
    try:
        results["feature_names"] = pipeline.named_steps["preprocessor"].get_feature_names_out()
    except Exception:
        results["feature_names"] = list(X.columns)
        
    results["target_name"] = config["target_name"]
    results["target_unit"] = config["target_unit"]

    # Extract OOB Score if requested
    oob_score = None
    if config.get("use_oob") and hasattr(pipeline.named_steps["model"], "oob_score_"):
        oob_score = pipeline.named_steps["model"].oob_score_
        results["oob_score"] = oob_score
        evaluation_config["oob_score"] = oob_score

    # Evaluate
    evaluation_result = evaluate(results)
    
    if oob_score is not None:
        evaluation_result["metrics"]["OOB Score"] = oob_score

    training_time = time.time() - start_time

    return {
        "results": results,
        "evaluation": evaluation_result,
        "training_time": training_time,
        "optimization_results": optimization_results
    }


def run_training(df, config, progress_callback=None):
    use_multiple_seeds = config.get("use_multiple_seeds", False)
    num_seeds = config.get("num_seeds", 1) if use_multiple_seeds else 1
    
    if not use_multiple_seeds or num_seeds == 1:
        return _run_single_seed(df, config, seed=42, progress_callback=progress_callback)
        
    start_time = time.time()
    all_metrics = []
    
    final_output = None
    
    for i in range(num_seeds):
        seed = 42 + i
        if progress_callback:
            progress_callback(f"Running Multiple Seeds ({i+1}/{num_seeds}) [Seed: {seed}]...")
            
        output = _run_single_seed(df, config, seed=seed)
        all_metrics.append(output["evaluation"]["metrics"])
        final_output = output
        
    # Aggregate metrics across seeds
    aggregated_metrics = {}
    metric_keys = all_metrics[0].keys()
    
    for key in metric_keys:
        values = []
        for m in all_metrics:
            val = m.get(key)
            if val is not None:
                if isinstance(val, dict): # if it's already CV aggregated
                    values.append(val["mean"])
                else:
                    values.append(val)
                    
        if values:
            aggregated_metrics[key] = {
                "mean": np.mean(values),
                "std": np.std(values)
            }
            
    final_output["evaluation"]["metrics"] = aggregated_metrics
    final_output["results"]["evaluation_config"]["validation"] += f" (Multi-Seed x{num_seeds})"
    final_output["training_time"] = time.time() - start_time
    
    return final_output