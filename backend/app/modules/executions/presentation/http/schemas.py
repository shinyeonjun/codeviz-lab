from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, Field

VisualizationKind = Literal[
    "array-bars",
    "array-cells",
    "stack-vertical",
    "queue-horizontal",
    "call-stack",
    "dp-table",
    "tree-binary",
    "graph-node-edge",
]
VisualizationMode = str
VisualizationRequestMode = str


class ExecutionCreate(BaseModel):
    language: Literal["python"] = "python"
    source_code: str = Field(min_length=1)
    stdin: str = ""
    visualization_mode: VisualizationRequestMode = Field(
        default="none",
        validation_alias=AliasChoices(
            "visualization_mode",
            "visualizationMode",
        ),
    )


class ExecutionStepRead(BaseModel):
    step_index: int
    line_number: int
    event_type: str
    function_name: str
    locals_snapshot: dict[str, Any]
    stdout_snapshot: str
    error_message: str | None = None


class ExecutionVisualizationStepRead(BaseModel):
    step_index: int
    line_number: int
    values: list[int | float] = Field(default_factory=list)
    active_indices: list[int] = Field(default_factory=list, serialization_alias="activeIndices")
    matched_indices: list[int] = Field(default_factory=list, serialization_alias="matchedIndices")
    payload: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None


class ExecutionVisualizationRead(BaseModel):
    kind: VisualizationKind
    source_variable: str | None = Field(default=None, serialization_alias="sourceVariable")
    step_states: list[ExecutionVisualizationStepRead] = Field(
        default_factory=list,
        serialization_alias="stepStates",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionRead(BaseModel):
    run_id: str
    language: str
    visualization_mode: VisualizationMode = Field(
        default="none",
        serialization_alias="visualizationMode",
    )
    status: str
    source_code: str
    stdin: str
    stdout: str
    stderr: str
    error_message: str | None = None
    step_count: int
    created_at: datetime
    completed_at: datetime | None = None
    steps: list[ExecutionStepRead] = Field(default_factory=list)
    visualization: ExecutionVisualizationRead | None = None
