from __future__ import annotations

import unittest

from snake_frame.board_analysis import (
    is_point_danger,
    reachable_space_ratio,
    simulate_next_snake,
    tail_is_reachable,
)


class TestBoardAnalysis(unittest.TestCase):
    def test_simulate_next_snake_grow_and_move(self) -> None:
        snake = [(3, 3), (2, 3), (1, 3)]
        self.assertEqual(
            simulate_next_snake(snake, (4, 3), (8, 8)),
            [(4, 3), (3, 3), (2, 3)],
        )
        self.assertEqual(
            simulate_next_snake(snake, (4, 3), (4, 3)),
            [(4, 3), (3, 3), (2, 3), (1, 3)],
        )

    def test_is_point_danger_allows_tail_cell(self) -> None:
        snake = [(3, 3), (2, 3), (1, 3)]
        self.assertTrue(is_point_danger(8, snake, (2, 3)))
        self.assertFalse(is_point_danger(8, snake, (1, 3)))
        self.assertTrue(is_point_danger(8, snake, (-1, 3)))

    def test_reachable_space_ratio_bounded(self) -> None:
        snake_after_move = [(1, 1), (1, 2), (2, 2)]
        ratio = reachable_space_ratio(6, snake_after_move, snake_after_move[0])
        self.assertGreaterEqual(ratio, 0.0)
        self.assertLessEqual(ratio, 1.0)

    def test_tail_is_reachable_handles_open_and_blocked_shapes(self) -> None:
        open_snake = [(2, 2), (2, 3), (2, 4)]
        self.assertTrue(tail_is_reachable(8, open_snake))

        blocked_snake = [(1, 1), (1, 0), (0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1), (2, 0)]
        self.assertFalse(tail_is_reachable(3, blocked_snake))


if __name__ == "__main__":
    unittest.main()
