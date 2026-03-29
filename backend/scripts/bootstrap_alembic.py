from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, inspect

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.core.config import settings


def _has_alembic_version_table() -> bool:
    engine = create_engine(settings.database_url, future=True)
    try:
        inspector = inspect(engine)
        return "alembic_version" in inspector.get_table_names()
    finally:
        engine.dispose()


def _has_application_tables() -> bool:
    engine = create_engine(settings.database_url, future=True)
    try:
        inspector = inspect(engine)
        table_names = set(inspector.get_table_names())
        return bool(table_names & {"users", "auth_sessions", "execution_runs", "exam_attempts"})
    finally:
        engine.dispose()


def _run_alembic(*args: str) -> int:
    return subprocess.call([sys.executable, "-m", "alembic", *args])


def main() -> int:
    if _has_alembic_version_table():
        return _run_alembic("upgrade", "head")

    if _has_application_tables():
        return _run_alembic("stamp", "head")

    return _run_alembic("upgrade", "head")


if __name__ == "__main__":
    raise SystemExit(main())
