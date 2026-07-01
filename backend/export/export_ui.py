"""
Module for rendering the Export panel in the Streamlit UI.

All export artifacts are cached in st.session_state["export_cache"]
so they are generated only once per trained model.  The cache is
invalidated in app.py whenever a new model is trained.
"""

import os
import tempfile
import streamlit as st

from export.export_utils import create_export_context
from export.csv_export import export_predictions_to_dataframe
from export.code_generator import generate_python_script
from export.pdf_generator import generate_pdf_report
from export.zip_generator import generate_experiment_zip


def _get_export_cache() -> dict:
    """Return the export cache dict, creating it if absent."""
    if "export_cache" not in st.session_state:
        st.session_state["export_cache"] = {}
    return st.session_state["export_cache"]


def _get_cached_context(config, results, evaluation):
    """Build the ExportContext once and cache it."""
    cache = _get_export_cache()
    if "context" not in cache:
        cache["context"] = create_export_context(
            config,
            results,
            evaluation,
            st.session_state.get("comparison_runs", [])
        )
    return cache["context"]


def _get_cached_script(context):
    """Generate the Python script once and cache the string."""
    cache = _get_export_cache()
    if "python" not in cache:
        cache["python"] = generate_python_script(context)
    return cache["python"]


def _get_cached_predictions(context):
    """Generate the predictions DataFrame once and cache it."""
    cache = _get_export_cache()
    if "csv_df" not in cache:
        cache["csv_df"] = export_predictions_to_dataframe(context)
    return cache["csv_df"]


def _get_cached_csv(pred_df):
    """Convert the predictions DataFrame to CSV string once and cache it."""
    cache = _get_export_cache()
    if "csv_str" not in cache:
        cache["csv_str"] = pred_df.to_csv(index=False)
    return cache["csv_str"]


def _get_cached_pdf(context):
    """Generate the PDF bytes once and cache them."""
    cache = _get_export_cache()
    if "pdf" not in cache:
        temp_dir = tempfile.gettempdir()
        temp_pdf_path = os.path.join(temp_dir, "temp_report.pdf")
        pdf_bytes = b""
        try:
            generate_pdf_report(context, temp_pdf_path)
            with open(temp_pdf_path, "rb") as f:
                pdf_bytes = f.read()
        except Exception as e:
            st.error(f"Error generating PDF report: {str(e)}")
        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
        cache["pdf"] = pdf_bytes
    return cache["pdf"]


def _get_cached_zip(context):
    """Generate the ZIP bytes once and cache them."""
    cache = _get_export_cache()
    if "zip" not in cache:
        zip_bytes = b""
        try:
            zip_buffer = generate_experiment_zip(context)
            zip_bytes = zip_buffer.getvalue()
        except Exception as e:
            st.error(f"Error compiling experiment ZIP: {str(e)}")
        cache["zip"] = zip_bytes
    return cache["zip"]


def show_export_section(config: dict, results: dict, evaluation: dict) -> None:
    """
    Renders the export options panel in the Streamlit application.

    Args:
        config (dict): The training run configuration.
        results (dict): The training results.
        evaluation (dict): The evaluation metrics.
    """
    st.divider()
    st.subheader("📤 Export & Experiment Replication")
    st.write(
        "Export your results, predictions, standalone code, or a full "
        "reproducibility bundle for academic review."
    )

    # Build context (cached)
    context = _get_cached_context(config, results, evaluation)

    # Common filename prefix
    model_safe = config.get("model_name", "model").lower().replace(" ", "_")

    # Tabbed Interface
    tab_script, tab_csv, tab_pdf, tab_zip = st.tabs([
        "Python Script",
        "Prediction CSV",
        "PDF Report",
        "Full Experiment ZIP"
    ])

    # 1. Python Script Tab
    with tab_script:
        st.write("### Standalone Python Script")
        st.info(
            "Download a standalone Python script to reproduce this training run. "
            "The generated script includes data loading, preprocessing, model fitting, "
            "and plotting, having zero dependency on Solvosys."
        )
        script_code = _get_cached_script(context)
        script_filename = f"run_{model_safe}.py"

        st.download_button(
            label="Download Standalone Script (.py)",
            data=script_code,
            file_name=script_filename,
            mime="text/x-python",
            use_container_width=True
        )

        with st.expander("Preview Standalone Script", expanded=False):
            st.code(script_code, language="python")

    # 2. Prediction CSV Tab
    with tab_csv:
        st.write("### Prediction CSV")
        st.info(
            "Download a CSV file containing the actual target values, model predictions, "
            "and residuals or probabilities on the test set."
        )

        pred_df = _get_cached_predictions(context)
        csv_data = _get_cached_csv(pred_df)
        csv_filename = f"predictions_{model_safe}.csv"

        st.download_button(
            label="Download Predictions CSV (.csv)",
            data=csv_data,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True
        )

        st.write("#### Predictions Preview")
        st.dataframe(pred_df.head(10))

    # 3. PDF Report Tab
    with tab_pdf:
        st.write("### Academic PDF Report")
        st.info(
            "Download an academic-quality publication report summarizing the dataset metadata, "
            "preprocessing steps, model hyperparameters, evaluation metrics, and embedded figures."
        )

        pdf_bytes = _get_cached_pdf(context)
        pdf_filename = f"report_{model_safe}.pdf"

        if pdf_bytes:
            st.download_button(
                label="Download PDF Research Report (.pdf)",
                data=pdf_bytes,
                file_name=pdf_filename,
                mime="application/pdf",
                use_container_width=True
            )

    # 4. Experiment ZIP Tab
    with tab_zip:
        st.write("### Experiment ZIP Bundle")
        st.info(
            "Download a complete reproducibility bundle containing the standalone Python script, "
            "prediction CSV, PDF report, plots (if generated), README, and requirements.txt."
        )

        zip_bytes = _get_cached_zip(context)
        zip_filename = f"experiment_bundle_{model_safe}.zip"

        if zip_bytes:
            st.download_button(
                label="Download Experiment Bundle (.zip)",
                data=zip_bytes,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )
