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

from preprocessing import build_preprocessor

def get_xgb_regressor(hp):
    from xgboost import XGBRegressor
    return XGBRegressor(
        n_estimators=hp.get("n_estimators", 100),
        learning_rate=hp.get("learning_rate", 0.1),
        max_depth=hp.get("max_depth", 6),
        subsample=hp.get("subsample", 1.0),
        colsample_bytree=hp.get("colsample_bytree", 1.0),
        random_state=hp.get("random_state", 42)
    )

def get_catboost_regressor(hp):
    from catboost import CatBoostRegressor
    return CatBoostRegressor(
        iterations=hp.get("iterations", 100),
        learning_rate=hp.get("learning_rate", 0.03),
        depth=hp.get("depth", 6),
        l2_leaf_reg=hp.get("l2_leaf_reg", 3.0),
        random_seed=hp.get("random_state", 42),
        verbose=0
    )

def get_xgb_classifier(hp):
    from xgboost import XGBClassifier
    return XGBClassifier(
        n_estimators=hp.get("n_estimators", 100),
        learning_rate=hp.get("learning_rate", 0.1),
        max_depth=hp.get("max_depth", 6),
        subsample=hp.get("subsample", 1.0),
        colsample_bytree=hp.get("colsample_bytree", 1.0),
        random_state=hp.get("random_state", 42)
    )

def get_catboost_classifier(hp):
    from catboost import CatBoostClassifier
    return CatBoostClassifier(
        iterations=hp.get("iterations", 100),
        learning_rate=hp.get("learning_rate", 0.03),
        depth=hp.get("depth", 6),
        l2_leaf_reg=hp.get("l2_leaf_reg", 3.0),
        random_seed=hp.get("random_state", 42),
        verbose=0
    )



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
            random_state=hp.get("random_state", 42)
        ),

    "Elastic Net":
        lambda hp: ElasticNet(
            alpha=hp.get("alpha", 1.0),
            l1_ratio=hp.get("l1_ratio", 0.5),
            max_iter=hp.get("max_iter", 1000),
            random_state=hp.get("random_state", 42)
        ),

    "Decision Tree":
        lambda hp: DecisionTreeRegressor(
            random_state=hp.get("random_state", 42),
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
            max_samples=hp.get("max_samples"),
            min_impurity_decrease=hp.get("min_impurity_decrease", 0.0),
            bootstrap=hp.get("bootstrap", True),
            oob_score=hp.get("oob_score", False),
            random_state=hp.get("random_state", 42)
        ),

    "XGBoost Regressor": get_xgb_regressor,

    "CatBoost Regressor": get_catboost_regressor

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
            random_state=hp.get("random_state", 42),
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
            max_samples=hp.get("max_samples"),
            min_impurity_decrease=hp.get("min_impurity_decrease", 0.0),
            bootstrap=hp.get("bootstrap", True),
            oob_score=hp.get("oob_score", False),
            random_state=hp.get("random_state", 42)
        ),

    "XGBoost Classifier": get_xgb_classifier,

    "CatBoost Classifier": get_catboost_classifier

}

# train_model and get_split_method moved to engine.py and validation.py

def get_model(problem_type, model_name, hyperparameters):
    if problem_type == "Regression":
        return REGRESSION_MODELS[model_name](hyperparameters)
    elif problem_type == "Classification":
        return CLASSIFICATION_MODELS[model_name](hyperparameters)
    else:
        raise ValueError(f"Unknown problem type: {problem_type}")