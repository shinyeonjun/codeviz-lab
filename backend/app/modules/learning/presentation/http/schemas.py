from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.modules.executions.presentation.http.schemas import VisualizationMode


class LearningCategoryRead(BaseModel):
    id: str
    name: str
    description: str
    order: int
    lesson_count: int = Field(serialization_alias="lessonCount")
    visualization_modes: list[VisualizationMode] = Field(serialization_alias="visualizationModes")


class LearningProgressRead(BaseModel):
    lesson_id: str = Field(serialization_alias="lessonId")
    status: Literal["studied", "completed"]
    first_studied_at: datetime = Field(serialization_alias="firstStudiedAt")
    last_studied_at: datetime = Field(serialization_alias="lastStudiedAt")
    study_count: int = Field(serialization_alias="studyCount")
    total_study_seconds: int = Field(serialization_alias="totalStudySeconds")
    completed_at: datetime | None = Field(default=None, serialization_alias="completedAt")


class LearningLessonSummaryRead(BaseModel):
    id: str
    title: str
    category_id: str = Field(serialization_alias="categoryId")
    category_name: str = Field(serialization_alias="categoryName")
    description: str
    language: Literal["python", "c", "java"]
    supported_languages: list[Literal["python", "c", "java"]] = Field(
        default_factory=lambda: ["python", "c", "java"],
        serialization_alias="supportedLanguages",
    )
    visualization_mode: VisualizationMode = Field(serialization_alias="visualizationMode")
    difficulty: str
    estimated_minutes: int = Field(serialization_alias="estimatedMinutes")
    tags: list[str]
    progress: LearningProgressRead | None = None


class LearningContentRead(BaseModel):
    title: str
    summary: str
    concept_points: list[str] = Field(serialization_alias="conceptPoints")
    walkthrough_code: str = Field(serialization_alias="walkthroughCode")


class LearningChallengeRead(BaseModel):
    title: str
    prompt: str
    starter_code: str = Field(serialization_alias="starterCode")
    checkpoints: list[str]


class LearningLessonRead(LearningLessonSummaryRead):
    learning_points: list[str] = Field(serialization_alias="learningPoints")
    source_code: str = Field(serialization_alias="sourceCode")
    learning_content: LearningContentRead = Field(serialization_alias="learningContent")
    implementation_challenge: LearningChallengeRead = Field(serialization_alias="implementationChallenge")
    previous_lesson_id: str | None = Field(default=None, serialization_alias="previousLessonId")
    next_lesson_id: str | None = Field(default=None, serialization_alias="nextLessonId")
    related_lesson_ids: list[str] = Field(default_factory=list, serialization_alias="relatedLessonIds")


class LearningCategoryProgressRead(BaseModel):
    category_id: str = Field(serialization_alias="categoryId")
    category_name: str = Field(serialization_alias="categoryName")
    studied_count: int = Field(serialization_alias="studiedCount")
    total_count: int = Field(serialization_alias="totalCount")
    completion_rate: float = Field(serialization_alias="completionRate")
    next_lesson_id: str | None = Field(default=None, serialization_alias="nextLessonId")


class LearningRecommendationRead(BaseModel):
    lesson: LearningLessonSummaryRead
    reason: str


class LearningInsightRead(BaseModel):
    total_lessons: int = Field(serialization_alias="totalLessons")
    studied_lessons: int = Field(serialization_alias="studiedLessons")
    completion_rate: float = Field(serialization_alias="completionRate")
    category_progress: list[LearningCategoryProgressRead] = Field(serialization_alias="categoryProgress")
    weak_categories: list[LearningCategoryProgressRead] = Field(serialization_alias="weakCategories")
    next_recommendations: list[LearningRecommendationRead] = Field(serialization_alias="nextRecommendations")
    review_recommendations: list[LearningRecommendationRead] = Field(serialization_alias="reviewRecommendations")
    daily_recommendation: LearningRecommendationRead | None = Field(
        default=None,
        serialization_alias="dailyRecommendation",
    )
