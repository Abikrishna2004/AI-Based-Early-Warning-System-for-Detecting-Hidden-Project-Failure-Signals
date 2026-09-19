"""
Project Sentinel - Size-Balanced 5-Fold Cross-Validation Script
================================================================
1. Identifies the project isolated alone in Fold 1 of standard GroupKFold and inspects its row count & risk distribution.
2. Implements Size-Balanced Group Assignment strategies (Greedy Min-Heap Bin Packing & Round-Robin on projects sorted by size descending).
3. Evaluates 5-fold cross-validation of baseline CatBoost on balanced folds.
4. Outputs per-fold breakdown and final aggregate statistics.
"""

import os
import time
from typing import Any, Dict, List, cast
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score, classification_report, f1_score
from catboost import CatBoostClassifier

def run_investigation_and_balanced_cv():
    print("=" * 90, flush=True)
    print("        PROJECT SENTINEL - ISOLATED FOLD 1 ANALYSIS & BALANCED 5-FOLD CV", flush=True)
    print("=" * 90, flush=True)

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

    print(f"\n[1/5] Loading dataset from '{dataset_path}'...", flush=True)
    df = pd.read_csv(dataset_path)

    drop_cols = [
        'project_id', 'project_name', 'source_collection', 'week_ending',
        'threshold_reliable', 'team_size_reliable'
    ]
    target_col = 'risk_level'
    feature_cols = [c for c in df.columns if c not in drop_cols and c != target_col]

    X = df[feature_cols]
    y = df[target_col]
    groups = df['project_id']

    # 2. Inspect Isolated Fold 1 Project in Standard GroupKFold
    print("\n[2/5] Inspecting Default GroupKFold Fold 1 Isolated Project...", flush=True)
    gkf = GroupKFold(n_splits=5)
    std_splits = list(gkf.split(X, y, groups=groups))
    fold1_tr, fold1_val = std_splits[0]
    fold1_projects = groups.iloc[fold1_val].unique()

    print(f"      Default GroupKFold Fold 1 Validation Project(s): {list(fold1_projects)}", flush=True)
    for pid in fold1_projects:
        p_df = df[df['project_id'] == pid]
        print(f"\n      --- Isolated Project ID Details: '{pid}' ---", flush=True)
        print(f"      Total Row Count: {len(p_df)} ({len(p_df)/len(df)*100:.2f}% of full dataset)", flush=True)
        print(f"      Risk Level Counts:\n{p_df['risk_level'].value_counts().to_string()}", flush=True)
        print(f"      Risk Level Proportions:\n{p_df['risk_level'].value_counts(normalize=True).to_string()}", flush=True)

    # 3. Construct Greedy Min-Heap Size-Balanced Group Assignment
    print("\n[3/5] Constructing Greedy Min-Heap Size-Balanced Group Assignment...", flush=True)
    proj_counts = df.groupby('project_id').size().reset_index(name='row_count')
    proj_counts = proj_counts.sort_values(by='row_count', ascending=False).reset_index(drop=True)

    # Greedy bin-packing: assign each project to the fold with current minimum total rows
    fold_sums = [0] * 5
    fold_assignments = {}
    for _, row in proj_counts.iterrows():
        pid = row['project_id']
        rc = row['row_count']
        min_fold = int(np.argmin(fold_sums))
        fold_assignments[pid] = min_fold
        fold_sums[min_fold] += rc

    df['balanced_fold'] = df['project_id'].map(fold_assignments)

    print("\n      --- Greedy Min-Heap Size-Balanced Fold Summary ---", flush=True)
    for f_idx in range(5):
        f_df = df[df['balanced_fold'] == f_idx]
        f_projs = f_df['project_id'].nunique()
        f_rows = len(f_df)
        f_risk_dist = f_df['risk_level'].value_counts(normalize=True).to_dict()
        print(f"      Fold {f_idx + 1}: {f_rows:6d} rows ({f_rows/len(df)*100:5.2f}%) across {f_projs:3d} projects | High: {f_risk_dist.get('High', 0):.3f}, Med: {f_risk_dist.get('Medium', 0):.3f}, Low: {f_risk_dist.get('Low', 0):.3f}", flush=True)

    # CatBoost Class Weights Setup
    temp_cb = CatBoostClassifier(iterations=10, verbose=False)
    temp_cb.fit(X, y)
    cb_classes = list(cast(Any, temp_cb).classes_)
    weights_dict = {'High': 1.5, 'Medium': 1.0, 'Low': 1.0}
    weights_list = [weights_dict[c] for c in cb_classes]

    # 4. Run Balanced 5-Fold Cross-Validation
    print("\n[4/5] Running 5-Fold Cross-Validation on Size-Balanced Folds...", flush=True)
    balanced_results = []
    start_cv = time.time()

    for fold_num in range(1, 6):
        f_idx = fold_num - 1
        val_mask = df['balanced_fold'] == f_idx
        tr_mask = ~val_mask

        X_tr, y_tr = X[tr_mask].reset_index(drop=True), y[tr_mask].reset_index(drop=True)
        X_val, y_val = X[val_mask].reset_index(drop=True), y[val_mask].reset_index(drop=True)
        g_tr, g_val = groups[tr_mask], groups[val_mask]

        print(f"\n      --- Fold {fold_num}/5 ---", flush=True)
        print(f"      Train: {len(X_tr)} rows ({g_tr.nunique()} projects) | Val: {len(X_val)} rows ({g_val.nunique()} projects)", flush=True)

        cb_model = CatBoostClassifier(
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
        cb_model.fit(X_tr, y_tr)
        t_elapsed = time.time() - t0

        preds = cb_model.predict(X_val)
        if hasattr(preds, 'ravel'):
            preds = preds.ravel()

        acc = accuracy_score(y_val, preds)
        rep = cast(Dict[str, Any], classification_report(y_val, preds, output_dict=True))
        macro_f1 = float(rep['macro avg']['f1-score'])
        macro_prec = float(rep['macro avg']['precision'])
        macro_rec = float(rep['macro avg']['recall'])
        high_rec = float(rep['High']['recall'])
        high_prec = float(rep['High']['precision'])
        high_f1 = float(rep['High']['f1-score'])

        print(f"      Fold {fold_num} completed in {t_elapsed:.2f}s | Acc: {acc:.4f} | Macro F1: {macro_f1:.4f} | High Recall: {high_rec:.4f}", flush=True)

        balanced_results.append({
            'Fold': f"Fold {fold_num}",
            'Train Projects': g_tr.nunique(),
            'Val Projects': g_val.nunique(),
            'Val Rows': len(X_val),
            'Accuracy': acc,
            'Macro Precision': macro_prec,
            'Macro Recall': macro_rec,
            'Macro F1': macro_f1,
            'High Precision': high_prec,
            'High Recall': high_rec,
            'High F1': high_f1
        })

    cv_duration = time.time() - start_cv
    print(f"\n[5/5] Size-Balanced Cross-Validation completed in {cv_duration/60:.2f} minutes.", flush=True)

    # 5. Output Final Results & Statistics
    res_df = pd.DataFrame(balanced_results)

    accs = [r['Accuracy'] for r in balanced_results]
    macro_f1s = [r['Macro F1'] for r in balanced_results]
    high_recs = [r['High Recall'] for r in balanced_results]

    mean_acc, std_acc = np.mean(accs), np.std(accs)
    mean_macro_f1, std_macro_f1 = np.mean(macro_f1s), np.std(macro_f1s)
    mean_high_rec, std_high_rec = np.mean(high_recs), np.std(high_recs)

    print("\n=========================================================================================================")
    print("                    SIZE-BALANCED 5-FOLD PROJECT-GROUPED CROSS-VALIDATION RESULTS")
    print("=========================================================================================================")
    print(res_df.to_string(index=False))
    print("=" * 105)
    print(f"  Balanced 5-Fold CV Mean ± Std Accuracy       : {mean_acc:.4f} ± {std_acc:.4f}")
    print(f"  Balanced 5-Fold CV Mean ± Std Macro F1       : {mean_macro_f1:.4f} ± {std_macro_f1:.4f}")
    print(f"  Balanced 5-Fold CV Mean ± Std High-Risk Recall: {mean_high_rec:.4f} ± {std_high_rec:.4f}")
    print("=========================================================================================================\n", flush=True)

if __name__ == '__main__':
    run_investigation_and_balanced_cv()
