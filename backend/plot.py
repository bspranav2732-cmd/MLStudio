
from io import BytesIO
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    precision_recall_curve
)

# ==========================================================
# Publication Style
# ==========================================================

def set_publication_style():

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
        "axes.labelsize": 14,
        "axes.titlesize": 14,
        "xtick.labelsize": 12,
        "ytick.labelsize": 12,
        "legend.fontsize": 10,
        "figure.dpi": 300,
        "axes.grid": True,
        "grid.alpha": 0.5,
        "grid.color": "lightgray",
        "grid.linestyle": "-"
    })

    sns.set_theme(
        style="whitegrid"
    )
   
# ==========================================================
# Figure Size
# ==========================================================

def get_figure_size(
    figure_width
):

    sizes = {
        "Single Column (90 mm)": (6, 4.5),
        "Double Column (190 mm)": (8, 6)
    }

    return sizes.get(
        figure_width,
        (8, 6)
    )
# ==========================================================
# Setup Figure
# ==========================================================

def setup_figure(
    figure_width
):
    set_publication_style()
    fig, ax = plt.subplots(
        figsize=get_figure_size(
            figure_width
        )
    )
    return fig, ax

def get_target_label(results):
    target = results.get(
        "target_name",
        "Target"
    )
    unit = results.get(
        "target_unit",
        ""
    )
    unit = results.get(
        "target_unit",
        ""
    )
    if unit.strip():
        return f"{target} ({unit})"
    return target

def clean_feature_names(

    names

):

    cleaned = []

    for name in names:

        name = name.replace(

            "num__",

            ""

        )

        name = name.replace(

            "cat__",

            ""

        )

        cleaned.append(name)

    return cleaned

def get_figure_size(width):
    if width == "Single Column (90 mm)":
        return (6, 4.5)
    elif width == "Double Column (190 mm)":
        return (8, 6)
    return (8, 6)

# Regression Data
def get_regression_data(
    results
):

    return (
        results["y_test"],
        results["y_test_pred"],
        get_target_label(results)
    )

# Classification Data
def get_classification_data(
    results
):

    return (
        results["y_test"],
        results["y_test_pred"]
    )

def plot_reference_line(
    ax,
    y_true,
    y_pred

):
    minimum = min(
        np.min(y_true),
        np.min(y_pred)
    )

    maximum = max(
        np.max(y_true),
        np.max(y_pred)

    )

    ax.plot(
        [minimum, maximum],
        [minimum, maximum],
        "r--",
        linewidth=2,
        label="Ideal Fit (y=x)"
    )

# Common Formatting
def apply_plot_style(
    ax,
    xlabel,
    ylabel,
    legend=True,
    legend_loc="lower right",
    grid=True
):
    
    ax.set_xlabel(
        xlabel
    )
    ax.set_ylabel(
        ylabel
    )

    if grid:
        ax.grid(
            True,
            linestyle="-",
            alpha=0.5,
            color="lightgray"
        )
    
    if legend:
        ax.legend(
            loc=legend_loc,
            fontsize=10,
            frameon=True,
            edgecolor="gray"
        )
    
    ax.tick_params(
        direction="out",
        length=5,
        width=1
    )
    
    plt.tight_layout()

def save_figure(
    fig,
    filename,
    export_format,
    plot_quality
):
    
    dpi_map = {
        "Screen Preview (150 DPI)":150,
        "Publication (300 DPI)":300,
        "High Quality (600 DPI)":600,
        "Ultra Quality (1200 DPI)":1200
    }
    dpi = dpi_map.get(
        plot_quality,
        300
    )

    os.makedirs(
        "outputs",
        exist_ok=True

    )

    filepath = os.path.join(
        "outputs",
        f"{filename}.{export_format.lower()}"

    )

    fig.savefig(
        filepath,
        dpi=dpi,
        bbox_inches="tight"
    )
    return filepath

# Actual vs Predicted
def plot_actual_vs_predicted(
    results,
    figure_width
):

    fig, ax = setup_figure(figure_width)

    y_true, y_pred, label = get_regression_data(results)

    ax.scatter(
        y_true,
        y_pred,
        alpha=0.6,
        color="royalblue",
        edgecolor="k",
        s=70,
        label="Predictions"
    )

    plot_reference_line(
        ax,
        y_true,
        y_pred
    )

    apply_plot_style(
        ax,
        xlabel=f"Actual {label}",
        ylabel=f"Predicted {label}"
    )

    return fig

# Residual Plot
def plot_residual_plot(
    results,
    figure_width
):

    fig, ax = setup_figure(figure_width)
    y_true, y_pred, label = get_regression_data(results)
    residuals = y_true - y_pred

    ax.scatter(
        y_pred,
        residuals,
        alpha=0.6,
        color="royalblue",
        edgecolor="k",
        s=70
    )

    ax.axhline(
        y=0,
        color="red",
        linestyle="--",
        linewidth=2
    )

    apply_plot_style(
        ax,
        xlabel=f"Predicted {label}",
        ylabel=f"Residual ({label})",
        legend=False
    )

    return fig


# Residual Distribution
def plot_residual_distribution(
    results,
    figure_width
):

    fig, ax = setup_figure(figure_width)
    y_true, y_pred, label = get_regression_data(results)
    residuals = y_true - y_pred

    ax.hist(
        residuals,
        bins=20,
        color="royalblue",
        edgecolor="black",
        alpha=0.8
    )

    apply_plot_style(
        ax,
        xlabel=f"Residual ({label})",
        ylabel="Frequency",
        legend=False
    )

    return fig
# ==========================================================
# Prediction Error
# ==========================================================

def plot_prediction_error(
    results,
    figure_width
):

    fig, ax = setup_figure(figure_width)

    y_true, y_pred, label = get_regression_data(results)

    error = y_pred - y_true

    ax.scatter(
        y_true,
        error,
        alpha=0.6,
        color="royalblue",
        edgecolor="k",
        s=70
    )

    ax.axhline(
        y=0,
        color="red",
        linestyle="--",
        linewidth=2
    )

    apply_plot_style(
        ax,
        xlabel=f"Actual {label}",
        ylabel=f"Prediction Error ({label})",
        legend=False
    )

    return fig

# ==========================================================
# Confusion Matrix
# ==========================================================

def plot_confusion_matrix(
    results,
    figure_width
):

    fig, ax = setup_figure(
        figure_width
    )

    y_true, y_pred = get_classification_data(
        results
    )

    cm = confusion_matrix(
        y_true,
        y_pred
    )

    sns.heatmap(

        cm,

        annot=True,

        fmt="d",

        cmap="Blues",

        square=True,

        linewidths=0.8,

        linecolor="white",

        cbar=False,

        annot_kws={
            "size":12,
            "weight":"bold"
        },

        ax=ax

    )

    apply_plot_style(

        ax,

        xlabel="Predicted Class",

        ylabel="Actual Class",

        legend=False,

        grid=False

    )

    return fig

# ==========================================================
# ROC Curve
# ==========================================================

def plot_roc_curve(
    results,
    figure_width
):

    if results["y_test_prob"] is None:

        st.warning(
            "ROC Curve unavailable."
        )

        return None

    fig, ax = setup_figure(
        figure_width
    )

    fpr, tpr, _ = roc_curve(

        results["y_test"],

        results["y_test_prob"]

    )

    roc_auc = auc(
        fpr,
        tpr
    )

    ax.plot(

        fpr,

        tpr,

        color="royalblue",

        linewidth=2,

        label=f"AUC = {roc_auc:.3f}"

    )

    ax.plot(

        [0,1],

        [0,1],

        "r--",

        linewidth=2

    )

    apply_plot_style(

        ax,

        xlabel="False Positive Rate",

        ylabel="True Positive Rate"

    )

    return fig

# ==========================================================
# Precision Recall Curve
# ==========================================================

def plot_precision_recall_curve(
    results,
    figure_width
):

    if results["y_test_prob"] is None:

        st.warning(
            "Precision-Recall Curve unavailable."
        )

        return None

    fig, ax = setup_figure(
        figure_width
    )

    precision, recall, _ = precision_recall_curve(

        results["y_test"],

        results["y_test_prob"]

    )

    ax.plot(

        recall,

        precision,

        color="royalblue",

        linewidth=2

    )

    apply_plot_style(

        ax,

        xlabel="Recall",

        ylabel="Precision",

        legend=False

    )

    return fig

# ==========================================================
# Feature Importance
# ==========================================================

def plot_feature_importance(

    results,
    figure_width

):

    pipeline = results["pipeline"]
    model = pipeline.named_steps["model"]
    if not hasattr(

        model,

        "feature_importances_"

    ):

        st.warning(

            "Feature importance is not available for this model."

        )

        return None
    importance = model.feature_importances_
    feature_names = clean_feature_names(
    results["feature_names"]

)
    order = np.argsort(
    importance

)[::-1]

    importance = importance[order]
    feature_names = np.array(
        feature_names

    )[order]

    max_features = 20
    if len(feature_names) > max_features:
        importance = importance[-max_features:]
        feature_names = feature_names[-max_features:]
    fig, ax = setup_figure(
        figure_width

    )

    ax.barh(

    feature_names[::-1],

    importance[::-1],

    color="royalblue",

    edgecolor="black"

)

    apply_plot_style(

        ax,
        xlabel="Feature Importance",
        ylabel="Features",
        legend=False

    )

    return fig

# ==========================================================
# Regression Plot Dictionary
# ==========================================================

REGRESSION_PLOTS = {

    "Actual vs Predicted": plot_actual_vs_predicted,
    "Residual Plot": plot_residual_plot,
    "Residual Distribution": plot_residual_distribution,
    "Prediction Error": plot_prediction_error,
    "Feature Importance": plot_feature_importance
}

# Classification Plot Dictionary

CLASSIFICATION_PLOTS = {

    "Confusion Matrix": plot_confusion_matrix,
    "ROC Curve": plot_roc_curve,
    "Precision-Recall Curve": plot_precision_recall_curve,
    "Feature Importance": plot_feature_importance
}

# Show Regression Plots
def show_regression_plots(

    results,
    selected_plots,
    figure_width,
    plot_quality,
    export_format

):

    for plot_name in selected_plots:
        if plot_name not in REGRESSION_PLOTS:
            continue

        st.subheader(plot_name)
        fig = REGRESSION_PLOTS[plot_name](

            results,
            figure_width
        )

        if fig is None:
            continue
        st.pyplot(fig)
        buffer = BytesIO()

        fig.savefig(
        buffer,
        format=export_format.lower(),
            dpi={
        "Screen Preview (150 DPI)":150,
        "Publication (300 DPI)":300,
        "High Quality (600 DPI)":600,
        "Ultra Quality (1200 DPI)":1200
        }[plot_quality],
        bbox_inches="tight"
)

    buffer.seek(0)

    st.download_button(

    label=f"⬇ Download {plot_name}",

    data=buffer,

    file_name=f"{plot_name}.{export_format.lower()}",

    mime=f"image/{export_format.lower()}"

)

        
    plt.close(fig)


# Show Classification Plots
def show_classification_plots(

    results,
    selected_plots,
    figure_width,
    plot_quality,
    export_format

):

    for plot_name in selected_plots:
        if plot_name not in CLASSIFICATION_PLOTS:
            continue
        st.subheader(plot_name)

        fig = CLASSIFICATION_PLOTS[plot_name](

            results,
            figure_width
        )

        if fig is None:
            continue
        st.pyplot(fig)

        

        buffer = BytesIO()

        fig.savefig(
        buffer,
        format=export_format.lower(),
            dpi={
        "Screen Preview (150 DPI)":150,
        "Publication (300 DPI)":300,
        "High Quality (600 DPI)":600,
        "Ultra Quality (1200 DPI)":1200
        }[plot_quality],
        bbox_inches="tight"
)

    buffer.seek(0)

    st.download_button(

    label=f"⬇ Download {plot_name}",

    data=buffer,

    file_name=f"{plot_name}.{export_format.lower()}",

    mime=f"image/{export_format.lower()}"

)

    plt.close(fig)

# Main Plot Function
def show_plots(

    results,
    selected_plots,
    figure_width,
    plot_quality,
    export_format

):

    if results["problem_type"] == "Regression":

        show_regression_plots(
            results,
            selected_plots,
            figure_width,
            plot_quality,
            export_format
        )

    else:

        show_classification_plots(

            results,
            selected_plots,
            figure_width,
            plot_quality,
            export_format
        )