import streamlit as st

# ==========================================================
# Pipeline
# ==========================================================

PIPELINE = [
    "Dataset",
    "Target",
    "Features",
    "Models",
    "Split",
    "Preprocessing",
    "Training",
    "Evaluation",
    "Plots",
    "Notebook",
    "Export"
]

# ==========================================================
# Sidebar
# ==========================================================

def show_sidebar(project):

    st.sidebar.title("📊 ML Studio")

    st.sidebar.divider()

    st.sidebar.subheader("📁 Current Project")

    st.sidebar.write(f"**Project:** {project['name']}")
    st.sidebar.write(f"**Dataset:** {project['dataset']}")
    st.sidebar.write(f"**Rows:** {project['rows']}")
    st.sidebar.write(f"**Columns:** {project['columns']}")
    st.sidebar.write(f"**Problem:** {project['problem']}")
    st.sidebar.write(f"**Target:** {project['target']}")
    st.sidebar.write(f"**Model:** {project['model']}")
    st.sidebar.write(f"**Split:** {project['split']}")

    if isinstance(project["features"], list):
        feature_count = len(project["features"])
    else:
        feature_count = project["features"]

    st.sidebar.write(f"**Features:** {feature_count}")

    st.sidebar.divider()

    current_step = 0

    if project["dataset"] != "No Dataset":
        current_step += 1

    if project["target"] != "-":
        current_step += 1

    if feature_count > 0:
        current_step += 1

    if project["model"] != "-":
        current_step += 1

    if project["split"] != "-":
        current_step += 1

    st.sidebar.subheader("🧠 Pipeline")

    for i, step in enumerate(PIPELINE):

        if i < current_step:
            st.sidebar.success(f"✔ {step}")

        elif i == current_step:
            st.sidebar.info(f"➜ {step}")

        else:
            st.sidebar.write(f"○ {step}")


# ==========================================================
# Dataset
# ==========================================================

def upload_dataset():

    return st.file_uploader(
        "Upload Dataset",
        type=["csv"]
    )
def show_dataset_summary(df, summary):

    st.success("✅ Dataset Loaded Successfully!")

    col1, col2, col3 = st.columns(3)

    col1.metric("Rows", summary["rows"])
    col2.metric("Columns", summary["columns"])
    col3.metric("Duplicates", summary["duplicates"])

    st.subheader("Dataset Preview")

    st.dataframe(df.head())


# ==========================================================
# Target
# ==========================================================

def select_target(df):

    st.subheader("🎯 Target Variable")

    target = st.selectbox(
        "Target Column (Y)",
        df.columns
    )

    target_unit = st.text_input(
        "Target Unit (Optional)",
        placeholder="Example: MPa, °C, %, mm³/Nm, -, HV"
    )

    return target, target_unit


# ==========================================================
# Problem Type
# ==========================================================

def select_problem_type():

    return st.radio(
        "Select Machine Learning Task",
        [
            "Regression",
            "Classification"
        ],
        horizontal=True
    )


# ==========================================================
# Features
# ==========================================================

def select_features(df, target):

    return st.multiselect(
        "Select Features (X)",
        [c for c in df.columns if c != target],
        default=[c for c in df.columns if c != target]
    )


# ==========================================================
# Model
# ==========================================================

def select_model(problem_type,
                 regression_models,
                 classification_models):

    if problem_type == "Regression":

        model_list = list(regression_models.keys())

    else:

        model_list = list(classification_models.keys())

    return st.selectbox(
        "Choose Model",
        model_list
    )


# ==========================================================
# Split
# ==========================================================

def select_split():

    st.subheader("Train/Test Split")

    split_method = st.selectbox(
        "Split Method",
        [
            "Train-Test Split",
            "K-Fold Cross Validation",
            "Stratified K-Fold Cross Validation"
        ]
    )

    train_percent = 80
    folds = 5

    if split_method == "Train-Test Split":

        train_percent = st.slider(
            "Training Percentage (%)",
            50,
            95,
            80,
            5
        )

        st.info(
            f"Training: {train_percent}% | Testing: {100-train_percent}%"
        )

    else:

        folds = st.selectbox(
            "Number of Folds",
            [3, 5, 10],
            index=1
        )

        st.info(
            f"{folds}-Fold Cross Validation Selected"
        )

    return split_method, train_percent, folds

# ==========================================================
# Evaluation Metrics
# ==========================================================
def show_metrics(problem_type, metrics):

    st.divider()

    st.subheader("📈 Evaluation Results")

    if problem_type == "Regression":

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("R² Score", f"{metrics['R2 Score']:.4f}")
        col2.metric("RMSE", f"{metrics['RMSE']:.4f}")
        col3.metric("MAE", f"{metrics['MAE']:.4f}")
        col4.metric("MAPE", f"{metrics['MAPE']:.2f}%")

    else:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Accuracy", f"{metrics['Accuracy']:.2%}")
        col2.metric("Precision", f"{metrics['Precision']:.2%}")
        col3.metric("Recall", f"{metrics['Recall']:.2%}")
        col4.metric("F1 Score", f"{metrics['F1 Score']:.2%}")

        st.subheader("Confusion Matrix")

        st.write(metrics["Confusion Matrix"])
# ==========================================================
# Plot Settings
# ==========================================================

def plot_settings():

    st.subheader("Plot Settings")

    plot_quality = st.selectbox(
        "Plot Quality",
        [
            "Screen Preview (150 DPI)",
            "Publication (300 DPI)",
            "High Quality (600 DPI)",
            "Ultra Quality (1200 DPI)"
        ],
        index=1
    )

    figure_width = st.selectbox(
        "Figure Width",
        [
            "Single Column (90 mm)",
            "Double Column (190 mm)"
        ]
    )

    export_format = st.selectbox(
        "Export Format",
        [
            "PNG",
            "TIFF",
            "PDF",
            "SVG"
        ]
    )

    return figure_width, plot_quality, export_format
def visualization_panel(problem_type):

    st.divider()

    st.subheader("📊 Visualization")

    if problem_type == "Regression":

        plots = st.multiselect(
            "Select Plots",
            [
                "Actual vs Predicted",
                "Residual Plot",
                "Residual Distribution",
                "Prediction Error",
                "Feature Importance"
            ],
            default=[
                "Actual vs Predicted",
                "Residual Plot"
            ]
        )

    else:

        plots = st.multiselect(
            "Select Plots",
            [
                "Confusion Matrix",
                "ROC Curve",
                "Precision-Recall Curve",
                "Feature Importance",
                "Class Distribution"
            ],
            default=[
                "Confusion Matrix"
            ]
        )

    figure_width, plot_quality, export_format = plot_settings()

    generate = st.button(
        "📈 Generate Plots",
        use_container_width=True
    )

    return {
    "selected_plots": plots,
    "figure_width": figure_width,
    "plot_quality": plot_quality,
    "export_format": export_format,
    "generate": generate
}

# ==========================================================
# Preprocessing
# ==========================================================

def preprocessing_panel(df, problem_type, model_name):

    st.subheader("🧹 Preprocessing")

    numeric_columns = list(
        df.select_dtypes(
            include=["number"]
        ).columns
    )

    categorical_columns = list(
        df.select_dtypes(
            include=["object", "category", "bool"]
        ).columns
    )

    has_missing = df.isnull().sum().sum() > 0

    tree_models = [

        "Decision Tree",

        "Random Forest",

        "XGBoost",

        "CatBoost"

    ]

    # -----------------------------------------------------
    # Missing Values
    # -----------------------------------------------------

    if has_missing:

        missing_method = st.selectbox(

            "Missing Value Strategy",

            [

                "None",

                "Mean",

                "Median",

                "Most Frequent",

                "Drop Rows"

            ]

        )

    else:

        st.success("✅ No missing values detected.")

        missing_method = "None"

    # -----------------------------------------------------
    # Encoding
    # -----------------------------------------------------

    if len(categorical_columns) > 0:

        encoding_method = st.selectbox(

            "Categorical Encoding",

            [

                "None",

                "One-Hot",

                "Ordinal"

            ]

        )

    else:

        st.success("✅ No categorical columns detected.")

        encoding_method = "None"

    # -----------------------------------------------------
    # Scaling
    # -----------------------------------------------------

    if len(numeric_columns) > 0:

        if model_name in tree_models:

            st.info(
                "Tree-based models generally do not require feature scaling."
            )

        scaling_method = st.selectbox(

            "Feature Scaling",

            [

                "None",

                "StandardScaler",

                "MinMaxScaler",

                "RobustScaler"

            ]

        )

    else:

        st.success("✅ No numeric columns detected.")

        scaling_method = "None"

    return {

    "missing_strategy": missing_method,

    "encoding_strategy": encoding_method,

    "scaling_strategy": scaling_method,

}
