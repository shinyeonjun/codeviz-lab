from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def create_database() -> None:
    from app.modules.auth.infrastructure.persistence import models  # noqa: F401
    from app.modules.exams.infrastructure.persistence import models as exam_models  # noqa: F401
    from app.modules.executions.infrastructure.persistence import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_manual_migrations()


def _apply_manual_migrations() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "execution_runs" in table_names:
        _migrate_execution_runs(inspector)
    if "execution_steps" in table_names:
        _migrate_execution_steps(inspector)
    if "exam_attempts" in table_names:
        _migrate_exam_attempts(inspector)
    if "auth_sessions" in table_names:
        _migrate_auth_sessions(inspector)


def _migrate_execution_runs(inspector) -> None:
    try:
        execution_run_columns = {
            column["name"] for column in inspector.get_columns("execution_runs")
        }
    except NoSuchTableError:
        return

    with engine.begin() as connection:
        if "visualization_mode" not in execution_run_columns:
            connection.execute(
                text(
                    "ALTER TABLE execution_runs "
                    "ADD COLUMN visualization_mode VARCHAR(50) NOT NULL DEFAULT 'none'"
                )
            )
            if "algorithm_key" in execution_run_columns:
                connection.execute(
                    text(
                        "UPDATE execution_runs "
                        "SET visualization_mode = CASE "
                        "WHEN algorithm_key IN ('insertion-sort', 'bubble-sort', 'binary-search') THEN 'array-bars' "
                        "ELSE 'none' "
                        "END "
                        "WHERE visualization_mode IS NULL OR visualization_mode = 'none'"
                    )
                )

        if "user_id" not in execution_run_columns:
            connection.execute(
                text(
                    "ALTER TABLE execution_runs "
                    "ADD COLUMN user_id VARCHAR(36)"
                )
            )


def _migrate_exam_attempts(inspector) -> None:
    try:
        exam_attempt_columns = {
            column["name"]: column for column in inspector.get_columns("exam_attempts")
        }
    except NoSuchTableError:
        return

    with engine.begin() as connection:
        if "user_id" not in exam_attempt_columns:
            connection.execute(
                text(
                    "ALTER TABLE exam_attempts "
                    "ADD COLUMN user_id VARCHAR(36)"
                )
            )

        workspace_column = exam_attempt_columns.get("workspace_id")
        if workspace_column and not workspace_column.get("nullable", True):
            connection.execute(
                text(
                    "ALTER TABLE exam_attempts "
                    "ALTER COLUMN workspace_id DROP NOT NULL"
                )
            )


def _migrate_auth_sessions(inspector) -> None:
    try:
        auth_session_columns = {
            column["name"]: column for column in inspector.get_columns("auth_sessions")
        }
    except NoSuchTableError:
        return

    workspace_column = auth_session_columns.get("workspace_id")
    if workspace_column and not workspace_column.get("nullable", True):
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE auth_sessions "
                    "ALTER COLUMN workspace_id DROP NOT NULL"
                )
            )


def _migrate_execution_steps(inspector) -> None:
    try:
        execution_step_columns = {
            column["name"] for column in inspector.get_columns("execution_steps")
        }
    except NoSuchTableError:
        return

    with engine.begin() as connection:
        if "globals_snapshot" not in execution_step_columns:
            connection.execute(
                text(
                    "ALTER TABLE execution_steps "
                    "ADD COLUMN globals_snapshot JSON NOT NULL DEFAULT '{}'::json"
                )
            )
        if "call_stack" not in execution_step_columns:
            connection.execute(
                text(
                    "ALTER TABLE execution_steps "
                    "ADD COLUMN call_stack JSON NOT NULL DEFAULT '[]'::json"
                )
            )
        if "metadata" not in execution_step_columns:
            connection.execute(
                text(
                    "ALTER TABLE execution_steps "
                    "ADD COLUMN metadata JSON NOT NULL DEFAULT '{}'::json"
                )
            )


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
