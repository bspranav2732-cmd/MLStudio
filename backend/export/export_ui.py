"""
Module for rendering the Export panel in the Streamlit UI.
"""

import os
import tempfile
import streamlit as st

from export.export_utils import create_export_context
from export.csv_export import export_predictions_to_dataframe
from export.code_generator import generate_python_script
from export.pdf_generator import generate_pdf_report
from export.zip_generator import generate_experiment_zip


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

    # Construct the unified export context
    context = create_export_context(config, results, evaluation)

    # Tabbed Interface
    tab_script, tab_csv, tab_pdf, tab_zip = st.tabs([
        "🐍 Python Script",
        "📊 Prediction CSV",
        "📄 PDF Report",
        "📦 Full Experiment ZIP"
    ])

    # 1. Python Script Tab
    with tab_script:
        st.write("### Standalone Python Script")
        st.info(
            "Download a standalone Python script to reproduce this training run. "
            "The generated script includes data loading, preprocessing, model fitting, "
            "and plotting, having zero dependency on ML Studio."
        )
        script_code = generate_python_script(context)
        
        # Filename selection
        model_safe = config.get("model_name", "model").lower().replace(" ", "_")
        script_filename = f"run_{model_safe}.py"

        st.download_button(
            label="⬇ Download Standalone Script (.py)",
            data=script_code,
            file_name=script_filename,
            mime="text/x-python",
            use_container_width=True
        )

        st.write("#### Script Preview")
        st.code(script_code, language="python")

    # 2. Prediction CSV Tab
    with tab_csv:
        st.write("### Prediction CSV")
        st.info(
            "Download a CSV file containing the actual target values, model predictions, "
            "and residuals or probabilities on the test set."
        )
        
        pred_df = export_predictions_to_dataframe(context)
        csv_filename = f"predictions_{model_safe}.csv"

        st.download_button(
            label="⬇ Download Predictions CSV (.csv)",
            data=pred_df.to_csv(index=False),
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
        
        pdf_filename = f"report_{model_safe}.pdf"

        # Generate PDF to a temporary path, read its bytes, and cleanup
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

        if pdf_bytes:
            st.download_button(
                label="⬇ Download PDF Research Report (.pdf)",
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
        
        zip_filename = f"experiment_bundle_{model_safe}.zip"
        
        zip_bytes = b""
        try:
            zip_buffer = generate_experiment_zip(context)
            zip_bytes = zip_buffer.getvalue()
        except Exception as e:
            st.error(f"Error compiling experiment ZIP: {str(e)}")

        if zip_bytes:
            st.download_button(
                label="⬇ Download Experiment Bundle (.zip)",
                data=zip_bytes,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )
