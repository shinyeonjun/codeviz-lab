from functools import lru_cache

from app.modules.examples.domain.catalog import EXAMPLE_CATALOG
from app.modules.examples.presentation.http.schemas import ExampleItem


@lru_cache
def _load_examples() -> tuple[ExampleItem, ...]:
    return tuple(ExampleItem.model_validate(item) for item in EXAMPLE_CATALOG)


class ExampleService:
    def __init__(self) -> None:
        self._examples = _load_examples()

    def get_examples(self, *, language: str | None = None) -> list[ExampleItem]:
        if language is None:
            return list(self._examples)
        return [example for example in self._examples if example.language == language]


def get_example_service() -> ExampleService:
    return ExampleService()
