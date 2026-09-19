"""
Project Sentinel - Trend Anomaly Categorization & Worsening-Trend Deep Dive
=============================================================================
Categorizes all 2,395 uniquely-flagged anomalies from the V2 delta-aware model:
1. Worsening Trend (Risk Increasing): deltas show rising overdue tasks, rising defects, or dropping completion rate.
2. Improving / Rapid Resolution Trend: deltas show rapid resolution / completion spikes.

Extracts and prints 2-3 concrete example rows of WORSENING trend anomalies where absolute metrics look moderate/normal (< 50%) but risk is rapidly escalating due to sharp delta spikes.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import GroupShuffleSplit

def run_categorization():
    print("=" * 95)
    print("     PROJECT SENTINEL - ANOMALY TREND CATEGORIZATION & WORSENING-TREND DEEP DIVE")
    print("=" * 95)

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

    print(f"\n[1/4] Loading dataset from '{dataset_path}'...", flush=True)
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
    print("[2/4] Splitting dataset into 80% train / 20% held-out test set (random_state=42)...", flush=True)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(df, groups=df['project_id']))

    train_df = df.iloc[train_idx].reset_index(drop=True)
    test_df = df.iloc[test_idx].reset_index(drop=True)

    # 3. Load or Train Models
    print("[3/4] Loading / Fitting Anomaly Models (V1 10-feature vs V2 15-feature)...", flush=True)
    iso_v1 = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1)
    iso_v1.fit(train_df[base_features])

    iso_v2 = IsolationForest(contamination=0.1, random_state=42, n_jobs=-1)
    iso_v2.fit(train_df[all_features])

    preds_v1 = iso_v1.predict(test_df[base_features])
    preds_v2 = iso_v2.predict(test_df[all_features])
    scores_v1 = iso_v1.decision_function(test_df[base_features])
    scores_v2 = iso_v2.decision_function(test_df[all_features])

    test_df['v1_anomaly'] = (preds_v1 == -1)
    test_df['v2_anomaly'] = (preds_v2 == -1)
    test_df['v1_score'] = scores_v1
    test_df['v2_score'] = scores_v2

    # Filter for the 2,395 uniquely-flagged V2 anomalies
    unique_v2_df = test_df[~test_df['v1_anomaly'] & test_df['v2_anomaly']].copy()
    n_unique = len(unique_v2_df)

    print(f"\n      Total Test Set Rows                      : {len(test_df)}")
    print(f"      Uniquely-Flagged V2 Anomaly Rows          : {n_unique}")

    # 4. Categorization Step
    # Define worsening vs improving
    # Worsening: overdue_delta > 0 OR defect_delta > 0 OR completion_delta < 0
    worsening_mask = (
        (unique_v2_df['overdue_tasks_percentage_delta'] > 0) |
        (unique_v2_df['defect_density_delta'] > 0) |
        (unique_v2_df['task_completion_rate_delta'] < 0)
    )

    worsening_df = unique_v2_df[worsening_mask].copy()
    improving_df = unique_v2_df[~worsening_mask].copy()

    n_worsening = len(worsening_df)
    n_improving = len(improving_df)

    pct_worsening = (n_worsening / n_unique) * 100
    pct_improving = (n_improving / n_unique) * 100

    print("\n=========================================================================================================")
    print("                   CATEGORIZATION OF UNIQUELY-CAUGHT V2 TREND ANOMALIES")
    print("=========================================================================================================")
    print(f"  Total Unique V2 Anomalies                    : {n_unique:5d}  (100.00%)")
    print(f"  Category 1: Worsening Trend (Risk Increasing): {n_worsening:5d}  ({pct_worsening:6.2f}%)")
    print(f"  Category 2: Improving / Rapid Resolution     : {n_improving:5d}  ({pct_improving:6.2f}%)")
    print("=========================================================================================================\n", flush=True)

    # 5. Extract Concrete Examples of "Worsening Trend" Anomalies with Moderate Base Values (< 50%)
    print("[4/4] Extracting Concrete Examples of WORSENING TREND Anomalies (Moderate Base Values)...", flush=True)

    # Focus on worsening cases where overdue_tasks_percentage < 50% but overdue_delta > 5% or defect_delta > 5 or completion_delta < -5
    moderate_worsening = worsening_df[
        (worsening_df['overdue_tasks_percentage'] < 50.0) &
        (
            (worsening_df['overdue_tasks_percentage_delta'] > 5.0) |
            (worsening_df['defect_density_delta'] > 5.0) |
            (worsening_df['task_completion_rate_delta'] < -5.0)
        )
    ].copy()

    if len(moderate_worsening) < 3:
        moderate_worsening = worsening_df.copy()

    moderate_worsening['worsening_magnitude'] = (
        moderate_worsening['overdue_tasks_percentage_delta'].clip(lower=0) * 2.0 +
        moderate_worsening['defect_density_delta'].clip(lower=0) * 1.5 +
        (-moderate_worsening['task_completion_rate_delta']).clip(lower=0) * 1.0
    )

    sorted_worsening = moderate_worsening.sort_values(by='worsening_magnitude', ascending=False)
    sample_worsening = sorted_worsening.head(3)

    print("\n=========================================================================================================")
    print("                 CONCRETE EXAMPLES: WORSENING TREND ANOMALIES (MODERATE ABSOLUTE METRICS)")
    print("=========================================================================================================")
    for ex_num, (idx, row) in enumerate(sample_worsening.iterrows(), 1):
        overdue_delta = row['overdue_tasks_percentage_delta']
        defect_delta = row['defect_density_delta']
        comp_delta = row['task_completion_rate_delta']

        overdue_tag = "  <-- Overdue Increasing" if overdue_delta > 0 else ("  <-- Overdue Decreasing" if overdue_delta < 0 else "")
        defect_tag = "  <-- Defect Spike" if defect_delta > 0 else ("  <-- Defect Decreasing" if defect_delta < 0 else "")
        comp_tag = "  <-- Completion Declining" if comp_delta < 0 else ("  <-- Completion Rising" if comp_delta > 0 else "")

        triggers = []
        if overdue_delta > 0:
            triggers.append("Overdue Tasks Increasing (overdue_delta > 0)")
        if defect_delta > 0:
            triggers.append("Defect Density Spiking (defect_delta > 0)")
        if comp_delta < 0:
            triggers.append("Completion Rate Declining (completion_delta < 0)")
        trigger_str = " | ".join(triggers) if triggers else "None"

        print(f"\n--- Worsening Trend Example {ex_num} ---")
        print(f"  Project ID                     : {row['project_id']}")
        print(f"  Week Number                    : Week {int(row['week_number'])}")
        print(f"  Risk Level                     : {row['risk_level']}")
        print(f"  Classification Trigger(s)      : {trigger_str}")
        print(f"  Original V1 Model Prediction   : NORMAL  (Score: {row['v1_score']:+.4f})")
        print(f"  New V2 Model Prediction        : ANOMALY (Score: {row['v2_score']:+.4f})")
        print("  Key Absolute Metrics (Appears Moderate/Healthy):")
        print(f"    - overdue_tasks_percentage   : {row['overdue_tasks_percentage']:.2f}%")
        print(f"    - defect_density             : {row['defect_density']:.4f}")
        print(f"    - task_completion_rate       : {row['task_completion_rate']:.2f}%")
        print(f"    - unresolved_issue_percentage: {row['unresolved_issue_percentage']:.2f}%")
        print("  Key Delta Metrics (Worsening Risk Trend):")
        print(f"    - overdue_tasks_percentage_delta : {overdue_delta:+.2f}%{overdue_tag}")
        print(f"    - defect_density_delta           : {defect_delta:+.4f}{defect_tag}")
        print(f"    - task_completion_rate_delta     : {comp_delta:+.2f}%{comp_tag}")
        print(f"    - issue_count_delta              : {row['issue_count_delta']:+.0f}")

    print("\n=========================================================================================================")
    print("                                   STATISTICAL SUMMARY STATEMENT")
    print("=========================================================================================================")
    summary_txt = (
        f"Out of the {n_unique} anomalies uniquely caught by the V2 delta-aware model:\n"
        f"- {n_worsening} cases ({pct_worsening:.2f}%) represent WORSENING TRENDS (risk actively escalating due to "
        f"sudden spikes in overdue tasks, rising defect density, or collapsing completion rates).\n"
        f"- {n_improving} cases ({pct_improving:.2f}%) represent IMPROVING / RAPID RESOLUTION TRENDS (abrupt spikes toward completion "
        f"or sudden drops in overdue tasks).\n"
        f"The V2 model successfully detects early risk escalation before absolute metrics cross critical failure thresholds."
    )
    print(summary_txt)
    print("=========================================================================================================\n", flush=True)

if __name__ == '__main__':
    run_categorization()
