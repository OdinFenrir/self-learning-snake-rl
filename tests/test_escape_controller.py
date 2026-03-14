from __future__ import annotations

import unittest

from snake_frame.escape_controller import EscapeController


class TestEscapeController(unittest.TestCase):
    def test_choose_action_returns_safe_candidate(self) -> None:
        ctrl = EscapeController()
        snake = [(5, 5), (4, 5), (3, 5), (2, 5)]
        action = ctrl.choose_action(
            board_cells=12,
            snake=snake,
            direction=(1, 0),
            food=(9, 5),
        )
        self.assertIn(action, (0, 1, 2))

    def test_choose_action_prefers_non_danger_when_straight_is_wall(self) -> None:
        ctrl = EscapeController()
        snake = [(11, 5), (10, 5), (9, 5), (8, 5)]
        action = ctrl.choose_action(
            board_cells=12,
            snake=snake,
            direction=(1, 0),
            food=(6, 5),
        )
        self.assertIn(action, (1, 2))


if __name__ == "__main__":
    unittest.main()
