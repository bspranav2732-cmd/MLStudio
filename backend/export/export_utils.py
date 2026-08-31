"""
Common export utilities for Solvosys.
"""

import os
from typing import Dict, Any, Optional

class ExportContext:
    """
    Standard context object containing all components of a Solvosys training run.
    This acts as the standard interface for all exporter modules.
    """
    def __init__(self, config: Dict[str, Any], results: Dict[str, Any], evaluation: Dict[str, Any], comparison_runs: Optional[list] = None):
        """
        Initialize the ExportContext.

        Args:
            config (dict): The training configuration.
            results (dict): The training results, including model and datasets.
            evaluation (dict): The evaluation metrics.
            comparison_runs (list, optional): Historical experiment runs list.
        """
        self.config = config
        self.results = results
        self.evaluation = evaluation
        self.comparison_runs = comparison_runs if comparison_runs is not None else []


def create_export_context(config: Dict[str, Any], results: Dict[str, Any], evaluation: Dict[str, Any], comparison_runs: Optional[list] = None) -> ExportContext:
    """
    Factory function to create an ExportContext object.

    Args:
        config (dict): The training configuration.
        results (dict): The training results.
        evaluation (dict): The evaluation metrics.
        comparison_runs (list, optional): Historical experiment runs list.

    Returns:
        ExportContext: The constructed context.
    """
    return ExportContext(config, results, evaluation, comparison_runs)


def format_hyperparameters(hyperparameters: Dict[str, Any]) -> str:
    """
    Format a dictionary of hyperparameters into a clean string representation.

    Args:
        hyperparameters (dict): Hyperparameter key-value pairs.

    Returns:
        str: Formatted string of hyperparameters.
    """
    if not hyperparameters:
        return "Default (scikit-learn defaults)"
    
    return ", ".join(f"{k}={v}" for k, v in hyperparameters.items())


def find_plot_file(plot_name: str) -> Optional[str]:
    """
    Locates a plot image on disk by testing space-separated and underscore-separated filenames
    in both the 'outputs/' directory and the current directory.

    Args:
        plot_name (str): The name of the plot.

    Returns:
        str or None: The path to the file if found, otherwise None.
    """
    for folder in ["outputs", "."]:
        for filename in [plot_name, plot_name.replace(" ", "_")]:
            for ext in [".png", ".jpg", ".jpeg"]:
                path = os.path.join(folder, f"{filename}{ext}")
                if os.path.exists(path):
                    return path
    return None
