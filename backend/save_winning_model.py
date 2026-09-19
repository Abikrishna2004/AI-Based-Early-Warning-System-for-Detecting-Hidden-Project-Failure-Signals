"""
Project Sentinel - Save Winning High-Recall CatBoost Model
===========================================================
Trains the recommended CatBoost model with High-class weighted 2.0x relative to Low/Medium
and saves it to disk as 'best_model_catboost.cbm'.
"""

import os
from typing import Any, cast
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from catboost import CatBoostClassifier

data_paths = [
    '../data/project_sentinel_final_real_dataset.csv',
    'data/project_sentinel_final_real_dataset.csv',
    'project_sentinel_final_real_dataset.csv'
]

dataset_path = None
for p in data_paths:
    if os.path.exists(p):
        dataset_path = p
        break

if not dataset_path:
    raise FileNotFoundError("Could not locate project_sentinel_final_real_dataset.csv")

df = pd.read_csv(dataset_path)

drop_cols = [
    'project_id',
    'project_name',
    'source_collection',
    'week_ending',
    'threshold_reliable',
    'team_size_reliable'
]

target_col = 'risk_level'
feature_cols = [col for col in df.columns if col not in drop_cols and col != target_col]

X = df[feature_cols]
y = df[target_col]
groups = df['project_id']

gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

print("[WINNING MODEL] Training CatBoost with High class_weight = 2.0x...")

# Fit base model to get full class ordering
temp_model = CatBoostClassifier(iterations=10, verbose=False)
temp_model.fit(X_train, y_train)
cb_classes = list(cast(Any, temp_model).classes_)
print(f"CatBoost class ordering: {cb_classes}")

weights_dict = {'High': 2.0, 'Medium': 1.0, 'Low': 1.0}
weights_list = [weights_dict[c] for c in cb_classes]

winning_cb = CatBoostClassifier(
    iterations=300,
    depth=6,
    learning_rate=0.1,
    random_state=42,
    class_weights=weights_list,
    verbose=False,
    thread_count=-1
)

winning_cb.fit(X_train, y_train)

model_filename = 'best_model_catboost.cbm'
winning_cb.save_model(model_filename)
print(f"[SUCCESS] Saved winning high-recall model to '{model_filename}'.")
