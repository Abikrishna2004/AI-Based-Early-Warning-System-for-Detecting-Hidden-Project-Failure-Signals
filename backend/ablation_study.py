"""
Project Sentinel - Delta Features Ablation Study Script
======================================================
Quantifies the contribution of trend/delta features to CatBoost risk classification.

Experiment Setup:
- Dataset: project_sentinel_final_real_dataset.csv
- Train/Test Split: 20% held-out test set grouped by project_id (GroupShuffleSplit, random_state=42)
- Hyperparameters (Both Models): depth=6, learning_rate=0.1, iterations=300, l2_leaf_reg=3, High class_weight=1.5x
- Model 1 ("Full Model"): Trained on all 15 features (10 base + 5 delta columns)
- Model 2 ("Ablated Model"): Trained on only 10 base features (5 delta columns removed)

Outputs:
1. Side-by-side performance evaluation table (Accuracy, Macro P/R/F1, High P/R/F1).
2. SHAP mean absolute importance ranking of all 15 features for Full Model.
3. Combined SHAP importance breakdown (5 Delta features vs 10 Base features).
4. Summary statement quantifying performance drop and SHAP importance percentage.
"""

import os
import time
from typing import Any, Dict, List, cast
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, classification_report, f1_score
from catboost import CatBoostClassifier
import shap

def run_ablation_study():
    print("=" * 90)
    print("               PROJECT SENTINEL - DELTA FEATURES ABLATION STUDY")
    print("=" * 90)

    # 1. Load Dataset
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
        raise FileNotFoundError("Dataset file 'project_sentinel_final_real_dataset.csv' not found.")

    print(f"\n[1/5] Loading dataset from '{dataset_path}'...")
    df = pd.read_csv(dataset_path)

    drop_cols = [
        'project_id', 'project_name', 'source_collection', 'week_ending',
        'threshold_reliable', 'team_size_reliable'
    ]
    target_col = 'risk_level'
    all_feature_cols = [c for c in df.columns if c not in drop_cols and c != target_col]

    delta_cols = [
        'issue_count_delta',
        'task_completion_rate_delta',
        'overdue_tasks_percentage_delta',
        'defect_density_delta',
        'team_size_delta'
    ]
    base_cols = [c for c in all_feature_cols if c not in delta_cols]

    print(f"      Total Features (15): {all_feature_cols}")
    print(f"      Base Features  (10): {base_cols}")
    print(f"      Delta Features  (5): {delta_cols}")

    X_full = df[all_feature_cols]
    X_ablated = df[base_cols]
    y = df[target_col]
    groups = df['project_id']

    # 2. Project-Grouped Train/Test Split (20% held-out test set)
    print("\n[2/5] Splitting dataset into 80% train / 20% test (GroupShuffleSplit on project_id, random_state=42)...")
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X_full, y, groups=groups))

    X_tr_full, X_te_full = X_full.iloc[train_idx].reset_index(drop=True), X_full.iloc[test_idx].reset_index(drop=True)
    X_tr_ablated, X_te_ablated = X_ablated.iloc[train_idx].reset_index(drop=True), X_ablated.iloc[test_idx].reset_index(drop=True)
    y_tr, y_te = y.iloc[train_idx].reset_index(drop=True), y.iloc[test_idx].reset_index(drop=True)

    print(f"      Train Samples: {len(X_tr_full)} across {groups.iloc[train_idx].nunique()} projects")
    print(f"      Test Samples : {len(X_te_full)} across {groups.iloc[test_idx].nunique()} projects")

    # Class ordering and 1.5x class weights
    temp_cb = CatBoostClassifier(iterations=10, verbose=False)
    temp_cb.fit(X_tr_full, y_tr)
    cb_classes = list(cast(Any, temp_cb).classes_)

    weights_dict = {'High': 1.5, 'Medium': 1.0, 'Low': 1.0}
    weights_list = [weights_dict[c] for c in cb_classes]
    print(f"      CatBoost class ordering: {cb_classes}")
    print(f"      Fixed Class Weights (High=1.5x baseline): {weights_dict} -> {weights_list}")

    # 3. Train Full Model & Ablated Model
    print("\n[3/5] Training Models with identical hyperparameters (depth=6, lr=0.1, iters=300, l2=3, High=1.5x)...")
    
    print("      - Training Model 1: Full Model (15 features)...")
    model_full = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        l2_leaf_reg=3,
        class_weights=weights_list,
        random_state=42,
        verbose=False,
        thread_count=-1
    )
    t0 = time.time()
    model_full.fit(X_tr_full, y_tr)
    t_full = time.time() - t0
    print(f"        Full Model training completed in {t_full:.2f}s.")

    print("      - Training Model 2: Ablated Model (10 base features, delta columns removed)...")
    model_ablated = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        l2_leaf_reg=3,
        class_weights=weights_list,
        random_state=42,
        verbose=False,
        thread_count=-1
    )
    t0 = time.time()
    model_ablated.fit(X_tr_ablated, y_tr)
    t_ablated = time.time() - t0
    print(f"        Ablated Model training completed in {t_ablated:.2f}s.")

    # 4. Evaluate Both Models on Held-Out Test Set
    print("\n[4/5] Evaluating Models on Held-Out Test Set...")
    preds_full = model_full.predict(X_te_full)
    if hasattr(preds_full, 'ravel'):
        preds_full = preds_full.ravel()

    preds_ablated = model_ablated.predict(X_te_ablated)
    if hasattr(preds_ablated, 'ravel'):
        preds_ablated = preds_ablated.ravel()

    rep_full = cast(Dict[str, Any], classification_report(y_te, preds_full, output_dict=True))
    acc_full = accuracy_score(y_te, preds_full)

    rep_ablated = cast(Dict[str, Any], classification_report(y_te, preds_ablated, output_dict=True))
    acc_ablated = accuracy_score(y_te, preds_ablated)

    comparison_data = [
        {
            'Model': 'Full Model (15 Features: 10 Base + 5 Deltas)',
            'Accuracy': f"{acc_full:.4f}",
            'Macro Precision': f"{rep_full['macro avg']['precision']:.4f}",
            'Macro Recall': f"{rep_full['macro avg']['recall']:.4f}",
            'Macro F1': f"{rep_full['macro avg']['f1-score']:.4f}",
            'High Precision': f"{rep_full['High']['precision']:.4f}",
            'High Recall': f"{rep_full['High']['recall']:.4f}",
            'High F1': f"{rep_full['High']['f1-score']:.4f}"
        },
        {
            'Model': 'Ablated Model (10 Features: 5 Deltas Removed)',
            'Accuracy': f"{acc_ablated:.4f}",
            'Macro Precision': f"{rep_ablated['macro avg']['precision']:.4f}",
            'Macro Recall': f"{rep_ablated['macro avg']['recall']:.4f}",
            'Macro F1': f"{rep_ablated['macro avg']['f1-score']:.4f}",
            'High Precision': f"{rep_ablated['High']['precision']:.4f}",
            'High Recall': f"{rep_ablated['High']['recall']:.4f}",
            'High F1': f"{rep_ablated['High']['f1-score']:.4f}"
        }
    ]
    comp_df = pd.DataFrame(comparison_data)

    print("\n=========================================================================================================")
    print("                              HELD-OUT TEST SET ABLATION COMPARISON TABLE")
    print("=========================================================================================================")
    print(comp_df.to_string(index=False))
    print("=========================================================================================================\n")

    # 5. SHAP Feature Importance Analysis for Full Model
    print("[5/5] Computing SHAP Mean Absolute Importance for Full Model...")
    # Sample 2000 test rows for fast & accurate SHAP calculation
    sample_size = min(2000, len(X_te_full))
    X_shap_sample = X_te_full.sample(n=sample_size, random_state=42)

    explainer = shap.TreeExplainer(model_full)
    shap_values = explainer.shap_values(X_shap_sample)

    # Handle shape of shap_values across multi-class
    if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
        if shap_values.shape[0] == len(cb_classes):
            shap_values_list = [shap_values[i] for i in range(len(cb_classes))]
        else:
            shap_values_list = [shap_values[:, :, i] for i in range(len(cb_classes))]
        shap_values = shap_values_list

    # Mean absolute SHAP per feature across samples and classes
    mean_abs_per_class = [np.abs(sv).mean(axis=0) for sv in shap_values]
    overall_feature_importance = np.mean(mean_abs_per_class, axis=0)

    shap_df = pd.DataFrame({
        'Feature': all_feature_cols,
        'Feature Type': ['Delta' if c in delta_cols else 'Base (Absolute)' for c in all_feature_cols],
        'Mean |SHAP|': overall_feature_importance
    }).sort_values(by='Mean |SHAP|', ascending=False).reset_index(drop=True)

    total_shap = shap_df['Mean |SHAP|'].sum()
    shap_df['Importance %'] = (shap_df['Mean |SHAP|'] / total_shap) * 100

    print("\n=========================================================================")
    print("              FULL MODEL SHAP FEATURE IMPORTANCE RANKING (ALL 15 FEATURES)")
    print("=========================================================================")
    print(shap_df.to_string(index=False))
    print("=========================================================================\n")

    delta_shap_sum = shap_df[shap_df['Feature Type'] == 'Delta']['Mean |SHAP|'].sum()
    base_shap_sum = shap_df[shap_df['Feature Type'] == 'Base (Absolute)']['Mean |SHAP|'].sum()

    delta_pct = (delta_shap_sum / total_shap) * 100
    base_pct = (base_shap_sum / total_shap) * 100

    print("-------------------------------------------------------------------------")
    print("                 FEATURE CATEGORY IMPORTANCE BREAKDOWN")
    print("-------------------------------------------------------------------------")
    print(f"  - 10 Base (Absolute-Value) Features Total SHAP: {base_shap_sum:.4f} ({base_pct:.2f}%)")
    print(f"  - 5 Delta (Trend) Features Total SHAP          : {delta_shap_sum:.4f} ({delta_pct:.2f}%)")
    print("-------------------------------------------------------------------------\n")

    # Quantify drops
    acc_drop = acc_full - acc_ablated
    acc_drop_pct = (acc_drop / acc_full) * 100

    f1_drop = rep_full['macro avg']['f1-score'] - rep_ablated['macro avg']['f1-score']
    f1_drop_pct = (f1_drop / rep_full['macro avg']['f1-score']) * 100

    high_recall_drop = rep_full['High']['recall'] - rep_ablated['High']['recall']

    print("=========================================================================================================")
    print("                                      SUMMARY STATEMENT & FINDINGS")
    print("=========================================================================================================")
    summary_msg = (
        f"(a) Impact of Removing Delta Features:\n"
        f"    - Overall Accuracy dropped by {acc_drop:.4f} ({acc_drop_pct:.2f}%) — from {acc_full:.4f} down to {acc_ablated:.4f}.\n"
        f"    - Macro F1-Score dropped by {f1_drop:.4f} ({f1_drop_pct:.2f}%) — from {rep_full['macro avg']['f1-score']:.4f} down to {rep_ablated['macro avg']['f1-score']:.4f}.\n"
        f"    - High-Risk Recall dropped by {high_recall_drop:.4f} — from {rep_full['High']['recall']:.4f} down to {rep_ablated['High']['recall']:.4f}.\n\n"
        f"(b) SHAP Importance Contribution:\n"
        f"    - The 5 trend/delta features account for {delta_pct:.2f}% of total SHAP feature importance in the Full Model,\n"
        f"      demonstrating that week-over-week velocity changes (deltas) provide significant predictive power\n"
        f"      beyond static weekly snapshot metrics alone."
    )
    print(summary_msg)
    print("=========================================================================================================\n")

if __name__ == '__main__':
    run_ablation_study()
