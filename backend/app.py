import streamlit as st
from dataset import load_dataset, dataset_summary
from ui import (
    show_sidebar,upload_dataset,show_dataset_summary,select_target,
    select_problem_type,select_features,model_configuration_panel,
    show_metrics, visualization_panel,preprocessing_panel )
from backend.theme import inject_css
from plot import show_plots
from models import (REGRESSION_MODELS,CLASSIFICATION_MODELS)
from hyperparameters import get_hyperparameters
from engine import run_training

# ----------------------------------------
# Page Configuration
# ----------------------------------------

st.set_page_config(
    page_title="Solvosys",
   
    layout="wide"
)

inject_css()
st.title("Solvosys")

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

    try:
        df = load_dataset(uploaded_file)
    except Exception as e:
        st.error(str(e))
        st.stop()

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
    # Model Configuration
    # ----------------------------------------

    model_config = model_configuration_panel(
        problem_type,
        REGRESSION_MODELS,
        CLASSIFICATION_MODELS
    )

    project["model"] = model_config["model"]
    project["split"] = model_config["split_method"]

    preprocessing = preprocessing_panel(
        df,
        problem_type,
        model_config["model"]
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
            if len(features) == 0:
                st.error("Select at least one feature before training.")
                st.stop()

            config = {
                "target": target,
                "target_name": target,
                "target_unit": target_unit,
                "features": features,
                "problem_type": problem_type,
                "model_name": model_config["model"],
                "hyperparameters": model_config["hyperparameters"],
                "split_method": model_config["split_method"],
                "train_percent": model_config["train_percent"],
                "folds": model_config["folds"],
                "repeats": model_config["repeats"],
                "optimization": model_config["optimization"],
                "opt_iters": model_config["opt_iters"],
                "opt_cv": model_config["opt_cv"],
                "use_multiple_seeds": model_config["use_multiple_seeds"],
                "num_seeds": model_config["num_seeds"],
                "use_oob": model_config["use_oob"],
                "preprocessing": preprocessing
            }

            try:
                progress_placeholder = st.empty()
                pipeline = run_training(
                    df, 
                    config, 
                    progress_callback=progress_placeholder.info
                )
                progress_placeholder.empty()
                
                st.session_state["results"] = pipeline["results"]
                st.session_state["evaluation"] = pipeline["evaluation"]
                st.session_state["training_time"] = pipeline.get("training_time", 0.0)
                st.session_state["config"] = config

                # Invalidate export cache so artifacts regenerate for new model
                st.session_state["export_cache"] = {}
                
                # Invalidate plot cache for new model
                if "generated_plots" in st.session_state:
                    del st.session_state["generated_plots"]
                if "generated_plots_key" in st.session_state:
                    del st.session_state["generated_plots_key"]
                if "plot_config" in st.session_state:
                    del st.session_state["plot_config"]

                st.success("Model Trained Successfully.")
            except Exception as e:
                import traceback
                import logging
                logging.error(f"Training failed: {traceback.format_exc()}")
                st.error(f"An error occurred during training: {str(e)}")

    # ==========================================================
    # Results & Comparison Tabs
    # ==========================================================
    st.divider()
    tab_current, tab_compare = st.tabs(["Current Experiment", "Compare Models"])

    with tab_current:
        # ==========================================================
        # Evaluation
        # ==========================================================
        if "evaluation" in st.session_state:
            
            # 1. Evaluation Protocol Badge
            if "evaluation_config" in st.session_state["results"]:
                eval_config = st.session_state["results"]["evaluation_config"]
                
                is_cv = "Cross Validation" in eval_config.get("validation", "") or "CV" in eval_config.get("validation", "")
                
                badge_md = "#### Evaluation Protocol\n\n"
                badge_md += f"**Validation**\n{eval_config.get('validation', 'N/A')}\n\n"
                badge_md += f"**Optimization**\n{eval_config.get('optimization', 'N/A')}\n\n"
                
                if is_cv:
                    badge_md += "**Reason**\nNested CV not yet implemented\n\n"
                
                if st.session_state["config"]["model_name"] == "Random Forest":
                    badge_md += f"**Random Forest OOB**\n{'Enabled' if eval_config.get('oob', False) else 'Disabled'}\n\n"
                    
                badge_md += f"**Random State**\n{eval_config.get('random_state', 'N/A')}\n\n"
                
                st.info(badge_md)

            # 2. Metrics
            show_metrics(
                st.session_state["results"]["problem_type"],
                st.session_state["evaluation"]["metrics"]
            )
            
            # Button to add current run to comparison list
            st.write("")
            if st.button("Add Current Run to Comparison", use_container_width=True):
                if "comparison_runs" not in st.session_state:
                    st.session_state["comparison_runs"] = []
                
                from comparison import add_run
                st.session_state["comparison_runs"] = add_run(
                    st.session_state["comparison_runs"],
                    st.session_state["config"],
                    st.session_state["evaluation"],
                    st.session_state.get("training_time", 0.0)
                )
                st.toast(f"Added model '{st.session_state['config']['model_name']}' to comparison!")
                st.rerun()

        # ==========================================================
        # Visualization
        # ==========================================================
        if "results" in st.session_state:
            results = st.session_state["results"]
            viz = visualization_panel(results["problem_type"])
            plot_config = st.session_state.get("plot_config")

            if plot_config:
                show_plots(
                    results=results,
                    selected_plots=plot_config["selected_plots"],
                    figure_width=plot_config["figure_width"],
                    plot_quality=plot_config["plot_quality"],
                    export_format=plot_config["export_format"]
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

    with tab_compare:
        from comparison_ui import show_comparison_tab
        show_comparison_tab(problem_type)