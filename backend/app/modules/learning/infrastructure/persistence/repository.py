from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.learning.infrastructure.persistence.models import UserLessonProgress


class LearningProgressRepository:
    def __init__(self, *, session: Session) -> None:
        self._session = session

    def list_by_user(self, user_id: str) -> list[UserLessonProgress]:
        statement = (
            select(UserLessonProgress)
            .where(UserLessonProgress.user_id == user_id)
            .order_by(UserLessonProgress.last_studied_at.desc())
        )
        return list(self._session.execute(statement).scalars().all())

    def list_lesson_ids_by_user(self, user_id: str) -> set[str]:
        statement = select(UserLessonProgress.lesson_id).where(
            UserLessonProgress.user_id == user_id
        )
        return set(self._session.execute(statement).scalars().all())

    def mark_studied(self, *, user_id: str, lesson_id: str) -> UserLessonProgress:
        progress = self._session.get(UserLessonProgress, {"user_id": user_id, "lesson_id": lesson_id})
        studied_at = datetime.now(UTC)

        if progress is None:
            progress = UserLessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status="studied",
                first_studied_at=studied_at,
                last_studied_at=studied_at,
                study_count=1,
                total_study_seconds=0,
            )
            self._session.add(progress)
        else:
            progress.status = "studied"
            progress.last_studied_at = studied_at
            progress.study_count += 1

        self._session.commit()
        self._session.refresh(progress)
        return progress
