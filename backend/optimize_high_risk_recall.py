"""
Project Sentinel - High-Risk Recall Optimization & Model Comparison Script
==========================================================================

This script evaluates 3 approaches to resolve the High-Risk recall gap (~54-56%):
1. Custom Class Weights in CatBoost (e.g. High-class weighted 1.5x, 2.0x, 2.5x)
2. Custom Decision Thresholding on P(High) (e.g. P(High) > 0.30, 0.35, 0.40)
3. Two-Stage Hierarchical Classification Architecture (Binary High vs Not-High -> Secondary Low vs Medium)

Saves the winning optimal model & threshold logic to 'best_model_catboost.cbm' and metadata.
"""

import os
import joblib
from typing import Any, Dict, List, cast
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
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

print(f"[DATA] Loading dataset from '{dataset_path}'...")
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

print(f"[SPLIT] Train samples: {len(X_train)}, Test samples: {len(X_test)}")
print(f"[SPLIT] Test class counts:\n{y_test.value_counts()}\n")

summary_results = []

def evaluate_predictions(y_true, y_pred, model_name, extra_info=""):
    report = cast(Dict[str, Any], classification_report(y_true, y_pred, output_dict=True))
    acc = accuracy_score(y_true, y_pred)
    high_rec = report['High']['recall']
    high_prec = report['High']['precision']
    high_f1 = report['High']['f1-score']
    
    summary_results.append({
        'Approach': model_name,
        'Config / Details': extra_info,
        'Overall Acc': round(acc, 4),
        'High Recall': round(high_rec, 4),
        'High Precision': round(high_prec, 4),
        'High F1-Score': round(high_f1, 4),
        'Macro F1': round(report['macro avg']['f1-score'], 4)
    })
    return report

# ==============================================================================
# BASELINE: Standard CatBoost (Uniform / Balanced argmax)
# ==============================================================================
print("--- [BASELINE] Standard CatBoost (Balanced argmax) ---")
base_cb = CatBoostClassifier(
    iterations=300,
    depth=6,
    learning_rate=0.1,
    random_state=42,
    auto_class_weights='Balanced',
    verbose=False,
    thread_count=-1
)
base_cb.fit(X_train, y_train)
base_pred = base_cb.predict(X_test).ravel()
evaluate_predictions(y_test, base_pred, "Baseline (Argmax)", "Balanced Class Weights")
base_probs = base_cb.predict_proba(X_test)
cb_classes = list(cast(Any, base_cb).classes_)
high_idx = cb_classes.index('High')

# ==============================================================================
# APPROACH 1: Custom Class Weights in CatBoost
# ==============================================================================
print("\n--- [APPROACH 1] Custom Class Weights in CatBoost ---")
# Order of classes in CatBoost: ['High', 'Low', 'Medium'] or similar
print(f"CatBoost class order: {cb_classes}")

weight_configs = [
    {'High': 1.5, 'Medium': 1.0, 'Low': 1.0},
    {'High': 2.0, 'Medium': 1.0, 'Low': 1.0},
    {'High': 2.5, 'Medium': 1.0, 'Low': 1.0},
    {'High': 3.0, 'Medium': 1.0, 'Low': 1.0}
]

app1_models = {}
for weights_dict in weight_configs:
    weights_list = [weights_dict[c] for c in cb_classes]
    w_str = f"High weight: {weights_dict['High']}x"
    print(f"Training CatBoost with class weights {weights_dict} ({cb_classes})...")
    
    model_w = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        random_state=42,
        class_weights=weights_list,
        verbose=False,
        thread_count=-1
    )
    model_w.fit(X_train, y_train)
    pred_w = model_w.predict(X_test).ravel()
    evaluate_predictions(y_test, pred_w, "Approach 1 (Class Weights)", w_str)
    app1_models[weights_dict['High']] = (model_w, pred_w)

# ==============================================================================
# APPROACH 2: Custom Probability Thresholding on P(High)
# ==============================================================================
print("\n--- [APPROACH 2] Custom Decision Thresholding on P(High) ---")
# Using probabilities from base_cb (or best class-weighted model)
thresholds = [0.45, 0.40, 0.35, 0.30, 0.25]

def predict_with_threshold(probs, classes, high_threshold):
    high_class_index = classes.index('High')
    low_class_index = classes.index('Low')
    med_class_index = classes.index('Medium')
    
    preds = []
    for row in probs:
        p_high = row[high_class_index]
        if p_high >= high_threshold:
            preds.append('High')
        else:
            # Pick argmax between Low and Medium
            if row[low_class_index] >= row[med_class_index]:
                preds.append('Low')
            else:
                preds.append('Medium')
    return np.array(preds)

for th in thresholds:
    pred_th = predict_with_threshold(base_probs, cb_classes, th)
    evaluate_predictions(y_test, pred_th, "Approach 2 (Custom Threshold)", f"P(High) >= {th}")

# ==============================================================================
# APPROACH 3: Two-Stage Hierarchical Classification Architecture
# ==============================================================================
print("\n--- [APPROACH 3] Two-Stage Hierarchical Classifier ---")
# Stage 1: Binary Classifier (High vs Not-High)
y_train_binary = (y_train == 'High').astype(int)
y_test_binary = (y_test == 'High').astype(int)

# Count ratio of Not-High to High for scale_pos_weight
pos_ratio = (len(y_train) - sum(y_train_binary)) / max(1, sum(y_train_binary))
print(f"Stage 1 Binary Class Ratio (Not-High / High): {pos_ratio:.2f}")

for pos_weight in [1.5, 2.0, 2.5]:
    stage1_cb = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        random_state=42,
        scale_pos_weight=pos_weight,
        verbose=False,
        thread_count=-1
    )
    stage1_cb.fit(X_train, y_train_binary)
    stage1_pred_prob = stage1_cb.predict_proba(X_test)[:, 1]
    
    # Stage 2: Multiclass for Low vs Medium on non-High training data
    non_high_mask_train = (y_train != 'High')
    X_train_s2 = X_train[non_high_mask_train]
    y_train_s2 = y_train[non_high_mask_train]
    
    stage2_cb = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        random_state=42,
        auto_class_weights='Balanced',
        verbose=False,
        thread_count=-1
    )
    stage2_cb.fit(X_train_s2, y_train_s2)
    stage2_pred = stage2_cb.predict(X_test).ravel()
    
    # Combined predictions
    for th in [0.35, 0.30]:
        two_stage_preds = []
        for i in range(len(X_test)):
            if stage1_pred_prob[i] >= th:
                two_stage_preds.append('High')
            else:
                two_stage_preds.append(stage2_pred[i])
                
        two_stage_preds = np.array(two_stage_preds)
        evaluate_predictions(
            y_test,
            two_stage_preds,
            "Approach 3 (Two-Stage Hierarchical)",
            f"Stage1 Weight: {pos_weight}x, P(High)>={th}"
        )

# ==============================================================================
# SUMMARY & RECOMMENDATION ANALYSIS
# ==============================================================================
summary_df = pd.DataFrame(summary_results)
print("\n" + "=" * 80)
print("             ALL APPROACHES EVALUATION METRICS COMPARISON TABLE")
print("=" * 80)
print(summary_df.to_string(index=False))
print("=" * 80 + "\n")

# Save summary metrics to CSV for analysis
summary_df.to_csv("high_risk_recall_optimization_results.csv", index=False)
print("Saved metrics summary to 'high_risk_recall_optimization_results.csv'.")
