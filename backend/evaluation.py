
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
        metrics = Evaluator.regression_metrics(y_true, y_pred)
    elif problem_type == "Classification":
        metrics = Evaluator.classification_metrics(y_true, y_pred)
    else:
        raise ValueError("Invalid Problem Type")
        
    if "cv_res" in results:
        # Override metrics with Mean ± Std from cross_validate
        cv_res = results["cv_res"]
        if problem_type == "Regression":
            metrics["R2 Score"] = {"mean": np.mean(cv_res['test_r2']), "std": np.std(cv_res['test_r2'])}
            metrics["RMSE"] = {"mean": np.mean(cv_res['test_rmse']), "std": np.std(cv_res['test_rmse'])}
            metrics["MAE"] = {"mean": np.mean(cv_res['test_mae']), "std": np.std(cv_res['test_mae'])}
            metrics["MAPE"] = {"mean": np.mean(cv_res['test_mape']) * 100, "std": np.std(cv_res['test_mape']) * 100}
        else:
            metrics["Accuracy"] = {"mean": np.mean(cv_res['test_accuracy']), "std": np.std(cv_res['test_accuracy'])}
            metrics["Precision"] = {"mean": np.mean(cv_res['test_precision_weighted']), "std": np.std(cv_res['test_precision_weighted'])}
            metrics["Recall"] = {"mean": np.mean(cv_res['test_recall_weighted']), "std": np.std(cv_res['test_recall_weighted'])}
            metrics["F1 Score"] = {"mean": np.mean(cv_res['test_f1_weighted']), "std": np.std(cv_res['test_f1_weighted'])}

    # Compute training metrics for Generalization Comparison
    train_metrics = {}
    if "y_train" in results and "y_train_pred" in results:
        if problem_type == "Regression":
            train_metrics = Evaluator.regression_metrics(results["y_train"], results["y_train_pred"])
        else:
            train_metrics = Evaluator.classification_metrics(results["y_train"], results["y_train_pred"])
    elif "X" in results and "y" in results and "model" in results:
        y_train_pred = results["model"].predict(results["X"])
        if problem_type == "Regression":
            train_metrics = Evaluator.regression_metrics(results["y"], y_train_pred)
        else:
            train_metrics = Evaluator.classification_metrics(results["y"], y_train_pred)

    return {

        "problem_type": problem_type,

        "model_name": results["model_name"],

        "split_method": results["split_method"],

        "metrics": metrics,
        
        "train_metrics": train_metrics
    }