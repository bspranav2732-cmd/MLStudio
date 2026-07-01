import time
from models import train_model
from evaluation import evaluate


def run_training(df, config):
    """
    Complete ML pipeline.
    """
    start_time = time.time()

    # -------------------------------
    # Prepare Dataset
    # -------------------------------

    X = df[config["features"]]
    y = df[config["target"]]

    # -------------------------------
    # Train Model
    # -------------------------------

    results = train_model(
        X=X,
        y=y,
        problem_type=config["problem_type"],
        model_name=config["model_name"],
        split_method=config["split_method"],
        preprocessing=config["preprocessing"],
        hyperparameters=config["hyperparameters"],
        train_percent=config["train_percent"],
        folds=config["folds"]
    )
    results["target_name"] = config["target_name"]
    results["target_unit"] = config["target_unit"]
    # -------------------------------
    # Evaluate
    # -------------------------------

    evaluation = evaluate(results)

    training_time = time.time() - start_time

    # -------------------------------
    # Return Pipeline
    # -------------------------------

    return {
        "results": results,
        "evaluation": evaluation,
        "training_time": training_time
    }