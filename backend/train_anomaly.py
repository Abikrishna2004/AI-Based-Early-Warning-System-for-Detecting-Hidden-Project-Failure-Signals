import os
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

# 1. Load dataset from data folder
script_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(script_dir, '..', 'data', 'project_sentinel_final_real_dataset.csv')
assert dataset_path is not None
df = pd.read_csv(dataset_path)

# 2. Extract 15 features (unsupervised training, ignoring risk_level)
feature_cols = [
    'week_number', 'issue_count', 'task_completion_rate',
    'unresolved_issue_percentage', 'overdue_tasks_percentage',
    'defect_density', 'critical_bug_count', 'team_size',
    'schedule_progress_percentage', 'stale_days_threshold_used',
    'issue_count_delta', 'task_completion_rate_delta',
    'overdue_tasks_percentage_delta', 'defect_density_delta', 'team_size_delta'
]

X = df[feature_cols]

print(f"Training IsolationForest on {X.shape[0]} rows, {X.shape[1]} features (contamination=0.1, random_state=42)...")

# 3. Fit IsolationForest
iso_forest = IsolationForest(
    contamination=0.1,
    random_state=42,
    n_jobs=-1
)
iso_forest.fit(X)

# 4. Save model using joblib
model_path = os.path.join(script_dir, 'anomaly_model.pkl')
joblib.dump(iso_forest, model_path)
print(f"IsolationForest model successfully saved to '{model_path}'.")
