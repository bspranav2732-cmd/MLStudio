import streamlit as st

# ==========================================================
# Sidebar
# ==========================================================

def show_sidebar(project):

    if "appearance" not in st.session_state:
        st.session_state["appearance"] = "Follow System"

    appearance = st.sidebar.selectbox(
        "Appearance",
        ["Light", "Dark", "Follow System"],
        index=["Light", "Dark", "Follow System"].index(st.session_state["appearance"])
    )
    if appearance != st.session_state["appearance"]:
        st.session_state["appearance"] = appearance
        st.rerun()

    st.sidebar.markdown("<h2 style='margin-bottom:0;'>Solvosys</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("<p style='font-size:12px; font-style:italic; color:#666666; margin-top:0;'>Machine Learning Workbench</p>", unsafe_allow_html=True)
    st.sidebar.divider()

    # DATA
    st.sidebar.write("**DATA**")
    st.sidebar.write(f"Upload Dataset: {project.get('dataset', '-')}")
    st.sidebar.write(f"Rows: {project.get('rows', '-')}")
    st.sidebar.write(f"Columns: {project.get('columns', '-')}")
    st.sidebar.divider()

    # CONFIGURATION
    st.sidebar.write("**CONFIGURATION**")
    st.sidebar.write(f"Problem Type: {project.get('problem', '-')}")
    st.sidebar.write(f"Target Variable: {project.get('target', '-')}")
    
    if isinstance(project.get("features"), list):
        feature_count = len(project["features"])
    else:
        try:
            feature_count = int(project.get("features", 0))
        except (ValueError, TypeError):
            feature_count = 0
    st.sidebar.write(f"Feature Selection: {feature_count} selected")
    st.sidebar.divider()

    # MODEL
    st.sidebar.write("**MODEL**")
    st.sidebar.write(f"Model Selection: {project.get('model', '-')}")
    
    config = st.session_state.get("config", {})
    hp = config.get("hyperparameters", {})
    if hp:
        hp_str = ", ".join([f"{k}={v}" for k, v in hp.items() if k != "random_state" and k != "random_seed"])
        if not hp_str:
            hp_str = "Manual (default random state)"
        st.sidebar.write(f"Hyperparameters: {hp_str}")
    else:
        st.sidebar.write("Hyperparameters: Default")
    st.sidebar.divider()

    # PREPROCESSING
    st.sidebar.write("**PREPROCESSING**")
    preprocessing = config.get("preprocessing", {})
    st.sidebar.write(f"Missing Values: {preprocessing.get('missing_strategy', '-')}")
    st.sidebar.write(f"Encoding: {preprocessing.get('encoding_strategy', '-')}")
    st.sidebar.write(f"Scaling: {preprocessing.get('scaling_strategy', '-')}")
    st.sidebar.divider()

    # VALIDATION
    st.sidebar.write("**VALIDATION**")
    st.sidebar.write(f"Split Method: {project.get('split', '-')}")
    
    train_percent = config.get("train_percent")
    if train_percent is not None:
        st.sidebar.write(f"Train/Test Percentage: {train_percent}%")
    else:
        st.sidebar.write("Train/Test Percentage: -")
        
    folds = config.get("folds")
    if folds is not None:
        st.sidebar.write(f"Cross Validation Folds: {folds}")
    else:
        st.sidebar.write("Cross Validation Folds: -")
    st.sidebar.divider()

    # VISUALIZATION
    st.sidebar.write("**VISUALIZATION**")
    if "results" in st.session_state:
        st.sidebar.write("Plot Settings: Active")
    else:
        st.sidebar.write("Plot Settings: Not Generated")
    st.sidebar.divider()

    # COMPARE
    st.sidebar.write("**COMPARE**")
    comparison_runs = len(st.session_state.get("comparison_runs", []))
    st.sidebar.write(f"Compare Models: {comparison_runs} runs saved")
    st.sidebar.divider()

    # EXPORT
    st.sidebar.write("**EXPORT**")
    if "results" in st.session_state:
        st.sidebar.write("Export Options: Ready")
    else:
        st.sidebar.write("Export Options: Pending")


# ==========================================================
# Dataset
# ==========================================================

def upload_dataset():

    return st.file_uploader(
        "Upload Dataset",
        type=["csv"]
    )
def show_dataset_summary(df, summary):

    st.success("Dataset Loaded Successfully.")

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

    st.subheader("Target Variable")

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
# Model Configuration
# ==========================================================

def model_configuration_panel(problem_type, regression_models, classification_models):
    st.subheader("Model Configuration")

    if problem_type == "Regression":
        model_list = list(regression_models.keys())
    else:
        model_list = list(classification_models.keys())

    model = st.selectbox(
        "Choose Model",
        model_list
    )

    validation_method = st.selectbox(
        "Validation",
        [
            "Train-Test Split",
            "K-Fold Cross Validation",
            "Stratified K-Fold Cross Validation",
            "Repeated K-Fold",
            "Repeated Stratified K-Fold"
        ]
    )

    train_percent = 80
    folds = 5
    repeats = 3

    if validation_method == "Train-Test Split":
        train_percent = st.slider(
            "Training Percentage (%)",
            50,
            95,
            80,
            5
        )
        st.info(f"Training: {train_percent}% | Testing: {100-train_percent}%")
    else:
        folds = st.selectbox(
            "Number of Folds",
            [3, 5, 10],
            index=1
        )
        if "Repeated" in validation_method:
            repeats = st.selectbox(
                "Number of Repeats",
                [2, 3, 5, 10],
                index=1
            )

    if validation_method != "Train-Test Split":
        optimization_method = st.selectbox(
            "Hyperparameter Optimization",
            ["None"],
            disabled=True,
            help="Nested CV for optimization is planned for a future release."
        )
        st.info("Cross Validation with Optimization is disabled to prevent data leakage. Nested CV will be supported in a future release.")
    else:
        optimization_method = st.selectbox(
            "Hyperparameter Optimization",
            ["None", "Random Search", "Grid Search"]
        )

    opt_iters = 10
    opt_cv = 3

    if optimization_method == "Random Search":
        opt_iters = st.slider("Random Search Iterations", 5, 100, 10, 5)
        opt_cv = st.selectbox("Optimization CV Folds", [2, 3, 5], index=1)
    elif optimization_method == "Grid Search":
        opt_cv = st.selectbox("Optimization CV Folds", [2, 3, 5], index=1)
        
    use_multiple_seeds = st.checkbox("Multiple Random Seed Evaluation")
    num_seeds = 1
    if use_multiple_seeds:
        num_seeds = st.selectbox("Number of Seeds", [5, 10, 20, 50], index=1)
        
    use_oob = False
    if model == "Random Forest":
        use_oob = st.checkbox("Enable OOB Score (Out-of-Bag)")

    from hyperparameters import get_hyperparameters
    with st.expander("Advanced Settings"):
        hyperparameters = get_hyperparameters(model)
        
    return {
        "model": model,
        "split_method": validation_method,
        "train_percent": train_percent,
        "folds": folds,
        "repeats": repeats,
        "optimization": optimization_method,
        "opt_iters": opt_iters,
        "opt_cv": opt_cv,
        "use_multiple_seeds": use_multiple_seeds,
        "num_seeds": num_seeds,
        "use_oob": use_oob,
        "hyperparameters": hyperparameters
    }

# ==========================================================
# Evaluation Metrics
# ==========================================================
def format_metric_value(value, format_type="float"):
    """
    Safely formats a metric for UI display.
    format_type: 'float' (e.g. 0.1234), 'percent_scaled' (e.g. 0.1234 -> 12.34%), 'percent_raw' (e.g. 12.34 -> 12.34%)
    """
    if isinstance(value, str):
        return value
    if value is None:
        return "N/A"
        
    if isinstance(value, dict) and "mean" in value and "std" in value:
        mean_val = value["mean"]
        std_val = value["std"]
        try:
            if format_type == "percent_scaled":
                return f"{mean_val:.2%} ± {std_val:.2%}"
            elif format_type == "percent_raw":
                return f"{mean_val:.2f}% ± {std_val:.2f}%"
            else:
                return f"{mean_val:.4f} ± {std_val:.4f}"
        except (ValueError, TypeError):
            return f"{mean_val} ± {std_val}"
            
    try:
        if format_type == "percent_scaled":
            return f"{value:.2%}"
        elif format_type == "percent_raw":
            return f"{value:.2f}%"
        else:
            return f"{value:.4f}"
    except (ValueError, TypeError):
        return str(value)

def show_metrics(problem_type, metrics):

    st.divider()

    st.subheader("Evaluation Results")

    if problem_type == "Regression":

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("R² Score", format_metric_value(metrics.get('R2 Score'), "float"))
        col2.metric("RMSE", format_metric_value(metrics.get('RMSE'), "float"))
        col3.metric("MAE", format_metric_value(metrics.get('MAE'), "float"))
        col4.metric("MAPE", format_metric_value(metrics.get('MAPE'), "percent_raw"))

    else:

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Accuracy", format_metric_value(metrics.get('Accuracy'), "percent_scaled"))
        col2.metric("Precision", format_metric_value(metrics.get('Precision'), "percent_scaled"))
        col3.metric("Recall", format_metric_value(metrics.get('Recall'), "percent_scaled"))
        col4.metric("F1 Score", format_metric_value(metrics.get('F1 Score'), "percent_scaled"))

        st.subheader("Confusion Matrix")

        st.write(metrics.get("Confusion Matrix", "N/A"))
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

    st.subheader("Visualization")

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

    if st.button(
        "Generate Plots",
        use_container_width=True
    ):
        st.session_state["plot_config"] = {
            "selected_plots": plots,
            "figure_width": figure_width,
            "plot_quality": plot_quality,
            "export_format": export_format
        }

    return {
        "selected_plots": plots,
        "figure_width": figure_width,
        "plot_quality": plot_quality,
        "export_format": export_format
    }

# ==========================================================
# Preprocessing
# ==========================================================

def preprocessing_panel(df, problem_type, model_name):

    st.subheader("Preprocessing")

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

        "XGBoost Regressor",

        "XGBoost Classifier",

        "CatBoost Regressor",

        "CatBoost Classifier"

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

        st.success("No missing values detected.")

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

        st.success("No categorical columns detected.")

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

        st.success("No numeric columns detected.")

        scaling_method = "None"

    return {

    "missing_strategy": missing_method,

    "encoding_strategy": encoding_method,

    "scaling_strategy": scaling_method,

}


def inject_custom_css() -> None:
    theme = st.session_state.get("theme", "Light")
    if theme == "Dark":
        bg = "#313338"
        sidebar_bg = "#2B2D31"
        panel_bg = "#383A40"
        hover_bg = "#404249"
        border_color = "#1E1F22"
        accent_color = "#2D6CDF"
        text_primary = "#F2F3F5"
        text_secondary = "#B5BAC1"
        input_bg = "#1E1F22"
        button_bg = "#2B2D31"
        button_hover = "#404249"
        button_pressed = "#1E1F22"
        table_even_row = "#2F3136"
        table_odd_row = "#383A40"
        
        # Alerts
        success_bg = "#1a4d2e"
        success_text = "#a3d9b1"
        success_border = "#2d6a4f"
        warn_bg = "#664400"
        warn_text = "#ffda85"
        warn_border = "#996600"
        err_bg = "#5c1a1a"
        err_text = "#ffb3b3"
        err_border = "#8a2525"
        info_bg = "#1a3c5c"
        info_text = "#a3cce8"
        info_border = "#255a8a"
    else:
        bg = "#ECECEC"
        sidebar_bg = "#E1E1E1"
        panel_bg = "#F6F6F6"
        hover_bg = "#E9E9E9"
        border_color = "#A7A7A7"
        accent_color = "#004C99"
        text_primary = "#1A1A1A"
        text_secondary = "#555555"
        input_bg = "#FFFFFF"
        button_bg = "#E1E1E1"
        button_hover = "#D0D0D0"
        button_pressed = "#C0C0C0"
        table_even_row = "#F6F6F6"
        table_odd_row = "#FFFFFF"
        
        # Alerts
        success_bg = "#e6f4ea"
        success_text = "#137333"
        success_border = "#ceead6"
        warn_bg = "#fef7e0"
        warn_text = "#b06000"
        warn_border = "#feefc3"
        err_bg = "#fce8e6"
        err_text = "#c5221f"
        err_border = "#fad2cf"
        info_bg = "#e8f0fe"
        info_text = "#1967d2"
        info_border = "#d2e3fc"

    st.markdown(f"""
<style>
/* 1. TYPOGRAPHY & BASIC COLORS */
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .stApp {{
    font-family: Tahoma, Verdana, 'Trebuchet MS', sans-serif !important;
    background-color: {bg} !important;
    color: {text_primary} !important;
}}

/* 2. MATERIAL SYMBOLS ICON FONT PROTECTION */
span.material-symbols-rounded,
span.material-symbols-outlined,
span[class*="material-symbols"],
[data-testid="collapsedControl"] span,
[data-testid="stSidebarCollapseButton"] span {{
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
    font-size: 24px !important;
    visibility: visible !important;
    -webkit-font-feature-settings: 'liga' !important;
    font-feature-settings: 'liga' !important;
}}

/* 3. SIDEBAR LAYOUT (FIX 9) */
[data-testid="stSidebar"] {{
    background-color: {sidebar_bg} !important;
    border-right: 1px solid {border_color} !important;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] label {{
    color: {text_primary} !important;
    font-family: Tahoma, Verdana, sans-serif !important;
}}
hr {{
    margin-top: 5px !important;
    margin-bottom: 5px !important;
    border-top: 1px solid {border_color} !important;
}}

/* 4. INPUT CONTROLS & FILE UPLOADER (FIX 3 & 4) */
div[data-baseweb="select"], div[data-baseweb="input"], .stNumberInput input, .stTextInput input, .stTextArea textarea {{
    border: 1px solid {border_color} !important;
    border-radius: 0px !important;
    background-color: {input_bg} !important;
    font-family: Tahoma, Verdana, sans-serif !important;
    color: {text_primary} !important;
    box-shadow: none !important;
    padding: 2px 4px !important;
}}
div[data-baseweb="select"] span:not([class*="material-symbols"]), div[data-baseweb="select"] div {{
    color: {text_primary} !important;
}}
div[data-baseweb="select"]:focus-within, div[data-baseweb="input"]:focus-within, .stNumberInput input:focus, .stTextInput input:focus {{
    border-color: {accent_color} !important;
    box-shadow: none !important;
    outline: none !important;
}}
[data-testid="stFileUploader"] {{
    background-color: {panel_bg} !important;
    border: 1px solid {border_color} !important;
    border-radius: 0px !important;
    padding: 10px !important;
}}
[data-testid="stFileUploader"] section {{
    background-color: transparent !important;
    color: {text_secondary} !important;
}}
[data-testid="stFileUploader"]:hover {{
    background-color: {hover_bg} !important;
}}
[data-testid="stFileUploaderDropzone"] {{
    background-color: transparent !important;
}}
span[data-baseweb="tag"] {{
    background-color: {sidebar_bg} !important;
    border: 1px solid {border_color} !important;
    color: {text_primary} !important;
}}
div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {{
    font-family: Tahoma, Verdana, sans-serif !important;
    color: {text_primary} !important;
}}

/* 5. BUTTONS (FIX 8) */
button, .stButton button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {{
    border: 1px solid {border_color} !important;
    border-radius: 2px !important;
    background-color: {button_bg} !important;
    color: {text_primary} !important;
    font-weight: normal !important;
    font-family: Tahoma, Verdana, sans-serif !important;
    box-shadow: none !important;
    transition: background-color 0.1s ease !important;
    padding: 4px 12px !important;
    min-height: 28px !important;
}}
button:hover, .stButton button:hover {{
    background-color: {button_hover} !important;
    border-color: {border_color} !important;
    color: {text_primary} !important;
}}
button:active, .stButton button:active {{
    background-color: {button_pressed} !important;
    border-color: {border_color} !important;
}}
[data-testid="stBaseButton-primary"] {{
    background-color: {accent_color} !important;
    color: #ffffff !important;
    border: 1px solid {accent_color} !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    background-color: {accent_color} !important;
    color: #ffffff !important;
    opacity: 0.9 !important;
}}

/* 6. METRIC CARDS (FIX 6) */
div[data-testid="stMetric"] {{
    border: 1px solid {border_color} !important;
    padding: 8px 12px !important;
    background-color: {panel_bg} !important;
    border-radius: 0px !important;
}}
div[data-testid="stMetricValue"] {{
    font-family: Tahoma, Verdana, sans-serif !important;
    font-weight: bold !important;
    color: {text_primary} !important;
    font-size: 24px !important;
}}
div[data-testid="stMetricLabel"] {{
    font-family: Tahoma, Verdana, sans-serif !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    color: {text_secondary} !important;
}}

/* 7. ALERTS (FIX 7) */
div[data-testid="stAlert"]:has(svg[data-testid="stIconSuccess"]),
div[data-testid="stNotification"]:has(svg[data-testid="stIconSuccess"]) {{
    background-color: {success_bg} !important;
    color: {success_text} !important;
    border: 1px solid {success_border} !important;
    border-radius: 0px !important;
}}
div[data-testid="stAlert"]:has(svg[data-testid="stIconWarning"]),
div[data-testid="stNotification"]:has(svg[data-testid="stIconWarning"]) {{
    background-color: {warn_bg} !important;
    color: {warn_text} !important;
    border: 1px solid {warn_border} !important;
    border-radius: 0px !important;
}}
div[data-testid="stAlert"]:has(svg[data-testid="stIconError"]),
div[data-testid="stNotification"]:has(svg[data-testid="stIconError"]) {{
    background-color: {err_bg} !important;
    color: {err_text} !important;
    border: 1px solid {err_border} !important;
    border-radius: 0px !important;
}}
div[data-testid="stAlert"]:has(svg[data-testid="stIconInfo"]),
div[data-testid="stNotification"]:has(svg[data-testid="stIconInfo"]) {{
    background-color: {info_bg} !important;
    color: {info_text} !important;
    border: 1px solid {info_border} !important;
    border-radius: 0px !important;
}}
div[data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
    color: inherit !important;
}}

/* 8. DATAFRAME (FIX 5) */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    border: 1px solid {border_color} !important;
    background-color: {panel_bg} !important;
}}
table {{
    border-collapse: collapse !important;
    width: 100% !important;
    font-family: Tahoma, Verdana, sans-serif !important;
    font-size: 12px !important;
    border: 1px solid {border_color} !important;
    background-color: {table_odd_row} !important;
    color: {text_primary} !important;
}}
th {{
    background-color: {sidebar_bg} !important;
    color: {text_primary} !important;
    font-weight: bold !important;
    border: 1px solid {border_color} !important;
    padding: 4px 8px !important;
    text-align: left !important;
}}
td {{
    border: 1px solid {border_color} !important;
    padding: 4px 8px !important;
}}
tr:nth-child(even) td {{
    background-color: {table_even_row} !important;
}}
tr:hover td {{
    background-color: {accent_color} !important;
    color: #ffffff !important;
}}

/* 9. TABS & PANELS */
div[data-testid="stTabBar"] {{
    border-bottom: 1px solid {border_color} !important;
    background-color: {sidebar_bg} !important;
    gap: 0px !important;
}}
div[data-testid="stTab"] {{
    border: 1px solid transparent !important;
    border-radius: 0px !important;
    padding: 6px 16px !important;
    background-color: {button_bg} !important;
    margin-right: 2px !important;
    font-family: Tahoma, Verdana, sans-serif !important;
    color: {text_secondary} !important;
}}
div[data-testid="stTab"][aria-selected="true"] {{
    background-color: {bg} !important;
    border: 1px solid {border_color} !important;
    border-bottom: 1px solid {bg} !important;
    color: {text_primary} !important;
    font-weight: bold !important;
}}
div[data-testid="stTab"]:hover {{
    background-color: {hover_bg} !important;
    color: {text_primary} !important;
}}
div[data-testid="stExpander"], div[data-testid="stExpanderDetails"] {{
    border: 1px solid {border_color} !important;
    border-radius: 0px !important;
    box-shadow: none !important;
    background-color: {panel_bg} !important;
}}

/* 10. HEADERS & TYPOGRAPHY (FIX 10) */
h1, h2, h3, h4, h5, h6 {{
    font-family: Tahoma, Verdana, sans-serif !important;
    font-weight: bold !important;
    color: {text_primary} !important;
    margin-top: 10px !important;
    margin-bottom: 5px !important;
}}
h1 {{
    font-size: 22px !important;
    border-bottom: 2px solid {accent_color} !important;
    padding-bottom: 4px !important;
}}
h2 {{
    font-size: 18px !important;
    border-bottom: 1px solid {border_color} !important;
    padding-bottom: 2px !important;
}}
h3 {{ font-size: 14px !important; }}

/* Base text — exclude Material Symbols icon spans */
p, label {{
    font-family: Tahoma, Verdana, sans-serif !important;
}}

/* Option items */
option {{
    background-color: {panel_bg} !important;
    color: {text_primary} !important;
}}
select {{
    background-color: {input_bg} !important;
    color: {text_primary} !important;
    border: 1px solid {border_color} !important;
}}
</style>
""", unsafe_allow_html=True)
