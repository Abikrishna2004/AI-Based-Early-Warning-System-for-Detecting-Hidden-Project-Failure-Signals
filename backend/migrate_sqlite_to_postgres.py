import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Import database models and init_db
from database import Base, Project, ProjectInput, Prediction, Recommendation

def migrate():
    sqlite_path = os.path.join(BASE_DIR, "sentinel.db")
    if not os.path.exists(sqlite_path):
        print(f"Error: SQLite database file not found at {sqlite_path}")
        sys.exit(1)

    postgres_url = os.environ.get("DATABASE_URL")
    if not postgres_url or not postgres_url.startswith("postgresql"):
        print("Error: DATABASE_URL is not set or not a valid PostgreSQL URL")
        sys.exit(1)

    print("Connecting to SQLite database...")
    sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
    SqliteSession = sessionmaker(bind=sqlite_engine)
    sqlite_session = SqliteSession()

    print("Connecting to Neon PostgreSQL database...")
    pg_engine = create_engine(postgres_url, pool_pre_ping=True)
    
    print("Creating tables in Neon PostgreSQL if they don't exist...")
    Base.metadata.create_all(bind=pg_engine)

    PgSession = sessionmaker(bind=pg_engine)
    pg_session = PgSession()

    try:
        # 1. Projects
        sqlite_projects = sqlite_session.query(Project).all()
        print(f"Migrating {len(sqlite_projects)} projects...")
        for p in sqlite_projects:
            existing = pg_session.query(Project).filter_by(project_id=p.project_id).first()
            if not existing:
                pg_session.add(Project(
                    project_id=p.project_id,
                    project_name=p.project_name,
                    created_date=p.created_date
                ))
        pg_session.commit()

        # 2. ProjectInputs
        sqlite_inputs = sqlite_session.query(ProjectInput).all()
        print(f"Migrating {len(sqlite_inputs)} project_inputs...")
        for inp in sqlite_inputs:
            existing = pg_session.query(ProjectInput).filter_by(input_id=inp.input_id).first()
            if not existing:
                pg_session.add(ProjectInput(
                    input_id=inp.input_id,
                    project_id=inp.project_id,
                    week_number=inp.week_number,
                    issue_count=inp.issue_count,
                    task_completion_rate=inp.task_completion_rate,
                    unresolved_issue_percentage=inp.unresolved_issue_percentage,
                    overdue_tasks_percentage=inp.overdue_tasks_percentage,
                    defect_density=inp.defect_density,
                    critical_bug_count=inp.critical_bug_count,
                    team_size=inp.team_size,
                    schedule_progress_percentage=inp.schedule_progress_percentage,
                    stale_days_threshold_used=inp.stale_days_threshold_used,
                    issue_count_delta=inp.issue_count_delta,
                    task_completion_rate_delta=inp.task_completion_rate_delta,
                    overdue_tasks_percentage_delta=inp.overdue_tasks_percentage_delta,
                    defect_density_delta=inp.defect_density_delta,
                    team_size_delta=inp.team_size_delta,
                    timestamp=inp.timestamp
                ))
        pg_session.commit()

        # 3. Predictions
        sqlite_preds = sqlite_session.query(Prediction).all()
        print(f"Migrating {len(sqlite_preds)} predictions...")
        for pred in sqlite_preds:
            existing = pg_session.query(Prediction).filter_by(prediction_id=pred.prediction_id).first()
            if not existing:
                pg_session.add(Prediction(
                    prediction_id=pred.prediction_id,
                    project_id=pred.project_id,
                    risk_level=pred.risk_level,
                    risk_probability=pred.risk_probability,
                    model_version=pred.model_version,
                    prediction_date=pred.prediction_date
                ))
        pg_session.commit()

        # 4. Recommendations
        sqlite_recs = sqlite_session.query(Recommendation).all()
        print(f"Migrating {len(sqlite_recs)} recommendations...")
        for rec in sqlite_recs:
            existing = pg_session.query(Recommendation).filter_by(recommendation_id=rec.recommendation_id).first()
            if not existing:
                pg_session.add(Recommendation(
                    recommendation_id=rec.recommendation_id,
                    prediction_id=rec.prediction_id,
                    risk_factor=rec.risk_factor,
                    recommendation=rec.recommendation,
                    priority=rec.priority
                ))
        pg_session.commit()

        # Reset Postgres primary key sequences
        for table, col in [("project_inputs", "input_id"), ("predictions", "prediction_id"), ("recommendations", "recommendation_id")]:
            res = pg_session.execute(text(f"SELECT COALESCE(MAX({col}), 0) FROM {table}")).scalar()
            max_id = int(res) if res is not None else 0
            if max_id > 0:
                pg_session.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', '{col}'), {max_id})"))
        pg_session.commit()

        print("\nMigration completed successfully!")
        
        # Print summary counts
        print("\n--- Neon PostgreSQL Data Summary ---")
        print(f"Projects: {pg_session.query(Project).count()}")
        print(f"Project Inputs: {pg_session.query(ProjectInput).count()}")
        print(f"Predictions: {pg_session.query(Prediction).count()}")
        print(f"Recommendations: {pg_session.query(Recommendation).count()}")

    except Exception as e:
        pg_session.rollback()
        print(f"Migration error: {e}")
        raise e
    finally:
        sqlite_session.close()
        pg_session.close()

if __name__ == "__main__":
    migrate()
