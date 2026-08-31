from sklearn.model_selection import (
    train_test_split,
    KFold,
    StratifiedKFold,
    RepeatedKFold,
    RepeatedStratifiedKFold
)

def get_validation_method(
    split_method,
    X,
    y,
    train_size=0.8,
    folds=5,
    repeats=1,
    problem_type=None,
    random_state=42,
    shuffle=True
):
    """
    Returns the appropriate scikit-learn cross-validator or performs train-test split.
    """
    import pandas as pd
    if split_method == "Train-Test Split":
        stratify = y if problem_type == "Classification" else None
        
        if stratify is not None:
            min_class_count = pd.Series(y).value_counts().min()
            if min_class_count < 2:
                raise ValueError(f"Stratified Train-Test Split failed: the dataset contains a class with only {min_class_count} sample(s). At least 2 samples per class are required.")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            train_size=train_size,
            random_state=random_state,
            shuffle=shuffle,
            stratify=stratify
        )
        return X_train, X_test, y_train, y_test
        
    elif split_method == "K-Fold Cross Validation":
        if problem_type == "Classification":
            min_class_count = pd.Series(y).value_counts().min()
            if min_class_count < folds:
                raise ValueError(f"Stratified K-Fold failed: a class has only {min_class_count} sample(s), but {folds} folds were requested.")
            return StratifiedKFold(
                n_splits=folds,
                shuffle=shuffle,
                random_state=random_state if shuffle else None
            )
        return KFold(
            n_splits=folds,
            shuffle=shuffle,
            random_state=random_state if shuffle else None
        )
        
    elif split_method == "Stratified K-Fold Cross Validation":
        min_class_count = pd.Series(y).value_counts().min()
        if min_class_count < folds:
            raise ValueError(f"Stratified K-Fold failed: a class has only {min_class_count} sample(s), but {folds} folds were requested.")
        return StratifiedKFold(
            n_splits=folds,
            shuffle=shuffle,
            random_state=random_state if shuffle else None
        )
        
    elif split_method == "Repeated K-Fold":
        if problem_type == "Classification":
            min_class_count = pd.Series(y).value_counts().min()
            if min_class_count < folds:
                raise ValueError(f"Repeated Stratified K-Fold failed: a class has only {min_class_count} sample(s), but {folds} folds were requested.")
            return RepeatedStratifiedKFold(
                n_splits=folds,
                n_repeats=repeats,
                random_state=random_state
            )
        return RepeatedKFold(
            n_splits=folds,
            n_repeats=repeats,
            random_state=random_state
        )
        
    elif split_method == "Repeated Stratified K-Fold":
        min_class_count = pd.Series(y).value_counts().min()
        if min_class_count < folds:
            raise ValueError(f"Repeated Stratified K-Fold failed: a class has only {min_class_count} sample(s), but {folds} folds were requested.")
        return RepeatedStratifiedKFold(
            n_splits=folds,
            n_repeats=repeats,
            random_state=random_state
        )
        
    else:
        raise ValueError(f"Invalid Split Method: {split_method}")
