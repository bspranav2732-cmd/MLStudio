"""
Module responsible for managing saved experiments for comparison.
"""

from typing import Dict, Any, List

def add_run(
    comparison_runs: List[Dict[str, Any]],
    config: Dict[str, Any],
    evaluation: Dict[str, Any],
    training_time: float
) -> List[Dict[str, Any]]:
    """
    Create a summary of the current experiment and add it to the comparison list.

    Do NOT store fitted models, pipelines, plots, predictions, or datasets.
    """
    train_metrics = evaluation.get("train_metrics", {})
    val_metrics = evaluation.get("metrics", {})
    
    training_r2 = evaluation.get("training_r2")
    if training_r2 is None and isinstance(train_metrics, dict):
        training_r2 = train_metrics.get("R2 Score")
        
    validation_r2 = evaluation.get("validation_r2")
    if validation_r2 is None and isinstance(val_metrics, dict):
        validation_r2 = val_metrics.get("R2 Score")

    training_acc = evaluation.get("training_accuracy")
    if training_acc is None and isinstance(train_metrics, dict):
        training_acc = train_metrics.get("Accuracy")

    validation_acc = evaluation.get("validation_accuracy")
    if validation_acc is None and isinstance(val_metrics, dict):
        validation_acc = val_metrics.get("Accuracy")

    run_summary = {
        "model_name": config.get("model_name", "Model"),
        "problem_type": config.get("problem_type", "Regression"),
        "train_metrics": train_metrics,
        "validation_metrics": val_metrics,
        "metrics": val_metrics,
        "training_r2": training_r2,
        "validation_r2": validation_r2,
        "training_accuracy": training_acc,
        "validation_accuracy": validation_acc,
        "hyperparameters": config.get("hyperparameters", {}),
        "execution_mode": config.get("execution_mode", "local"),
        "training_time": training_time
    }
    
    comparison_runs.append(run_summary)
    return comparison_runs


def remove_run(comparison_runs: List[Dict[str, Any]], indices: List[int]) -> List[Dict[str, Any]]:
    """
    Remove selected experiments from the comparison list by their indices.
    """
    # Sort indices in descending order to avoid index shifting during removal
    for idx in sorted(indices, reverse=True):
        if 0 <= idx < len(comparison_runs):
            comparison_runs.pop(idx)
    return comparison_runs


def clear_runs() -> List[Dict[str, Any]]:
    """
    Clear all saved experiments.
    """
    return []
