import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

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

# Define target and features
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

train_projects = groups.iloc[train_idx]
test_projects = groups.iloc[test_idx]

unique_train_projects = set(train_projects.unique())
unique_test_projects = set(test_projects.unique())
overlap_projects = unique_train_projects.intersection(unique_test_projects)

print("--- Train/Test Set Shapes ---")
print(f"X_train shape: {X_train.shape}")
print(f"y_train shape: {y_train.shape}")
print(f"X_test shape:  {X_test.shape}")
print(f"y_test shape:   {y_test.shape}")
print()

print("--- Group (project_id) Statistics ---")
print(f"Total unique projects in dataset:  {df['project_id'].nunique()}")
print(f"Unique projects in Training set:  {len(unique_train_projects)}")
print(f"Unique projects in Test set:      {len(unique_test_projects)}")
print(f"Number of overlapping projects:   {len(overlap_projects)}")
if len(overlap_projects) == 0:
    print("SUCCESS: 0 overlapping projects! Data leakage prevented.")
else:
    print(f"WARNING: Found {len(overlap_projects)} overlapping projects!")
