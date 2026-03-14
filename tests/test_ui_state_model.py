from __future__ import annotations

import unittest

from snake_frame.ui_state_model import ModelState, TrainingState, UIStateModel
from snake_frame.ui_state_model import derive_control_authority_policy


class TestUIStateModel(unittest.TestCase):
    def test_disable_storage_mutations_while_training(self) -> None:
        state = UIStateModel(
            model_state=ModelState.READY,
            training_state=TrainingState.RUNNING,
            game_running=True,
        )
        self.assertFalse(state.is_action_enabled("save"))
        self.assertFalse(state.is_action_enabled("load"))
        self.assertFalse(state.is_action_enabled("delete"))
        self.assertTrue(state.is_action_enabled("train_stop"))

    def test_enable_train_start_when_idle(self) -> None:
        state = UIStateModel(
            model_state=ModelState.NONE,
            training_state=TrainingState.IDLE,
            game_running=False,
        )
        self.assertTrue(state.is_action_enabled("train_start"))
        self.assertFalse(state.is_action_enabled("train_stop"))

    def test_ready_without_inference_and_without_sync_pending_keeps_manual_control(self) -> None:
        policy = derive_control_authority_policy(
            is_ready=True,
            is_inference_available=False,
            is_sync_pending=False,
            game_running=True,
        )
        self.assertFalse(policy.agent_can_steer)
        self.assertTrue(policy.manual_can_steer)
        self.assertFalse(policy.run_paused_waiting_snapshot)
        self.assertIsNone(policy.status_banner_text)


if __name__ == "__main__":
    unittest.main()
