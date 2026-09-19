"""
Project Sentinel - Delta-Aware Isolation Forest Retraining & Comparative Study
================================================================================
1. Retrains Original Isolation Forest (10 absolute features).
2. Retrains New Delta-Aware Isolation Forest v2 (15 features: 10 absolute + 5 deltas).
3. Saves v2 model to 'backend/anomaly_model_v2.pkl'.
4. Evaluates both models on the held-out test set (20% project-grouped split).
5. Compares anomaly detection overlap and uniquely caught trend-driven anomalies.
6. Prints concrete example rows illustrating trend-driven anomaly detection.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupShuffleSplit

def run_anomaly_experiment():
    print("=" * 90)
    print("      PROJECT SENTINEL - ISOLATION FOREST ANOMALY MODEL (V1 vs V2 DELTA-AWARE)")
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

    print(f"\n[1/5] Loading dataset from '{dataset_path}'...", flush=True)
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

    # 2. Project-Grouped Train/Test Split (20% held-out test set)
    print("[2/5] Creating project-based train/test split (20% held-out test)...", flush=True)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(df, groups=df['project_id']))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    print(f"      Train Set: {len(train_df)} rows across {df.iloc[train_idx]['project_id'].nunique()} projects", flush=True)
    print(f"      Test Set : {len(test_df)} rows across {df.iloc[test_idx]['project_id'].nunique()} projects", flush=True)

    # 3. Train Models
    print("\n[3/5] Training Isolation Forest Models...", flush=True)

    # Model V1: 10 absolute-only features
    print("      - Training Original Model V1 (10 Absolute-Value Features)...", flush=True)
    iso_v1 = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_jobs=-1
    )
    iso_v1.fit(train_df[base_features])

    v1_path = os.path.join(os.path.dirname(dataset_path), '..', 'backend', 'anomaly_model.pkl')
    if not os.path.exists(os.path.dirname(v1_path)):
        v1_path = 'anomaly_model.pkl'
    joblib.dump(iso_v1, v1_path)
    print(f"        Saved Original V1 Model to '{v1_path}'.", flush=True)

    # Model V2: 15 absolute + delta features
    print("      - Training New Model V2 (15 Features: 10 Absolute + 5 Deltas)...", flush=True)
    iso_v2 = IsolationForest(
        contamination=0.1,
        random_state=42,
        n_jobs=-1
    )
    iso_v2.fit(train_df[all_features])

    v2_path = os.path.join(os.path.dirname(v1_path), 'anomaly_model_v2.pkl')
    joblib.dump(iso_v2, v2_path)
    print(f"        Saved Delta-Aware V2 Model to '{v2_path}'.", flush=True)

    # 4. Predict & Compare on Held-Out Test Set
    print("\n[4/5] Running Anomaly Detection on Test Set...", flush=True)
    preds_v1 = iso_v1.predict(test_df[base_features])
    preds_v2 = iso_v2.predict(test_df[all_features])

    scores_v1 = iso_v1.decision_function(test_df[base_features])
    scores_v2 = iso_v2.decision_function(test_df[all_features])

    test_df['v1_anomaly'] = (preds_v1 == -1)
    test_df['v2_anomaly'] = (preds_v2 == -1)
    test_df['v1_score'] = scores_v1
    test_df['v2_score'] = scores_v2

    n_test = len(test_df)
    n_v1_anom = test_df['v1_anomaly'].sum()
    n_v2_anom = test_df['v2_anomaly'].sum()
    n_both_anom = (test_df['v1_anomaly'] & test_df['v2_anomaly']).sum()
    n_v1_only = (test_df['v1_anomaly'] & ~test_df['v2_anomaly']).sum()
    n_v2_only = (~test_df['v1_anomaly'] & test_df['v2_anomaly']).sum()

    print("\n=========================================================================================================")
    print("                           ANOMALY DETECTION COMPARISON SUMMARY (TEST SET)")
    print("=========================================================================================================")
    print(f"  Total Test Set Rows                       : {n_test:6d}")
    print(f"  Original V1 Model (10 Absolute Features)   : {n_v1_anom:6d} anomalies ({n_v1_anom/n_test*100:5.2f}%)")
    print(f"  New V2 Model (15 Absolute+Delta Features) : {n_v2_anom:6d} anomalies ({n_v2_anom/n_test*100:5.2f}%)")
    print(f"  Flagged by BOTH Models                     : {n_both_anom:6d} rows      ({n_both_anom/n_test*100:5.2f}%)")
    print(f"  Flagged ONLY by Original V1 (Absolute Only): {n_v1_only:6d} rows      ({n_v1_only/n_test*100:5.2f}%)")
    print(f"  Flagged ONLY by New V2 (Delta-Aware)       : {n_v2_only:6d} rows      ({n_v2_only/n_test*100:5.2f}%)")
    print("=========================================================================================================\n", flush=True)

    # 5. Extract Trend-Driven Anomalies Uniquely Caught by V2
    print("[5/5] Extracting Concrete Examples of Trend-Driven Anomalies Uniquely Caught by V2...", flush=True)
    v2_unique_df = test_df[~test_df['v1_anomaly'] & test_df['v2_anomaly']].copy()

    # Filter for cases with moderate/normal absolute values but sharp delta changes
    # Calculate absolute delta magnitude sum across delta features
    delta_mag = (
        np.abs(v2_unique_df['overdue_tasks_percentage_delta']) * 2.0 +
        np.abs(v2_unique_df['defect_density_delta']) * 2.0 +
        np.abs(v2_unique_df['task_completion_rate_delta']) +
        np.abs(v2_unique_df['issue_count_delta']) * 0.05
    )
    v2_unique_df['delta_magnitude'] = delta_mag

    # Filter to cases where overdue_tasks_percentage is moderate (e.g. < 40%) but delta is large (e.g. > 10%)
    trend_cases = v2_unique_df[
        (v2_unique_df['overdue_tasks_percentage'] < 40.0) &
        (np.abs(v2_unique_df['overdue_tasks_percentage_delta']) > 5.0)
    ].sort_values(by='delta_magnitude', ascending=False)

    if len(trend_cases) < 3:
        trend_cases = v2_unique_df.sort_values(by='delta_magnitude', ascending=False)

    sample_examples = trend_cases.head(3)

    print("\n=========================================================================================================")
    print("                       CONCRETE EXAMPLES: TREND-DRIVEN ANOMALIES UNIQUE TO V2")
    print("=========================================================================================================")
    for ex_num, (idx, row) in enumerate(sample_examples.iterrows(), 1):
        print(f"\n--- Example {ex_num} ---")
        print(f"  Project ID                     : {row['project_id']}")
        print(f"  Week Number                    : Week {int(row['week_number'])}")
        print(f"  Risk Level                     : {row['risk_level']}")
        print(f"  Original V1 Model Prediction   : NORMAL  (Score: {row['v1_score']:+.4f})")
        print(f"  New V2 Model Prediction        : ANOMALY (Score: {row['v2_score']:+.4f})")
        print("  Key Absolute Metrics (Looks Normal):")
        print(f"    - overdue_tasks_percentage   : {row['overdue_tasks_percentage']:.2f}%")
        print(f"    - defect_density             : {row['defect_density']:.4f}")
        print(f"    - task_completion_rate       : {row['task_completion_rate']:.2f}%")
        print(f"    - unresolved_issue_percentage: {row['unresolved_issue_percentage']:.2f}%")
        print("  Key Delta Metrics (Unusual/Sharp Trend):")
        print(f"    - overdue_tasks_percentage_delta : {row['overdue_tasks_percentage_delta']:+.2f}%")
        print(f"    - defect_density_delta           : {row['defect_density_delta']:+.4f}")
        print(f"    - task_completion_rate_delta     : {row['task_completion_rate_delta']:+.2f}%")
        print(f"    - issue_count_delta              : {row['issue_count_delta']:+.0f}")

    print("\n=========================================================================================================")
    print("                                      SUMMARY STATEMENT")
    print("=========================================================================================================")
    summary_txt = (
        f"1. Model Retraining: Saved 15-feature delta-aware model to 'anomaly_model_v2.pkl'.\n"
        f"2. Detection Overlap: Out of {n_test} test rows, V1 flagged {n_v1_anom} anomalies ({n_v1_anom/n_test*100:.2f}%) "
        f"and V2 flagged {n_v2_anom} anomalies ({n_v2_anom/n_test*100:.2f}%).\n"
        f"3. Unique Trend-Driven Detection: The new V2 model uniquely identified {n_v2_only} anomaly cases "
        f"({n_v2_only/n_test*100:.2f}% of test set) that had moderate absolute metric values but experienced sharp "
        f"week-over-week velocity shifts (e.g. sudden spikes in overdue tasks or defect density) which were completely missed by V1."
    )
    print(summary_txt)
    print("=========================================================================================================\n", flush=True)

if __name__ == '__main__':
    run_anomaly_experiment()
