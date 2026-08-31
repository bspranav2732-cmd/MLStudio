import numpy as np

def get_parameter_space(model_name):
    """
    Returns the searchable parameter space for Grid Search and Random Search.
    """
    
    if model_name == "Random Forest":
        return {
            "model__n_estimators": [300, 500, 700, 1000, 1500],
            "model__max_depth": [3, 5, 6, 8, 10, 12, 15, None],
            "model__min_samples_split": [2, 3, 5, 8, 10, 15],
            "model__min_samples_leaf": [1, 2, 3, 4, 5],
            "model__max_features": ["sqrt", "log2", 0.4, 0.5, 0.6, 0.7, 0.8, 1.0],
            "model__max_samples": [0.6, 0.7, 0.8, 0.9, None],
            "model__min_impurity_decrease": [0.0, 0.001, 0.005, 0.01]
        }
        
    elif model_name in ["XGBoost Regressor", "XGBoost Classifier"]:
        return {
            "model__n_estimators": [50, 100, 200, 300],
            "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
            "model__max_depth": [3, 5, 7, 9],
            "model__subsample": [0.6, 0.8, 1.0],
            "model__colsample_bytree": [0.6, 0.8, 1.0]
        }
        
    elif model_name in ["CatBoost Regressor", "CatBoost Classifier"]:
        return {
            "model__iterations": [50, 100, 200, 300],
            "model__learning_rate": [0.01, 0.05, 0.1, 0.2],
            "model__depth": [4, 6, 8, 10],
            "model__l2_leaf_reg": [1, 3, 5, 7, 9]
        }
        
    elif model_name == "Decision Tree":
        return {
            "model__max_depth": [None, 5, 10, 20, 30],
            "model__min_samples_split": [2, 5, 10],
            "model__min_samples_leaf": [1, 2, 4]
        }
        
    elif model_name == "Logistic Regression":
        return {
            "model__C": [0.01, 0.1, 1.0, 10.0, 100.0],
            "model__solver": ["lbfgs", "liblinear", "newton-cg", "saga"]
        }
        
    elif model_name == "Lasso Regression":
        return {
            "model__alpha": [0.001, 0.01, 0.1, 1.0, 10.0, 100.0]
        }
        
    elif model_name == "Elastic Net":
        return {
            "model__alpha": [0.001, 0.01, 0.1, 1.0, 10.0, 100.0],
            "model__l1_ratio": [0.1, 0.3, 0.5, 0.7, 0.9]
        }
        
    elif model_name == "Polynomial Regression":
        return {
            "model__poly__degree": [2, 3, 4, 5]
        }
        
    elif model_name == "Linear Regression":
        return {} # No hyperparameters to tune
        
    return {}
