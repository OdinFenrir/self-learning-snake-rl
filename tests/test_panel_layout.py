from __future__ import annotations

import unittest

from snake_frame.panel_layout import build_panel_layout, build_right_panel_layout
from snake_frame.settings import Settings


class TestPanelLayout(unittest.TestCase):
    def test_layout_bounds_and_sizes(self) -> None:
        settings = Settings()
        layout = build_panel_layout(
            settings,
            min_graph_height=260,
            max_graph_height=470,
            graph_margin=18,
            graph_top=52,
            control_row_height=40,
            control_gap=10,
            reserve_for_controls_and_status=468,
        )
        self.assertGreaterEqual(layout.graph_rect.height, 260)
        self.assertLessEqual(layout.graph_rect.height, 470)
        self.assertGreater(layout.width, 0)
        self.assertGreater(layout.half_width, 0)
        self.assertGreater(layout.controls_top, layout.graph_rect.bottom - 1)

    def test_layout_handles_tight_vertical_space(self) -> None:
        settings = Settings(board_cells=10, cell_px=32, left_panel_px=120)
        layout = build_panel_layout(
            settings,
            min_graph_height=260,
            max_graph_height=470,
            graph_margin=18,
            graph_top=52,
            control_row_height=40,
            control_gap=10,
            reserve_for_controls_and_status=400,
        )
        self.assertGreaterEqual(layout.graph_rect.height, 1)
        self.assertLessEqual(layout.graph_rect.bottom, settings.window_px)
        self.assertGreaterEqual(layout.width, 1)

    def test_right_panel_layout_bounds(self) -> None:
        settings = Settings()
        settings.apply_window_size(1600, 820)
        layout = build_right_panel_layout(settings)
        self.assertGreater(layout.utility_row_height, 0)
        self.assertGreater(layout.training_graph_rect.height, 0)
        self.assertGreater(layout.run_graph_rect.height, 0)
        self.assertGreaterEqual(layout.training_graph_rect.top, layout.training_badges_y + layout.training_badges_height)
        self.assertGreaterEqual(layout.training_graph_rect.left, settings.right_panel_offset_x)
        self.assertLessEqual(layout.training_graph_rect.right, settings.right_panel_offset_x + settings.right_panel_px)
        self.assertLessEqual(layout.training_graph_rect.bottom, settings.window_height_px)


if __name__ == "__main__":
    unittest.main()
