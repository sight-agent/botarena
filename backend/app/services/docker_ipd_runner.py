from __future__ import annotations

import base64
import json
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class DockerRunConfig:
    image: str
    cpus: str = "1"
    memory: str = "256m"
    pids_limit: int = 128
    tmpfs: str = "/tmp:rw,noexec,nosuid,size=64m"
    user: str = "1000:1000"
    timeout_seconds: int = 20


@dataclass(frozen=True)
class DockerIpdResult:
    steps: list[dict]
    cum_a: int
    cum_b: int
    exec_ms_a: float = 0.0
    exec_ms_b: float = 0.0
    avg_exec_ms_a: float = 0.0
    avg_exec_ms_b: float = 0.0
    error_log: str | None = None


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def run_ipd_in_docker(*, cfg: DockerRunConfig, bot_a_code: str, bot_b_code: str, seed: int) -> DockerIpdResult:
    payload = {
        "bot_a_b64": _b64(bot_a_code),
        "bot_b_b64": _b64(bot_b_code),
        "seed": int(seed),
    }

    cmd = [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        cfg.tmpfs,
        "--user",
        cfg.user,
        "--pids-limit",
        str(cfg.pids_limit),
        "--cpus",
        cfg.cpus,
        "--memory",
        cfg.memory,
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        cfg.image,
        "python",
        "-I",
        "-c",
        "import sys,runpy; sys.path.insert(0,'/app'); runpy.run_module('runner.harness', run_name='__main__')",
    ]

    try:
        p = subprocess.run(
            cmd,
            input=json.dumps(payload).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=cfg.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return DockerIpdResult(steps=[], cum_a=0, cum_b=0, error_log="docker_timeout")

    if p.returncode != 0:
        err = (p.stderr or b"").decode("utf-8", errors="replace")[:65536]
        out = (p.stdout or b"").decode("utf-8", errors="replace")[:65536]
        return DockerIpdResult(steps=[], cum_a=0, cum_b=0, error_log=f"docker_failed rc={p.returncode}\n{err}\n{out}")

    try:
        body = json.loads((p.stdout or b"{}").decode("utf-8"))
        return DockerIpdResult(
            steps=list(body.get("steps") or []),
            cum_a=int(body["cum_a"]),
            cum_b=int(body["cum_b"]),
            exec_ms_a=float(body.get("exec_ms_a") or 0.0),
            exec_ms_b=float(body.get("exec_ms_b") or 0.0),
            avg_exec_ms_a=float(body.get("avg_exec_ms_a") or 0.0),
            avg_exec_ms_b=float(body.get("avg_exec_ms_b") or 0.0),
            error_log=body.get("error_log"),
        )
    except Exception as e:  # noqa: BLE001
        out = (p.stdout or b"").decode("utf-8", errors="replace")[:65536]
        err = (p.stderr or b"").decode("utf-8", errors="replace")[:65536]
        return DockerIpdResult(steps=[], cum_a=0, cum_b=0, error_log=f"invalid_runner_output: {e}\n{err}\n{out}")

