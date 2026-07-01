"""
Module for rendering the Experiment Comparison interface in Solvosys.
"""

import streamlit as st
import pandas as pd
from comparison import remove_run, clear_runs


def show_comparison_tab(active_problem_type: str) -> None:
    """
    Render the Compare Models section in Streamlit.

    Args:
        active_problem_type (str): "Regression" or "Classification".
    """
    st.divider()
    st.subheader("Compare Models")

    # Initialize comparison list in session state if not present
    if "comparison_runs" not in st.session_state:
        st.session_state["comparison_runs"] = []

    comparison_runs = st.session_state["comparison_runs"]

    # Filter runs by the active problem type to compare comparable experiments
    runs = [run for run in comparison_runs if run["problem_type"] == active_problem_type]

    if not runs:
        st.info(
            "No models added yet.\n\n"
            "Train a model and click the **Add Current Run to Comparison** button."
        )
        return

    st.write(f"Showing comparison for **{active_problem_type}** experiments.")

    # ----------------------------------------------------
    # Table 1 — Generalization Comparison
    # ----------------------------------------------------
    st.write("### 1. Generalization Comparison")
    st.write("Analyzes the performance gap between training data and validation/test data.")

    gen_data = []
    for run in runs:
        train_m = run["train_metrics"]
        val_m = run["validation_metrics"]
        model_name = run["model_name"]

        if active_problem_type == "Regression":
            train_score = train_m.get("R2 Score", 0.0)
            val_score = val_m.get("R2 Score", 0.0)
            gap = abs(train_score - val_score)
            
            gen_data.append({
                "Model": model_name,
                "Training R²": f"{train_score:.4f}",
                "Validation R²": f"{val_score:.4f}",
                "Gap": f"{gap:.4f}"
            })
        else:
            train_score = train_m.get("Accuracy", 0.0)
            val_score = val_m.get("Accuracy", 0.0)
            gap = abs(train_score - val_score)
            
            gen_data.append({
                "Model": model_name,
                "Training Accuracy": f"{train_score:.2%}",
                "Validation Accuracy": f"{val_score:.2%}",
                "Gap": f"{gap:.2%}"
            })

    gen_df = pd.DataFrame(gen_data)
    st.table(gen_df)

    # ----------------------------------------------------
    # Table 2 — Performance Comparison
    # ----------------------------------------------------
    st.write("### 2. Performance Comparison")
    st.write("Compares overall performance metrics and execution time across all saved runs.")

    perf_data = []
    for run in runs:
        m = run["metrics"]
        model_name = run["model_name"]
        t_time = run["training_time"]
        
        # Hyperparameters summary
        hp = run["hyperparameters"]
        hp_str = ", ".join(f"{k}={v}" for k, v in hp.items()) if hp else "Default"

        if active_problem_type == "Regression":
            perf_data.append({
                "Model": model_name,
                "R²": f"{m.get('R2 Score', 0.0):.4f}",
                "RMSE": f"{m.get('RMSE', 0.0):.4f}",
                "MAE": f"{m.get('MAE', 0.0):.4f}",
                "MAPE": f"{m.get('MAPE', 0.0):.2f}%",
                "Hyperparameters": hp_str,
                "Training Time": f"{t_time:.3f}s"
            })
        else:
            perf_data.append({
                "Model": model_name,
                "Accuracy": f"{m.get('Accuracy', 0.0):.2%}",
                "Precision": f"{m.get('Precision', 0.0):.2%}",
                "Recall": f"{m.get('Recall', 0.0):.2%}",
                "F1 Score": f"{m.get('F1 Score', 0.0):.2%}",
                "Hyperparameters": hp_str,
                "Training Time": f"{t_time:.3f}s"
            })

    perf_df = pd.DataFrame(perf_data)
    st.table(perf_df)

    # ----------------------------------------------------
    # Remove & Clear Section
    # ----------------------------------------------------
    st.write("### 3. Manage Saved Runs")
    col1, col2 = st.columns(2)

    with col1:
        # Multiselect using the run position in the master comparison_runs list
        # Map localized run list to master list indices
        run_options = []
        master_indices = []
        for master_idx, run in enumerate(comparison_runs):
            if run["problem_type"] == active_problem_type:
                run_options.append(f"{run['model_name']} ({master_idx + 1})")
                master_indices.append(master_idx)

        selected_options = st.multiselect("Select runs to remove:", run_options)
        
        if st.button("Remove Selected", use_container_width=True):
            if selected_options:
                indices_to_remove = []
                for opt in selected_options:
                    # Extract the master index inside parenthesis
                    master_idx = int(opt.split("(")[-1].replace(")", "")) - 1
                    indices_to_remove.append(master_idx)
                
                remove_run(st.session_state["comparison_runs"], indices_to_remove)
                st.success("Selected runs removed successfully!")
                st.rerun()
            else:
                st.warning("Please select at least one run to remove.")

    with col2:
        st.write("")  # Alignment spacing
        st.write("")
        if st.button("Clear Comparison", use_container_width=True):
            st.session_state["comparison_runs"] = clear_runs()
            st.success("Comparison cleared successfully!")
            st.rerun()
