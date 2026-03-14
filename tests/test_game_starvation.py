from __future__ import annotations

import unittest

from snake_frame.game import SnakeGame
from snake_frame.settings import Settings


class TestGameStarvation(unittest.TestCase):
    def test_starvation_ends_episode_when_no_food_progress(self) -> None:
        settings = Settings(board_cells=8, ticks_per_move=1)
        game = SnakeGame(settings, starvation_factor=1)
        game.food = (-1, -1)

        sequence = ((1, 0), (0, 1), (-1, 0), (0, -1))
        limit = int(settings.board_cells * settings.board_cells)

        for i in range(limit + 8):
            if game.game_over:
                break
            dx, dy = sequence[i % len(sequence)]
            game.queue_direction(dx, dy)
            game.update()

        self.assertTrue(game.game_over)
        self.assertEqual(game.death_reason, "starvation")


if __name__ == "__main__":
    unittest.main()
