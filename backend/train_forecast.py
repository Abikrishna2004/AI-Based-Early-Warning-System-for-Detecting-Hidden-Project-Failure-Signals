import os
import pandas as pd
import numpy as np

# Load training dataset
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, '..', 'data', 'project_sentinel_final_real_dataset.csv')
assert dataset_path is not None
df = pd.read_csv(dataset_path)

print(f"Loaded dataset with {len(df)} rows across {df['project_id'].nunique()} unique projects.")

# Demonstrate project time series extraction for overdue_tasks_percentage
sample_project_id = df['project_id'].unique()[0]
project_df = df[df['project_id'] == sample_project_id].sort_values('week_number')

overdue_series = project_df['overdue_tasks_percentage'].tail(6).tolist()
weeks_series = project_df['week_number'].tail(6).tolist()

print(f"\nSample Project ID: {sample_project_id}")
print(f"Last 6 Weeks: {weeks_series}")
print(f"Overdue Tasks %: {overdue_series}")

# Linear fit demonstration
X = np.arange(1, len(overdue_series) + 1)
Y = np.array(overdue_series)
m, c = np.polyfit(X, Y, 1)

w1 = np.clip(m * (len(overdue_series) + 1) + c, 0, 100)
w2 = np.clip(m * (len(overdue_series) + 2) + c, 0, 100)
w3 = np.clip(m * (len(overdue_series) + 3) + c, 0, 100)

print(f"Linear Fit Slope: {m:.2f} percentage points/week")
print(f"Forecast (+1 week): {w1:.1f}%")
print(f"Forecast (+2 weeks): {w2:.1f}%")
print(f"Forecast (+3 weeks): {w3:.1f}%")
