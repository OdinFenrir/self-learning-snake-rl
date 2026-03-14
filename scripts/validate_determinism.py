from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from snake_frame.smoke_runner import run_headless_smoke  # noqa: E402


def _default_window(value: float) -> dict[str, float]:
    margin = max(1.0, abs(float(value)) * 0.25)
    return {"min": float(value - margin), "max": float(value + margin)}


def _check_windows(metrics: dict, windows: dict[str, dict[str, float]]) -> list[str]:
    failures: list[str] = []
    for key, bounds in windows.items():
        if key not in metrics:
            failures.append(f"missing metric '{key}'")
            continue
        val = float(metrics[key])
        lower = float(bounds["min"])
        upper = float(bounds["max"])
        if val < lower or val > upper:
            failures.append(f"{key}={val:.4f} outside [{lower:.4f}, {upper:.4f}]")
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(description="Run fixed-seed deterministic smoke validation against baseline windows.")
    parser.add_argument("--baseline", type=str, default="tests/baselines/deterministic_windows.json")
    parser.add_argument("--update-baseline", action="store_true")
    parser.add_argument("--seed", type=int, default=1337)
    parser.add_argument("--train-steps", type=int, default=2048)
    parser.add_argument("--game-steps", type=int, default=300)
    args = parser.parse_args()

    metrics = run_headless_smoke(
        train_steps=int(args.train_steps),
        game_steps=int(args.game_steps),
        seed=int(args.seed),
        budgets=None,
    )
    baseline_path = Path(args.baseline)
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    tracked = {
        "training_avg20": float(metrics["training_avg20"]),
        "training_best": float(metrics["training_best"]),
        "run_avg20": float(metrics["run_avg20"]),
        "run_best": float(metrics["run_best"]),
        "train_steps_done": float(metrics["train_steps_done"]),
    }

    if args.update_baseline or not baseline_path.exists():
        payload = {
            "seed": int(args.seed),
            "train_steps": int(args.train_steps),
            "game_steps": int(args.game_steps),
            "metric_windows": {k: _default_window(v) for k, v in tracked.items()},
        }
        baseline_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Baseline updated: {baseline_path}")
        return

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    windows = baseline.get("metric_windows", {})
    failures = _check_windows(tracked, windows)
    if failures:
        print("Deterministic validation failures:")
        for item in failures:
            print(f"- {item}")
        raise SystemExit(1)
    print("Deterministic validation passed.")


if __name__ == "__main__":
    main()
