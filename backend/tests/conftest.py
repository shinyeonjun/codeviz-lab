import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

TEST_DATABASE_HOST = os.getenv("TEST_DATABASE_HOST", "127.0.0.1")
TEST_DATABASE_PORT = os.getenv("TEST_DATABASE_PORT", "55433")
TEST_DATABASE_USER = os.getenv("TEST_DATABASE_USER", "codeviz")
TEST_DATABASE_PASSWORD = os.getenv("TEST_DATABASE_PASSWORD", "codeviz")
TEST_DATABASE_ADMIN_DB = os.getenv("TEST_DATABASE_ADMIN_DB", "postgres")
TEST_DATABASE_NAME = f"codeviz_test_{uuid4().hex}"
TEST_DATABASE_ADMIN_URL = os.getenv(
    "TEST_DATABASE_ADMIN_URL",
    (
        "postgresql+psycopg://"
        f"{TEST_DATABASE_USER}:{TEST_DATABASE_PASSWORD}"
        f"@{TEST_DATABASE_HOST}:{TEST_DATABASE_PORT}/{TEST_DATABASE_ADMIN_DB}"
    ),
)
TEST_DATABASE_URL = (
    "postgresql+psycopg://"
    f"{TEST_DATABASE_USER}:{TEST_DATABASE_PASSWORD}"
    f"@{TEST_DATABASE_HOST}:{TEST_DATABASE_PORT}/{TEST_DATABASE_NAME}"
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["RUNNER_TIMEOUT_SECONDS"] = "2"
os.environ["RUNNER_BACKEND"] = "local"

from app.core.database import Base, create_database, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.modules.executions import models  # noqa: F401, E402


def _create_test_database() -> None:
    admin_engine = create_engine(TEST_DATABASE_ADMIN_URL, future=True, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'))
    finally:
        admin_engine.dispose()


def _drop_test_database() -> None:
    admin_engine = create_engine(TEST_DATABASE_ADMIN_URL, future=True, isolation_level="AUTOCOMMIT")
    try:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) "
                    "FROM pg_stat_activity "
                    "WHERE datname = :database_name AND pid <> pg_backend_pid()"
                ),
                {"database_name": TEST_DATABASE_NAME},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DATABASE_NAME}"'))
    finally:
        admin_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    _drop_test_database()
    _create_test_database()
    create_database()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    _drop_test_database()


@pytest.fixture(autouse=True)
def clean_database():
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def authenticated_client(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"tester-{uuid4().hex[:8]}@example.com",
            "password": "password123!",
            "name": "테스터",
        },
    )
    assert response.status_code == 201
    return client
