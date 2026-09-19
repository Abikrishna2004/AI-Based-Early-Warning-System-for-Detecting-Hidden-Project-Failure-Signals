import pandas as pd
import numpy as np
from typing import Any, cast
from sklearn.model_selection import GroupShuffleSplit
from catboost import CatBoostClassifier
import shap
import matplotlib.pyplot as plt

import os

# 1. Load trained CatBoost model
model_path = 'best_model_catboost.cbm'
cb_model = CatBoostClassifier()
cb_model.load_model(model_path)

# 2. Load dataset and reproduce exact train/test split
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

X_test = X.iloc[test_idx]
y_test = y.iloc[test_idx]

# 3. Sample 1000 rows from X_test for fast SHAP computation
X_sample = X_test.sample(n=1000, random_state=42)

print("Computing SHAP values using TreeExplainer on 1000 test samples...")
explainer = shap.TreeExplainer(cb_model)
shap_values = explainer.shap_values(X_sample)

classes = list(cast(Any, cb_model).classes_)

# Normalize shap_values output format into a list of 2D arrays per class
if isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
    if shap_values.shape[0] == len(classes):
        shap_values_list = [shap_values[i] for i in range(len(classes))]
    else:
        shap_values_list = [shap_values[:, :, i] for i in range(len(classes))]
    shap_values = shap_values_list

# 4. Top 10 most important features overall across all classes
mean_abs_per_class = [np.abs(sv).mean(axis=0) for sv in shap_values]
overall_feature_importance = np.mean(mean_abs_per_class, axis=0)

feature_importance_df = pd.DataFrame({
    'Feature': feature_cols,
    'Mean |SHAP|': overall_feature_importance
}).sort_values(by='Mean |SHAP|', ascending=False).reset_index(drop=True)

print("\n================ TOP 10 FEATURES OVERALL (Mean |SHAP|) ================")
print(feature_importance_df.head(10).to_string(index=False))
print("========================================================================\n")

# 5. Single example row predicted as High risk
preds = cb_model.predict(X_sample)
if hasattr(preds, 'ravel'):
    preds = preds.ravel()

high_risk_indices = np.where(preds == 'High')[0]

if len(high_risk_indices) > 0:
    sample_idx = high_risk_indices[0]
    high_class_idx = classes.index('High')
    
    sample_shap_high = shap_values[high_class_idx][sample_idx]
    sample_features = X_sample.iloc[sample_idx]
    
    factor_df = pd.DataFrame({
        'Feature': feature_cols,
        'Value': sample_features.values,
        'SHAP_Value': sample_shap_high
    }).sort_values(by='SHAP_Value', ascending=False).reset_index(drop=True)
    
    top5_factors = factor_df.head(5)
    
    print("================ SINGLE HIGH-RISK EXAMPLE EXPLANATION ================")
    print(f"Sample Row Index in X_test: {X_sample.index[sample_idx]}")
    print(f"Model Prediction: High Risk\n")
    print("Actual Feature Values for this Project Sample:")
    for col, val in sample_features.items():
        print(f"  {col}: {val}")
    
    print("\nTop 5 Contributing SHAP Factors pushing towards High Risk:")
    factor_str_list = []
    for _, row in top5_factors.iterrows():
        print(f"  - {row['Feature']} = {row['Value']} (SHAP impact: +{row['SHAP_Value']:.4f})")
        factor_str_list.append(f"{row['Feature']} ({row['Value']})")
    
    explanation_sentence = f"This project was classified High Risk primarily due to: {', '.join(factor_str_list)}."
    print("\nFormatted Explanation Sentence:")
    print(f"\"{explanation_sentence}\"")
    print("======================================================================\n")

# 6. Save SHAP Summary Plot
plt.figure(figsize=(10, 8))
shap.summary_plot(shap_values, X_sample, class_names=classes, show=False)
plt.tight_layout()
plt.savefig('shap_summary.png', bbox_inches='tight', dpi=300)
plt.close()
print("Saved SHAP summary plot as 'shap_summary.png'.")
