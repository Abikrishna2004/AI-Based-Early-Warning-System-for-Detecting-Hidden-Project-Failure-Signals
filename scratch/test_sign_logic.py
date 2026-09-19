import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupShuffleSplit

import os
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))

data_paths = [
    os.path.join(project_root, 'data', 'project_sentinel_final_real_dataset.csv'),
    os.path.join(project_root, 'backend', 'data', 'project_sentinel_final_real_dataset.csv'),
    'data/project_sentinel_final_real_dataset.csv',
    '../data/project_sentinel_final_real_dataset.csv',
    'backend/data/project_sentinel_final_real_dataset.csv',
    'project_sentinel_final_real_dataset.csv'
]
dataset_path = None
for p in data_paths:
    if os.path.exists(p):
        dataset_path = p
        break

if not dataset_path:
    raise FileNotFoundError("Could not locate project_sentinel_final_real_dataset.csv in any standard location.")

df = pd.read_csv(dataset_path)
base_features = [
    'week_number', 'issue_count', 'task_completion_rate',
    'unresolved_issue_percentage', 'overdue_tasks_percentage',
    'defect_density', 'critical_bug_count', 'team_size',
    'schedule_progress_percentage', 'stale_days_threshold_used'
]
delta_features = [
    'issue_count_delta', 'task_completion_rate_delta',
    'overdue_tasks_percentage_delta', 'defect_density_delta', 'team_size_delta'
]
all_features = base_features + delta_features

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(df, groups=df['project_id']))

train_df = df.iloc[train_idx].reset_index(drop=True)
test_df = df.iloc[test_idx].reset_index(drop=True)

iso_v1 = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1).fit(train_df[base_features])
iso_v2 = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1).fit(train_df[all_features])

test_df['v1_anomaly'] = (iso_v1.predict(test_df[base_features]) == -1)
test_df['v2_anomaly'] = (iso_v2.predict(test_df[all_features]) == -1)
test_df['v1_score'] = iso_v1.decision_function(test_df[base_features])
test_df['v2_score'] = iso_v2.decision_function(test_df[all_features])

unique_v2 = test_df[~test_df['v1_anomaly'] & test_df['v2_anomaly']].copy()

worsening_mask = (
    (unique_v2['overdue_tasks_percentage_delta'] > 0) |
    (unique_v2['defect_density_delta'] > 0) |
    (unique_v2['task_completion_rate_delta'] < 0)
)

worsening_df = unique_v2[worsening_mask].copy()

print("Worsening rows total:", len(worsening_df))
print("Overdue delta > 0:", len(worsening_df[worsening_df['overdue_tasks_percentage_delta'] > 0]))
print("Completion delta < 0:", len(worsening_df[worsening_df['task_completion_rate_delta'] < 0]))
print("Defect delta > 0:", len(worsening_df[worsening_df['defect_density_delta'] > 0]))

# Check overdue spike examples
overdue_spikes = worsening_df[
    (worsening_df['overdue_tasks_percentage_delta'] > 5.0) &
    (worsening_df['overdue_tasks_percentage'] < 50.0)
].sort_values(by='overdue_tasks_percentage_delta', ascending=False)

print("\nTop Overdue Spike Examples:")
print(overdue_spikes[['project_id', 'week_number', 'overdue_tasks_percentage', 'overdue_tasks_percentage_delta', 'task_completion_rate_delta', 'defect_density_delta']].head(5))
