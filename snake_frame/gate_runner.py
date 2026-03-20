from __future__ import annotations

from dataclasses import dataclass
import subprocess
import sys
from pathlib import Path


@dataclass(frozen=True)
class GateResult:
    ok: bool
    command: list[str]
    returncode: int
    stdout_tail: str
    stderr_tail: str


def _tail(text: str, lines: int = 6) -> str:
    data = [ln for ln in str(text or "").splitlines() if ln.strip()]
    if not data:
        return ""
    return "\n".join(data[-lines:])


def run_quick_gate_detailed(cycles: int = 3, timeout_seconds: float = 600.0) -> GateResult:
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "quick_gate.py"
    count = max(1, int(cycles))
    cmd = [sys.executable, str(script), "--cycles", str(count)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=max(5.0, float(timeout_seconds)),
        )
    except Exception as exc:
        return GateResult(
            ok=False,
            command=cmd,
            returncode=-1,
            stdout_tail="",
            stderr_tail=f"{type(exc).__name__}: {exc}",
        )
    return GateResult(
        ok=proc.returncode == 0,
        command=cmd,
        returncode=int(proc.returncode),
        stdout_tail=_tail(proc.stdout),
        stderr_tail=_tail(proc.stderr),
    )


def run_quick_gate(cycles: int = 3, timeout_seconds: float = 600.0) -> bool:
    return bool(run_quick_gate_detailed(cycles=cycles, timeout_seconds=timeout_seconds).ok)

