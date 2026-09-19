import pandas as pd
from sklearn.model_selection import GroupShuffleSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

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

print("Training Random Forest Classifier (n_estimators=200, class_weight='balanced', random_state=42)...")

# Initialize and train Random Forest model
rf_model = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    class_weight='balanced',
    n_jobs=-1
)
rf_model.fit(X_train, y_train)

# Evaluate on test set
y_pred = rf_model.predict(X_test)

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
