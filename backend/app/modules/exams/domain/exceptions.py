class ExamCategoryNotFoundError(ValueError):
    def __init__(self, category_id: str) -> None:
        super().__init__(f"시험 카테고리를 찾을 수 없습니다: {category_id}")
        self.category_id = category_id


class ExamLessonNotFoundError(ValueError):
    def __init__(self, lesson_id: str) -> None:
        super().__init__(f"시험 문제를 찾을 수 없습니다: {lesson_id}")
        self.lesson_id = lesson_id


class ExamAssessmentNotConfiguredError(ValueError):
    def __init__(self, lesson_id: str) -> None:
        super().__init__(f"시험 채점 정보가 설정되지 않았습니다: {lesson_id}")
        self.lesson_id = lesson_id
