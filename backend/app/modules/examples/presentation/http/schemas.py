from pydantic import BaseModel


class ExampleItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    language: str
    source_code: str
    focus_points: list[str]
