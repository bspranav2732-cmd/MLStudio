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
# KNN
# ==========================================================

def knn_params():

    params = {}

    params["n_neighbors"] = st.slider(
        "Number of Neighbors",
        1,
        30,
        5
    )

    params["weights"] = st.selectbox(
        "Weights",
        [
            "uniform",
            "distance"
        ]
    )

    params["metric"] = st.selectbox(
        "Distance Metric",
        [
            "minkowski",
            "euclidean",
            "manhattan"
        ]
    )

    return params

# ==========================================================
# Support Vector Machine
# ==========================================================

def svm_params():

    params = {}

    params["C"] = st.slider(
        "Regularization (C)",
        0.01,
        10.0,
        1.0,
        step=0.01
    )

    params["kernel"] = st.selectbox(
        "Kernel",
        [
            "rbf",
            "linear",
            "poly",
            "sigmoid"
        ]
    )

    params["gamma"] = st.selectbox(
        "Gamma",
        [
            "scale",
            "auto"
        ]
    )

    return params

# ==========================================================
# Naive Bayes
# ==========================================================

def naive_bayes_params():

    st.info(
        "Gaussian Naive Bayes has no tunable hyperparameters."
    )

    return {}


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

    "Decision Tree":
        decision_tree_params,

    "Random Forest":
        random_forest_params,

    "Logistic Regression":
        logistic_regression_params,

    "K-Nearest Neighbors":
        knn_params,

    "Support Vector Machine":
        svm_params,

    "Naive Bayes":
        naive_bayes_params

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