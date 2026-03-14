from __future__ import annotations

import unittest

from snake_frame.observation import RIGHT, build_observation, observation_size, valid_action_mask
from snake_frame.settings import ObsConfig


class TestObservation(unittest.TestCase):
    def test_base_observation_feature_order(self) -> None:
        board_cells = 10
        snake = [(5, 5), (4, 5), (3, 5)]
        direction = RIGHT
        food = (7, 4)
        obs = build_observation(
            board_cells=board_cells,
            snake=snake,
            direction=direction,
            food=food,
            obs_config=ObsConfig(use_extended_features=False, use_path_features=False),
        )
        self.assertEqual(obs.shape[0], 11)
        expected = [
            0.0,  # danger_straight
            0.0,  # danger_left
            0.0,  # danger_right
            0.0,  # dir_up
            1.0,  # dir_right
            0.0,  # dir_down
            0.0,  # dir_left
            0.0,  # food_left
            1.0,  # food_right
            1.0,  # food_up
            0.0,  # food_down
        ]
        self.assertEqual([float(v) for v in obs.tolist()], expected)

    def test_extended_and_path_features_have_expected_sizes(self) -> None:
        board_cells = 10
        snake = [(5, 5), (4, 5), (3, 5)]
        direction = RIGHT
        food = (7, 4)
        cfg = ObsConfig(use_extended_features=True, use_path_features=True)
        obs = build_observation(
            board_cells=board_cells,
            snake=snake,
            direction=direction,
            food=food,
            obs_config=cfg,
        )
        self.assertEqual(obs.shape[0], observation_size(cfg))
        path = [float(v) for v in obs[-3:].tolist()]
        self.assertEqual(len(path), 3)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in path))

    def test_tail_path_features_have_expected_sizes_and_ranges(self) -> None:
        board_cells = 10
        snake = [(5, 5), (4, 5), (3, 5), (3, 4), (4, 4)]
        direction = RIGHT
        food = (7, 4)
        cfg = ObsConfig(
            use_extended_features=True,
            use_path_features=True,
            use_tail_path_features=True,
        )
        obs = build_observation(
            board_cells=board_cells,
            snake=snake,
            direction=direction,
            food=food,
            obs_config=cfg,
        )
        self.assertEqual(obs.shape[0], observation_size(cfg))
        tail_feats = [float(v) for v in obs[-8:].tolist()]
        self.assertEqual(len(tail_feats), 8)
        self.assertTrue(all(0.0 <= v <= 1.0 for v in tail_feats))

    def test_valid_action_mask_marks_body_collision_invalid(self) -> None:
        mask = valid_action_mask(
            board_cells=6,
            snake=[(2, 2), (3, 2), (3, 1), (2, 1)],
            direction=(1, 0),
        )
        self.assertEqual(mask, (False, True, True))


if __name__ == "__main__":
    unittest.main()
