from typing import Literal

from pydantic import BaseModel


class HealthPayload(BaseModel):
    name: str
    version: str
    status: Literal["ok"]
