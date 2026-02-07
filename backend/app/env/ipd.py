from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Literal

Action = Literal["C", "D"]

ROUNDS = 200

# Standard IPD payoff matrix.
# (act_a, act_b) -> (reward_a, reward_b)
PAYOFF: dict[tuple[Action, Action], tuple[int, int]] = {
    ("C", "C"): (3, 3),
    ("D", "C"): (5, 0),
    ("C", "D"): (0, 5),
    ("D", "D"): (1, 1),
}


def is_valid_action(x: Any) -> bool:
    return x in ("C", "D")


def payoff(act_a: Action, act_b: Action) -> tuple[int, int]:
    return PAYOFF[(act_a, act_b)]


def observation(*, round_num: int, history: list[list[Action]]) -> dict[str, Any]:
    # JSON-serializable structure. (Tuples are avoided on purpose.)
    return {"round": round_num, "max_rounds": ROUNDS, "history": history}


def _ensure_jsonable(x: Any) -> None:
    # Used for bot state validation; raises TypeError on failure.
    json.dumps(x)


@dataclass(frozen=True)
class Step:
    round: int
    obs_a: dict[str, Any]
    act_a: Action
    obs_b: dict[str, Any]
    act_b: Action
    reward_a: int
    reward_b: int
    cum_a: int
    cum_b: int


@dataclass(frozen=True)
class RunResult:
    steps: list[Step]
    cum_a: int
    cum_b: int


Policy = Callable[[dict[str, Any], dict[str, Any]], tuple[Action, dict[str, Any]]]


def run_policies(
    policy_a: Policy,
    policy_b: Policy,
    *,
    rounds: int = ROUNDS,
    state_a: dict[str, Any] | None = None,
    state_b: dict[str, Any] | None = None,
) -> RunResult:
    """
    Deterministic, in-process IPD runner (no sandbox). Used for unit tests and logic validation.
    """
    history: list[list[Action]] = []
    steps: list[Step] = []
    cum_a = 0
    cum_b = 0
    st_a: dict[str, Any] = {} if state_a is None else dict(state_a)
    st_b: dict[str, Any] = {} if state_b is None else dict(state_b)

    for r in range(1, rounds + 1):
        obs_a = observation(round_num=r, history=list(history))
        obs_b = observation(round_num=r, history=list(history))

        act_a, st_a2 = policy_a(obs_a, st_a)
        act_b, st_b2 = policy_b(obs_b, st_b)

        if not is_valid_action(act_a) or not is_valid_action(act_b):
            raise ValueError("invalid_action")

        _ensure_jsonable(st_a2)
        _ensure_jsonable(st_b2)

        st_a = st_a2
        st_b = st_b2

        ra, rb = payoff(act_a, act_b)
        cum_a += ra
        cum_b += rb

        steps.append(
            Step(
                round=r,
                obs_a=obs_a,
                act_a=act_a,
                obs_b=obs_b,
                act_b=act_b,
                reward_a=ra,
                reward_b=rb,
                cum_a=cum_a,
                cum_b=cum_b,
            )
        )
        history.append([act_a, act_b])

    return RunResult(steps=steps, cum_a=cum_a, cum_b=cum_b)

