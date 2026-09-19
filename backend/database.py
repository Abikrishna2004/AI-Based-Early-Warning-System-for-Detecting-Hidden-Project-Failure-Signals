import os
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

# SQLite Database Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("SENTINEL_DB_PATH", os.path.join(BASE_DIR, "sentinel.db"))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_utc_now():
    return datetime.now(timezone.utc)

# 1. Projects Table
class Project(Base):
    __tablename__ = "projects"

    project_id = Column(String, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    created_date = Column(DateTime, default=get_utc_now, nullable=False)

    inputs = relationship("ProjectInput", back_populates="project", cascade="all, delete-orphan")
    predictions = relationship("Prediction", back_populates="project", cascade="all, delete-orphan")

# 2. Project Inputs Table
class ProjectInput(Base):
    __tablename__ = "project_inputs"

    input_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    
    # 15 feature columns
    week_number = Column(Float, nullable=False)
    issue_count = Column(Float, nullable=False)
    task_completion_rate = Column(Float, nullable=False)
    unresolved_issue_percentage = Column(Float, nullable=False)
    overdue_tasks_percentage = Column(Float, nullable=False)
    defect_density = Column(Float, nullable=False)
    critical_bug_count = Column(Float, nullable=False)
    team_size = Column(Float, nullable=False)
    schedule_progress_percentage = Column(Float, nullable=False)
    stale_days_threshold_used = Column(Float, nullable=False)
    issue_count_delta = Column(Float, nullable=False)
    task_completion_rate_delta = Column(Float, nullable=False)
    overdue_tasks_percentage_delta = Column(Float, nullable=False)
    defect_density_delta = Column(Float, nullable=False)
    team_size_delta = Column(Float, nullable=False)
    
    timestamp = Column(DateTime, default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="inputs")

# 3. Predictions Table
class Prediction(Base):
    __tablename__ = "predictions"

    prediction_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=False, index=True)
    risk_level = Column(String, nullable=False)
    risk_probability = Column(Float, nullable=False)
    model_version = Column(String, default="catboost_v1", nullable=False)
    prediction_date = Column(DateTime, default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="predictions")
    recommendations = relationship("Recommendation", back_populates="prediction", cascade="all, delete-orphan")

# 4. Recommendations Table
class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    prediction_id = Column(Integer, ForeignKey("predictions.prediction_id"), nullable=False, index=True)
    risk_factor = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    priority = Column(Integer, nullable=False)  # 1, 2, or 3 based on SHAP rank order

    prediction = relationship("Prediction", back_populates="recommendations")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
