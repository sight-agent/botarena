from datetime import datetime

from pydantic import BaseModel, Field


class BotVersionOut(BaseModel):
    id: int
    version_num: int
    code: str
    created_at: datetime


class BotOut(BaseModel):
    id: int
    name: str
    description: str | None
    submitted_env: str | None = None
    active_version_id: int | None
    created_at: datetime
    updated_at: datetime


class BotWithVersionsOut(BotOut):
    versions: list[BotVersionOut]


class BotCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    code: str = Field(min_length=1)


class BotVersionCreateIn(BaseModel):
    code: str = Field(min_length=1)


class SetActiveVersionIn(BaseModel):
    version_id: int

