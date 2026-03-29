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
    from app.modules.workspaces.infrastructure.persistence import models as workspace_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_manual_migrations()


def _apply_manual_migrations() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "execution_runs" not in table_names:
        return

    try:
        execution_run_columns = {
            column["name"] for column in inspect(engine).get_columns("execution_runs")
        }
    except NoSuchTableError:
        return

    if "visualization_mode" not in execution_run_columns:
        with engine.begin() as connection:
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

    if "workspace_id" not in execution_run_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE execution_runs "
                    "ADD COLUMN workspace_id VARCHAR(36)"
                )
            )


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
