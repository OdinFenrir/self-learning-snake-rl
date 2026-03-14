from __future__ import annotations

import time
import unittest
from unittest.mock import patch

try:
    from snake_frame.training import PpoTrainingController
except Exception as exc:  # pragma: no cover - env-dependent import gate
    raise RuntimeError(
        "ML dependency setup is required for training-controller tests. "
        "Install with `pip install -r requirements.txt`."
    ) from exc


class _FakeModel:
    def __init__(self, num_timesteps: int = 0) -> None:
        self.num_timesteps = int(num_timesteps)


class _FakeAgent:
    def __init__(self, mode: str = "complete") -> None:
        self.mode = str(mode)
        self.model = _FakeModel(num_timesteps=10)
        self.best_eval_score = None
        self.best_eval_step = 0
        self.last_eval_score = None
        self.eval_runs_completed = 0

    def train(self, total_timesteps, stop_flag, on_progress=None, on_score=None, on_episode_info=None):
        if self.mode == "error":
            raise RuntimeError("boom")
        if self.mode == "save_error":
            raise RuntimeError("model save failed after training")
        if on_progress is not None:
            on_progress(self.model.num_timesteps + 1)
        if self.mode == "wait_stop":
            while not stop_flag():
                time.sleep(0.01)
            self.model.num_timesteps += 2
            return int(self.model.num_timesteps)
        self.model.num_timesteps += int(total_timesteps)
        if on_score is not None:
            on_score(7)
        if on_episode_info is not None:
            on_episode_info({"score": 7, "death_reason": "body"})
        return int(self.model.num_timesteps)

class TestTrainingController(unittest.TestCase):
    def _wait_for_completion(self, controller: PpoTrainingController, timeout_s: float = 2.0) -> str | None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            msg = controller.poll_completion()
            if msg is not None:
                return msg
            time.sleep(0.01)
        return None

    def test_complete_flow_reports_complete(self) -> None:
        scores: list[int] = []
        agent = _FakeAgent(mode="complete")
        controller = PpoTrainingController(agent=agent, on_score=scores.append)
        self.assertTrue(controller.start(target_steps=5))
        message = self._wait_for_completion(controller)
        self.assertEqual(message, "Training complete")
        self.assertEqual(scores, [7])

    def test_stop_flow_reports_stopped(self) -> None:
        agent = _FakeAgent(mode="wait_stop")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=5))
        time.sleep(0.05)
        controller.stop()
        message = self._wait_for_completion(controller)
        self.assertEqual(message, "Training stopped")

    def test_error_flow_reports_error(self) -> None:
        agent = _FakeAgent(mode="error")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=5))
        message = self._wait_for_completion(controller)
        self.assertIsNotNone(message)
        self.assertTrue(str(message).startswith("Training error:"))

    def test_save_failure_after_training_reports_error(self) -> None:
        agent = _FakeAgent(mode="save_error")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=5))
        message = self._wait_for_completion(controller)
        self.assertEqual(message, "Training error: model save failed after training")

    def test_start_clamps_target_steps_to_at_least_one(self) -> None:
        agent = _FakeAgent(mode="complete")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=0))
        snap = controller.snapshot()
        self.assertEqual(snap.target_steps, 1)
        _ = self._wait_for_completion(controller)

    def test_start_returns_false_and_rolls_back_when_thread_start_fails(self) -> None:
        agent = _FakeAgent(mode="complete")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        with patch("snake_frame.training.threading.Thread.start", side_effect=RuntimeError("thread boom")):
            started = controller.start(target_steps=5)
        self.assertFalse(started)
        snap = controller.snapshot()
        self.assertFalse(snap.active)
        self.assertEqual(snap.target_steps, 0)
        self.assertEqual(str(snap.last_error), "thread boom")

    def test_snapshot_uses_live_model_timesteps_while_training_active(self) -> None:
        agent = _FakeAgent(mode="wait_stop")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=5))
        time.sleep(0.05)
        agent.model.num_timesteps = 123
        snap = controller.snapshot()
        self.assertGreaterEqual(int(snap.current_steps), 123)
        controller.stop()
        _ = self._wait_for_completion(controller)

    def test_snapshot_uses_live_eval_stats_while_training_active(self) -> None:
        agent = _FakeAgent(mode="wait_stop")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertTrue(controller.start(target_steps=5))
        time.sleep(0.05)
        agent.best_eval_score = 321.5
        agent.best_eval_step = 50000
        agent.last_eval_score = 310.25
        agent.eval_runs_completed = 2
        snap = controller.snapshot()
        self.assertEqual(snap.best_eval_score, 321.5)
        self.assertEqual(int(snap.best_eval_step), 50000)
        self.assertEqual(snap.last_eval_score, 310.25)
        self.assertEqual(int(snap.eval_runs_completed), 2)
        controller.stop()
        _ = self._wait_for_completion(controller)

    def test_sets_and_clears_external_training_flag(self) -> None:
        agent = _FakeAgent(mode="wait_stop")
        controller = PpoTrainingController(agent=agent, on_score=lambda _s: None)
        self.assertFalse(bool(getattr(agent, "_external_training_active", False)))
        self.assertTrue(controller.start(target_steps=5))
        self.assertTrue(bool(getattr(agent, "_external_training_active", False)))
        controller.stop()
        _ = self._wait_for_completion(controller)
        self.assertFalse(bool(getattr(agent, "_external_training_active", False)))


if __name__ == "__main__":
    unittest.main()
