from __future__ import annotations

import unittest

from snake_frame.controls_builder import build_controls
from snake_frame.layout_engine import LayoutEngine
from snake_frame.settings import Settings


class TestLayoutEngine(unittest.TestCase):
    def test_layout_scales_for_common_window_sizes(self) -> None:
        sizes = [
            (1400, 820),
            (1920, 1080),
            (2560, 1440),
        ]
        for width, height in sizes:
            settings = Settings()
            engine = LayoutEngine(settings)
            snap = engine.update(width, height)
            self.assertGreaterEqual(snap.window.width, 1280)
            self.assertGreaterEqual(snap.window.height, 720)
            self.assertGreaterEqual(settings.left_panel_px, settings.min_left_panel_px)
            self.assertGreaterEqual(settings.right_panel_px, settings.min_right_panel_px)
            self.assertEqual(settings.window_px, settings.board_cells * settings.cell_px)

    def test_build_controls_rects_stay_inside_window(self) -> None:
        settings = Settings()
        _ = LayoutEngine(settings).update(1920, 1080)
        controls = build_controls(
            settings,
            min_graph_height=320,
            max_graph_height=680,
            graph_margin=18,
            graph_top=120,
            control_row_height=40,
            control_gap=10,
            status_line_height=22,
            status_line_count=16,
        )
        window_h = int(settings.window_height_px or settings.window_px)
        self.assertLessEqual(controls.training_graph_rect.bottom, window_h)
        self.assertLessEqual(controls.run_graph_rect.bottom, window_h)
        self.assertGreaterEqual(controls.training_graph_rect.x, settings.right_panel_offset_x)


if __name__ == "__main__":
    unittest.main()
