import pytest
import tempfile
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, create_engine
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_session
from app.models import SQLModel
from app.seed import seed_database


@pytest.fixture(scope="session")
def test_db():
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    test_database_url = f"sqlite:///{db_path}"

    # Create test engine
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})

    # Create tables and seed data
    SQLModel.metadata.create_all(engine)
    seed_database(engine)

    yield engine

    # Cleanup
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def session(test_db):
    with Session(test_db) as session:
        yield session


@pytest.fixture
def client(test_db):
    def get_test_session():
        with Session(test_db) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
