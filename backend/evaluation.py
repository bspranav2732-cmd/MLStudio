
import numpy as np
from sklearn.metrics import (

    # Regression
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    mean_absolute_percentage_error,

    # Classification
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


class Evaluator:

    @staticmethod
    def regression_metrics(y_true, y_pred):

        return {

            "R2 Score": r2_score(y_true, y_pred),

           

"RMSE": np.sqrt(
    mean_squared_error(
        y_true,
        y_pred
    )
),

            "MAE": mean_absolute_error(
                y_true,
                y_pred
            ),

            "MAPE": mean_absolute_percentage_error(
                y_true,
                y_pred
            ) * 100
        }

    @staticmethod
    def classification_metrics(y_true, y_pred):

        return {

            "Accuracy": accuracy_score(
                y_true,
                y_pred
            ),

            "Precision": precision_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

            "Recall": recall_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

            "F1 Score": f1_score(
                y_true,
                y_pred,
                average="weighted",
                zero_division=0
            ),

            "Confusion Matrix": confusion_matrix(
                y_true,
                y_pred
            )
        }


def evaluate(results):

    problem_type = results["problem_type"]

    y_true = results["y_test"]
    y_pred = results["y_test_pred"]

    if problem_type == "Regression":

        metrics = Evaluator.regression_metrics(
            y_true,
            y_pred
        )

    elif problem_type == "Classification":

        metrics = Evaluator.classification_metrics(
            y_true,
            y_pred
        )

    else:

        raise ValueError(
            "Invalid Problem Type"
        )

    return {

        "problem_type": problem_type,

        "model_name": results["model_name"],

        "split_method": results["split_method"],

        "metrics": metrics
    }