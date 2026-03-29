from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

from app.modules.executions.presentation.http.schemas import VisualizationMode


class ExamCategoryRead(BaseModel):
    id: str
    name: str
    description: str
    question_count: int = Field(serialization_alias="questionCount")


class ExamSessionCreate(BaseModel):
    category_id: str = Field(
        validation_alias=AliasChoices("category_id", "categoryId"),
        serialization_alias="categoryId",
    )
    question_count: int = Field(
        default=3,
        ge=1,
        le=10,
        validation_alias=AliasChoices("question_count", "questionCount"),
        serialization_alias="questionCount",
    )


class ExamQuestionRead(BaseModel):
    id: str
    lesson_id: str = Field(serialization_alias="lessonId")
    category_id: str = Field(serialization_alias="categoryId")
    category_name: str = Field(serialization_alias="categoryName")
    title: str
    prompt: str
    visualization_mode: VisualizationMode = Field(serialization_alias="visualizationMode")
    starter_code: str = Field(serialization_alias="starterCode")
    difficulty: str
    estimated_minutes: int = Field(serialization_alias="estimatedMinutes")
    tags: list[str]


class ExamSessionRead(BaseModel):
    session_id: str = Field(serialization_alias="sessionId")
    category_id: str = Field(serialization_alias="categoryId")
    category_name: str = Field(serialization_alias="categoryName")
    question_count: int = Field(serialization_alias="questionCount")
    questions: list[ExamQuestionRead]


class ExamSubmissionCreate(BaseModel):
    lesson_id: str = Field(
        validation_alias=AliasChoices("lesson_id", "lessonId"),
        serialization_alias="lessonId",
    )
    source_code: str = Field(
        min_length=1,
        validation_alias=AliasChoices("source_code", "sourceCode"),
        serialization_alias="sourceCode",
    )


class ExamCaseResultRead(BaseModel):
    case_id: str = Field(
        validation_alias=AliasChoices("case_id", "caseId"),
        serialization_alias="caseId",
    )
    passed: bool
    input_summary: str = Field(
        validation_alias=AliasChoices("input_summary", "inputSummary"),
        serialization_alias="inputSummary",
    )
    expected: Any = None
    actual: Any = None
    message: str


class ExamSubmissionRead(BaseModel):
    lesson_id: str = Field(
        validation_alias=AliasChoices("lesson_id", "lessonId"),
        serialization_alias="lessonId",
    )
    question_id: str = Field(
        validation_alias=AliasChoices("question_id", "questionId"),
        serialization_alias="questionId",
    )
    status: Literal["passed", "failed", "error", "timeout"]
    score: int
    passed_count: int = Field(
        validation_alias=AliasChoices("passed_count", "passedCount"),
        serialization_alias="passedCount",
    )
    total_count: int = Field(
        validation_alias=AliasChoices("total_count", "totalCount"),
        serialization_alias="totalCount",
    )
    error_message: str | None = Field(
        default=None,
        validation_alias=AliasChoices("error_message", "errorMessage"),
        serialization_alias="errorMessage",
    )
    results: list[ExamCaseResultRead] = Field(default_factory=list)
