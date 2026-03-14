from __future__ import annotations

from dataclasses import dataclass

from .settings import Settings


@dataclass(frozen=True)
class WindowMetrics:
    width: int
    height: int
    board_size: int
    board_offset_x: int
    board_offset_y: int


@dataclass(frozen=True)
class PanelMetrics:
    left_width: int
    right_width: int
    right_offset_x: int


@dataclass(frozen=True)
class GraphMetrics:
    graph_top: int
    graph_margin: int
    min_graph_height: int
    max_graph_height: int
    control_row_height: int
    control_gap: int
    status_line_height: int
    status_line_count: int


@dataclass(frozen=True)
class LayoutSnapshot:
    window: WindowMetrics
    panels: PanelMetrics
    graph: GraphMetrics


class LayoutEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def update(self, width: int, height: int) -> LayoutSnapshot:
        self.settings.apply_window_size(width, height)
        scale = max(0.7, min(1.8, float(getattr(self.settings, "ui_scale", 1.0))))
        graph_margin = int(round(18 * scale))
        graph_top = int(round(120 * scale))
        min_graph_height = int(round(320 * scale))
        max_graph_height = int(round(680 * scale))
        row_height = int(round(40 * scale))
        control_gap = int(round(10 * scale))
        status_height = int(round(22 * scale))
        status_count = 16
        return LayoutSnapshot(
            window=WindowMetrics(
                width=int(self.settings.window_width_px),
                height=int(self.settings.window_height_px or self.settings.window_px),
                board_size=int(self.settings.window_px),
                board_offset_x=int(self.settings.board_offset_x),
                board_offset_y=int(self.settings.board_offset_y),
            ),
            panels=PanelMetrics(
                left_width=int(self.settings.left_panel_px),
                right_width=int(self.settings.right_panel_px),
                right_offset_x=int(self.settings.right_panel_offset_x),
            ),
            graph=GraphMetrics(
                graph_top=graph_top,
                graph_margin=graph_margin,
                min_graph_height=min_graph_height,
                max_graph_height=max_graph_height,
                control_row_height=row_height,
                control_gap=control_gap,
                status_line_height=status_height,
                status_line_count=status_count,
            ),
        )
