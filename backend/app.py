import time
start = time.time()
import streamlit as st
from dataset import load_dataset, dataset_summary
from ui import (
    show_sidebar,upload_dataset,show_dataset_summary,select_target,
    select_problem_type,select_features,select_model,select_split,
    show_metrics, visualization_panel,preprocessing_panel )
from plot import show_plots
from models import (REGRESSION_MODELS,CLASSIFICATION_MODELS)
from hyperparameters import get_hyperparameters
from engine import run_training

# ----------------------------------------
# Page Configuration
# ----------------------------------------

st.set_page_config(
    page_title="ML Studio",
   
    layout="wide"
)

st.title("ML Studio")

if "project" not in st.session_state:

    st.session_state.project = {

        "name": "Untitled",

        "dataset": "No Dataset",

        "rows": "-",

        "columns": "-",

        "problem": "-",

        "target": "-",

        "features": 0,

        "model": "-",

        "split": "-",

        "step": 0
    }

project = st.session_state.project

# Initial Sidebar
show_sidebar(project)

# ----------------------------------------
# Upload Dataset
# ----------------------------------------

uploaded_file = upload_dataset()

if uploaded_file is not None:

    # Load Dataset
    df = load_dataset(uploaded_file)

    summary = dataset_summary(df)

    # Update Project
    project["dataset"] = uploaded_file.name
    project["rows"] = summary["rows"]
    project["columns"] = summary["columns"]

    show_dataset_summary(df, summary)

    # ----------------------------------------
    # Target Selection
    # ----------------------------------------

    target, target_unit = select_target(df)

    project["target"] = target
    

    # ----------------------------------------
    # Problem Type
    # ----------------------------------------

    problem_type = select_problem_type()

    project["problem"] = problem_type

    # ----------------------------------------
    # Feature Selection
    # ----------------------------------------

    features = select_features(df, target)

    project["features"] = features

    # ----------------------------------------
    # Model Selection
    # ----------------------------------------

    model = select_model(
        problem_type,
        REGRESSION_MODELS,
        CLASSIFICATION_MODELS
    )

    project["model"] = model
   
    hyperparameters = get_hyperparameters(model)
    # ----------------------------------------
    # Train/Test Split
    # ----------------------------------------

    split_method, train_percent, folds = select_split()

    project["split"] = split_method

    preprocessing = preprocessing_panel(
    df,
    problem_type,
    model
)

    # ==========================================================
    # Train Model
    # ==========================================================

    st.divider()

    if st.button(
        "Train Model",
        use_container_width=True
    ):

        with st.spinner("Training Model..."):

            config = {
                "target": target,
                "target_name": target,
                "target_unit": target_unit,
                "features": features,
                "problem_type": problem_type,
                "model_name": model,
                "hyperparameters": hyperparameters,
                "split_method": split_method,
                "train_percent": train_percent,
                "folds": folds,
                "preprocessing": preprocessing
            }

            pipeline = run_training(df, config)
            st.session_state["results"] = pipeline["results"]
            st.session_state["evaluation"] = pipeline["evaluation"]
            st.session_state["config"] = config

            st.success("✅ Model Trained Successfully!")

    # ==========================================================
    # Evaluation
    # ==========================================================

    if "evaluation" in st.session_state:

        show_metrics(
            st.session_state["results"]["problem_type"],
            st.session_state["evaluation"]["metrics"]
        )

    # ==========================================================
    # Visualization
    # ==========================================================

    if "results" in st.session_state:

        results = st.session_state["results"]

        viz = visualization_panel(
            results["problem_type"]
        )

        if viz["generate"]:

            show_plots(
                results=results,
                selected_plots=viz["selected_plots"],
                figure_width=viz["figure_width"],
                plot_quality=viz["plot_quality"],
                export_format=viz["export_format"]
            )

    # ==========================================================
    # Export System
    # ==========================================================
    if "results" in st.session_state and "evaluation" in st.session_state and "config" in st.session_state:
        from export.export_ui import show_export_section
        show_export_section(
            st.session_state["config"],
            st.session_state["results"],
            st.session_state["evaluation"]
        )
print(f"Startup Time: {time.time() - start:.2f} seconds")