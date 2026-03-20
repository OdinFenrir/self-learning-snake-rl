from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time


DEFAULT_TARGETS = [
    "tests/test_app_actions.py",
    "tests/test_model_manager.py",
    "tests/test_persistence.py",
    "tests/test_state_io_recovery.py",
    "tests/test_training_controller.py",
    "tests/test_ppo_agent_seed.py",
    "tests/test_ppo_callback.py",
    "tests/test_live_artifacts.py",
    "tests/test_report_contracts.py",
    "tests/test_agent_performance_report.py",
    "tests/test_analysis_tool_orchestration.py",
    "tests/test_e2e_smoke.py::TestE2ESmoke::test_training_inference_handoff_and_gameplay_steps",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a short reliability gate for multi-model save/load/report flows."
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=5,
        help="How many repeated cycles to run for the quick gate (default: 5).",
    )
    parser.add_argument(
        "--full-suite",
        action="store_true",
        help="Run full pytest suite after quick-gate cycles.",
    )
    parser.add_argument(
        "--python",
        type=str,
        default="",
        help="Python executable to use (default: current interpreter).",
    )
    parser.add_argument(
        "--targets",
        nargs="*",
        default=DEFAULT_TARGETS,
        help="Optional explicit pytest targets.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Use verbose pytest output.",
    )
    return parser.parse_args()


def _run_pytest(
    python_exe: str,
    root: Path,
    targets: list[str],
    verbose: bool,
) -> subprocess.CompletedProcess[str]:
    q_flag = "-vv" if verbose else "-q"
    cmd = [python_exe, "-m", "pytest", q_flag, *targets]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    return subprocess.run(
        cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
        env=env,
    )


def _print_tail(text: str, n: int = 8) -> str:
    lines = [ln for ln in str(text or "").splitlines() if ln.strip()]
    if not lines:
        return ""
    return "\n".join(lines[-n:])


def main() -> int:
    args = _parse_args()
    if int(args.cycles) < 1:
        print("ERROR: --cycles must be >= 1")
        return 2
    root = Path(__file__).resolve().parents[1]
    python_exe = str(args.python).strip() or sys.executable
    targets = [str(t) for t in list(args.targets or []) if str(t).strip()]
    if not targets:
        print("ERROR: no pytest targets provided")
        return 2

    started = time.perf_counter()
    print(f"quick_gate: python={python_exe}")
    print(f"quick_gate: cycles={int(args.cycles)} targets={len(targets)}")
    for idx in range(1, int(args.cycles) + 1):
        tick = time.perf_counter()
        res = _run_pytest(python_exe, root, targets, bool(args.verbose))
        took = time.perf_counter() - tick
        if res.returncode != 0:
            print(f"[FAIL] cycle {idx}/{int(args.cycles)} in {took:.2f}s")
            out = _print_tail(res.stdout)
            err = _print_tail(res.stderr)
            if out:
                print("stdout tail:")
                print(out)
            if err:
                print("stderr tail:")
                print(err)
            return int(res.returncode)
        print(f"[PASS] cycle {idx}/{int(args.cycles)} in {took:.2f}s")

    if bool(args.full_suite):
        print("quick_gate: running full suite...")
        tick = time.perf_counter()
        res = _run_pytest(python_exe, root, [], bool(args.verbose))
        took = time.perf_counter() - tick
        if res.returncode != 0:
            print(f"[FAIL] full suite in {took:.2f}s")
            out = _print_tail(res.stdout)
            err = _print_tail(res.stderr)
            if out:
                print("stdout tail:")
                print(out)
            if err:
                print("stderr tail:")
                print(err)
            return int(res.returncode)
        print(f"[PASS] full suite in {took:.2f}s")

    total = time.perf_counter() - started
    print(f"quick_gate: PASS in {total:.2f}s")
    print("quick_gate: no artifacts created by this script (pytest cache behavior unchanged).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
