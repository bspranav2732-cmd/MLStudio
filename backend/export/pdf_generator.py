"""
Module for generating academic-quality PDF reports of Solvosys experiments using ReportLab.
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
            self.drawString(54, 750, "Solvosys Research & Experiment Report")
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
        f"Generated by Solvosys Workbench on {timestamp}<br/>"
        f"Task Class: {problem_type} | Target Variable: {target_display} | Split Strategy: {config.get('split_method')}"
    )
    story.append(Paragraph(meta_text, metadata_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#333333"), spaceAfter=15))

    # ----------------------------------------------------
    # Section 1: Introduction & Environment Setup
    # ----------------------------------------------------
    story.append(Paragraph("1. DATASET STATISTICS", h1_style))
    intro_p = (
        f"This academic report contains the training configuration, evaluation metrics, and resulting "
        f"visualizations for a machine learning experiment run. The experiment was modeled as a "
        f"<b>{problem_type}</b> task with the objective of learning the mappings for target variable <b>{target_display}</b>."
    )
    story.append(Paragraph(intro_p, body_style))
    story.append(Spacer(1, 5))

    # Calculate Dataset Statistics for numerical features
    import pandas as pd
    import numpy as np

    if "X_test" in results:
        X_df = pd.concat([results["X_train"], results["X_test"]])
    else:
        X_df = results.get("X", results.get("X_train"))

    stats_data = [
        [
            Paragraph("<b>Feature</b>", table_header_style),
            Paragraph("<b>Min</b>", table_header_style),
            Paragraph("<b>Max</b>", table_header_style),
            Paragraph("<b>Mean</b>", table_header_style),
            Paragraph("<b>Variance</b>", table_header_style),
            Paragraph("<b>Std Dev</b>", table_header_style)
        ]
    ]

    # Style: Academic Booktabs Format (clean top, header, and bottom lines)
    booktabs_style = TableStyle([
        ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor("#333333")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#666666")),
        ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor("#333333")),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ])

    if X_df is not None:
        num_cols = X_df.select_dtypes(include=[np.number])
        if not num_cols.empty:
            for col_name in num_cols.columns:
                col_data = num_cols[col_name]
                min_val = col_data.min()
                max_val = col_data.max()
                mean_val = col_data.mean()
                var_val = col_data.var()
                std_val = col_data.std()
                stats_data.append([
                    Paragraph(str(col_name), table_cell_style),
                    Paragraph(f"{min_val:.4f}", table_cell_style),
                    Paragraph(f"{max_val:.4f}", table_cell_style),
                    Paragraph(f"{mean_val:.4f}", table_cell_style),
                    Paragraph(f"{var_val:.4f}", table_cell_style),
                    Paragraph(f"{std_val:.4f}", table_cell_style)
                ])
        else:
            stats_data.append([
                Paragraph("No numerical features found in dataset.", table_cell_style),
                "", "", "", "", ""
            ])
    else:
        stats_data.append([
            Paragraph("Dataset data not available.", table_cell_style),
            "", "", "", "", ""
        ])

    stats_table = Table(stats_data, colWidths=[154, 70, 70, 70, 70, 70])
    stats_table.setStyle(booktabs_style)
    story.append(stats_table)
    story.append(Spacer(1, 5))
    
    # Add note below the table
    story.append(Paragraph("Dataset statistics are reported only for numerical features.", body_style))
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

    # ==========================================================
    # Section: Experiment Comparison
    # ==========================================================
    story.append(Spacer(1, 15))
    story.append(Paragraph("Experiment Comparison", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC"), spaceBefore=5, spaceAfter=15))

    comparison_runs = context.comparison_runs
    problem_type = config.get("problem_type", "Regression")
    active_runs = [run for run in comparison_runs if run.get("problem_type") == problem_type]
    
    if len(active_runs) >= 1:
        story.append(Paragraph(
            "This section compares the current experiment against other saved runs in the history. "
            "The currently active experiment is highlighted with a background shading and bold text for clarity.",
            body_style
        ))
        story.append(Spacer(1, 10))
        
        # 1. Generalization Comparison Table
        story.append(Paragraph("Generalization Comparison", h2_style))
        story.append(Spacer(1, 5))
        
        if problem_type == "Regression":
            headers1 = [
                Paragraph("<b>Model</b>", table_header_style),
                Paragraph("<b>Training R²</b>", table_header_style),
                Paragraph("<b>Validation R²</b>", table_header_style),
                Paragraph("<b>Gap</b>", table_header_style)
            ]
            col_widths1 = [180, 100, 100, 100]
        else:
            headers1 = [
                Paragraph("<b>Model</b>", table_header_style),
                Paragraph("<b>Training Accuracy</b>", table_header_style),
                Paragraph("<b>Validation Accuracy</b>", table_header_style),
                Paragraph("<b>Gap</b>", table_header_style)
            ]
            col_widths1 = [180, 100, 100, 100]

        table_data1 = [headers1]
        highlighted_rows = []
        
        # Current run metrics for matching
        curr_model_name = config.get("model_name", "")
        curr_metrics = context.evaluation.get("metrics", {})
        
        for idx, run in enumerate(active_runs):
            model_name_val = run["model_name"]
            train_m = run["train_metrics"]
            val_m = run["validation_metrics"]
            
            # Check if this row is the current run
            is_current = (model_name_val == curr_model_name and run.get("metrics") == curr_metrics)
            row_label = f"{model_name_val} (Current)" if is_current else model_name_val
            
            if is_current:
                highlighted_rows.append(idx + 1)
                
            if problem_type == "Regression":
                train_score = train_m.get("R2 Score", 0.0)
                val_score = val_m.get("R2 Score", 0.0)
                gap = abs(train_score - val_score)
                row = [
                    Paragraph(row_label, table_cell_style),
                    Paragraph(f"{train_score:.4f}", table_cell_style),
                    Paragraph(f"{val_score:.4f}", table_cell_style),
                    Paragraph(f"{gap:.4f}", table_cell_style)
                ]
            else:
                train_score = train_m.get("Accuracy", 0.0)
                val_score = val_m.get("Accuracy", 0.0)
                gap = abs(train_score - val_score)
                row = [
                    Paragraph(row_label, table_cell_style),
                    Paragraph(f"{train_score:.2%}", table_cell_style),
                    Paragraph(f"{val_score:.2%}", table_cell_style),
                    Paragraph(f"{gap:.2%}", table_cell_style)
                ]
            table_data1.append(row)

        t1 = Table(table_data1, colWidths=col_widths1)
        t1_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor("#000000")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#000000")),
            ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor("#000000")),
        ]
        for r_idx in highlighted_rows:
            t1_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor("#F0F4FA")))
            t1_style.append(('FONTNAME', (0, r_idx), (-1, r_idx), 'Times-Bold'))
            
        t1.setStyle(TableStyle(t1_style))
        story.append(t1)
        story.append(Spacer(1, 15))

        # 2. Performance Comparison Table
        story.append(Paragraph("Performance Comparison", h2_style))
        story.append(Spacer(1, 5))
        
        if problem_type == "Regression":
            headers2 = [
                Paragraph("<b>Model</b>", table_header_style),
                Paragraph("<b>R²</b>", table_header_style),
                Paragraph("<b>RMSE</b>", table_header_style),
                Paragraph("<b>MAE</b>", table_header_style),
                Paragraph("<b>MAPE</b>", table_header_style)
            ]
            col_widths2 = [160, 80, 80, 80, 80]
        else:
            headers2 = [
                Paragraph("<b>Model</b>", table_header_style),
                Paragraph("<b>Accuracy</b>", table_header_style),
                Paragraph("<b>Precision</b>", table_header_style),
                Paragraph("<b>Recall</b>", table_header_style),
                Paragraph("<b>F1 Score</b>", table_header_style)
            ]
            col_widths2 = [160, 80, 80, 80, 80]

        table_data2 = [headers2]
        for idx, run in enumerate(active_runs):
            model_name_val = run["model_name"]
            m = run["metrics"]
            is_current = (model_name_val == curr_model_name and run.get("metrics") == curr_metrics)
            row_label = f"{model_name_val} (Current)" if is_current else model_name_val
            
            if problem_type == "Regression":
                row = [
                    Paragraph(row_label, table_cell_style),
                    Paragraph(f"{m.get('R2 Score', 0.0):.4f}", table_cell_style),
                    Paragraph(f"{m.get('RMSE', 0.0):.4f}", table_cell_style),
                    Paragraph(f"{m.get('MAE', 0.0):.4f}", table_cell_style),
                    Paragraph(f"{m.get('MAPE', 0.0):.2f}%", table_cell_style)
                ]
            else:
                row = [
                    Paragraph(row_label, table_cell_style),
                    Paragraph(f"{m.get('Accuracy', 0.0):.2%}", table_cell_style),
                    Paragraph(f"{m.get('Precision', 0.0):.2%}", table_cell_style),
                    Paragraph(f"{m.get('Recall', 0.0):.2%}", table_cell_style),
                    Paragraph(f"{m.get('F1 Score', 0.0):.2%}", table_cell_style)
                ]
            table_data2.append(row)

        t2 = Table(table_data2, colWidths=col_widths2)
        t2_style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#F5F5F5")),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LINEABOVE', (0, 0), (-1, 0), 1.0, colors.HexColor("#000000")),
            ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.HexColor("#000000")),
            ('LINEBELOW', (0, -1), (-1, -1), 1.0, colors.HexColor("#000000")),
        ]
        for r_idx in highlighted_rows:
            t2_style.append(('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor("#F0F4FA")))
            t2_style.append(('FONTNAME', (0, r_idx), (-1, r_idx), 'Times-Bold'))
            
        t2.setStyle(TableStyle(t2_style))
        story.append(t2)
        story.append(Spacer(1, 10))
    else:
        # Less than one run: display a short note explaining comparison is available after adding more experiments.
        note_text = (
            "<i>Note: Experiment comparison matrices and generalization gap tables become "
            "available in this section after you save one or more runs to the comparison history.</i>"
        )
        story.append(Paragraph(note_text, body_style))
        story.append(Spacer(1, 10))

    # Document generation
    NumberedCanvas.model_name = model_name
    doc.build(story, canvasmaker=NumberedCanvas)

    return os.path.abspath(filepath)
