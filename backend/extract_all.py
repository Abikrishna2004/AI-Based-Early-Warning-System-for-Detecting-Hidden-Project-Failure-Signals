"""
Project Sentinel - Local real-data extraction (v2 - improved accuracy)
Run this directly on your machine (where MongoDB is already running
with the JiraReposAnon database restored). Connects to MongoDB,
computes weekly per-project features with proper trend signals,
and writes ONE CSV file.

Usage:
    pip install pymongo pandas numpy
    python extract_all.py
"""

from datetime import datetime, timezone, timedelta
from collections import defaultdict
from statistics import median
from pymongo import MongoClient
import pandas as pd

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "JiraReposAnon"

COLLECTIONS = ["Mindville", "Mojang", "RedHat", "Spring", "Apache"]

COLLECTION_LIMITS = {
    "Mindville": 300000,
    "Mojang": 300000,
    "RedHat": 300000,
    "Spring": 300000,
    "Apache": 600000,
}
DEFAULT_LIMIT = 300000

MIN_ISSUES_FOR_PROJECT = 15
ACTIVE_TEAM_WINDOW_WEEKS = 8      # "team_size" = distinct assignees active in the last N weeks
MIN_STALE_DAYS = 14               # floor for the adaptive overdue threshold
STALE_MULTIPLIER = 1.5            # overdue threshold = max(MIN_STALE_DAYS, multiplier * project's own median resolution time)


def parse_date(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


client = MongoClient(MONGO_URI)
db = client[DB_NAME]
now = datetime.now(timezone.utc)

all_rows = []

for coll_name in COLLECTIONS:
    print(f"\n--- Processing collection: {coll_name} ---")
    coll = db[coll_name]

    projection = {
        "fields.project.key": 1, "fields.project.name": 1,
        "fields.created": 1, "fields.resolutiondate": 1,
        "fields.issuetype.name": 1, "fields.priority.name": 1,
        "fields.assignee.accountId": 1, "fields.assignee.name": 1,
        "fields.assignee.displayName": 1,
    }

    issues_by_project = defaultdict(list)
    project_names = {}

    limit = COLLECTION_LIMITS.get(coll_name, DEFAULT_LIMIT)
    cursor = coll.find({}, projection).limit(limit)
    n = 0
    for doc in cursor:
        n += 1
        if n % 50000 == 0:
            print(f"  ...read {n} issues so far")

        fl = doc.get("fields", {}) or {}
        proj = fl.get("project", {}) or {}
        pkey = proj.get("key")
        if not pkey:
            continue
        project_names[pkey] = proj.get("name")

        created = parse_date(fl.get("created"))
        if created is None:
            continue
        resolutiondate = parse_date(fl.get("resolutiondate"))
        issuetype = (fl.get("issuetype") or {}).get("name", "")
        priority = (fl.get("priority") or {}).get("name", "")
        assignee = fl.get("assignee")
        aid = None
        if assignee:
            aid = assignee.get("accountId") or assignee.get("name") or assignee.get("displayName")

        issues_by_project[pkey].append({
            "created": created,
            "resolved": resolutiondate,
            "is_bug": bool(issuetype and "bug" in issuetype.lower()),
            "is_critical": bool(priority and priority.lower() in ("highest", "critical", "blocker")),
            "assignee": aid,
        })

    print(f"  Read {n} issues across {len(issues_by_project)} projects")

    for pkey, issues in issues_by_project.items():
        if len(issues) < MIN_ISSUES_FOR_PROJECT:
            continue

        # Sort once by creation date - enables efficient incremental scanning
        # instead of re-filtering the whole list every week (fixes both
        # performance and a subtle correctness issue on large projects).
        issues.sort(key=lambda i: i["created"])

        start = issues[0]["created"]
        end_candidates = [i["created"] for i in issues] + [i["resolved"] for i in issues if i["resolved"]]
        end = min(max(end_candidates), now)

        # Adaptive overdue threshold: based on THIS project's own real
        # median resolution time, not one fixed number for every project.
        resolution_times = [
            (i["resolved"] - i["created"]).days
            for i in issues if i["resolved"] and i["resolved"] >= i["created"]
        ]
        if resolution_times:
            stale_days = max(MIN_STALE_DAYS, STALE_MULTIPLIER * median(resolution_times))
        else:
            stale_days = MIN_STALE_DAYS * 2  # fallback if nothing has ever been resolved

        week = start
        week_num = 0
        ptr = 0  # index of first issue not yet "created" as of current week
        prev_metrics = None

        while week <= end:
            week_end = week + timedelta(days=7)

            # advance pointer instead of rescanning from the start each time
            while ptr < len(issues) and issues[ptr]["created"] <= week_end:
                ptr += 1
            created_so_far = issues[:ptr]
            total = len(created_so_far)

            if total == 0:
                week = week_end
                week_num += 1
                continue

            resolved_so_far = [i for i in created_so_far if i["resolved"] and i["resolved"] <= week_end]
            resolved_count = len(resolved_so_far)

            overdue = [
                i for i in created_so_far
                if (i["resolved"] is None or i["resolved"] > week_end)
                and (week_end - i["created"]).days >= stale_days
            ]

            bug_count = sum(1 for i in created_so_far if i["is_bug"])
            critical_bug_count = sum(1 for i in created_so_far if i["is_bug"] and i["is_critical"])

            # Active team = distinct assignees on issues created in the
            # recent rolling window, not all-time cumulative (which can only
            # grow and never reflects real turnover/team changes).
            window_start = week_end - timedelta(weeks=ACTIVE_TEAM_WINDOW_WEEKS)
            active_assignees = set(
                i["assignee"] for i in created_so_far
                if i["assignee"] and i["created"] >= window_start
            )

            task_completion_rate = round(100 * resolved_count / total, 1)
            unresolved_issue_percentage = round(100 * (total - resolved_count) / total, 1)
            overdue_tasks_percentage = round(100 * len(overdue) / total, 1)
            defect_density = round(100 * bug_count / total, 1)

            row = {
                "source_collection": coll_name,
                "project_id": pkey,
                "project_name": project_names.get(pkey),
                "week_number": week_num,
                "week_ending": week_end.date().isoformat(),
                "issue_count": total,
                "task_completion_rate": task_completion_rate,
                "unresolved_issue_percentage": unresolved_issue_percentage,
                "overdue_tasks_percentage": overdue_tasks_percentage,
                "defect_density": defect_density,
                "critical_bug_count": critical_bug_count,
                "team_size": len(active_assignees),
                "schedule_progress_percentage": task_completion_rate,
                "stale_days_threshold_used": round(stale_days, 1),
            }

            # Week-over-week deltas - the actual "weak signal" trend features.
            if prev_metrics is not None:
                row["issue_count_delta"] = row["issue_count"] - prev_metrics["issue_count"]
                row["task_completion_rate_delta"] = round(task_completion_rate - prev_metrics["task_completion_rate"], 1)
                row["overdue_tasks_percentage_delta"] = round(overdue_tasks_percentage - prev_metrics["overdue_tasks_percentage"], 1)
                row["defect_density_delta"] = round(defect_density - prev_metrics["defect_density"], 1)
                row["team_size_delta"] = row["team_size"] - prev_metrics["team_size"]
            else:
                row["issue_count_delta"] = 0
                row["task_completion_rate_delta"] = 0.0
                row["overdue_tasks_percentage_delta"] = 0.0
                row["defect_density_delta"] = 0.0
                row["team_size_delta"] = 0

            prev_metrics = row
            all_rows.append(row)

            week = week_end
            week_num += 1

df = pd.DataFrame(all_rows)
out_path = "real_weekly_features_combined.csv"
df.to_csv(out_path, index=False)

print(f"\n=== DONE ===")
print(f"Total weekly rows: {len(df)}")
print(f"Projects included: {df['project_id'].nunique()}")
print(f"Saved to: {out_path}")
print(df.groupby('source_collection')['project_id'].nunique())