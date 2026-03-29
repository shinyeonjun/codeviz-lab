from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.exams.infrastructure.persistence.models import ExamAttempt
from app.modules.exams.presentation.http.schemas import ExamSubmissionRead


class ExamAttemptRepository:
    def __init__(self, *, session: Session) -> None:
        self._session = session

    def save_attempt(
        self,
        *,
        user_id: str,
        source_code: str,
        submission: ExamSubmissionRead,
    ) -> None:
        attempt = ExamAttempt(
            id=str(uuid4()),
            user_id=user_id,
            lesson_id=submission.lesson_id,
            question_id=submission.question_id,
            source_code=source_code,
            status=submission.status,
            score=submission.score,
            passed_count=submission.passed_count,
            total_count=submission.total_count,
            error_message=submission.error_message,
            result_payload=submission.model_dump(mode="json", by_alias=True),
        )
        self._session.add(attempt)
        self._session.commit()

    def list_recent_attempts(self, *, user_id: str, limit: int = 5) -> list[ExamAttempt]:
        statement = (
            select(ExamAttempt)
            .where(ExamAttempt.user_id == user_id)
            .order_by(ExamAttempt.created_at.desc())
            .limit(limit)
        )
        return list(self._session.execute(statement).scalars().all())
