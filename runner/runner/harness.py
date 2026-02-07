from __future__ import annotations

import base64
import json
import os
import select
import subprocess
import sys
import time
from typing import Any, Literal

Action = Literal["C", "D"]

ROUNDS = 200
MAX_STEP_MS = 50  # per bot call wall-clock
MAX_MATCH_MS = 15000
MAX_LOG_BYTES = 64 * 1024

PAYOFF: dict[tuple[Action, Action], tuple[int, int]] = {
    ("C", "C"): (3, 3),
    ("D", "C"): (5, 0),
    ("C", "D"): (0, 5),
    ("D", "D"): (1, 1),
}


def is_valid_action(x: Any) -> bool:
    return x in ("C", "D")


def observation(*, round_num: int, history: list[list[Action]]) -> dict[str, Any]:
    return {"round": round_num, "max_rounds": ROUNDS, "history": history}


def _ensure_jsonable(x: Any) -> None:
    json.dumps(x)


def _readline_timeout(pipe, timeout_s: float) -> str | None:
    r, _, _ = select.select([pipe], [], [], timeout_s)
    if not r:
        return None
    line = pipe.readline()
    if not line:
        return ""
    return line


def _truncate(s: str, limit: int = MAX_LOG_BYTES) -> str:
    if len(s) <= limit:
        return s
    return s[:limit] + "\n...truncated..."


def _bot_proc(*, code_path: str, seed: int) -> subprocess.Popen:
    # Run isolated python (-I), no site packages, no user env.
    # Python isolated mode (-I) doesn't reliably include WORKDIR on sys.path.
    # We explicitly add /app so `runner.*` imports work inside the sandbox image.
    return subprocess.Popen(
        [
            "python",
            "-I",
            "-u",
            "-c",
            (
                "import sys,runpy; "
                "sys.path.insert(0,'/app'); "
                f"sys.argv=['runner.bot_worker','--code-path','{code_path}','--seed','{seed}']; "
                "runpy.run_module('runner.bot_worker', run_name='__main__')"
            ),
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        bot_a_b64 = payload["bot_a_b64"]
        bot_b_b64 = payload["bot_b_b64"]
        seed = int(payload["seed"])
    except Exception:
        sys.stdout.write(json.dumps({"error_log": "invalid_input"}) + "\n")
        return 2

    os.makedirs("/tmp", exist_ok=True)
    path_a = "/tmp/bot_a.py"
    path_b = "/tmp/bot_b.py"

    try:
        code_a = base64.b64decode(bot_a_b64.encode("ascii"), validate=True).decode("utf-8")
        code_b = base64.b64decode(bot_b_b64.encode("ascii"), validate=True).decode("utf-8")
    except Exception:
        sys.stdout.write(json.dumps({"error_log": "invalid_base64"}) + "\n")
        return 2

    with open(path_a, "w", encoding="utf-8") as f:
        f.write(code_a)
    with open(path_b, "w", encoding="utf-8") as f:
        f.write(code_b)

    start = time.monotonic()

    p_a = _bot_proc(code_path=path_a, seed=seed)
    p_b = _bot_proc(code_path=path_b, seed=seed + 1)

    try:
        # If load fails, bot_worker prints a JSON error line then exits nonzero.
        for p in (p_a, p_b):
            line = _readline_timeout(p.stdout, 1.0)  # type: ignore[arg-type]
            if line and line.strip().startswith('{"error"'):
                err = line.strip()
                sys.stdout.write(json.dumps({"error_log": _truncate(err)}) + "\n")
                return 3

        history: list[list[Action]] = []
        steps: list[dict[str, Any]] = []
        cum_a = 0
        cum_b = 0
        st_a: dict[str, Any] = {}
        st_b: dict[str, Any] = {}

        for r in range(1, ROUNDS + 1):
            if (time.monotonic() - start) * 1000 > MAX_MATCH_MS:
                sys.stdout.write(json.dumps({"error_log": "match_timeout"}) + "\n")
                return 4

            obs = observation(round_num=r, history=list(history))
            msg_a = json.dumps({"obs": obs, "state": st_a}) + "\n"
            msg_b = json.dumps({"obs": obs, "state": st_b}) + "\n"

            assert p_a.stdin is not None and p_b.stdin is not None
            p_a.stdin.write(msg_a)
            p_a.stdin.flush()
            p_b.stdin.write(msg_b)
            p_b.stdin.flush()

            line_a = _readline_timeout(p_a.stdout, MAX_STEP_MS / 1000)  # type: ignore[arg-type]
            line_b = _readline_timeout(p_b.stdout, MAX_STEP_MS / 1000)  # type: ignore[arg-type]
            if line_a is None or line_b is None:
                sys.stdout.write(json.dumps({"error_log": "step_timeout"}) + "\n")
                return 4
            if line_a == "" or line_b == "":
                sys.stdout.write(json.dumps({"error_log": "bot_exited"}) + "\n")
                return 4

            resp_a = json.loads(line_a)
            resp_b = json.loads(line_b)
            if "error" in resp_a:
                sys.stdout.write(json.dumps({"error_log": _truncate(resp_a.get("detail", "bot_a_error"))}) + "\n")
                return 5
            if "error" in resp_b:
                sys.stdout.write(json.dumps({"error_log": _truncate(resp_b.get("detail", "bot_b_error"))}) + "\n")
                return 5

            act_a = resp_a.get("act")
            act_b = resp_b.get("act")
            st_a2 = resp_a.get("state")
            st_b2 = resp_b.get("state")

            if not is_valid_action(act_a) or not is_valid_action(act_b):
                sys.stdout.write(json.dumps({"error_log": "invalid_action"}) + "\n")
                return 6

            _ensure_jsonable(st_a2)
            _ensure_jsonable(st_b2)

            st_a = st_a2
            st_b = st_b2

            ra, rb = PAYOFF[(act_a, act_b)]
            cum_a += ra
            cum_b += rb

            steps.append(
                {
                    "round": r,
                    "obs_a": obs,
                    "act_a": act_a,
                    "obs_b": obs,
                    "act_b": act_b,
                    "reward_a": ra,
                    "reward_b": rb,
                    "cum_a": cum_a,
                    "cum_b": cum_b,
                }
            )
            history.append([act_a, act_b])

        sys.stdout.write(json.dumps({"steps": steps, "cum_a": cum_a, "cum_b": cum_b}) + "\n")
        return 0
    finally:
        for p in (p_a, p_b):
            try:
                p.kill()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())

