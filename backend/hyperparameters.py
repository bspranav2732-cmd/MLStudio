import streamlit as st


# ==========================================================
# Polynomial Regression
# ==========================================================

def polynomial_regression_params():

    params = {}

    params["degree"] = st.slider(
        "Polynomial Degree",
        min_value=2,
        max_value=10,
        value=2
    )

    return params

# ==========================================================
# Linear Regression
# ==========================================================

def linear_regression_params():

    st.info(
        "Linear Regression has no tunable hyperparameters."
    )

    return {}
# ==========================================================
# Logistic Regression
# ==========================================================

def logistic_regression_params():

    params = {}

    params["C"] = st.slider(
        "Regularization Strength (C)",
        0.01,
        10.0,
        1.0,
        step=0.01
    )

    params["solver"] = st.selectbox(
        "Solver",
        [
            "lbfgs",
            "liblinear",
            "newton-cg",
            "saga"
        ]
    )

    params["max_iter"] = st.slider(
        "Maximum Iterations",
        100,
        5000,
        1000,
        step=100
    )

    return params
# ==========================================================
# Lasso Regression
# ==========================================================

def lasso_regression_params():
    params = {}
    params["alpha"] = st.slider("Alpha (Regularization)", 0.0001, 10.0, 1.0, step=0.0001)
    params["max_iter"] = st.slider("Maximum Iterations", 100, 10000, 1000, step=100)
    params["random_state"] = 42
    return params

# ==========================================================
# Elastic Net
# ==========================================================

def elastic_net_params():
    params = {}
    params["alpha"] = st.slider("Alpha (Regularization)", 0.0001, 10.0, 1.0, step=0.0001)
    params["l1_ratio"] = st.slider("L1 Ratio (l1_ratio)", 0.0, 1.0, 0.5, step=0.01)
    params["max_iter"] = st.slider("Maximum Iterations", 100, 10000, 1000, step=100)
    params["random_state"] = 42
    return params

# ==========================================================
# XGBoost Regressor
# ==========================================================

def xgboost_regressor_params():
    params = {}
    params["n_estimators"] = st.slider("Number of Boosting Rounds (n_estimators)", 10, 1000, 100, step=10)
    params["learning_rate"] = st.slider("Learning Rate (learning_rate)", 0.001, 1.0, 0.1, step=0.001)
    params["max_depth"] = st.slider("Maximum Depth (max_depth)", 1, 20, 6)
    params["subsample"] = st.slider("Subsample Ratio (subsample)", 0.1, 1.0, 1.0, step=0.05)
    params["colsample_bytree"] = st.slider("Column Sample Ratio (colsample_bytree)", 0.1, 1.0, 1.0, step=0.05)
    params["random_state"] = 42
    return params

# ==========================================================
# CatBoost Regressor
# ==========================================================

def catboost_regressor_params():
    params = {}
    params["iterations"] = st.slider("Number of Iterations (iterations)", 10, 1000, 100, step=10)
    params["learning_rate"] = st.slider("Learning Rate (learning_rate)", 0.001, 1.0, 0.03, step=0.001)
    params["depth"] = st.slider("Tree Depth (depth)", 1, 16, 6)
    params["l2_leaf_reg"] = st.slider("L2 Leaf Regularization (l2_leaf_reg)", 0.1, 10.0, 3.0, step=0.1)
    params["random_seed"] = 42
    return params

# ==========================================================
# XGBoost Classifier
# ==========================================================

def xgboost_classifier_params():
    params = {}
    params["n_estimators"] = st.slider("Number of Boosting Rounds (n_estimators)", 10, 1000, 100, step=10)
    params["learning_rate"] = st.slider("Learning Rate (learning_rate)", 0.001, 1.0, 0.1, step=0.001)
    params["max_depth"] = st.slider("Maximum Depth (max_depth)", 1, 20, 6)
    params["subsample"] = st.slider("Subsample Ratio (subsample)", 0.1, 1.0, 1.0, step=0.05)
    params["colsample_bytree"] = st.slider("Column Sample Ratio (colsample_bytree)", 0.1, 1.0, 1.0, step=0.05)
    params["random_state"] = 42
    return params

# ==========================================================
# CatBoost Classifier
# ==========================================================

def catboost_classifier_params():
    params = {}
    params["iterations"] = st.slider("Number of Iterations (iterations)", 10, 1000, 100, step=10)
    params["learning_rate"] = st.slider("Learning Rate (learning_rate)", 0.001, 1.0, 0.03, step=0.001)
    params["depth"] = st.slider("Tree Depth (depth)", 1, 16, 6)
    params["l2_leaf_reg"] = st.slider("L2 Leaf Regularization (l2_leaf_reg)", 0.1, 10.0, 3.0, step=0.1)
    params["random_seed"] = 42
    return params


# ==========================================================
# Random Forest
# ==========================================================

def random_forest_params():

    params = {}

    params["n_estimators"] = st.slider(

    "Number of Trees",

    min_value=50,

    max_value=1000,

    value=100,

    step=50,

    help="""
More trees generally improve performance but increase training time.
"""
)

    depth = st.number_input(
        "Maximum Depth (0 = None)",
        min_value=0,
        value=0
    )

    params["max_depth"] = None if depth == 0 else depth

    params["min_samples_split"] = st.slider(
        "Minimum Samples Split",
        2,
        20,
        2
    )

    params["min_samples_leaf"] = st.slider(
        "Minimum Samples Leaf",
        1,
        20,
        1
    )

    params["max_features"] = st.selectbox(
        "Maximum Features",
        [
            "sqrt",
            "log2",
            None
        ]
    )

    return params


# ==========================================================
# Decision Tree
# ==========================================================

def decision_tree_params():

    params = {}

    depth = st.number_input(
        "Maximum Depth (0 = None)",
        min_value=0,
        value=0
    )

    params["max_depth"] = None if depth == 0 else depth

    params["min_samples_split"] = st.slider(
        "Minimum Samples Split",
        2,
        20,
        2
    )

    params["min_samples_leaf"] = st.slider(
        "Minimum Samples Leaf",
        1,
        20,
        1
    )

    return params


# ==========================================================
# Dispatcher
# ==========================================================

MODEL_PARAMETER_MAP = {

    "Linear Regression":
        linear_regression_params,

    "Polynomial Regression":
        polynomial_regression_params,

    "Lasso Regression":
        lasso_regression_params,

    "Elastic Net":
        elastic_net_params,

    "Decision Tree":
        decision_tree_params,

    "Random Forest":
        random_forest_params,

    "XGBoost Regressor":
        xgboost_regressor_params,

    "CatBoost Regressor":
        catboost_regressor_params,

    "Logistic Regression":
        logistic_regression_params,

    "XGBoost Classifier":
        xgboost_classifier_params,

    "CatBoost Classifier":
        catboost_classifier_params

}


# ==========================================================
# Main Function
# ==========================================================

def get_hyperparameters(model_name):

    st.subheader("Hyperparameters")

    mode = st.radio(

        "Hyperparameter Mode",

        [

            "Default",

            "Manual"

        ],

        horizontal=True

    )

    if mode == "Default":

        st.info(

            "Using the default hyperparameters recommended by scikit-learn."

        )

        return {}

    if model_name in MODEL_PARAMETER_MAP:

        return MODEL_PARAMETER_MAP[model_name]()

    st.info(

        "This model has no tunable hyperparameters."

    )

    return {}