import pandas as pd

# Load the dataset
dataset_path = 'project_sentinel_final_real_dataset.csv'
assert dataset_path is not None
df = pd.read_csv(dataset_path)

# 1. Shape of the dataset
print("--- Dataset Shape (Rows, Columns) ---")
print(df.shape)
print()

# 2. List of all column names
print("--- Column Names ---")
print(df.columns.tolist())
print()

# 3. Value counts for risk_level column
print("--- Value Counts for 'risk_level' ---")
if 'risk_level' in df.columns:
    print(df['risk_level'].value_counts(dropna=False))
else:
    print("Column 'risk_level' NOT found in dataset.")
print()

# 4. Total number of missing values across the entire dataset
print("--- Total Missing Values Across Entire Dataset ---")
print(df.isnull().sum().sum())
