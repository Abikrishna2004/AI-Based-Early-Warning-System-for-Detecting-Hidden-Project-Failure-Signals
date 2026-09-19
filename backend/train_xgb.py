import pandas as pd
from typing import Any, cast
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from xgboost import XGBClassifier

# Load dataset
dataset_path = 'project_sentinel_final_real_dataset.csv'
assert dataset_path is not None
df = pd.read_csv(dataset_path)

# Columns to drop for features
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

# GroupShuffleSplit with test_size=0.2, random_state=42
gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
train_idx, test_idx = next(gss.split(X, y, groups=groups))

X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]

# Target Label Encoding
le = LabelEncoder()
y_train_encoded = le.fit_transform(y_train)
y_test_encoded = le.transform(y_test)

print("Label Mapping:")
for code, class_name in enumerate(cast(Any, le).classes_):
    print(f"  {class_name} -> {code}")
print()

print("Training XGBoost Classifier (n_estimators=300, max_depth=6, learning_rate=0.1, eval_metric='mlogloss', random_state=42)...")

# Initialize and train XGBoost classifier
xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    eval_metric='mlogloss',
    n_jobs=-1
)
xgb_model.fit(X_train, y_train_encoded)

# Evaluate on test set
y_pred_encoded = xgb_model.predict(X_test)
y_pred = le.inverse_transform(y_pred_encoded)

# Metrics
acc = accuracy_score(y_test, y_pred)
cls_report = classification_report(y_test, y_pred, digits=4)
conf_matrix = confusion_matrix(y_test, y_pred, labels=['Low', 'Medium', 'High'])

print("\n================ EVALUATION RESULTS ================")
print(f"Accuracy Score: {acc:.4f} ({acc * 100:.2f}%)\n")

print("Classification Report:")
print(cls_report)

print("Confusion Matrix (Labels: ['Low', 'Medium', 'High']):")
print(conf_matrix)
