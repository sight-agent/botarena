from datetime import datetime

from pydantic import BaseModel, Field


class BotOut(BaseModel):
    id: int
    env_id: str
    name: str
    description: str | None
    submitted: bool
    created_at: datetime
    updated_at: datetime


class BotDetailOut(BotOut):
    code: str


class BotCreateIn(BaseModel):
    env_id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    code: str = Field(min_length=1)


class BotUpdateCodeIn(BaseModel):
    code: str = Field(min_length=1)

