from __future__ import annotations

import unittest
from unittest.mock import patch

try:
    import numpy as np
    from snake_frame.ppo_env import RIGHT, SnakePPOEnv, action_to_direction
    from snake_frame.settings import ObsConfig, RewardConfig
    _IMPORT_ERROR = None
except Exception as exc:  # pragma: no cover - env-dependent import gate
    _IMPORT_ERROR = exc

_SKIP_REASON = (
    "ML dependency setup required for full PPO env tests. "
    "Install with `pip install -r requirements.txt`. "
    f"Import error: {_IMPORT_ERROR}"
)


@unittest.skipIf(_IMPORT_ERROR is not None, _SKIP_REASON)
class TestPpoEnv(unittest.TestCase):
    def test_ctor_seed_initial_state_is_reproducible(self) -> None:
        env_a = SnakePPOEnv(board_cells=10, seed=123)
        env_b = SnakePPOEnv(board_cells=10, seed=123)
        self.assertEqual(env_a.food, env_b.food)
        self.assertEqual(env_a.snake, env_b.snake)

    def test_observation_shape_and_dtype(self) -> None:
        env = SnakePPOEnv(board_cells=20, seed=1)
        obs, _ = env.reset()
        self.assertEqual(obs.shape, (11,))
        self.assertEqual(obs.dtype, np.float32)

    def test_extended_observation_shape(self) -> None:
        env = SnakePPOEnv(board_cells=20, seed=2, obs_config=ObsConfig(use_extended_features=True))
        obs, _ = env.reset()
        self.assertEqual(obs.shape, (17,))
        self.assertEqual(obs.dtype, np.float32)

    def test_path_feature_observation_shape(self) -> None:
        env = SnakePPOEnv(
            board_cells=20,
            seed=2,
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True),
        )
        obs, _ = env.reset()
        self.assertEqual(obs.shape, (20,))
        self.assertEqual(obs.dtype, np.float32)
        for value in obs[-3:]:
            self.assertGreaterEqual(float(value), 0.0)
            self.assertLessEqual(float(value), 1.0)

    def test_tail_path_feature_observation_shape(self) -> None:
        env = SnakePPOEnv(
            board_cells=20,
            seed=2,
            obs_config=ObsConfig(use_extended_features=True, use_path_features=True, use_tail_path_features=True),
        )
        obs, _ = env.reset()
        self.assertEqual(obs.shape, (28,))
        self.assertEqual(obs.dtype, np.float32)
        for value in obs[-8:]:
            self.assertGreaterEqual(float(value), 0.0)
            self.assertLessEqual(float(value), 1.0)

    def test_action_mapping(self) -> None:
        self.assertEqual(action_to_direction(RIGHT, 0), RIGHT)
        self.assertEqual(action_to_direction(RIGHT, 1), (0, -1))
        self.assertEqual(action_to_direction(RIGHT, 2), (0, 1))

    def test_food_eat_increments_score(self) -> None:
        env = SnakePPOEnv(board_cells=10, seed=3)
        env.reset()
        head_x, head_y = env.snake[0]
        env.direction = RIGHT
        env.food = (head_x + 1, head_y)

        _obs, reward, terminated, truncated, info = env.step(0)

        self.assertFalse(terminated)
        self.assertFalse(truncated)
        self.assertEqual(env.score, 1)
        self.assertEqual(int(info["score"]), 1)
        self.assertGreater(reward, 0.0)

    def test_wall_collision_terminates(self) -> None:
        env = SnakePPOEnv(board_cells=5, seed=7)
        env.reset()
        env.snake = [(4, 2), (3, 2), (2, 2)]
        env.direction = RIGHT

        _obs, reward, terminated, truncated, info = env.step(0)

        self.assertTrue(terminated)
        self.assertFalse(truncated)
        self.assertLess(reward, -30.0)
        self.assertEqual(int(info["score"]), 0)
        self.assertEqual(str(info.get("death_reason")), "wall")

    def test_starvation_sets_truncated_reason(self) -> None:
        reward_cfg = RewardConfig(board_starvation_factor=0)
        env = SnakePPOEnv(board_cells=5, seed=9, reward_config=reward_cfg)
        env.reset()
        env.food = (-1, -1)
        _obs, _reward, terminated, truncated, info = env.step(0)
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        self.assertEqual(str(info.get("death_reason")), "starvation")

    def test_reset_with_same_seed_is_reproducible(self) -> None:
        env = SnakePPOEnv(board_cells=10)
        env.reset(seed=42)
        first_food = env.food
        env.reset(seed=42)
        second_food = env.food
        self.assertEqual(first_food, second_food)

    def test_invalid_action_raises_value_error(self) -> None:
        env = SnakePPOEnv(board_cells=10, seed=4)
        env.reset()
        with self.assertRaises(ValueError):
            env.step(9)

    def test_action_masks_mark_wall_collision_invalid(self) -> None:
        env = SnakePPOEnv(board_cells=5, seed=4)
        env.reset()
        env.snake = [(4, 2), (3, 2), (2, 2)]
        env.direction = RIGHT
        mask = env.action_masks()
        self.assertEqual(mask.tolist(), [False, True, True])

    def test_reachable_space_penalty_can_be_disabled(self) -> None:
        reward_cfg = RewardConfig(use_reachable_space_penalty=False)
        env = SnakePPOEnv(board_cells=10, seed=5, reward_config=reward_cfg)
        env.reset()
        with patch("snake_frame.ppo_env.reachable_space_ratio", return_value=0.0):
            _obs, reward, terminated, truncated, _info = env.step(0)
        self.assertFalse(terminated)
        self.assertFalse(truncated)
        # No trap penalty should be applied when disabled.
        self.assertGreater(reward, -float(reward_cfg.death_penalty))

    def test_reachable_space_penalty_applies_when_space_is_low(self) -> None:
        base_cfg = RewardConfig(
            use_reachable_space_penalty=False,
            living_penalty=0.0,
            approach_food_reward=0.0,
            retreat_food_penalty=0.0,
            low_safe_options_penalty=0.0,
            high_safe_options_bonus=0.0,
        )
        penalty_cfg = RewardConfig(
            use_reachable_space_penalty=True,
            trap_penalty_threshold=0.5,
            trap_penalty=2.0,
            endgame_length_ratio_start=0.0,
            endgame_trap_penalty_scale=0.0,
            living_penalty=0.0,
            approach_food_reward=0.0,
            retreat_food_penalty=0.0,
            low_safe_options_penalty=0.0,
            high_safe_options_bonus=0.0,
        )
        env_base = SnakePPOEnv(board_cells=10, seed=6, reward_config=base_cfg)
        env_penalty = SnakePPOEnv(board_cells=10, seed=6, reward_config=penalty_cfg)
        env_base.reset()
        env_penalty.reset()
        with patch("snake_frame.ppo_env.reachable_space_ratio", return_value=0.0):
            _obs, reward_base, _terminated, _truncated, _info = env_base.step(0)
        with patch("snake_frame.ppo_env.reachable_space_ratio", return_value=0.0):
            _obs, reward_penalty, _terminated, _truncated, _info = env_penalty.step(0)
        self.assertLess(reward_penalty, reward_base)


if __name__ == "__main__":
    unittest.main()
