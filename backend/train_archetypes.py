"""
Project Sentinel - Failure Pattern Mining Script
=================================================
Trains K-Means clustering (n_clusters=4) to group historical project-weeks
into 4 distinct behavioral archetypes:
  1. Stable Healthy
  2. Slow Decline
  3. Sudden Collapse
  4. Recovering
"""

from typing import Any, cast
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

# Define the 15 feature columns
FEATURE_COLS = [
    'week_number', 'issue_count', 'task_completion_rate',
    'unresolved_issue_percentage', 'overdue_tasks_percentage',
    'defect_density', 'critical_bug_count', 'team_size',
    'schedule_progress_percentage', 'stale_days_threshold_used',
    'issue_count_delta', 'task_completion_rate_delta',
    'overdue_tasks_percentage_delta', 'defect_density_delta', 'team_size_delta'
]

# Generate realistic training samples representing historical project-weeks
np.random.seed(42)
n_samples = 1000

# Cluster 0: Stable Healthy
c0 = np.column_stack([
    np.random.uniform(1, 30, 250), # week_number
    np.random.uniform(2, 10, 250), # issue_count
    np.random.uniform(85, 98, 250), # task_completion_rate
    np.random.uniform(5, 15, 250), # unresolved_issue_percentage
    np.random.uniform(2, 10, 250), # overdue_tasks_percentage
    np.random.uniform(1, 5, 250),  # defect_density
    np.random.uniform(0, 0.5, 250),# critical_bug_count
    np.random.uniform(6, 12, 250), # team_size
    np.random.uniform(80, 95, 250),# schedule_progress_percentage
    np.random.uniform(10, 15, 250),# stale_days_threshold_used
    np.random.uniform(-1, 1, 250), # issue_count_delta
    np.random.uniform(0, 3, 250),  # task_completion_rate_delta
    np.random.uniform(-2, 0, 250), # overdue_tasks_percentage_delta
    np.random.uniform(-0.5, 0.5, 250), # defect_density_delta
    np.random.uniform(0, 1, 250)   # team_size_delta
])

# Cluster 1: Slow Decline
c1 = np.column_stack([
    np.random.uniform(10, 40, 250),
    np.random.uniform(15, 25, 250),
    np.random.uniform(50, 68, 250),
    np.random.uniform(30, 45, 250),
    np.random.uniform(20, 35, 250),
    np.random.uniform(8, 16, 250),
    np.random.uniform(1, 2, 250),
    np.random.uniform(5, 8, 250),
    np.random.uniform(55, 70, 250),
    np.random.uniform(20, 30, 250),
    np.random.uniform(1, 4, 250),
    np.random.uniform(-4, -1, 250),
    np.random.uniform(2, 6, 250),
    np.random.uniform(0.5, 2.0, 250),
    np.random.uniform(-1, 0, 250)
])

# Cluster 2: Sudden Collapse
c2 = np.column_stack([
    np.random.uniform(15, 35, 250),
    np.random.uniform(25, 45, 250),
    np.random.uniform(30, 48, 250),
    np.random.uniform(50, 75, 250),
    np.random.uniform(45, 70, 250),
    np.random.uniform(20, 35, 250),
    np.random.uniform(2, 5, 250),
    np.random.uniform(3, 6, 250),
    np.random.uniform(35, 50, 250),
    np.random.uniform(30, 45, 250),
    np.random.uniform(5, 12, 250),
    np.random.uniform(-10, -4, 250),
    np.random.uniform(8, 18, 250),
    np.random.uniform(3.0, 6.0, 250),
    np.random.uniform(-2, -0.5, 250)
])

# Cluster 3: Recovering
c3 = np.column_stack([
    np.random.uniform(12, 35, 250),
    np.random.uniform(10, 20, 250),
    np.random.uniform(65, 82, 250),
    np.random.uniform(20, 35, 250),
    np.random.uniform(15, 25, 250),
    np.random.uniform(5, 12, 250),
    np.random.uniform(0, 1, 250),
    np.random.uniform(7, 10, 250),
    np.random.uniform(70, 85, 250),
    np.random.uniform(15, 25, 250),
    np.random.uniform(-3, 0, 250),
    np.random.uniform(2, 6, 250),
    np.random.uniform(-5, -1, 250),
    np.random.uniform(-2.0, -0.5, 250),
    np.random.uniform(0, 1.5, 250)
])

X_train = np.vstack([c0, c1, c2, c3])
df_train = pd.DataFrame(X_train, columns=FEATURE_COLS)

# Train KMeans
kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
kmeans.fit(df_train)

# Determine cluster assignments to human-readable names based on average overdue & completion
cluster_centers = cast(Any, kmeans).cluster_centers_
centers_df = cast(Any, pd.DataFrame(cluster_centers, columns=FEATURE_COLS))

# Map each cluster index to archetype
archetype_map = {}
for i in range(4):
    avg_comp = float(centers_df.loc[i, 'task_completion_rate'])
    avg_overdue = float(centers_df.loc[i, 'overdue_tasks_percentage'])
    avg_defect = float(centers_df.loc[i, 'defect_density'])
    comp_delta = float(centers_df.loc[i, 'task_completion_rate_delta'])

    if avg_comp >= 80:
        name = "Stable Healthy"
        desc = "High velocity sprint cadence with low defect accumulation and stable delivery progress."
    elif avg_overdue >= 40 or avg_defect >= 18:
        name = "Sudden Collapse"
        desc = "Abrupt surge in defect density and critical bugs causing immediate milestone bottlenecks."
    elif comp_delta > 1.0 or (avg_comp >= 65 and avg_overdue <= 30):
        name = "Recovering"
        desc = "Improving velocity deltas and active backlog remediation indicating positive trajectory recovery."
    else:
        name = "Slow Decline"
        desc = "Gradually decreasing task completion rate accompanied by creeping overdue task accumulation."
    
    archetype_map[i] = {"name": name, "description": desc}

# Save trained KMeans model and archetype mapping dictionary
artifact_data = {
    "kmeans_model": kmeans,
    "archetype_map": archetype_map
}

base_dir = os.path.dirname(__file__)
save_path = os.path.join(base_dir, "archetype_model.pkl")
joblib.dump(artifact_data, save_path)

print(f"Successfully trained KMeans archetype model and saved to {save_path}.")
print("Cluster Archetype Map:")
for k, v in archetype_map.items():
    print(f"  Cluster {k}: {v['name']} -> {v['description']}")
