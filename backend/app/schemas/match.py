from datetime import datetime

from pydantic import BaseModel


class MatchStepOut(BaseModel):
    round: int
    obs_a: dict
    act_a: str
    obs_b: dict
    act_b: str
    reward_a: int
    reward_b: int
    cum_a: int
    cum_b: int


class MatchOut(BaseModel):
    id: int
    env_id: str
    bot_id: int
    bot_code_hash: str
    opponent_name: str
    seed: int
    status: str
    started_at: datetime
    finished_at: datetime | None
    error_log: str | None
    steps: list[MatchStepOut]


class RunTestOut(BaseModel):
    match_id: int
    cum_a: int
    cum_b: int

