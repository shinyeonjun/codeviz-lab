class LearningLessonNotFoundError(Exception):
    def __init__(self, lesson_id: str) -> None:
        super().__init__(f"학습 콘텐츠를 찾을 수 없습니다: {lesson_id}")
        self.lesson_id = lesson_id
