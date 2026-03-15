from __future__ import annotations

import unittest

from snake_frame.gameplay_controller import ControlMode, GameplayController
from snake_frame.settings import ObsConfig, Settings


class _FakeGame:
    def __init__(self) -> None:
        self.game_over = False
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.direction = (1, 0)
        self.food = (14, 10)
        self.death_reason = "none"
        self.score = 0

    def queue_direction(self, dx: int, dy: int) -> None:
        _ = (dx, dy)

    def reset(self) -> None:
        self.score = 0

    def update(self) -> None:
        return None


class _FakeAgent:
    def __init__(self) -> None:
        self.is_ready = True

    def request_inference_sync(self) -> None:
        return None

    def predict_action(self, _obs, action_masks=None) -> int:
        _ = action_masks
        return 0


class TestDynamicController(unittest.TestCase):
    def test_mode_transitions_ppo_to_escape_on_risk(self) -> None:
        ctrl = GameplayController(
            game=_FakeGame(),
            agent=_FakeAgent(),
            settings=Settings(),
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True),
        )
        mode = ctrl._select_mode(
            significant_risk=True,
            imminent_danger=False,
            cycle_repeat=False,
            no_progress_steps=1,
            safe_option_count=2,
            proposed_tail_reachable=True,
            proposed_capacity_shortfall=0,
        )
        self.assertEqual(mode, ControlMode.ESCAPE)

    def test_mode_transitions_escape_to_space_fill_on_cycle(self) -> None:
        ctrl = GameplayController(
            game=_FakeGame(),
            agent=_FakeAgent(),
            settings=Settings(),
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True),
        )
        ctrl._dynamic.current_mode = ControlMode.ESCAPE
        ctrl._dynamic.cooldown_until_step = 0
        mode = ctrl._select_mode(
            significant_risk=True,
            imminent_danger=False,
            cycle_repeat=True,
            no_progress_steps=50,
            safe_option_count=2,
            proposed_tail_reachable=True,
            proposed_capacity_shortfall=0,
        )
        self.assertEqual(mode, ControlMode.SPACE_FILL)

    def test_mode_recovery_to_ppo_when_risk_clears(self) -> None:
        ctrl = GameplayController(
            game=_FakeGame(),
            agent=_FakeAgent(),
            settings=Settings(),
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True),
        )
        ctrl._dynamic.current_mode = ControlMode.SPACE_FILL
        ctrl._dynamic.cooldown_until_step = 0
        mode = ctrl._select_mode(
            significant_risk=False,
            imminent_danger=False,
            cycle_repeat=False,
            no_progress_steps=1,
            safe_option_count=2,
            proposed_tail_reachable=True,
            proposed_capacity_shortfall=0,
        )
        self.assertEqual(mode, ControlMode.PPO)

    def test_cycle_detection_triggers_repeat(self) -> None:
        game = _FakeGame()
        ctrl = GameplayController(
            game=game,
            agent=_FakeAgent(),
            settings=Settings(),
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True),
        )
        repeats = []
        proposed_eval = (0.0, True, 0)
        for _ in range(8):
            repeats.append(
                ctrl._register_cycle_state(
                    snake=list(game.snake),
                    direction=tuple(game.direction),
                    board_cells=20,
                    free_ratio=0.5,
                    proposed_eval=proposed_eval,
                )
            )
        self.assertTrue(any(repeats))


if __name__ == "__main__":
    unittest.main()
