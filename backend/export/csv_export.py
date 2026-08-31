"""
Module for exporting predictions as CSV (pandas DataFrame).
"""

import pandas as pd
from export.export_utils import ExportContext

def export_predictions_to_dataframe(context: ExportContext) -> pd.DataFrame:
    """
    Generate a pandas DataFrame containing predictions and metrics.

    For Regression, returns: Actual, Predicted, Residual
    For Classification, returns: Actual, Predicted, Probability (if available)

    Args:
        context (ExportContext): The export context.

    Returns:
        pd.DataFrame: The predictions DataFrame.
    """
    results = context.results
    problem_type = results.get("problem_type")

    # Reset index to align pandas series and numpy arrays perfectly
    actual = pd.Series(results["y_test"]).reset_index(drop=True)
    predicted = pd.Series(results["y_test_pred"]).reset_index(drop=True)

    if problem_type == "Regression":
        residual = actual - predicted
        df = pd.DataFrame({
            "Actual": actual,
            "Predicted": predicted,
            "Residual": residual
        })
    elif problem_type == "Classification":
        df_dict = {
            "Actual": actual,
            "Predicted": predicted
        }
        
        # Check if probability is available
        prob = results.get("y_test_prob")
        if prob is not None:
            df_dict["Probability"] = pd.Series(prob).reset_index(drop=True)
            
        df = pd.DataFrame(df_dict)
    else:
        raise ValueError(f"Unknown problem type: {problem_type}")

    return df
