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


class LearningLessonSummaryRead(BaseModel):
    id: str
    title: str
    category_id: str = Field(serialization_alias="categoryId")
    category_name: str = Field(serialization_alias="categoryName")
    description: str
    language: Literal["python"]
    visualization_mode: VisualizationMode = Field(serialization_alias="visualizationMode")
    difficulty: str
    estimated_minutes: int = Field(serialization_alias="estimatedMinutes")
    tags: list[str]


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
