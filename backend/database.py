import os
from datetime import datetime, timezone
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not configured.")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
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

# 5. RAG Knowledge Sources Table
class RAGSource(Base):
    __tablename__ = "rag_sources"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    source_id = Column(String, unique=True, nullable=False, index=True)  # SRC-YYMMDD-NNN
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=True, index=True)  # NULL for independent sources
    source_type = Column(String, nullable=False)  # PROJECT_ANALYSIS, PROJECT_DOCUMENT, PROJECT_MANUAL_DATA, INDEPENDENT_DOCUMENT, INDEPENDENT_MANUAL_DATA, INDEPENDENT_DATASET
    source_name = Column(String, nullable=False)
    file_name = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    content = Column(String, nullable=True)
    metadata_json = Column(String, nullable=True)
    processing_status = Column(String, default="COMPLETED", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    project = relationship("Project", backref="sources")
    chunks = relationship("RAGChunk", back_populates="source", cascade="all, delete-orphan")
    session_associations = relationship("RAGSessionSource", back_populates="source", cascade="all, delete-orphan")

# 6. RAG Chunks Table
class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    source_id = Column(String, ForeignKey("rag_sources.source_id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(String, nullable=False)
    metadata_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    source = relationship("RAGSource", back_populates="chunks")

# 7. RAG Sessions Table
class RAGSession(Base):
    __tablename__ = "rag_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    rag_session_id = Column(String, unique=True, nullable=False, index=True)  # RAG-YYMMDD-NNN
    project_id = Column(String, ForeignKey("projects.project_id"), nullable=True, index=True)
    query = Column(String, nullable=False)
    model = Column(String, default="all-MiniLM-L6-v2 + DistilGPT2/RAG", nullable=False)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)

    project = relationship("Project", backref="rag_sessions")
    source_associations = relationship("RAGSessionSource", back_populates="rag_session", cascade="all, delete-orphan")
    outputs = relationship("RAGOutput", back_populates="rag_session", cascade="all, delete-orphan")

# 8. RAG Session Sources Junction Table
class RAGSessionSource(Base):
    __tablename__ = "rag_session_sources"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    rag_session_id = Column(String, ForeignKey("rag_sessions.rag_session_id"), nullable=False, index=True)
    source_id = Column(String, ForeignKey("rag_sources.source_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    rag_session = relationship("RAGSession", back_populates="source_associations")
    source = relationship("RAGSource", back_populates="session_associations")

# 9. RAG Outputs Table
class RAGOutput(Base):
    __tablename__ = "rag_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    rag_session_id = Column(String, ForeignKey("rag_sessions.rag_session_id"), nullable=False, index=True)
    response = Column(String, nullable=False)
    retrieved_context = Column(String, nullable=False)
    metadata_json = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_utc_now, nullable=False)

    rag_session = relationship("RAGSession", back_populates="outputs")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
