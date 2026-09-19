import pandas as pd

# Load dataset
dataset_path = 'project_sentinel_final_real_dataset.csv'
assert dataset_path is not None
df = pd.read_csv(dataset_path)

# Columns to drop (identifiers / metadata)
drop_cols = [
    'project_id',
    'project_name',
    'source_collection',
    'week_ending',
    'threshold_reliable',
    'team_size_reliable'
]

# Drop identifier/metadata columns
df_clean = df.drop(columns=drop_cols)

# Target column
target_col = 'risk_level'

# Feature columns (all remaining columns except target)
feature_cols = [col for col in df_clean.columns if col != target_col]

# Print Target Column Confirmation
print("--- Target Column ---")
print(f"Target Column: '{target_col}'")
print()

# Print Final Feature Columns
print(f"--- Feature Columns ({len(feature_cols)} Total) ---")
for idx, col in enumerate(feature_cols, 1):
    print(f"{idx}. {col}")

print()
print("--- Dataset Feature Matrix Shape ---")
X = df_clean[feature_cols]
y = df_clean[target_col]
print(f"Features shape (X): {X.shape}")
print(f"Target shape (y):   {y.shape}")
