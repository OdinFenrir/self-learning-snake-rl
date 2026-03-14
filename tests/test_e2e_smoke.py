from __future__ import annotations

import unittest

from snake_frame.smoke_runner import run_headless_smoke


def _missing_ml_dependencies() -> list[str]:
    missing: list[str] = []
    for module_name in ("torch", "stable_baselines3"):
        try:
            __import__(module_name)
        except Exception as exc:  # pragma: no cover - env-dependent import gate
            missing.append(f"{module_name}: {exc}")
    return missing


class TestE2ESmoke(unittest.TestCase):
    def test_training_inference_handoff_and_gameplay_steps(self) -> None:
        missing = _missing_ml_dependencies()
        if missing:
            self.fail(
                "Headless smoke requires ML dependencies. "
                "Install with `pip install -r requirements.txt`. "
                f"Missing/failed imports: {', '.join(missing)}"
            )
        metrics = run_headless_smoke(
            train_steps=1024,
            game_steps=120,
            timeout_seconds=120.0,
            seed=1337,
            budgets=None,
        )
        self.assertGreaterEqual(int(metrics["train_steps_target_effective"]), int(metrics["train_steps_target"]))
        self.assertGreaterEqual(int(metrics["train_step_granularity"]), 1)
        self.assertGreaterEqual(int(metrics["train_steps_done"]), 1000)
        self.assertGreaterEqual(int(metrics["train_steps_done"]), int(metrics["train_steps_target_effective"]))
        self.assertLess(int(metrics["train_steps_done"]) - int(metrics["train_steps_target_effective"]), int(metrics["train_step_granularity"]))
        self.assertGreaterEqual(len(metrics["run_episode_scores"]), 0)
        self.assertGreaterEqual(float(metrics["inference_step_ms_p95"]), 0.0)
        self.assertGreaterEqual(float(metrics["frame_ms_p95"]), 0.0)
        self.assertGreaterEqual(float(metrics["frame_ms_avg"]), 0.0)
        self.assertGreaterEqual(float(metrics["frame_ms_jitter"]), 0.0)
        self.assertIn("cycle_repeats_total", metrics)
        self.assertIn("stuck_episodes_total", metrics)
        self.assertIn("no_progress_steps", metrics)
        self.assertIn("starvation_limit", metrics)


if __name__ == "__main__":
    unittest.main()
