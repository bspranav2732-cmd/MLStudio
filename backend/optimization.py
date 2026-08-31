import time
import sys
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

def run_optimization(pipeline, param_space, cv, X, y, strategy="Random Search", n_iter=10, random_state=42, problem_type="Regression"):
    """
    Runs hyperparameter optimization using Grid Search or Random Search.
    Returns the best estimator, best parameters, and best score.
    """
    scoring = "r2" if problem_type == "Regression" else "accuracy"
    
    # n_jobs=1 is used intentionally: on Windows, joblib multiprocessing
    # introduces significant overhead for small-to-medium datasets that
    # makes n_jobs=-1 slower (verified via diagnostic: 17.7s vs 10.8s
    # on 80 rows). The Streamlit frozen-app environment compounds this.
    n_jobs = 1
    
    # Debug diagnostics
    n_samples, n_features = X.shape
    total_combinations = 1
    for k, v in param_space.items():
        total_combinations *= len(v)
    
    if strategy == "Random Search":
        actual_iters = min(n_iter, total_combinations)
        total_fits = actual_iters * (cv.get_n_splits(X, y) if hasattr(cv, 'get_n_splits') else cv)
        print(f"\n{'='*50}", file=sys.stderr)
        print(f"Random Search started", file=sys.stderr)
        print(f"  Dataset: {n_samples} rows × {n_features} features", file=sys.stderr)
        print(f"  Search space: {total_combinations} total combinations", file=sys.stderr)
        print(f"  {actual_iters} iterations × {total_fits // actual_iters} folds = {total_fits} fits", file=sys.stderr)
        print(f"  n_jobs={n_jobs}, scoring={scoring}", file=sys.stderr)
        print(f"{'='*50}", file=sys.stderr)
    
    if strategy == "Grid Search":
        search = GridSearchCV(
            estimator=pipeline,
            param_grid=param_space,
            cv=cv,
            scoring=scoring,
            n_jobs=n_jobs,
            verbose=1
        )
    elif strategy == "Random Search":
        search = RandomizedSearchCV(
            estimator=pipeline,
            param_distributions=param_space,
            n_iter=n_iter,
            cv=cv,
            scoring=scoring,
            n_jobs=n_jobs,
            verbose=1,
            random_state=random_state
        )
    else:
        raise ValueError("Invalid Optimization Strategy")
        
    # Fit the search with timing
    fit_start = time.time()
    search.fit(X, y)
    fit_elapsed = time.time() - fit_start
    
    # Strip 'model__' prefix from best parameters for cleaner reporting
    clean_params = {}
    for k, v in search.best_params_.items():
        if k.startswith("model__"):
            clean_params[k.replace("model__", "")] = v
        elif k.startswith("poly__"):
            clean_params[k.replace("poly__", "")] = v
        else:
            clean_params[k] = v
    
    print(f"\n{'='*50}", file=sys.stderr)
    print(f"{strategy} completed in {fit_elapsed:.2f}s", file=sys.stderr)
    print(f"  Best CV {scoring}: {search.best_score_:.4f}", file=sys.stderr)
    print(f"  Best parameters: {clean_params}", file=sys.stderr)
    print(f"{'='*50}\n", file=sys.stderr)
            
    return {
        "best_estimator": search.best_estimator_,
        "best_params": clean_params,
        "best_score": search.best_score_,
        "cv_results": search.cv_results_
    }
