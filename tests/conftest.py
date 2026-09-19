import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend directory and tests directory are in Python path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

tests_dir = os.path.abspath(os.path.dirname(__file__))
if tests_dir not in sys.path:
    sys.path.insert(0, tests_dir)

from fastapi.testclient import TestClient
from main import app, load_artifacts
from database import Base, get_db

# Shared test payloads
VALID_HEALTHY_PAYLOAD = {
    "project_id": "TEST-PROJ-001",
    "project_name": "Test Healthy Sprint",
    "week_number": 12.0,
    "issue_count": 5.0,
    "task_completion_rate": 90.0,
    "unresolved_issue_percentage": 10.0,
    "overdue_tasks_percentage": 5.0,
    "defect_density": 2.0,
    "critical_bug_count": 0.0,
    "team_size": 8.0,
    "schedule_progress_percentage": 85.0,
    "stale_days_threshold_used": 14.0,
    "issue_count_delta": -1.0,
    "task_completion_rate_delta": 2.5,
    "overdue_tasks_percentage_delta": -2.0,
    "defect_density_delta": -0.5,
    "team_size_delta": 0.0
}

VALID_CRITICAL_PAYLOAD = {
    "project_id": "TEST-PROJ-002",
    "project_name": "Test Critical Sprint",
    "week_number": 20.0,
    "issue_count": 32.0,
    "task_completion_rate": 42.9,
    "unresolved_issue_percentage": 57.1,
    "overdue_tasks_percentage": 57.1,
    "defect_density": 28.6,
    "critical_bug_count": 3.0,
    "team_size": 4.0,
    "schedule_progress_percentage": 42.9,
    "stale_days_threshold_used": 39.0,
    "issue_count_delta": 8.0,
    "task_completion_rate_delta": -8.5,
    "overdue_tasks_percentage_delta": 14.2,
    "defect_density_delta": 4.2,
    "team_size_delta": -2.0
}

@pytest.fixture
def valid_healthy_payload():
    return VALID_HEALTHY_PAYLOAD.copy()

@pytest.fixture
def valid_critical_payload():
    return VALID_CRITICAL_PAYLOAD.copy()

# Set isolated test database path
TEST_DB_PATH = os.path.join(backend_dir, "test_sentinel.db")
TEST_SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session", autouse=True)
def init_test_environment():
    """Session-scoped fixture to pre-warm backend model artifacts once and initialize isolated test DB."""
    # Create test database tables
    Base.metadata.create_all(bind=test_engine)
    
    # Pre-warm model artifacts once for all tests
    load_artifacts()
    
    yield
    
    # Teardown test database after session completes
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except Exception:
            pass

@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient session fixture."""
    with TestClient(app) as c:
        yield c

