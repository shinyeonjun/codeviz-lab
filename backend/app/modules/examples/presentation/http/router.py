from fastapi import APIRouter, Depends, Query

from app.common.responses import success_response
from app.modules.examples.application.services.example_service import (
    ExampleService,
    get_example_service,
)
from app.modules.examples.presentation.http.schemas import ExampleItem

router = APIRouter()


@router.get("")
def read_examples(
    language: str | None = Query(default=None),
    service: ExampleService = Depends(get_example_service),
) -> dict[str, object]:
    examples: list[ExampleItem] = service.get_examples(language=language)
    return success_response([example.model_dump() for example in examples])
