"""Pytest fixtures and test environment configuration."""

import os
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Set test environment flags
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_demo_access_token
from app.main import app

# In-memory test SQLite engine
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def init_test_db():
    """Create in-memory schema for each test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide transactional database session for tests."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def viewer_token() -> str:
    """Generate a runtime synthetic Bearer token for viewer role."""
    return create_demo_access_token(
        user_id="test_viewer_1",
        email="viewer@test.local",
        name="Test Viewer",
        roles=["viewer"]
    )


@pytest.fixture
def operator_token() -> str:
    """Generate a runtime synthetic Bearer token for operator role."""
    return create_demo_access_token(
        user_id="test_operator_1",
        email="operator@test.local",
        name="Test Operator",
        roles=["operator", "viewer"]
    )


@pytest.fixture
def admin_token() -> str:
    """Generate a runtime synthetic Bearer token for admin role."""
    return create_demo_access_token(
        user_id="test_admin_1",
        email="admin@test.local",
        name="Test Admin",
        roles=["admin", "operator", "viewer"]
    )
