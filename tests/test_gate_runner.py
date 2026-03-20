from __future__ import annotations

from subprocess import CompletedProcess
from unittest.mock import patch

from snake_frame.gate_runner import run_quick_gate, run_quick_gate_detailed


def test_run_quick_gate_detailed_pass() -> None:
    with patch(
        "snake_frame.gate_runner.subprocess.run",
        return_value=CompletedProcess(args=["python"], returncode=0, stdout="ok\nline2\n", stderr=""),
    ) as run_mock:
        result = run_quick_gate_detailed(cycles=2, timeout_seconds=10.0)
    assert result.ok
    assert result.returncode == 0
    assert "ok" in result.stdout_tail
    called_args = run_mock.call_args.args[0]
    assert "--cycles" in called_args
    idx = called_args.index("--cycles")
    assert called_args[idx + 1] == "2"


def test_run_quick_gate_detailed_fail() -> None:
    with patch(
        "snake_frame.gate_runner.subprocess.run",
        return_value=CompletedProcess(args=["python"], returncode=3, stdout="", stderr="boom"),
    ):
        result = run_quick_gate_detailed(cycles=1)
    assert not result.ok
    assert result.returncode == 3
    assert "boom" in result.stderr_tail


def test_run_quick_gate_returns_boolean() -> None:
    with patch("snake_frame.gate_runner.run_quick_gate_detailed") as detailed:
        detailed.return_value = type("R", (), {"ok": True})()
        assert run_quick_gate(cycles=1)
        detailed.return_value = type("R", (), {"ok": False})()
        assert not run_quick_gate(cycles=1)

