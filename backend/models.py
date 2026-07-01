from sklearn.model_selection import (
    train_test_split,
    KFold,
    StratifiedKFold,
    cross_val_predict
)

from sklearn.linear_model import (
    LinearRegression,
    LogisticRegression,
    Lasso,
    ElasticNet
)

from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import Pipeline

from sklearn.tree import (
    DecisionTreeRegressor,
    DecisionTreeClassifier
)

from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier
)

from xgboost import XGBRegressor, XGBClassifier
from catboost import CatBoostRegressor, CatBoostClassifier
from preprocessing import build_preprocessor


# ==========================================================
# Available Models
# ==========================================================

REGRESSION_MODELS = {

    "Linear Regression":
        lambda hp: LinearRegression(),

    "Polynomial Regression":
        lambda hp: Pipeline([
            (
                "poly",
                PolynomialFeatures(
                    degree=hp.get("degree", 2),
                    include_bias=False
                )
            ),
            (
                "linear",
                LinearRegression()
            )
        ]),

    "Lasso Regression":
        lambda hp: Lasso(
            alpha=hp.get("alpha", 1.0),
            max_iter=hp.get("max_iter", 1000),
            random_state=42
        ),

    "Elastic Net":
        lambda hp: ElasticNet(
            alpha=hp.get("alpha", 1.0),
            l1_ratio=hp.get("l1_ratio", 0.5),
            max_iter=hp.get("max_iter", 1000),
            random_state=42
        ),

    "Decision Tree":
        lambda hp: DecisionTreeRegressor(
            random_state=42,
            max_depth=hp.get("max_depth"),
            min_samples_split=hp.get("min_samples_split", 2),
            min_samples_leaf=hp.get("min_samples_leaf", 1)
        ),

    "Random Forest":
        lambda hp: RandomForestRegressor(
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth"),
            min_samples_split=hp.get("min_samples_split", 2),
            min_samples_leaf=hp.get("min_samples_leaf", 1),
            max_features=hp.get("max_features", "sqrt"),
            random_state=42
        ),

    "XGBoost Regressor":
        lambda hp: XGBRegressor(
            n_estimators=hp.get("n_estimators", 100),
            learning_rate=hp.get("learning_rate", 0.1),
            max_depth=hp.get("max_depth", 6),
            subsample=hp.get("subsample", 1.0),
            colsample_bytree=hp.get("colsample_bytree", 1.0),
            random_state=42
        ),

    "CatBoost Regressor":
        lambda hp: CatBoostRegressor(
            iterations=hp.get("iterations", 100),
            learning_rate=hp.get("learning_rate", 0.03),
            depth=hp.get("depth", 6),
            l2_leaf_reg=hp.get("l2_leaf_reg", 3.0),
            random_seed=42,
            verbose=0
        )

}


CLASSIFICATION_MODELS = {

    "Logistic Regression":
        lambda hp: LogisticRegression(
            C=hp.get("C", 1.0),
            solver=hp.get("solver", "lbfgs"),
            max_iter=hp.get("max_iter", 1000)
        ),

    "Decision Tree":
        lambda hp: DecisionTreeClassifier(
            random_state=42,
            max_depth=hp.get("max_depth"),
            min_samples_split=hp.get("min_samples_split", 2),
            min_samples_leaf=hp.get("min_samples_leaf", 1)
        ),

    "Random Forest":
        lambda hp: RandomForestClassifier(
            n_estimators=hp.get("n_estimators", 100),
            max_depth=hp.get("max_depth"),
            min_samples_split=hp.get("min_samples_split", 2),
            min_samples_leaf=hp.get("min_samples_leaf", 1),
            max_features=hp.get("max_features", "sqrt"),
            random_state=42
        ),

    "XGBoost Classifier":
        lambda hp: XGBClassifier(
            n_estimators=hp.get("n_estimators", 100),
            learning_rate=hp.get("learning_rate", 0.1),
            max_depth=hp.get("max_depth", 6),
            subsample=hp.get("subsample", 1.0),
            colsample_bytree=hp.get("colsample_bytree", 1.0),
            random_state=42
        ),

    "CatBoost Classifier":
        lambda hp: CatBoostClassifier(
            iterations=hp.get("iterations", 100),
            learning_rate=hp.get("learning_rate", 0.03),
            depth=hp.get("depth", 6),
            l2_leaf_reg=hp.get("l2_leaf_reg", 3.0),
            random_seed=42,
            verbose=0
        )

}

# ==========================================================
# Split Method
# ==========================================================

def get_split_method(
    split_method,
    X,
    y,
    train_size=0.8,
    folds=5
):

    if split_method == "Train-Test Split":

        return train_test_split(
            X,
            y,
            train_size=train_size,
            random_state=42
        )

    elif split_method == "K-Fold Cross Validation":

        return KFold(
            n_splits=folds,
            shuffle=True,
            random_state=42
        )

    elif split_method == "Stratified K-Fold Cross Validation":

        return StratifiedKFold(
            n_splits=folds,
            shuffle=True,
            random_state=42
        )

    else:

        raise ValueError("Invalid Split Method")


# ==========================================================
# Model Selection
# ==========================================================

def get_model(
    problem_type,
    model_name,
    hyperparameters=None
):

    if hyperparameters is None:
        hyperparameters = {}

    if problem_type == "Regression":

        return REGRESSION_MODELS[
            model_name
        ](hyperparameters)

    return CLASSIFICATION_MODELS[
        model_name
    ](hyperparameters)

## ==========================================================
# Train Model
# ==========================================================

def train_model(
    X,
    y,
    problem_type,
    model_name,
    split_method,
    preprocessing,
    hyperparameters=None,
    train_percent=80,
    folds=5
):
    if hyperparameters is None:
        hyperparameters = {}

    model = get_model(
        problem_type,
        model_name,
        hyperparameters
    )
        # ------------------------------------------------------
    # Train-Test Split
    # ------------------------------------------------------

    if split_method == "Train-Test Split":

        X_train, X_test, y_train, y_test = get_split_method(
            split_method,
            X,
            y,
            train_size=train_percent / 100
        )

        # ----------------------------------------------
        # Build Preprocessor
        # ----------------------------------------------

        preprocessor = build_preprocessor(
            X_train,
            preprocessing["missing_strategy"],
            preprocessing["encoding_strategy"],
            preprocessing["scaling_strategy"]
        )

        # ----------------------------------------------
        # Build Pipeline
        # ----------------------------------------------

        pipeline = Pipeline(
            steps=[
                (
                    "preprocessor",
                    preprocessor
                ),
                (
                    "model",
                    model
                )
            ]
        )

        # ----------------------------------------------
        # Train
        # ----------------------------------------------
        
        pipeline.fit(
            X_train,
            y_train
        )
        feature_names = pipeline.named_steps[
            "preprocessor"
        ].get_feature_names_out()
        # ----------------------------------------------
        # Predict
        # ----------------------------------------------

        y_train_pred = pipeline.predict(
            X_train
        )

        y_test_pred = pipeline.predict(
            X_test
        )

        # Prediction probabilities (if supported)

        if hasattr(pipeline, "predict_proba"):

            y_test_prob = pipeline.predict_proba(X_test)[:, 1]

        else:

            y_test_prob = None

        return {

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
            "feature_names": feature_names,
        }

       # ------------------------------------------------------
    # Cross Validation
    # ------------------------------------------------------

    else:

        cv = get_split_method(
            split_method,
            X,
            y,
            folds=folds
        )

        preprocessor = build_preprocessor(
            X,
            preprocessing["missing_strategy"],
            preprocessing["encoding_strategy"],
            preprocessing["scaling_strategy"]
        )

        pipeline = Pipeline(

            steps=[

                (
                    "preprocessor",
                    preprocessor
                ),

                (
                    "model",
                    model
                )

            ]

        )

        y_pred = cross_val_predict(

            pipeline,

            X,

            y,

            cv=cv

        )

        if hasattr(pipeline, "predict_proba"):
            try:
                y_prob = cross_val_predict(
                    pipeline,
                    X,
                    y,
                    cv=cv,
                    method="predict_proba"
                )[:, 1]
            except Exception:
                y_prob = None
        else:
            y_prob = None

        pipeline.fit(
            X,
            y
        )

        feature_names = pipeline.named_steps[
            "preprocessor"
        ].get_feature_names_out()

        return {

            "problem_type": problem_type,

            "model_name": model_name,

            "split_method": split_method,

            "model": pipeline,

            "pipeline": pipeline,

            "feature_names": feature_names,

            "X": X,

            "y": y,

            "y_test": y,

            "y_test_pred": y_pred,

            "y_test_prob": y_prob

        }