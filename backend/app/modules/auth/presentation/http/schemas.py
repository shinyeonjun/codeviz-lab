from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class WorkspaceRead(BaseModel):
    id: str
    title: str
    is_guest: bool = Field(serialization_alias="isGuest")
    created_at: datetime = Field(serialization_alias="createdAt")


class AuthUserRead(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime = Field(serialization_alias="createdAt")


class AuthSessionRead(BaseModel):
    is_authenticated: bool = Field(serialization_alias="isAuthenticated")
    is_guest: bool = Field(serialization_alias="isGuest")
    user: AuthUserRead | None = None
    current_workspace: WorkspaceRead = Field(serialization_alias="currentWorkspace")
    workspaces: list[WorkspaceRead]


class RegisterCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)


class LoginCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class WorkspaceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)


class WorkspaceSelectCreate(BaseModel):
    workspace_id: str = Field(
        validation_alias=AliasChoices("workspace_id", "workspaceId"),
        serialization_alias="workspaceId",
    )


class ExecutionActivityRead(BaseModel):
    run_id: str = Field(serialization_alias="runId")
    status: str
    visualization_mode: str = Field(serialization_alias="visualizationMode")
    source_preview: str = Field(serialization_alias="sourcePreview")
    created_at: datetime = Field(serialization_alias="createdAt")


class ExamAttemptActivityRead(BaseModel):
    attempt_id: str = Field(serialization_alias="attemptId")
    lesson_id: str = Field(serialization_alias="lessonId")
    question_id: str = Field(serialization_alias="questionId")
    status: str
    score: int
    created_at: datetime = Field(serialization_alias="createdAt")


class WorkspaceActivityRead(BaseModel):
    current_workspace: WorkspaceRead = Field(serialization_alias="currentWorkspace")
    recent_executions: list[ExecutionActivityRead] = Field(
        default_factory=list,
        serialization_alias="recentExecutions",
    )
    recent_exam_attempts: list[ExamAttemptActivityRead] = Field(
        default_factory=list,
        serialization_alias="recentExamAttempts",
    )
