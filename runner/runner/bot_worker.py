from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
import traceback
from types import ModuleType
from typing import Any, Callable


def _load_module(path: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location("bot", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("invalid_bot_module")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--code-path", required=True)
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()

    random.seed(int(args.seed))

    try:
        mod = _load_module(args.code_path)
        act: Callable[[dict[str, Any], dict[str, Any]], tuple[str, dict[str, Any]]] = getattr(mod, "act")
        if not callable(act):
            raise RuntimeError("act_not_callable")
    except Exception:
        err = traceback.format_exc(limit=20)
        sys.stdout.write(json.dumps({"error": "load_failed", "detail": err}) + "\n")
        sys.stdout.flush()
        return 2

    # Protocol: newline-delimited JSON on stdin, newline-delimited JSON responses on stdout.
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            obs = msg["obs"]
            state = msg["state"]
            action, new_state = act(obs, state)
            sys.stdout.write(json.dumps({"act": action, "state": new_state}) + "\n")
            sys.stdout.flush()
        except Exception:
            err = traceback.format_exc(limit=20)
            sys.stdout.write(json.dumps({"error": "act_failed", "detail": err}) + "\n")
            sys.stdout.flush()
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

