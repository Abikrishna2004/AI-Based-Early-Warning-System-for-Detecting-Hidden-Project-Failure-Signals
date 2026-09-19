"""
Project Sentinel - Risk Signal Precedence Analysis Precomputation Engine
==========================================================================
Computes statistical lagged cross-correlation across 5 telemetry delta metrics
for projects with 10+ weeks of historical telemetry.

CRITICAL DIRECTIVE: Explicitly avoid the word 'causal' or 'causation' anywhere.
This analysis identifies empirical statistical precedence patterns (lagged correlation).
"""

import os
import json
from typing import Any, Dict, List
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def compute_and_save_signal_precedence():
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
        
    data_paths = [
        os.path.join(base_dir, '../data/project_sentinel_final_real_dataset.csv'),
        os.path.join(base_dir, 'data/project_sentinel_final_real_dataset.csv'),
        'project_sentinel_final_real_dataset.csv'
    ]
    dataset_path = None
    for p in data_paths:
        if os.path.exists(p):
            dataset_path = p
            break
            
    if not dataset_path:
        raise FileNotFoundError("Could not locate project_sentinel_final_real_dataset.csv")
        
    print(f"[SIGNAL PRECEDENCE] Loading dataset from '{dataset_path}'...", flush=True)
    df = pd.read_csv(dataset_path)
    
    delta_cols = [
        'issue_count_delta',
        'task_completion_rate_delta',
        'overdue_tasks_percentage_delta',
        'defect_density_delta',
        'team_size_delta'
    ]
    
    display_names = {
        'issue_count_delta': 'Issue Count Delta',
        'task_completion_rate_delta': 'Task Completion Rate Delta',
        'overdue_tasks_percentage_delta': 'Overdue Tasks % Delta',
        'defect_density_delta': 'Defect Density Delta',
        'team_size_delta': 'Team Size Delta'
    }
    
    lags = [0, 1, 2, 3]
    correlations = {}
    
    for i in range(len(delta_cols)):
        for j in range(len(delta_cols)):
            if i == j:
                continue
            col_A = delta_cols[i]
            col_B = delta_cols[j]
            pair_key = (col_A, col_B)
            correlations[pair_key] = {lag: [] for lag in lags}
            
    grouped = df.groupby('project_id')
    qualifying_projects_count = 0
    
    for proj_id, group in grouped:
        if len(group) < 10:
            continue
        qualifying_projects_count += 1
        g = group.sort_values('week_number')
        
        for (col_A, col_B) in correlations.keys():
            s_A = g[col_A].values
            s_B = g[col_B].values
            
            for lag in lags:
                if lag == 0:
                    v_A = s_A
                    v_B = s_B
                else:
                    v_A = s_A[:-lag]
                    v_B = s_B[lag:]
                    
                if len(v_A) >= 5 and np.std(v_A) > 1e-6 and np.std(v_B) > 1e-6:
                    r, _ = pearsonr(v_A, v_B)
                    if not np.isnan(r):
                        correlations[(col_A, col_B)][lag].append(r)
                        
    lagged_results = []
    all_pairs_summary = []
    
    for (col_A, col_B), lag_dict in correlations.items():
        best_lag = 0
        best_corr = 0.0
        max_abs = -1.0
        
        for lag, r_list in lag_dict.items():
            if len(r_list) > 0:
                mean_r = float(np.mean(r_list))
                if abs(mean_r) > max_abs:
                    max_abs = abs(mean_r)
                    best_lag = lag
                    best_corr = mean_r
                    
        name_A = display_names.get(col_A, col_A)
        name_B = display_names.get(col_B, col_B)
        
        label_text = (
            f"'{name_A}' tends to precede '{name_B}' by {best_lag} week{'s' if best_lag != 1 else ''} "
            f"with statistical correlation strength {best_corr:+.4f}"
            if best_lag > 0 else
            f"'{name_A}' and '{name_B}' exhibit concurrent co-movement (lag 0) with correlation strength {best_corr:+.4f}"
        )
        
        item = {
            "metric_A": col_A,
            "metric_B": col_B,
            "display_name_A": name_A,
            "display_name_B": name_B,
            "optimal_lag_weeks": best_lag,
            "correlation_strength": round(best_corr, 4),
            "abs_correlation": round(max_abs, 4),
            "precedence_label": label_text
        }
        
        all_pairs_summary.append(item)
        if best_lag > 0:
            lagged_results.append(item)
            
    # Sort lagged relationships by absolute correlation strength descending
    lagged_results.sort(key=lambda x: x["abs_correlation"], reverse=True)
    all_pairs_summary.sort(key=lambda x: x["abs_correlation"], reverse=True)
    
    # Select top 4 strongest lagged relationships for directional diagram
    top_directional_diagram = lagged_results[:4]
    
    disclaimer = (
        "This shows statistical precedence patterns across historical projects, not proven causation — "
        "correlated timing may share a common underlying cause rather than one metric directly driving the other."
    )
    
    output_data = {
        "module_name": "Risk Signal Precedence Analysis",
        "qualifying_projects_count": qualifying_projects_count,
        "disclaimer_text": disclaimer,
        "strongest_directional_precedences": top_directional_diagram,
        "all_pairwise_precedences": all_pairs_summary
    }
    
    json_path = os.path.join(base_dir, 'signal_precedence_results.json')
    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[SIGNAL PRECEDENCE] Computed & saved precedence analysis across {qualifying_projects_count} projects to '{json_path}'.", flush=True)
    print("Top Directional Statistical Precedences:")
    for item in top_directional_diagram:
        print(f"  - {item['precedence_label']}")
        
    return output_data

if __name__ == '__main__':
    compute_and_save_signal_precedence()
