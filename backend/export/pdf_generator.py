"""
Module for generating academic-quality PDF reports of ML Studio experiments using ReportLab.
"""

import os
from datetime import datetime
from typing import Optional, List, Tuple

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

from export.export_utils import ExportContext, format_hyperparameters, find_plot_file

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to draw header, footer, and 'Page X of Y' numbering.
    """
    model_name = "Model"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Times-Roman", 9)
        self.setFillColor(colors.HexColor("#333333"))

        # Header (Only on page 2 and later)
        if self._pageNumber > 1:
            self.drawString(54, 750, "ML Studio Research & Experiment Report")
            self.drawRightString(558, 750, f"Model: {self.model_name}")
            self.setStrokeColor(colors.HexColor("#cccccc"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer (All pages)
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawCentredString(306, 36, page_text)
        self.restoreState()



def generate_pdf_report(context: ExportContext, filepath: str) -> str:
    """
    Generate an academic-style ReportLab PDF report for the given training run.

    Args:
        context (ExportContext): The export context.
        filepath (str): Target file path to write the PDF report.

    Returns:
        str: Absolute path to the generated PDF.
    """
    config = context.config
    results = context.results
    evaluation = context.evaluation

    # Target directory check
    os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

    # Document setup (0.75 in margins = 54 points)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Academic Typography (Times-Roman / Times-Bold / Times-Italic)
    title_style = ParagraphStyle(
        "AcademicTitle",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        spaceAfter=15
    )

    metadata_style = ParagraphStyle(
        "AcademicMetadata",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        spaceAfter=10
    )

    h1_style = ParagraphStyle(
        "AcademicH1",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=12,
        leading=14,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        "AcademicH2",
        parent=styles["Normal"],
        fontName="Times-BoldItalic",
        fontSize=10,
        leading=12,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "AcademicBody",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=10,
        leading=13,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    )

    caption_style = ParagraphStyle(
        "AcademicCaption",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        spaceBefore=4,
        spaceAfter=12
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Times-Bold",
        fontSize=9,
        leading=11,
        alignment=TA_LEFT
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Times-Roman",
        fontSize=9,
        leading=11,
        alignment=TA_LEFT
    )

    story = []

    # ----------------------------------------------------
    # Header Section
    # ----------------------------------------------------
    model_name = config.get("model_name", "Model")
    problem_type = config.get("problem_type", "Task")
    target = config.get("target", "Target")
    target_unit = config.get("target_unit", "").strip()
    target_display = f"{target} ({target_unit})" if target_unit else target

    title_text = f"Experimental Analysis: Prediction of {target} using {model_name}"
    story.append(Paragraph(title_text, title_style))

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta_text = (
        f"Generated by ML Studio Workbench on {timestamp}<br/>"
        f"Task Class: {problem_type} | Target Variable: {target_display} | Split Strategy: {config.get('split_method')}"
    )
    story.append(Paragraph(meta_text, metadata_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333"), spaceAfter=15))

    # ----------------------------------------------------
    # Section 1: Introduction & Environment Setup
    # ----------------------------------------------------
    story.append(Paragraph("1. INTRODUCTION & EXPERIMENT METADATA", h1_style))
    intro_p = (
        f"This academic report contains the training configuration, evaluation metrics, and resulting "
        f"visualizations for a machine learning experiment run. The experiment was modeled as a "
        f"<b>{problem_type}</b> task with the objective of learning the mappings for target variable <b>{target_display}</b>."
    )
    story.append(Paragraph(intro_p, body_style))

    # Metadata Table
    dataset_name = results.get("dataset", "Uploaded Dataset")
    rows = results.get("X_train", results.get("X", [])).shape[0]
    if "X_test" in results:
        rows += results["X_test"].shape[0]

    cols_count = len(config.get("features", [])) + 1

    metadata_data = [
        [Paragraph("Metadata Field", table_header_style), Paragraph("Value", table_header_style)],
        [Paragraph("Dataset Name", table_cell_style), Paragraph(str(dataset_name), table_cell_style)],
        [Paragraph("Total Rows", table_cell_style), Paragraph(str(rows), table_cell_style)],
        [Paragraph("Features Selected Count", table_cell_style), Paragraph(str(len(config.get("features", []))), table_cell_style)],
        [Paragraph("Target Column", table_cell_style), Paragraph(target_display, table_cell_style)],
        [Paragraph("Problem Class", table_cell_style), Paragraph(problem_type, table_cell_style)]
    ]

    # Style: Academic Booktabs Format (clean top, header, and bottom lines)
    booktabs_style = TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor("#333333")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#666666")),
        ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor("#333333")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])

    meta_table = Table(metadata_data, colWidths=[200, 304])
    meta_table.setStyle(booktabs_style)
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # ----------------------------------------------------
    # Section 2: Data Preprocessing
    # ----------------------------------------------------
    story.append(Paragraph("2. DATA PREPROCESSING PIPELINE", h1_style))
    prep = config.get("preprocessing", {})
    
    prep_data = [
        [Paragraph("Pipeline Step", table_header_style), Paragraph("Strategy", table_header_style)],
        [Paragraph("Missing Value Imputation", table_cell_style), Paragraph(prep.get("missing_strategy", "None"), table_cell_style)],
        [Paragraph("Categorical Column Encoding", table_cell_style), Paragraph(prep.get("encoding_strategy", "None"), table_cell_style)],
        [Paragraph("Numeric Feature Scaling", table_cell_style), Paragraph(prep.get("scaling_strategy", "None"), table_cell_style)]
    ]

    prep_table = Table(prep_data, colWidths=[200, 304])
    prep_table.setStyle(booktabs_style)
    story.append(prep_table)
    story.append(Spacer(1, 8))

    features_str = ", ".join(config.get("features", []))
    story.append(Paragraph(f"<b>Configured Feature Set (X):</b> {features_str}", body_style))
    story.append(Spacer(1, 10))

    # ----------------------------------------------------
    # Section 3: Model Configuration & Hyperparameters
    # ----------------------------------------------------
    story.append(Paragraph("3. MODEL CONFIGURATION & HYPERPARAMETERS", h1_style))
    hp = config.get("hyperparameters", {})
    
    hp_rows = [[Paragraph("Hyperparameter", table_header_style), Paragraph("Value", table_header_style)]]
    if not hp:
        hp_rows.append([Paragraph("Defaults", table_cell_style), Paragraph("All parameters set to scikit-learn defaults.", table_cell_style)])
    else:
        for k, v in hp.items():
            hp_rows.append([Paragraph(str(k), table_cell_style), Paragraph(str(v), table_cell_style)])

    hp_table = Table(hp_rows, colWidths=[200, 304])
    hp_table.setStyle(booktabs_style)
    story.append(hp_table)
    story.append(Spacer(1, 10))

    # ----------------------------------------------------
    # Section 4: Performance Evaluation
    # ----------------------------------------------------
    story.append(Paragraph("4. PERFORMANCE EVALUATION", h1_style))
    metrics = evaluation.get("metrics", {})

    metrics_rows = [[Paragraph("Performance Metric", table_header_style), Paragraph("Value", table_header_style)]]
    
    if problem_type == "Regression":
        metrics_rows.append([Paragraph("R² Score (Coefficient of Determination)", table_cell_style), Paragraph(f"{metrics.get('R2 Score', 0.0):.4f}", table_cell_style)])
        metrics_rows.append([Paragraph("RMSE (Root Mean Squared Error)", table_cell_style), Paragraph(f"{metrics.get('RMSE', 0.0):.4f}", table_cell_style)])
        metrics_rows.append([Paragraph("MAE (Mean Absolute Error)", table_cell_style), Paragraph(f"{metrics.get('MAE', 0.0):.4f}", table_cell_style)])
        metrics_rows.append([Paragraph("MAPE (Mean Absolute Percentage Error)", table_cell_style), Paragraph(f"{metrics.get('MAPE', 0.0):.2f}%", table_cell_style)])
    else:
        metrics_rows.append([Paragraph("Accuracy", table_cell_style), Paragraph(f"{metrics.get('Accuracy', 0.0):.2%}", table_cell_style)])
        metrics_rows.append([Paragraph("Precision (Weighted Average)", table_cell_style), Paragraph(f"{metrics.get('Precision', 0.0):.2%}", table_cell_style)])
        metrics_rows.append([Paragraph("Recall (Weighted Average)", table_cell_style), Paragraph(f"{metrics.get('Recall', 0.0):.2%}", table_cell_style)])
        metrics_rows.append([Paragraph("F1 Score (Weighted Average)", table_cell_style), Paragraph(f"{metrics.get('F1 Score', 0.0):.2%}", table_cell_style)])

    metrics_table = Table(metrics_rows, colWidths=[200, 304])
    metrics_table.setStyle(booktabs_style)
    story.append(metrics_table)
    story.append(Spacer(1, 10))

    # Confusion Matrix (Classification only)
    if problem_type == "Classification" and "Confusion Matrix" in metrics:
        story.append(Paragraph("Confusion Matrix Grid", h2_style))
        cm = metrics["Confusion Matrix"]
        
        # Build clean visual grid representing the confusion matrix
        cm_data = [["", "Predicted"]]
        header_row = ["Actual"]
        for col_idx in range(len(cm[0])):
            header_row.append(f"Class {col_idx}")
        cm_data.append(header_row)

        for row_idx, row in enumerate(cm):
            row_data = [f"Class {row_idx}"]
            for val in row:
                row_data.append(str(val))
            cm_data.append(row_data)

        # Build widths dynamically
        num_classes = len(cm[0])
        col_widths = [100] + [60] * num_classes

        # Setup Table Style
        cm_table_style = TableStyle([
            ('SPAN', (1, 0), (1 + num_classes - 1, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (1, 1), (-1, -1), 0.5, colors.HexColor("#999999")),
            ('BACKGROUND', (1, 1), (-1, 1), colors.HexColor("#f2f2f2")),
            ('BACKGROUND', (0, 2), (0, -1), colors.HexColor("#f2f2f2")),
            ('FONTNAME', (1, 0), (1, 0), 'Times-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Times-Bold'),
            ('FONTNAME', (0, 2), (0, -1), 'Times-Bold'),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])

        cm_table = Table(cm_data, colWidths=col_widths)
        cm_table.setStyle(cm_table_style)
        story.append(cm_table)
        story.append(Spacer(1, 10))

    # ----------------------------------------------------
    # Section 5: Visualizations
    # ----------------------------------------------------
    story.append(Paragraph("5. VISUALIZATIONS & PLOTS", h1_style))
    story.append(Paragraph("This section displays the experimental plots generated by the workbench during evaluation.", body_style))
    story.append(Spacer(1, 5))

    # Search and collect plots from outputs directory
    available_plots = []
    plot_names = []
    if problem_type == "Regression":
        plot_names = [
            "Actual vs Predicted",
            "Residual Plot",
            "Residual Distribution",
            "Prediction Error",
            "Feature Importance"
        ]
    else:
        plot_names = [
            "Confusion Matrix",
            "ROC Curve",
            "Precision-Recall Curve",
            "Feature Importance"
        ]

    fig_idx = 1
    for name in plot_names:
        img_path = find_plot_file(name)
        if img_path:
            # We scale the image to fit beautifully on the page. Margins are 54pt each, so printable width is 504pt.
            # Scaling matplotlib figures: 360pt (5 inches) wide, 270pt (3.75 inches) high
            fig_img = Image(img_path, width=324, height=243)
            caption_text = f"<i>Figure {fig_idx}: Experimental plot depicting '{name}' mapping.</i>"
            caption_flowable = Paragraph(caption_text, caption_style)
            
            # Keep Image and its Caption on the same page
            story.append(Spacer(1, 5))
            story.append(KeepTogether([fig_img, caption_flowable]))
            story.append(Spacer(1, 10))
            fig_idx += 1

    if fig_idx == 1:
        story.append(Paragraph("<i>No matching plots were found in the outputs directory to embed. Make sure plots are generated first in the application dashboard.</i>", body_style))

    # Document generation
    NumberedCanvas.model_name = model_name
    doc.build(story, canvasmaker=NumberedCanvas)

    return os.path.abspath(filepath)
