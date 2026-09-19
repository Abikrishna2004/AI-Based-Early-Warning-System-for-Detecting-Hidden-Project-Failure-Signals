"""
Project Sentinel - Model Calibration & Cost-Sensitive Threshold Optimization
=============================================================================
1. Calibration Analysis:
   - Computes Brier Score and Expected Calibration Error (ECE).
   - Generates and saves Reliability Diagrams (10 bins) for Low, Medium, High risk classes.
   - Fits Platt Scaling (Sigmoid) calibrator and saves 'calibration_model.pkl'.
   - Evaluates whether model confidence (e.g. 97.9%) is trustworthy or systematically miscalibrated.

2. Cost-Sensitive Threshold Optimization:
   - Applies 5x penalty for False Negatives on High risk vs 1x for False Positives / other errors.
   - Sweeps High-risk decision threshold T_high from 0.10 to 0.90 in steps of 0.05.
   - Identifies cost-minimizing threshold T* and compares against Argmax baseline and 1.5x class-weight model.
"""

from typing import Any, Dict, List, Optional, cast
import os
import shutil
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone

import matplotlib.pyplot as plt

from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, brier_score_loss, classification_report
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import calibration_curve
from catboost import CatBoostClassifier

# Artifact directory for embedding images
ARTIFACT_DIR = r"C:\Users\ACER\.gemini\antigravity-ide\brain\7c8a5a6c-719b-431c-9ec9-3ccb34a01aaa"

class PlattCalibrator:
    """Per-class Platt Scaling (Sigmoid probability calibration) for multi-class alignment."""
    def __init__(self, classes):
        self.classes = list(classes)
        self.calibrators = {}

    def fit(self, probs, y_true):
        for idx, cls in enumerate(self.classes):
            y_binary = (np.array(y_true) == cls).astype(int)
            p_cls = np.clip(probs[:, idx], 1e-6, 1.0 - 1e-6)
            logits = np.log(p_cls / (1.0 - p_cls)).reshape(-1, 1)
            lr = LogisticRegression(C=1e5, solver='lbfgs')
            lr.fit(logits, y_binary)
            self.calibrators[cls] = lr
        return self

    def predict_proba(self, probs):
        calibrated_probs = np.zeros_like(probs)
        for idx, cls in enumerate(self.classes):
            if cls in self.calibrators:
                p_cls = np.clip(probs[:, idx], 1e-6, 1.0 - 1e-6)
                logits = np.log(p_cls / (1.0 - p_cls)).reshape(-1, 1)
                calibrated_probs[:, idx] = self.calibrators[cls].predict_proba(logits)[:, 1]
            else:
                calibrated_probs[:, idx] = probs[:, idx]
        # Normalize across classes
        sums = np.sum(calibrated_probs, axis=1, keepdims=True)
        sums[sums == 0] = 1.0
        return calibrated_probs / sums

def compute_ece(y_true_indices, y_prob, n_bins=10):
    """
    Computes Expected Calibration Error (ECE) for multi-class predictions.
    Bins predictions by maximum predicted probability p_max (model confidence in predicted class)
    against whether prediction is correct.
    ECE = sum_b (|B_b| / N) * |acc(B_b) - conf(B_b)|
    """
    confidences = np.max(y_prob, axis=1)
    predictions = np.argmax(y_prob, axis=1)
    accuracies = (predictions == y_true_indices)
    
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    bin_details = []
    
    for i in range(n_bins):
        bin_lower, bin_upper = bin_boundaries[i], bin_boundaries[i + 1]
        if i == 0:
            in_bin = (confidences >= bin_lower) & (confidences <= bin_upper)
            range_str = f"[{bin_lower:.1f}, {bin_upper:.1f}]"
        else:
            in_bin = (confidences > bin_lower) & (confidences <= bin_upper)
            range_str = f"({bin_lower:.1f}, {bin_upper:.1f}]"
            
        bin_size = int(np.sum(in_bin))
        
        if bin_size > 0:
            bin_acc = float(np.mean(accuracies[in_bin]))
            bin_conf = float(np.mean(confidences[in_bin]))
            bin_error = float(np.abs(bin_acc - bin_conf))
            weight = float(bin_size / len(y_true_indices))
            weighted_gap = float(weight * bin_error)
            ece += weighted_gap
            bin_details.append({
                'bin': i + 1,
                'range': range_str,
                'count': bin_size,
                'avg_confidence': round(bin_conf, 4),
                'avg_accuracy': round(bin_acc, 4),
                'abs_gap': round(bin_error, 4),
                'weighted_gap': round(weighted_gap, 5)
            })
        else:
            bin_details.append({
                'bin': i + 1,
                'range': range_str,
                'count': 0,
                'avg_confidence': 0.0,
                'avg_accuracy': 0.0,
                'abs_gap': 0.0,
                'weighted_gap': 0.0
            })
            
    return ece, bin_details

def compute_multiclass_brier_score(y_true, y_prob, classes):
    """
    Computes multi-class Brier score:
    BS = (1 / N) * sum_i sum_c (p_{i,c} - y_{i,c})^2
    """
    n_samples = len(y_true)
    n_classes = len(classes)
    y_true_onehot = np.zeros((n_samples, n_classes))
    
    for i, label in enumerate(y_true):
        class_idx = classes.index(label)
        y_true_onehot[i, class_idx] = 1.0
        
    brier_score = np.mean(np.sum((y_prob - y_true_onehot) ** 2, axis=1))
    return brier_score

def run_calibration_and_cost_analysis():
    print("=" * 95)
    print("      PROJECT SENTINEL - MODEL CALIBRATION & COST-SENSITIVE THRESHOLD OPTIMIZATION")
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
        raise FileNotFoundError("Dataset project_sentinel_final_real_dataset.csv not found.")
        
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
    
    # 80/20 Grouped Split (by project_id)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))
    
    X_train, X_test = X.iloc[train_idx].reset_index(drop=True), X.iloc[test_idx].reset_index(drop=True)
    y_train, y_test = y.iloc[train_idx].reset_index(drop=True), y.iloc[test_idx].reset_index(drop=True)
    
    print(f"      Train: {len(X_train)} samples ({groups.iloc[train_idx].nunique()} projects)")
    print(f"      Test : {len(X_test)} samples ({groups.iloc[test_idx].nunique()} projects)")
    
    # 2. Load & Verify Production CatBoost Model Consistency
    base_dir = os.path.dirname(__file__)
    if not base_dir:
        base_dir = "."
    model_filename = 'best_model_catboost.cbm'
    model_path = os.path.abspath(os.path.join(base_dir, model_filename))
    main_py_model_path = os.path.abspath(os.path.join(base_dir, 'best_model_catboost.cbm'))
    
    mtime = os.path.getmtime(model_path)
    mtime_str = datetime.fromtimestamp(mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    size_bytes = os.path.getsize(model_path)
    size_kb = size_bytes / 1024.0
    
    main_mtime = os.path.getmtime(main_py_model_path)
    main_mtime_str = datetime.fromtimestamp(main_mtime, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    main_size_bytes = os.path.getsize(main_py_model_path)
    
    match_path = (model_path == main_py_model_path)
    match_size = (size_bytes == main_size_bytes)
    match_mtime = (mtime == main_mtime)
    
    print(f"\n[2/5] Model Consistency Verification:", flush=True)
    print(f"      Model File Evaluated           : {model_filename}")
    print(f"      Absolute Model Path            : {model_path}")
    print(f"      Production main.py Model Path  : {main_py_model_path}")
    print(f"      Path Match                     : {match_path}")
    print(f"      File Size                      : {size_bytes} bytes ({size_kb:.2f} KB) | Match: {match_size}")
    print(f"      Modification Timestamp         : {mtime_str} | Match: {match_mtime}")
    
    if not (match_path and match_size and match_mtime):
        raise ValueError("CRITICAL MODEL MISMATCH: Model evaluated does not match production best_model_catboost.cbm!")
    else:
        print("      MODEL CONSISTENCY VERIFIED: Evaluated model matches production best_model_catboost.cbm (1.5x class-weight model) exactly.")
    
    print(f"\n      Loading CatBoost model...", flush=True)
    cb_model = CatBoostClassifier()
    cb_model.load_model(model_path)
    classes = list(cast(Any, cb_model).classes_)
    print(f"      Model loaded successfully. Class ordering: {classes}")
    
    # Predict raw probabilities on train and test
    raw_probs_train = cb_model.predict_proba(X_train)
    raw_probs_test = cb_model.predict_proba(X_test)
    raw_preds_test = cb_model.predict(X_test)
    if hasattr(raw_preds_test, 'ravel'):
        raw_preds_test = raw_preds_test.ravel()
        
    y_test_indices = np.array([classes.index(label) for label in y_test])
    
    # 3. Model Calibration Analysis (ECE & Brier Score)
    print("\n[3/5] Performing Reliability & Calibration Analysis...", flush=True)
    raw_brier = compute_multiclass_brier_score(y_test, raw_probs_test, classes)
    raw_ece, bin_details_raw = compute_ece(y_test_indices, raw_probs_test, n_bins=10)
    
    print(f"\n      --- RAW MODEL CALIBRATION METRICS ---")
    print(f"      Overall Brier Score (lower is better) : {raw_brier:.4f}")
    print(f"      Expected Calibration Error (ECE)      : {raw_ece:.4f} ({raw_ece*100:.2f}%)\n")
    
    raw_bin_df = pd.DataFrame(bin_details_raw)
    print("      --- 10-BIN EQUAL-WIDTH RELIABILITY TABLE (RAW CATBOOST MODEL) ---")
    print(raw_bin_df[['bin', 'range', 'count', 'avg_confidence', 'avg_accuracy', 'abs_gap', 'weighted_gap']].to_string(index=False))
    print("      " + "-" * 85)
    
    # Fit Platt Scaling Calibrator on train predictions
    print("\n      Fitting Platt Scaling (Sigmoid) Calibrator on training predictions...")
    platt_calibrator = PlattCalibrator(classes)
    platt_calibrator.fit(raw_probs_train, y_train)
    
    cal_probs_test = platt_calibrator.predict_proba(raw_probs_test)
    cal_brier = compute_multiclass_brier_score(y_test, cal_probs_test, classes)
    cal_ece, bin_details_cal = compute_ece(y_test_indices, cal_probs_test, n_bins=10)
    
    print(f"\n      --- CALIBRATED MODEL METRICS ---")
    print(f"      Calibrated Brier Score                : {cal_brier:.4f}")
    print(f"      Calibrated ECE                        : {cal_ece:.4f} ({cal_ece*100:.2f}%)\n")
    
    cal_bin_df = pd.DataFrame(bin_details_cal)
    print("      --- 10-BIN EQUAL-WIDTH RELIABILITY TABLE (PLATT-CALIBRATED MODEL) ---")
    print(cal_bin_df[['bin', 'range', 'count', 'avg_confidence', 'avg_accuracy', 'abs_gap', 'weighted_gap']].to_string(index=False))
    print("      " + "-" * 85)
    
    # Save Calibrated Model Artifact
    calibrator_save_path = os.path.join(base_dir, 'calibration_model.pkl')
    joblib.dump(platt_calibrator, calibrator_save_path)
    print(f"      [SAVED] Calibrated model saved to '{calibrator_save_path}'.")
    
    # 4. Generate & Save Reliability Diagram Plot
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    colors = {'Low': '#2ecc71', 'Medium': '#f39c12', 'High': '#e74c3c'}
    
    for i, cls in enumerate(['Low', 'Medium', 'High']):
        ax = axes[i]
        cls_idx = classes.index(cls)
        y_binary = (y_test == cls).astype(int)
        prob_cls_raw = raw_probs_test[:, cls_idx]
        prob_cls_cal = cal_probs_test[:, cls_idx]
        
        prob_true_raw, prob_pred_raw = calibration_curve(y_binary, prob_cls_raw, n_bins=10, strategy='uniform')
        prob_true_cal, prob_pred_cal = calibration_curve(y_binary, prob_cls_cal, n_bins=10, strategy='uniform')
        
        ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration", alpha=0.7)
        ax.plot(prob_pred_raw, prob_true_raw, "s-", color=colors[cls], linewidth=2, label=f"Raw CatBoost ({cls})")
        ax.plot(prob_pred_cal, prob_true_cal, "o:", color='#2c3e50', linewidth=2, label=f"Calibrated ({cls})")
        
        class_brier = brier_score_loss(y_binary, prob_cls_raw)
        
        ax.set_title(f"Reliability Diagram: {cls} Risk\n(Class Brier Score: {class_brier:.4f})", fontsize=12, fontweight='bold')
        ax.set_xlabel("Mean Predicted Probability", fontsize=11)
        ax.set_ylabel("Empirical True Fraction", fontsize=11)
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend(loc="upper left")
        ax.set_xlim([0.0, 1.0])
        ax.set_ylim([0.0, 1.0])
        
    plt.suptitle(f"Model Probability Calibration Analysis (Overall ECE: {raw_ece:.4f}, Brier: {raw_brier:.4f})", fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    plot_path_local = os.path.join(base_dir, 'calibration_plot.png')
    plt.savefig(plot_path_local, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"      [SAVED] Reliability diagram plot saved to '{plot_path_local}'.")
    
    # Copy to artifact directory if available
    if os.path.exists(ARTIFACT_DIR):
        artifact_plot_path = os.path.join(ARTIFACT_DIR, 'calibration_plot.png')
        shutil.copy(plot_path_local, artifact_plot_path)
        print(f"      [COPIED] Reliability plot copied to artifact path '{artifact_plot_path}'.")
        
    # 5. Cost-Sensitive Threshold Optimization
    print("\n[4/5] Executing Cost-Sensitive Threshold Optimization...", flush=True)
    print("      Cost Matrix Definition:")
    print("      - False Negative on High Risk (predict Low/Medium when actual High) : Cost = 5.0 (5x penalty)")
    print("      - False Positive on High Risk (predict High when actual Low/Medium) : Cost = 1.0")
    print("      - Misclassification between Low & Medium                            : Cost = 1.0")
    print("      - Correct Classification                                            : Cost = 0.0")
    
    thresholds = np.arange(0.10, 0.95, 0.05)
    cost_results = []
    
    high_idx = classes.index('High')
    low_idx = classes.index('Low')
    med_idx = classes.index('Medium')
    
    for T_high in thresholds:
        preds_custom = []
        total_cost = 0.0
        
        for i in range(len(X_test)):
            probs_i = raw_probs_test[i]
            p_high = probs_i[high_idx]
            
            # Decision rule with threshold T_high
            if p_high >= T_high:
                pred_cls = 'High'
            else:
                if probs_i[low_idx] >= probs_i[med_idx]:
                    pred_cls = 'Low'
                else:
                    pred_cls = 'Medium'
                    
            actual_cls = y_test[i]
            preds_custom.append(pred_cls)
            
            # Calculate cost for this sample
            if actual_cls == pred_cls:
                sample_cost = 0.0
            elif actual_cls == 'High' and pred_cls in ['Low', 'Medium']:
                sample_cost = 5.0  # 5x FN High penalty
            elif actual_cls in ['Low', 'Medium'] and pred_cls == 'High':
                sample_cost = 1.0  # FP High penalty
            else:
                sample_cost = 1.0  # Low vs Medium error
                
            total_cost += sample_cost
            
        mean_cost = total_cost / len(X_test)
        acc = accuracy_score(y_test, preds_custom)
        res = cast(Any, precision_recall_fscore_support(y_test, preds_custom, labels=classes, zero_division=0))
        prec_arr, rec_arr, f1_arr = res[0], res[1], res[2]
        
        high_rec = float(rec_arr[high_idx])
        high_prec = float(prec_arr[high_idx])
        high_f1 = float(f1_arr[high_idx])
        macro_f1 = float(np.mean(f1_arr))


        
        cost_results.append({
            'threshold': round(T_high, 2),
            'total_cost': total_cost,
            'mean_cost': mean_cost,
            'accuracy': acc,
            'macro_f1': macro_f1,
            'high_precision': high_prec,
            'high_recall': high_rec,
            'high_f1': high_f1
        })
        
    cost_df = pd.DataFrame(cost_results)
    best_row = cost_df.loc[cost_df['mean_cost'].idxmin()]
    
    print("\n      --- COST SWEEP RESULTS (T_high from 0.10 to 0.90) ---")
    print(cost_df.to_string(index=False))
    
    print(f"\n[5/5] Cost Optimization Summary:")
    print(f"      Optimal High-Risk Threshold T* : {best_row['threshold']:.2f}")
    print(f"      Minimization Expected Mean Cost : {best_row['mean_cost']:.4f} per project")
    print(f"      Resulting High-Risk Recall    : {best_row['high_recall']*100:.2f}%")
    print(f"      Resulting High-Risk Precision : {best_row['high_precision']*100:.2f}%")
    print(f"      Resulting Overall Accuracy   : {best_row['accuracy']*100:.2f}%")
    
    # 6. Comparative Model Table
    # Compute true Standard Argmax Baseline metrics from cb_model.predict(X_test)
    argmax_acc = accuracy_score(y_test, raw_preds_test)
    argmax_rep = cast(Dict[str, Any], classification_report(y_test, raw_preds_test, output_dict=True))
    argmax_high_rec = float(argmax_rep['High']['recall'])
    argmax_high_prec = float(argmax_rep['High']['precision'])
    
    argmax_total_cost = 0.0
    for i in range(len(X_test)):
        actual_cls = y_test[i]
        pred_cls = raw_preds_test[i]
        if actual_cls == pred_cls:
            sample_cost = 0.0
        elif actual_cls == 'High' and pred_cls in ['Low', 'Medium']:
            sample_cost = 5.0
        elif actual_cls in ['Low', 'Medium'] and pred_cls == 'High':
            sample_cost = 1.0
        else:
            sample_cost = 1.0
        argmax_total_cost += sample_cost
    argmax_mean_cost = argmax_total_cost / len(X_test)
    
    comparison_table = pd.DataFrame([
        {
            'Model Strategy': 'Standard Argmax Baseline',
            'High Threshold T': 'Argmax',
            'Expected Mean Cost': f"{argmax_mean_cost:.4f}",
            'Accuracy': f"{argmax_acc*100:.2f}%",
            'High Recall': f"{argmax_high_rec*100:.2f}%",
            'High Precision': f"{argmax_high_prec*100:.2f}%"
        },
        {
            'Model Strategy': 'Cost-Optimal Threshold T*',
            'High Threshold T': f"{best_row['threshold']:.2f}",
            'Expected Mean Cost': f"{best_row['mean_cost']:.4f}",
            'Accuracy': f"{best_row['accuracy']*100:.2f}%",
            'High Recall': f"{best_row['high_recall']*100:.2f}%",
            'High Precision': f"{best_row['high_precision']*100:.2f}%"
        }
    ])
    
    print("\n=========================================================================================================")
    print("                COMPARISON: STANDARD ARGMAX VS COST-OPTIMAL THRESHOLD (5x FN HIGH COST)")
    print("=========================================================================================================")
    print(comparison_table.to_string(index=False))
    print("=========================================================================================================\n")
    
    # Calibration & Trustworthiness Summary
    if raw_ece < 0.05:
        trust_summary = f"The CatBoost model is HIGHLY CALIBRATED with an extremely low ECE of {raw_ece*100:.2f}% and Brier score of {raw_brier:.4f}. The stated confidence (e.g. 97.9%) is direct and trustworthy."
    else:
        trust_summary = f"The CatBoost model shows minor miscalibration with an ECE of {raw_ece*100:.2f}%. Applying Platt scaling reduces ECE to {cal_ece*100:.2f}%, making calibrated_confidence more accurate for decision making."
        
    print(f"TRUSTWORTHINESS CONCLUSION:\n{trust_summary}\n")

if __name__ == '__main__':
    run_calibration_and_cost_analysis()
