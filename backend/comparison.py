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
    run_summary = {
        "model_name": config.get("model_name", "Model"),
        "problem_type": config.get("problem_type", "Regression"),
        "train_metrics": evaluation.get("train_metrics", {}),
        "validation_metrics": evaluation.get("metrics", {}),  # Validation metrics
        "metrics": evaluation.get("metrics", {}),              # Overall performance metrics
        "hyperparameters": config.get("hyperparameters", {}),
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
