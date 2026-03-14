from __future__ import annotations

import unittest

import pygame

from snake_frame.graph_renderer import ScoreGraphRenderer


class TestGraphRenderer(unittest.TestCase):
    def test_draw_with_short_and_long_series(self) -> None:
        pygame.init()
        try:
            surface = pygame.Surface((360, 500))
            font = pygame.font.SysFont("Arial", 18)
            renderer = ScoreGraphRenderer(font)
            rect = pygame.Rect(18, 52, 324, 360)
            renderer.draw(surface, rect, [1])  # should not crash
            renderer.draw(surface, rect, [1, 2, 3, 2, 4, 5, 4, 6, 3])  # should not crash
            self.assertTrue(True)
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
