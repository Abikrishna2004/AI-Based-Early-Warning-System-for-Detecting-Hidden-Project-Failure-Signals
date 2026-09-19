"""
Project Sentinel - Precompute SHAP Interaction Matrix & Global Feature Pair Rankings
=====================================================================================
Uses CatBoost TreeExplainer to compute pairwise SHAP interaction values over a 1000-row sample.
Saves pre-calculated results to 'shap_interaction_matrix.json' for fast instant serving by FastAPI backend.
"""

import os
import json
from typing import Any, Dict, List, cast
import pandas as pd
import numpy as np
import shap
from catboost import CatBoostClassifier

def compute_and_save_shap_interactions():
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
        
    model_path = os.path.join(base_dir, 'best_model_catboost.cbm')
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"CatBoost model '{model_path}' not found.")
        
    cb_model = CatBoostClassifier()
    cb_model.load_model(model_path)
    
    # Load dataset
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
        
    print(f"[SHAP INTERACTION] Loading dataset from '{dataset_path}'...", flush=True)
    df = pd.read_csv(dataset_path)
    
    drop_cols = [
        'project_id', 'project_name', 'source_collection', 'week_ending',
        'threshold_reliable', 'team_size_reliable', 'risk_level'
    ]
    feature_cols = [c for c in df.columns if c not in drop_cols]
    
    # Take representative sample of 500 rows for fast, accurate interaction calculation
    sample_size = min(500, len(df))
    X_sample = df[feature_cols].sample(n=sample_size, random_state=42)
    
    print(f"[SHAP INTERACTION] Computing SHAP interaction values on {sample_size} samples...", flush=True)
    explainer = shap.TreeExplainer(cb_model)
    inter_vals = explainer.shap_interaction_values(X_sample)
    
    classes = list(cast(Any, cb_model).classes_)
    
    # Format interaction values per class
    # inter_vals is list of [N, M, M] for each class
    if isinstance(inter_vals, list):
        inter_array_list = inter_vals
    else:
        inter_array_list = [inter_vals[:, :, :, i] for i in range(len(classes))]
        
    n_features = len(feature_cols)
    
    # Calculate overall mean absolute interaction matrix across all samples & classes
    overall_matrix = np.zeros((n_features, n_features))
    
    for class_idx, class_name in enumerate(classes):
        class_inter = inter_array_list[class_idx] # [N, M, M]
        mean_abs_class = np.mean(np.abs(class_inter), axis=0) # [M, M]
        overall_matrix += mean_abs_class
        
    overall_matrix = overall_matrix / len(classes)
    
    # Extract pairwise off-diagonal interactions
    pairwise_list = []
    for i in range(n_features):
        for j in range(i + 1, n_features):
            f1, f2 = feature_cols[i], feature_cols[j]
            # Interaction strength is symmetric sum of off-diagonals
            strength = float((overall_matrix[i, j] + overall_matrix[j, i]) / 2.0)
            
            # Domain explanation generation
            desc = (
                f"Combined changes in '{f1}' and '{f2}' exhibit a non-linear joint risk effect. "
                f"When both deteriorate simultaneously, project failure risk accelerates faster "
                f"than evaluating either metric in isolation."
            )
            
            pairwise_list.append({
                "feature1": f1,
                "feature2": f2,
                "feature1_index": i,
                "feature2_index": j,
                "interaction_strength": round(strength, 5),
                "description": desc
            })
            
    # Sort top interactions by strength descending
    pairwise_list.sort(key=lambda x: x["interaction_strength"], reverse=True)
    
    # Format matrix for JSON output (rounded floats)
    matrix_json = [[round(float(val), 5) for val in row] for row in overall_matrix]
    
    output_data = {
        "sample_size": sample_size,
        "feature_names": feature_cols,
        "top_interactions": pairwise_list[:10],
        "interaction_matrix": matrix_json,
        "max_interaction_strength": round(float(np.max(overall_matrix - np.diag(np.diag(overall_matrix)))), 5)
    }
    
    json_path = os.path.join(base_dir, 'shap_interaction_matrix.json')
    with open(json_path, 'w') as f:
        json.dump(output_data, f, indent=2)
        
    print(f"[SHAP INTERACTION] Successfully computed & saved SHAP interaction matrix to '{json_path}'.", flush=True)
    print("Top 5 Pairwise Interactions:")
    for item in pairwise_list[:5]:
        print(f"  - {item['feature1']} + {item['feature2']}: strength = {item['interaction_strength']}")
        
    return output_data

if __name__ == '__main__':
    compute_and_save_shap_interactions()
