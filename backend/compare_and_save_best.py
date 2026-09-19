import os
from typing import Any, Dict, List, cast
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from catboost import CatBoostClassifier

# 1. Load dataset & prepare features
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

# GroupShuffleSplit (test_size=0.2, random_state=42)
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

results = []

# --- 2. Train & Evaluate Random Forest ---
print("Training Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
rf_pred = rf_model.predict(X_test)

rf_acc = accuracy_score(y_test, rf_pred)
rf_report = cast(Dict[str, Any], classification_report(y_test, rf_pred, output_dict=True))

results.append({
    'Model Name': 'Random Forest',
    'Accuracy': rf_acc,
    'Macro Precision': rf_report['macro avg']['precision'],
    'Macro Recall': rf_report['macro avg']['recall'],
    'Macro F1-score': rf_report['macro avg']['f1-score'],
    'High Risk Recall': rf_report['High']['recall']
})

# --- 3. Train & Evaluate XGBoost ---
print("Training XGBoost...")
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train)

xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric='mlogloss',
    n_jobs=-1
)
xgb_model.fit(X_train, y_train_encoded)
xgb_pred_encoded = xgb_model.predict(X_test)
xgb_pred = le.inverse_transform(xgb_pred_encoded)

xgb_acc = accuracy_score(y_test, xgb_pred)
xgb_report = cast(Dict[str, Any], classification_report(y_test, xgb_pred, output_dict=True))

results.append({
    'Model Name': 'XGBoost',
    'Accuracy': xgb_acc,
    'Macro Precision': xgb_report['macro avg']['precision'],
    'Macro Recall': xgb_report['macro avg']['recall'],
    'Macro F1-score': xgb_report['macro avg']['f1-score'],
    'High Risk Recall': xgb_report['High']['recall']
})

# --- 4. Train & Evaluate CatBoost (High-Risk Weighted 2.0x) ---
print("Training CatBoost (High-Risk Weighted 2.0x)...")
temp_cb = CatBoostClassifier(iterations=10, verbose=False)
temp_cb.fit(X_train, y_train)
cb_classes = list(cast(Any, temp_cb).classes_)

weights_dict = {'High': 2.0, 'Medium': 1.0, 'Low': 1.0}
weights_list = [weights_dict[c] for c in cb_classes]

cb_model = CatBoostClassifier(
    iterations=300,
    depth=6,
    learning_rate=0.1,
    random_state=42,
    class_weights=weights_list,
    verbose=False,
    thread_count=-1
)
cb_model.fit(X_train, y_train)
cb_pred = cb_model.predict(X_test)
if hasattr(cb_pred, 'ravel'):
    cb_pred = cb_pred.ravel()

cb_acc = accuracy_score(y_test, cb_pred)
cb_report = cast(Dict[str, Any], classification_report(y_test, cb_pred, output_dict=True))

results.append({
    'Model Name': 'CatBoost (High Weighted 2.0x)',
    'Accuracy': cb_acc,
    'Macro Precision': cb_report['macro avg']['precision'],
    'Macro Recall': cb_report['macro avg']['recall'],
    'Macro F1-score': cb_report['macro avg']['f1-score'],
    'High Risk Recall': cb_report['High']['recall']
})

# --- 5. Summary Table & Sorting ---
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(by='High Risk Recall', ascending=False).reset_index(drop=True)

print("\n================ MODEL COMPARISON SUMMARY TABLE ================")
print(results_df.to_string(index=False))
print("=================================================================\n")

# --- 6. Save Best Model (CatBoost) ---
model_filename = 'best_model_catboost.cbm'
cb_model.save_model(model_filename)
print(f"CatBoost model successfully saved to disk as '{model_filename}' using save_model().")
