import pandas as pd

def load_dataset(file_path):
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")
        
    if len(df) < 2:
        raise ValueError("Dataset must contain at least 2 rows for evaluation.")
    if len(df.columns) < 2:
        raise ValueError("Dataset must contain at least 2 columns (features and target).")
    if df.columns.duplicated().any():
        raise ValueError("Dataset contains duplicate column names. Please rename or remove duplicates.")
        
    return df


def dataset_summary(df):

    summary = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "column_names": df.columns.tolist(),
        "data_types": df.dtypes.astype(str).to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum())
    }

    return summary

def choose_target(df):

    print("\nAvailable Columns\n")

    for i, col in enumerate(df.columns, start=1):
        print(f"{i}. {col}")

    while True:

        try:
            choice = int(input("\nChoose Target Column Number: "))

            if 1 <= choice <= len(df.columns):
                target = df.columns[choice - 1]
                return target

            else:
                print("Invalid selection.")

        except ValueError:
            print("Please enter a number.")