"""
Module for generating standalone, educational Python scripts to reproduce ML training runs.
"""

from typing import Dict, Any, List
import streamlit as st
from export.export_utils import ExportContext


def get_imports_code(config: Dict[str, Any]) -> str:
    """
    Generate import statements based on the configuration.

    Args:
        config (dict): The training configuration.

    Returns:
        str: Import statements python code.
    """
    split_method = config.get("split_method")
    model_name = config.get("model_name")
    problem_type = config.get("problem_type")

    imports = [
        "import numpy as np",
        "import pandas as pd",
        "import matplotlib.pyplot as plt",
        "import seaborn as sns",
        "from sklearn.pipeline import Pipeline",
        "from sklearn.compose import ColumnTransformer",
        "from sklearn.impute import SimpleImputer",
    ]

    # Preprocessing imports
    preprocessing = config.get("preprocessing", {})
    encoding_strategy = preprocessing.get("encoding_strategy", "None")
    scaling_strategy = preprocessing.get("scaling_strategy", "None")

    if encoding_strategy == "One-Hot":
        imports.append("from sklearn.preprocessing import OneHotEncoder")
    elif encoding_strategy == "Ordinal":
        imports.append("from sklearn.preprocessing import OrdinalEncoder")

    if scaling_strategy == "StandardScaler":
        imports.append("from sklearn.preprocessing import StandardScaler")
    elif scaling_strategy == "MinMaxScaler":
        imports.append("from sklearn.preprocessing import MinMaxScaler")
    elif scaling_strategy == "RobustScaler":
        imports.append("from sklearn.preprocessing import RobustScaler")

    # Split strategy imports
    if split_method == "Train-Test Split":
        imports.append("from sklearn.model_selection import train_test_split")
    elif split_method == "K-Fold Cross Validation":
        imports.append("from sklearn.model_selection import KFold, cross_val_predict")
    elif split_method == "Stratified K-Fold Cross Validation":
        imports.append("from sklearn.model_selection import StratifiedKFold, cross_val_predict")

    # Model imports
    if model_name == "Linear Regression":
        imports.append("from sklearn.linear_model import LinearRegression")
    elif model_name == "Polynomial Regression":
        imports.append("from sklearn.linear_model import LinearRegression")
        imports.append("from sklearn.preprocessing import PolynomialFeatures")
    elif model_name == "Lasso Regression":
        imports.append("from sklearn.linear_model import Lasso")
    elif model_name == "Elastic Net":
        imports.append("from sklearn.linear_model import ElasticNet")
    elif model_name == "Decision Tree":
        if problem_type == "Regression":
            imports.append("from sklearn.tree import DecisionTreeRegressor")
        else:
            imports.append("from sklearn.tree import DecisionTreeClassifier")
    elif model_name == "Random Forest":
        if problem_type == "Regression":
            imports.append("from sklearn.ensemble import RandomForestRegressor")
        else:
            imports.append("from sklearn.ensemble import RandomForestClassifier")
    elif model_name == "XGBoost Regressor":
        imports.append("from xgboost import XGBRegressor")
    elif model_name == "CatBoost Regressor":
        imports.append("from catboost import CatBoostRegressor")
    elif model_name == "Logistic Regression":
        imports.append("from sklearn.linear_model import LogisticRegression")
    elif model_name == "XGBoost Classifier":
        imports.append("from xgboost import XGBClassifier")
    elif model_name == "CatBoost Classifier":
        imports.append("from catboost import CatBoostClassifier")

    # Metric imports
    if problem_type == "Regression":
        imports.append(
            "from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error"
        )
    else:
        imports.append(
            "from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix"
        )
        # For classification, we will also import curves if probability is supported
        if model_name in ["Logistic Regression", "Random Forest", "Decision Tree", "XGBoost Classifier", "CatBoost Classifier"]:
            imports.append("from sklearn.metrics import roc_curve, auc, precision_recall_curve")

    return "\n".join(sorted(list(set(imports)), key=lambda s: (not s.startswith("import"), s)))


def get_model_instantiation_code(problem_type: str, model_name: str, hp: Dict[str, Any]) -> str:
    """
    Generate model instantiation python code based on model name and hyperparameters.

    Args:
        problem_type (str): "Regression" or "Classification".
        model_name (str): Model name.
        hp (dict): Hyperparameters.

    Returns:
        str: Model creation python code.
    """
    if model_name == "Linear Regression":
        return "model = LinearRegression()"
    
    elif model_name == "Polynomial Regression":
        degree = hp.get("degree", 2)
        return (
            f"model = Pipeline([\n"
            f"    ('poly', PolynomialFeatures(degree={degree}, include_bias=False)),\n"
            f"    ('linear', LinearRegression())\n"
            f"])"
        )
    
    elif model_name == "Decision Tree":
        max_depth = hp.get("max_depth")
        min_samples_split = hp.get("min_samples_split", 2)
        min_samples_leaf = hp.get("min_samples_leaf", 1)
        
        class_name = "DecisionTreeRegressor" if problem_type == "Regression" else "DecisionTreeClassifier"
        return (
            f"model = {class_name}(\n"
            f"    max_depth={max_depth},\n"
            f"    min_samples_split={min_samples_split},\n"
            f"    min_samples_leaf={min_samples_leaf},\n"
            f"    random_state=42\n"
            f")"
        )
        
    elif model_name == "Random Forest":
        n_estimators = hp.get("n_estimators", 100)
        max_depth = hp.get("max_depth")
        min_samples_split = hp.get("min_samples_split", 2)
        min_samples_leaf = hp.get("min_samples_leaf", 1)
        max_features = hp.get("max_features", "sqrt")
        
        # max_features should be string or None
        mf_str = repr(max_features)
        
        class_name = "RandomForestRegressor" if problem_type == "Regression" else "RandomForestClassifier"
        return (
            f"model = {class_name}(\n"
            f"    n_estimators={n_estimators},\n"
            f"    max_depth={max_depth},\n"
            f"    min_samples_split={min_samples_split},\n"
            f"    min_samples_leaf={min_samples_leaf},\n"
            f"    max_features={mf_str},\n"
            f"    random_state=42\n"
            f")"
        )
        
    elif model_name == "Logistic Regression":
        c = hp.get("C", 1.0)
        solver = hp.get("solver", "lbfgs")
        max_iter = hp.get("max_iter", 1000)
        return (
            f"model = LogisticRegression(\n"
            f"    C={c},\n"
            f"    solver='{solver}',\n"
            f"    max_iter={max_iter}\n"
            f")"
        )
        
    elif model_name == "Lasso Regression":
        alpha = hp.get("alpha", 1.0)
        max_iter = hp.get("max_iter", 1000)
        return (
            f"model = Lasso(\n"
            f"    alpha={alpha},\n"
            f"    max_iter={max_iter},\n"
            f"    random_state=42\n"
            f")"
        )
        
    elif model_name == "Elastic Net":
        alpha = hp.get("alpha", 1.0)
        l1_ratio = hp.get("l1_ratio", 0.5)
        max_iter = hp.get("max_iter", 1000)
        return (
            f"model = ElasticNet(\n"
            f"    alpha={alpha},\n"
            f"    l1_ratio={l1_ratio},\n"
            f"    max_iter={max_iter},\n"
            f"    random_state=42\n"
            f")"
        )

    elif model_name == "XGBoost Regressor":
        n_estimators = hp.get("n_estimators", 100)
        learning_rate = hp.get("learning_rate", 0.1)
        max_depth = hp.get("max_depth", 6)
        subsample = hp.get("subsample", 1.0)
        colsample_bytree = hp.get("colsample_bytree", 1.0)
        return (
            f"model = XGBRegressor(\n"
            f"    n_estimators={n_estimators},\n"
            f"    learning_rate={learning_rate},\n"
            f"    max_depth={max_depth},\n"
            f"    subsample={subsample},\n"
            f"    colsample_bytree={colsample_bytree},\n"
            f"    random_state=42\n"
            f")"
        )

    elif model_name == "CatBoost Regressor":
        iterations = hp.get("iterations", 100)
        learning_rate = hp.get("learning_rate", 0.03)
        depth = hp.get("depth", 6)
        l2_leaf_reg = hp.get("l2_leaf_reg", 3.0)
        return (
            f"model = CatBoostRegressor(\n"
            f"    iterations={iterations},\n"
            f"    learning_rate={learning_rate},\n"
            f"    depth={depth},\n"
            f"    l2_leaf_reg={l2_leaf_reg},\n"
            f"    random_seed=42,\n"
            f"    verbose=0\n"
            f")"
        )

    elif model_name == "XGBoost Classifier":
        n_estimators = hp.get("n_estimators", 100)
        learning_rate = hp.get("learning_rate", 0.1)
        max_depth = hp.get("max_depth", 6)
        subsample = hp.get("subsample", 1.0)
        colsample_bytree = hp.get("colsample_bytree", 1.0)
        return (
            f"model = XGBClassifier(\n"
            f"    n_estimators={n_estimators},\n"
            f"    learning_rate={learning_rate},\n"
            f"    max_depth={max_depth},\n"
            f"    subsample={subsample},\n"
            f"    colsample_bytree={colsample_bytree},\n"
            f"    random_state=42\n"
            f")"
        )

    elif model_name == "CatBoost Classifier":
        iterations = hp.get("iterations", 100)
        learning_rate = hp.get("learning_rate", 0.03)
        depth = hp.get("depth", 6)
        l2_leaf_reg = hp.get("l2_leaf_reg", 3.0)
        return (
            f"model = CatBoostClassifier(\n"
            f"    iterations={iterations},\n"
            f"    learning_rate={learning_rate},\n"
            f"    depth={depth},\n"
            f"    l2_leaf_reg={l2_leaf_reg},\n"
            f"    random_seed=42,\n"
            f"    verbose=0\n"
            f")"
        )
        
    return "model = None  # Model creation placeholder"


def generate_python_script(context: ExportContext) -> str:
    """
    Generate a standalone educational Python script reproducing the experiment.

    Args:
        context (ExportContext): The export context.

    Returns:
        str: Python code string.
    """
    config = context.config
    results = context.results
    
    # Identify the dataset filename
    dataset_name = "dataset.csv"
    if "project" in st.session_state:
        dataset_name = st.session_state.project.get("dataset", "dataset.csv")
    
    problem_type = config.get("problem_type")
    features = config.get("features", [])
    target = config.get("target")
    target_unit = config.get("target_unit", "").strip()
    
    # Target label with unit (if present)
    target_label = f"{target} ({target_unit})" if target_unit else target
    
    # Split configuration
    split_method = config.get("split_method")
    train_percent = config.get("train_percent", 80)
    folds = config.get("folds", 5)
    
    # Preprocessing configuration
    preprocessing = config.get("preprocessing", {})
    missing_strategy = preprocessing.get("missing_strategy", "None")
    encoding_strategy = preprocessing.get("encoding_strategy", "None")
    scaling_strategy = preprocessing.get("scaling_strategy", "None")
    
    # Build preprocessing strings
    # Numeric pipeline
    if missing_strategy == "None":
        num_imputer_code = "numeric_imputer = 'passthrough'"
        cat_imputer_code = "categorical_imputer = 'passthrough'"
    elif missing_strategy == "Mean":
        num_imputer_code = "numeric_imputer = SimpleImputer(strategy='mean')"
        cat_imputer_code = "categorical_imputer = SimpleImputer(strategy='most_frequent')"
    elif missing_strategy == "Median":
        num_imputer_code = "numeric_imputer = SimpleImputer(strategy='median')"
        cat_imputer_code = "categorical_imputer = SimpleImputer(strategy='most_frequent')"
    elif missing_strategy == "Most Frequent":
        num_imputer_code = "numeric_imputer = SimpleImputer(strategy='most_frequent')"
        cat_imputer_code = "categorical_imputer = SimpleImputer(strategy='most_frequent')"
    else:
        num_imputer_code = "numeric_imputer = 'passthrough'"
        cat_imputer_code = "passthrough"

    if encoding_strategy == "None":
        encoder_code = "encoder = 'passthrough'"
    elif encoding_strategy == "One-Hot":
        encoder_code = "encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)"
    elif encoding_strategy == "Ordinal":
        encoder_code = "encoder = OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)"
    else:
        encoder_code = "encoder = 'passthrough'"

    if scaling_strategy == "None":
        scaler_code = "scaler = 'passthrough'"
    elif scaling_strategy == "StandardScaler":
        scaler_code = "scaler = StandardScaler()"
    elif scaling_strategy == "MinMaxScaler":
        scaler_code = "scaler = MinMaxScaler()"
    elif scaling_strategy == "RobustScaler":
        scaler_code = "scaler = RobustScaler()"
    else:
        scaler_code = "scaler = 'passthrough'"

    # Header and comments
    code = f'''# ==============================================================================
# MACHINE LEARNING PIPELINE
# Generated by Solvosys
# ==============================================================================
# This script contains the exact data pipeline, preprocessing, model configuration,
# training, and evaluation steps used during your session.
# Save this file as 'run_experiment.py' and ensure the dataset CSV file is placed
# in the same directory.
# ==============================================================================

'''
    
    # Imports Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 0. Imports\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += get_imports_code(config) + "\n\n\n"
    
    # Load Dataset Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 1. Load Dataset\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += f"DATASET_PATH = '{dataset_name}'\n"
    code += "print(f'Loading dataset: {DATASET_PATH}')\n"
    code += "df = pd.read_csv(DATASET_PATH)\n\n\n"
    
    # Feature & Target Selection Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 2. Feature & Target Selection\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += f"FEATURES = {repr(features)}\n"
    code += f"TARGET = {repr(target)}\n\n"
    code += "X = df[FEATURES]\n"
    code += "y = df[TARGET]\n\n\n"
    
    # Split Strategy Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 3. Split Strategy\n"
    code += "# ------------------------------------------------------------------------------\n"
    if split_method == "Train-Test Split":
        code += f"X_train, X_test, y_train, y_test = train_test_split(\n"
        code += f"    X, y, train_size={train_percent / 100}, random_state=42\n"
        code += f")\n"
    elif split_method == "K-Fold Cross Validation":
        code += f"cv = KFold(n_splits={folds}, shuffle=True, random_state=42)\n"
    elif split_method == "Stratified K-Fold Cross Validation":
        code += f"cv = StratifiedKFold(n_splits={folds}, shuffle=True, random_state=42)\n"
    code += "\n\n"
    
    # Preprocessing Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 4. Preprocessing Pipeline\n"
    code += "# ------------------------------------------------------------------------------\n"
    if split_method == "Train-Test Split":
        code += "# Feature types are detected from the training split to prevent leakage\n"
        code += "numeric_features = list(X_train.select_dtypes(include='number').columns)\n"
        code += "categorical_features = list(X_train.select_dtypes(include=['object', 'category', 'bool']).columns)\n"
    else:
        code += "# Feature types are detected from the full dataset for cross-validation\n"
        code += "numeric_features = list(X.select_dtypes(include='number').columns)\n"
        code += "categorical_features = list(X.select_dtypes(include=['object', 'category', 'bool']).columns)\n"
    
    code += "\n# Define handling strategies\n"
    code += f"{num_imputer_code}\n"
    code += f"{cat_imputer_code}\n"
    code += f"{encoder_code}\n"
    code += f"{scaler_code}\n\n"
    
    code += "# Assemble pipelines\n"
    code += "numeric_pipeline = Pipeline(steps=[\n"
    code += "    ('imputer', numeric_imputer),\n"
    code += "    ('scaler', scaler)\n"
    code += "])\n\n"
    
    code += "categorical_pipeline = Pipeline(steps=[\n"
    code += "    ('imputer', categorical_imputer),\n"
    code += "    ('encoder', encoder)\n"
    code += "])\n\n"
    
    code += "preprocessor = ColumnTransformer(\n"
    code += "    transformers=[\n"
    code += "        ('numeric', numeric_pipeline, numeric_features),\n"
    code += "        ('categorical', categorical_pipeline, categorical_features)\n"
    code += "    ],\n"
    code += "    remainder='drop',\n"
    code += "    verbose_feature_names_out=False\n"
    code += ")\n\n\n"
    
    # Model Setup Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 5. Model Configuration\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += f"# Model: {config.get('model_name')}\n"
    code += get_model_instantiation_code(problem_type, config.get("model_name"), config.get("hyperparameters", {})) + "\n\n\n"
    
    # Pipeline & Fitting Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 6. Build and Fit Pipeline\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += "pipeline = Pipeline(steps=[\n"
    code += "    ('preprocessor', preprocessor),\n"
    code += "    ('model', model)\n"
    code += "])\n\n"
    
    if split_method == "Train-Test Split":
        code += "print('Fitting pipeline on training data...')\n"
        code += "pipeline.fit(X_train, y_train)\n"
        code += "print('Training complete.')\n\n"
        code += "y_train_pred = pipeline.predict(X_train)\n"
        code += "y_test_pred = pipeline.predict(X_test)\n\n"
        
        if problem_type == "Classification":
            code += "y_test_prob = None\n"
            code += "if hasattr(pipeline, 'predict_proba'):\n"
            code += "    y_test_prob = pipeline.predict_proba(X_test)[:, 1]\n"
    else:
        code += "print('Generating out-of-fold cross-validation predictions...')\n"
        code += "y_pred = cross_val_predict(pipeline, X, y, cv=cv)\n\n"
        code += "print('Fitting pipeline on full dataset...')\n"
        code += "pipeline.fit(X, y)\n"
        code += "print('Pipeline fitted on full dataset.')\n"
        
    code += "\n\n"
    
    # Evaluation Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 7. Evaluation Metrics\n"
    code += "# ------------------------------------------------------------------------------\n"
    if split_method == "Train-Test Split":
        eval_y_true = "y_test"
        eval_y_pred = "y_test_pred"
    else:
        eval_y_true = "y"
        eval_y_pred = "y_pred"
        
    if problem_type == "Regression":
        code += f"r2 = r2_score({eval_y_true}, {eval_y_pred})\n"
        code += f"mse = mean_squared_error({eval_y_true}, {eval_y_pred})\n"
        code += f"rmse = np.sqrt(mse)\n"
        code += f"mae = mean_absolute_error({eval_y_true}, {eval_y_pred})\n"
        code += f"mape = mean_absolute_percentage_error({eval_y_true}, {eval_y_pred}) * 100\n\n"
        
        code += "print('\\n' + '=' * 40)\n"
        code += f"print('EVALUATION METRICS ({split_method})')\n"
        code += "print('=' * 40)\n"
        code += "print(f'R^2 Score: {r2:.4f}')\n"
        code += "print(f'RMSE:      {rmse:.4f}')\n"
        code += "print(f'MAE:       {mae:.4f}')\n"
        code += "print(f'MAPE:      {mape:.2f}%')\n"
        code += "print('=' * 40)\n"
    else:
        code += f"accuracy = accuracy_score({eval_y_true}, {eval_y_pred})\n"
        code += f"precision = precision_score({eval_y_true}, {eval_y_pred}, average='weighted', zero_division=0)\n"
        code += f"recall = recall_score({eval_y_true}, {eval_y_pred}, average='weighted', zero_division=0)\n"
        code += f"f1 = f1_score({eval_y_true}, {eval_y_pred}, average='weighted', zero_division=0)\n"
        code += f"cm = confusion_matrix({eval_y_true}, {eval_y_pred})\n\n"
        
        code += "print('\\n' + '=' * 40)\n"
        code += f"print('EVALUATION METRICS ({split_method})')\n"
        code += "print('=' * 40)\n"
        code += "print(f'Accuracy:  {accuracy:.2%}')\n"
        code += "print(f'Precision: {precision:.2%}')\n"
        code += "print(f'Recall:    {recall:.2%}')\n"
        code += "print(f'F1 Score:  {f1:.2%}')\n"
        code += "print('\\nConfusion Matrix:')\n"
        code += "print(cm)\n"
        code += "print('=' * 40)\n"
        
    code += "\n\n"
    
    # Plot Generation Section
    code += "# ------------------------------------------------------------------------------\n"
    code += "# 8. Publication-Quality Plots\n"
    code += "# ------------------------------------------------------------------------------\n"
    code += "sns.set_theme(style='whitegrid')\n"
    code += "plt.rcParams.update({\n"
    code += "    'font.family': 'serif',\n"
    code += "    'font.size': 12,\n"
    code += "    'axes.labelsize': 14,\n"
    code += "    'axes.titlesize': 14,\n"
    code += "    'xtick.labelsize': 12,\n"
    code += "    'ytick.labelsize': 12,\n"
    code += "    'legend.fontsize': 10,\n"
    code += "    'figure.dpi': 150,\n"
    code += "    'axes.grid': True,\n"
    code += "    'grid.alpha': 0.5,\n"
    code += "    'grid.color': 'lightgray',\n"
    code += "    'grid.linestyle': '-'\n"
    code += "})\n\n"
    
    if problem_type == "Regression":
        # Plot 1: Actual vs Predicted
        code += "# 1. Actual vs Predicted Scatter Plot\n"
        code += "fig, ax = plt.subplots(figsize=(8, 6))\n"
        code += f"ax.scatter({eval_y_true}, {eval_y_pred}, alpha=0.6, color='royalblue', edgecolor='k', s=70, label='Predictions')\n"
        code += f"min_val = min({eval_y_true}.min(), {eval_y_pred}.min())\n"
        code += f"max_val = max({eval_y_true}.max(), {eval_y_pred}.max())\n"
        code += "ax.plot([min_val, max_val], [min_val, max_val], 'r--', linewidth=2, label='Ideal Fit (y=x)')\n"
        code += f"ax.set_xlabel('Actual {target_label}')\n"
        code += f"ax.set_ylabel('Predicted {target_label}')\n"
        code += "ax.legend(loc='lower right', frameon=True, edgecolor='gray')\n"
        code += "plt.tight_layout()\n"
        code += "plt.savefig('actual_vs_predicted.png', dpi=300)\n"
        code += "print('Saved plot: actual_vs_predicted.png')\n"
        code += "plt.close()\n\n"
        
        # Plot 2: Residual Plot
        code += "# 2. Residual Plot\n"
        code += "fig, ax = plt.subplots(figsize=(8, 6))\n"
        code += f"residuals = {eval_y_true} - {eval_y_pred}\n"
        code += f"ax.scatter({eval_y_pred}, residuals, alpha=0.6, color='royalblue', edgecolor='k', s=70)\n"
        code += "ax.axhline(y=0, color='red', linestyle='--', linewidth=2)\n"
        code += f"ax.set_xlabel('Predicted {target_label}')\n"
        code += f"ax.set_ylabel('Residual ({target_label})')\n"
        code += "plt.tight_layout()\n"
        code += "plt.savefig('residuals_plot.png', dpi=300)\n"
        code += "print('Saved plot: residuals_plot.png')\n"
        code += "plt.close()\n\n"
        
        # Plot 3: Residual Distribution
        code += "# 3. Residual Distribution Histogram\n"
        code += "fig, ax = plt.subplots(figsize=(8, 6))\n"
        code += "ax.hist(residuals, bins=20, color='royalblue', edgecolor='black', alpha=0.8)\n"
        code += f"ax.set_xlabel('Residual ({target_label})')\n"
        code += "ax.set_ylabel('Frequency')\n"
        code += "plt.tight_layout()\n"
        code += "plt.savefig('residuals_distribution.png', dpi=300)\n"
        code += "print('Saved plot: residuals_distribution.png')\n"
        code += "plt.close()\n\n"
        
    else:
        # Plot 1: Confusion Matrix
        code += "# 1. Confusion Matrix Heatmap\n"
        code += "fig, ax = plt.subplots(figsize=(8, 6))\n"
        code += "sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', square=True, linewidths=0.8, linecolor='white', cbar=False,\n"
        code += "            annot_kws={'size': 12, 'weight': 'bold'}, ax=ax)\n"
        code += "ax.set_xlabel('Predicted Class')\n"
        code += "ax.set_ylabel('Actual Class')\n"
        code += "plt.tight_layout()\n"
        code += "plt.savefig('confusion_matrix.png', dpi=300)\n"
        code += "print('Saved plot: confusion_matrix.png')\n"
        code += "plt.close()\n\n"
        
        # Plot 2: ROC and PR Curves (if split is Train-Test and we have probabilities)
        if split_method == "Train-Test Split":
            code += "# 2. ROC & Precision-Recall Curves (if probabilities are supported)\n"
            code += "if hasattr(pipeline, 'predict_proba'):\n"
            # ROC Curve
            code += "    fig, ax = plt.subplots(figsize=(8, 6))\n"
            code += "    fpr, tpr, _ = roc_curve(y_test, y_test_prob)\n"
            code += "    roc_auc = auc(fpr, tpr)\n"
            code += "    ax.plot(fpr, tpr, color='royalblue', linewidth=2, label=f'AUC = {roc_auc:.3f}')\n"
            code += "    ax.plot([0, 1], [0, 1], 'r--', linewidth=2)\n"
            code += "    ax.set_xlabel('False Positive Rate')\n"
            code += "    ax.set_ylabel('True Positive Rate')\n"
            code += "    ax.legend(loc='lower right', frameon=True, edgecolor='gray')\n"
            code += "    plt.tight_layout()\n"
            code += "    plt.savefig('roc_curve.png', dpi=300)\n"
            code += "    print('Saved plot: roc_curve.png')\n"
            code += "    plt.close()\n\n"
            # PR Curve
            code += "    fig, ax = plt.subplots(figsize=(8, 6))\n"
            code += "    precision, recall, _ = precision_recall_curve(y_test, y_test_prob)\n"
            code += "    ax.plot(recall, precision, color='royalblue', linewidth=2)\n"
            code += "    ax.set_xlabel('Recall')\n"
            code += "    ax.set_ylabel('Precision')\n"
            code += "    plt.tight_layout()\n"
            code += "    plt.savefig('precision_recall_curve.png', dpi=300)\n"
            code += "    print('Saved plot: precision_recall_curve.png')\n"
            code += "    plt.close()\n\n"
            
    # Feature Importance Plot (if model has feature_importances_)
    code += "# 9. Feature Importance Plot (if supported by the model)\n"
    code += "model_step = pipeline.named_steps['model']\n"
    code += "if hasattr(model_step, 'feature_importances_'):\n"
    code += "    importances = model_step.feature_importances_\n"
    code += "    feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()\n"
    code += "    original_features = FEATURES\n\n"
    code += "    # Aggregate one-hot encoded features back to original feature names\n"
    code += "    aggregated = {}\n"
    code += "    cleaned_names = [name.replace('num__', '').replace('cat__', '') for name in feature_names]\n"
    code += "    for name, imp in zip(cleaned_names, importances):\n"
    code += "        matched = False\n"
    code += "        sorted_orig = sorted(original_features, key=len, reverse=True)\n"
    code += "        for orig in sorted_orig:\n"
    code += "            if name == orig or name.startswith(orig + '_'):\n"
    code += "                aggregated[orig] = aggregated.get(orig, 0.0) + imp\n"
    code += "                matched = True\n"
    code += "                break\n"
    code += "        if not matched:\n"
    code += "            aggregated[name] = aggregated.get(name, 0.0) + imp\n\n"
    code += "    agg_names = np.array(list(aggregated.keys()))\n"
    code += "    agg_imps = np.array(list(aggregated.values()))\n"
    code += "    order = np.argsort(agg_imps)[::-1]\n"
    code += "    agg_imps = agg_imps[order]\n"
    code += "    agg_names = agg_names[order]\n\n"
    code += "    # Keep top 15 features max\n"
    code += "    if len(agg_names) > 15:\n"
    code += "        agg_imps = agg_imps[:15]\n"
    code += "        agg_names = agg_names[:15]\n\n"
    code += "    fig, ax = plt.subplots(figsize=(8, 6))\n"
    code += "    ax.barh(agg_names[::-1], agg_imps[::-1], color='royalblue', edgecolor='black')\n"
    code += "    ax.set_xlabel('Feature Importance')\n"
    code += "    ax.set_ylabel('Features')\n"
    code += "    plt.tight_layout()\n"
    code += "    plt.savefig('feature_importance.png', dpi=300)\n"
    code += "    print('Saved plot: feature_importance.png')\n"
    code += "    plt.close()\n"

    return code
