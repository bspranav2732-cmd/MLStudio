import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold, cross_validate, cross_val_predict
from sklearn.pipeline import make_pipeline

# 1. Load the dataset
# Make sure 'exam.csv' is in the same directory as this script
df = pd.read_csv('datasets/exam.csv')

# 2. Separate features (X) and target (y)
# Reshaping X because scikit-learn expects a 2D array for features
X = df['study_hours'].values.reshape(-1, 1)
y = df['exam_score'].values

# 3. Create a Polynomial Regression Pipeline
# This automatically transforms features to 2nd degree, then fits a Linear Regression
poly_model = make_pipeline(
    PolynomialFeatures(degree=2, include_bias=False),
    LinearRegression()
)

# 4. Setup 5-Fold Cross-Validation
kf = KFold(n_splits=5, shuffle=True, random_state=42)

# 5. Perform Cross-Validation and calculate metrics
scores = cross_validate(
    poly_model,
    X,
    y,
    cv=kf,
    scoring=[
        'r2',
        'neg_mean_squared_error',
        'neg_mean_absolute_error',
        'neg_mean_absolute_percentage_error'
    ]
)

# 6. Extract and calculate final metrics
# Calculate means
r2_mean = scores['test_r2'].mean()
rmse_mean = np.sqrt(-scores['test_neg_mean_squared_error']).mean()
mae_mean = (-scores['test_neg_mean_absolute_error']).mean()
mape_mean = (-scores['test_neg_mean_absolute_percentage_error']).mean() * 100 # Convert to percentage

# Calculate 95% Confidence Interval for R2
r2_std = scores['test_r2'].std()
r2_ci_lower = r2_mean - (1.96 * r2_std)
r2_ci_upper = r2_mean + (1.96 * r2_std)

# 7. Print Results in Journal-Ready Format
print("2nd Degree Polynomial Regression Results")
print("-" * 40)
print(f"Mean R²   : {r2_mean:.4f} [95% CI: {r2_ci_lower:.4f}, {r2_ci_upper:.4f}]")
print(f"Mean RMSE : {rmse_mean:.4f}")
print(f"Mean MAE  : {mae_mean:.4f}")
print(f"Mean MAPE : {mape_mean:.4f}%")

print("Generating cross-validated predictions and plot...")
y_pred_cv = cross_val_predict(poly_model, X, y, cv=kf)

# Maintain seaborn grid but force serif font
sns.set_theme(style="whitegrid", rc={"font.family": "serif"}) 

fig, ax = plt.subplots(figsize=(8, 6))

ax.scatter(y, y_pred_cv, alpha=0.6, color='royalblue', edgecolor='k')
min_val = min(y.min(), y_pred_cv.min())
max_val = max(y.max(), y_pred_cv.max())
ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='Ideal Fit (y=x)')

ax.set_xlabel('Actual Exam Score')
ax.set_ylabel('Predicted Exam Score')
ax.legend(loc='lower right')

# Embed metrics inside the plot (Top-Left Corner)
metrics_text = f"Polynomial (Degree=2)\nCV $R^2$ = {r2_mean:.4f}\nCV RMSE = {rmse_mean:.4f}"
ax.text(0.05, 0.95, metrics_text, transform=ax.transAxes,
         fontsize=12, verticalalignment='top', 
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='gray'))

plt.tight_layout()
plt.savefig('poly_actual_vs_predicted_high_res.png', dpi=300, bbox_inches='tight')
plt.show()