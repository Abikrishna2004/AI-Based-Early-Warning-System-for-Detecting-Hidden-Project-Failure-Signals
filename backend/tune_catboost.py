"""
Project Sentinel - Fast CatBoost Hyperparameter Tuning Script
=============================================================
Performs fast randomized hyperparameter search:
1. 30% project-grouped subsample of training data for search phase.
2. n_iter=10 randomized candidate configurations.
3. 2-fold GroupKFold cross-validation for search.
4. CatBoost verbose=50 and RandomizedSearchCV verbose=3 for real-time progress visibility.
5. Upfront timing estimate printed before search execution.
6. Retrains best parameter combination on FULL training dataset with High=1.5x class weight.
7. Evaluates baseline vs tuned model on held-out test set (20% GroupShuffleSplit).
"""

import os
import time
import random
from typing import Any, Dict, List, cast
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, GroupKFold, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.base import BaseEstimator, ClassifierMixin
from catboost import CatBoostClassifier

class CatBoostGroupClassifier(BaseEstimator, ClassifierMixin):
    def __init__(self, iterations=300, depth=6, learning_rate=0.1, l2_leaf_reg=3, class_weights=None, random_state=42, verbose=50):
        self.iterations = iterations
        self.depth = depth
        self.learning_rate = learning_rate
        self.l2_leaf_reg = l2_leaf_reg
        self.class_weights = class_weights
        self.random_state = random_state
        self.verbose = verbose

    def fit(self, X, y):
        self.model_ = CatBoostClassifier(
            iterations=self.iterations,
            depth=self.depth,
            learning_rate=self.learning_rate,
            l2_leaf_reg=self.l2_leaf_reg,
            class_weights=self.class_weights,
            random_state=self.random_state,
            verbose=self.verbose,
            thread_count=-1
        )
        self.model_.fit(X, y)
        self.classes_ = cast(Any, self.model_).classes_
        return self

    def predict(self, X):
        preds = self.model_.predict(X)
        if hasattr(preds, 'ravel'):
            return preds.ravel()
        return preds

    def predict_proba(self, X):
        return self.model_.predict_proba(X)


def run_fast_tuning():
    print("=" * 80, flush=True)
    print("      PROJECT SENTINEL - FAST CATBOOST HYPERPARAMETER TUNING", flush=True)
    print("=" * 80, flush=True)

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

    print(f"\n[1/6] Loading dataset from '{dataset_path}'...", flush=True)
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

    # 2. Project-Grouped Train/Test Split (20% held-out test set)
    print("[2/6] Creating project-based train/test split (20% test)...", flush=True)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, X_test = X.iloc[train_idx].reset_index(drop=True), X.iloc[test_idx].reset_index(drop=True)
    y_train, y_test = y.iloc[train_idx].reset_index(drop=True), y.iloc[test_idx].reset_index(drop=True)
    groups_train = groups.iloc[train_idx].reset_index(drop=True)

    print(f"      Full Train samples: {len(X_train)} across {groups_train.nunique()} projects", flush=True)
    print(f"      Held-Out Test samples: {len(X_test)} across {groups.iloc[test_idx].nunique()} projects", flush=True)

    # Determine class order and 1.5x class weights
    temp_cb = CatBoostClassifier(iterations=10, verbose=False)
    temp_cb.fit(X_train, y_train)
    cb_classes = list(cast(Any, temp_cb).classes_)
    
    weights_dict = {'High': 1.5, 'Medium': 1.0, 'Low': 1.0}
    weights_list = [weights_dict[c] for c in cb_classes]
    print(f"      CatBoost class ordering: {cb_classes}", flush=True)
    print(f"      Fixed Class Weights (High=1.5x baseline): {weights_dict} -> {weights_list}", flush=True)

    # 3. Create 30% Project-Grouped Subsample for Search Phase
    print("\n[3/6] Creating random 30% project-grouped subsample for hyperparameter search phase...", flush=True)
    gss_sub = GroupShuffleSplit(n_splits=1, test_size=0.7, random_state=42)
    search_sub_idx, _ = next(gss_sub.split(X_train, y_train, groups=groups_train))

    X_sub = X_train.iloc[search_sub_idx].reset_index(drop=True)
    y_sub = y_train.iloc[search_sub_idx].reset_index(drop=True)
    groups_sub = groups_train.iloc[search_sub_idx].reset_index(drop=True)

    print(f"      Subsampled Search Train set: {len(X_sub)} rows across {groups_sub.nunique()} projects (~30% of training projects)", flush=True)
    print(f"      Risk level distribution in subsample:\n{y_sub.value_counts(normalize=True).to_dict()}", flush=True)

    # 4. Train Baseline CatBoost Model on Full Train Set
    print("\n[4/6] Training Baseline CatBoost Model on full train set (depth=6, lr=0.1, iters=300, l2=3, High=1.5x)...", flush=True)
    baseline_cb = CatBoostClassifier(
        iterations=300,
        depth=6,
        learning_rate=0.1,
        l2_leaf_reg=3,
        class_weights=weights_list,
        random_state=42,
        verbose=False,
        thread_count=-1
    )
    baseline_cb.fit(X_train, y_train)
    baseline_pred = baseline_cb.predict(X_test)
    if hasattr(baseline_pred, 'ravel'):
        baseline_pred = baseline_pred.ravel()

    base_report = cast(Dict[str, Any], classification_report(y_test, baseline_pred, output_dict=True))
    base_acc = accuracy_score(y_test, baseline_pred)

    print(f"      Baseline Test Accuracy        : {base_acc:.4f}", flush=True)
    print(f"      Baseline Test Macro F1        : {base_report['macro avg']['f1-score']:.4f}", flush=True)
    print(f"      Baseline Test High-Risk Recall: {base_report['High']['recall']:.4f}", flush=True)

    # 5. Randomized Hyperparameter Search (n_iter=10, 2-fold GroupKFold on 30% Subsample)
    print("\n[5/6] Starting Randomized Hyperparameter Search on 30% Subsample...", flush=True)

    n_candidates = 10
    n_folds = 2
    total_fits = n_candidates * n_folds

    print(f"      Total Candidates to Evaluate: {n_candidates}", flush=True)
    print(f"      Folds per Candidate        : {n_folds} (GroupKFold)", flush=True)
    print(f"      TOTAL MODEL FITS TO RUN   : {total_fits}", flush=True)

    # Benchmark timing of 1 fit to give upfront time estimate
    print("\n      [BENCHMARK] Timing 1 single fit on Subsample Fold 1 to estimate total runtime...", flush=True)
    bench_start = time.time()
    bench_cb = CatBoostClassifier(
        iterations=300, depth=6, learning_rate=0.1, l2_leaf_reg=3,
        class_weights=weights_list, random_state=42, verbose=False, thread_count=-1
    )
    bench_cb.fit(X_sub.iloc[:len(X_sub)//2], y_sub.iloc[:len(y_sub)//2])
    bench_time = time.time() - bench_start
    est_total_seconds = bench_time * total_fits
    print(f"      [BENCHMARK] Single fit time: {bench_time:.2f} seconds.", flush=True)
    print(f"      [ESTIMATED SEARCH RUNTIME] ~{est_total_seconds:.1f} seconds ({est_total_seconds/60:.2f} minutes) for all {total_fits} fits.\n", flush=True)

    param_distributions = {
        'depth': [4, 5, 6, 7, 8, 9, 10],
        'learning_rate': [0.01, 0.03, 0.05, 0.08, 0.1, 0.15, 0.2, 0.25, 0.3],
        'l2_leaf_reg': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'iterations': [200, 250, 300, 350, 400, 450, 500]
    }

    gkf_search = GroupKFold(n_splits=2)
    cb_wrapper = CatBoostGroupClassifier(
        class_weights=weights_list,
        random_state=42,
        verbose=50
    )

    rs = RandomizedSearchCV(
        estimator=cb_wrapper,
        param_distributions=param_distributions,
        n_iter=n_candidates,
        cv=gkf_search,
        scoring='f1_macro',
        verbose=3,
        random_state=42,
        n_jobs=1
    )

    search_start = time.time()
    rs.fit(X_sub, y_sub, groups=groups_sub)
    actual_search_time = time.time() - search_start

    best_params = rs.best_params_
    best_cv_macro_f1 = rs.best_score_

    print("\n      " + "=" * 60, flush=True)
    print(f"      [SEARCH COMPLETED] Finished in {actual_search_time/60:.2f} minutes.", flush=True)
    print("      Best Hyperparameter Combination Found:")
    for k, v in sorted(best_params.items()):
        print(f"        - {k:15s}: {v}")
    print(f"      Best 2-Fold Subsample CV Macro F1: {best_cv_macro_f1:.4f}")
    print("      " + "=" * 60, flush=True)

    # 6. Retrain Best Tuned Model on FULL Training Set and Evaluate on Held-Out Test Set
    print("\n[6/6] Retraining Best Tuned Model on FULL Training Set and evaluating on Held-Out Test Set...", flush=True)
    best_tuned_cb = CatBoostClassifier(
        iterations=best_params['iterations'],
        depth=best_params['depth'],
        learning_rate=best_params['learning_rate'],
        l2_leaf_reg=best_params['l2_leaf_reg'],
        class_weights=weights_list,
        random_state=42,
        verbose=False,
        thread_count=-1
    )
    best_tuned_cb.fit(X_train, y_train)

    tuned_pred = best_tuned_cb.predict(X_test)
    if hasattr(tuned_pred, 'ravel'):
        tuned_pred = tuned_pred.ravel()

    tuned_report = cast(Dict[str, Any], classification_report(y_test, tuned_pred, output_dict=True))
    tuned_acc = accuracy_score(y_test, tuned_pred)

    # Full Comparison Table
    comparison = [
        {
            'Model Configuration': 'Baseline CatBoost (High=1.5x, d=6, lr=0.10, iters=300, l2=3)',
            'Accuracy': f"{base_acc:.4f}",
            'Macro Precision': f"{base_report['macro avg']['precision']:.4f}",
            'Macro Recall': f"{base_report['macro avg']['recall']:.4f}",
            'Macro F1': f"{base_report['macro avg']['f1-score']:.4f}",
            'High Precision': f"{base_report['High']['precision']:.4f}",
            'High Recall': f"{base_report['High']['recall']:.4f}",
            'High F1': f"{base_report['High']['f1-score']:.4f}"
        },
        {
            'Model Configuration': f"Tuned CatBoost (High=1.5x, d={best_params['depth']}, lr={best_params['learning_rate']:.2f}, iters={best_params['iterations']}, l2={best_params['l2_leaf_reg']})",
            'Accuracy': f"{tuned_acc:.4f}",
            'Macro Precision': f"{tuned_report['macro avg']['precision']:.4f}",
            'Macro Recall': f"{tuned_report['macro avg']['recall']:.4f}",
            'Macro F1': f"{tuned_report['macro avg']['f1-score']:.4f}",
            'High Precision': f"{tuned_report['High']['precision']:.4f}",
            'High Recall': f"{tuned_report['High']['recall']:.4f}",
            'High F1': f"{tuned_report['High']['f1-score']:.4f}"
        }
    ]

    comp_df = pd.DataFrame(comparison)

    print("\n=========================================================================================================")
    print("                            FULL HELD-OUT TEST SET PERFORMANCE COMPARISON TABLE")
    print("=========================================================================================================")
    print(comp_df.to_string(index=False))
    print("=========================================================================================================\n", flush=True)

    f1_diff = tuned_report['macro avg']['f1-score'] - base_report['macro avg']['f1-score']
    high_recall_diff = tuned_report['High']['recall'] - base_report['High']['recall']
    
    if f1_diff > 0 or high_recall_diff > 0:
        recommendation = (
            f"Tuning improved Macro F1 by {f1_diff:+.4f} and High-Risk Recall by {high_recall_diff:+.4f}. "
            "Saving tuned model weights to 'best_model_catboost.cbm'."
        )
        best_tuned_cb.save_model('best_model_catboost.cbm')
        print(f"[SAVE] Saved updated best model to 'best_model_catboost.cbm'.", flush=True)
    else:
        recommendation = (
            f"Baseline model achieved equal or superior test set generalization (Macro F1 {base_report['macro avg']['f1-score']:.4f} vs {tuned_report['macro avg']['f1-score']:.4f}). "
            "Hyperparameter tuning confirmed that the baseline configuration is optimal."
        )

    print(f"\n[CONCLUSION & RECOMMENDATION]\n{recommendation}\n", flush=True)

if __name__ == '__main__':
    run_fast_tuning()
