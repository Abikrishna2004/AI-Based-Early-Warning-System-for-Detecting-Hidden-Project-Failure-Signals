import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from database import Base, Project, ProjectInput, Prediction, Recommendation

def clear_database():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or not db_url.startswith("postgresql"):
        print("Error: DATABASE_URL environment variable is not configured for PostgreSQL.")
        sys.exit(1)

    print(f"Connecting to Neon PostgreSQL database...")
    engine = create_engine(db_url, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        print("\n--- Current Data Counts Before Clearing ---")
        print(f"Projects: {session.query(Project).count()}")
        print(f"Project Inputs: {session.query(ProjectInput).count()}")
        print(f"Predictions: {session.query(Prediction).count()}")
        print(f"Recommendations: {session.query(Recommendation).count()}")

        print("\nClearing all table records and resetting primary key sequences...")
        session.execute(text("TRUNCATE TABLE recommendations, predictions, project_inputs, projects RESTART IDENTITY CASCADE;"))
        session.commit()

        print("\n--- Current Data Counts After Clearing ---")
        print(f"Projects: {session.query(Project).count()}")
        print(f"Project Inputs: {session.query(ProjectInput).count()}")
        print(f"Predictions: {session.query(Prediction).count()}")
        print(f"Recommendations: {session.query(Recommendation).count()}")

        print("\nDatabase cleared successfully!")

    except Exception as e:
        session.rollback()
        print(f"Error clearing database: {e}")
        sys.exit(1)
    finally:
        session.close()

if __name__ == "__main__":
    clear_database()
