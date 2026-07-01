# ML Studio

A Python-based Machine Learning Studio that allows users to train and compare machine learning models without writing code.

## Objective

Build an application where users can:

* Upload datasets
* Select input (X) and output (Y) columns
* Automatically preprocess data
* Train multiple machine learning models
* Compare model performance
* Detect overfitting and underfitting
* Generate plots
* Export the entire workflow as a Jupyter Notebook

The first version is being developed as a Python application before adding a graphical user interface.

---

## Current Progress

### ✅ Milestone 1

* Dataset Loader
* Dataset Summary
* Missing Value Detection
* Duplicate Detection
* Column Information

### 🚧 In Progress

* Feature (X) and Target (Y) Selection

### 📅 Upcoming

* Automatic Feature Detection
* Train/Test Split
* Linear Regression
* Decision Tree
* Random Forest
* XGBoost
* CatBoost
* Model Comparison
* Plot Generation
* Notebook Generator

---

## Project Structure

```
backend/
│
├── datasets/
├── outputs/
├── dataset.py
├── models.py
├── evaluation.py
├── notebook.py
├── mlstudio.py
```

---

## Technologies

* Python
* Pandas
* NumPy
* Scikit-Learn
* Matplotlib

---

## Future Plans

* Desktop GUI
* Web Application
* Project Saving
* PDF Reports
* Experiment Tracking
* Notebook Export
