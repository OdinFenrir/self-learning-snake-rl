from __future__ import annotations

from dataclasses import dataclass

import pygame

from .settings import Settings


@dataclass(frozen=True)
class PanelLayout:
    graph_rect: pygame.Rect
    controls_top: int
    x: int
    width: int
    half_width: int
    row_height: int
    gap: int


def build_panel_layout(
    settings: Settings,
    *,
    min_graph_height: int,
    max_graph_height: int,
    graph_margin: int,
    graph_top: int,
    control_row_height: int,
    control_gap: int,
    reserve_for_controls_and_status: int,
    panel_x: int | None = None,
    panel_width: int | None = None,
) -> PanelLayout:
    x0 = int(panel_x) if panel_x is not None else 0
    panel_w = int(panel_width) if panel_width is not None else int(settings.left_panel_px)
    usable_width = max(1, int(panel_w - (graph_margin * 2)))
    window_h = int(settings.window_height_px or settings.window_px)
    max_height_by_space = max(1, int(window_h - graph_top - graph_margin - reserve_for_controls_and_status))
    desired_min = max(1, int(min_graph_height))
    desired_max = max(desired_min, int(max_graph_height))
    if max_height_by_space < desired_min:
        graph_height = max_height_by_space
    else:
        graph_height = min(desired_max, max_height_by_space)
    controls_top = int(graph_top + graph_height + graph_margin)
    graph_rect = pygame.Rect(
        int(x0 + graph_margin),
        int(graph_top),
        usable_width,
        int(graph_height),
    )
    x = int(x0 + graph_margin)
    width = usable_width
    gap = int(control_gap)
    half_width = int((width - gap) // 2)
    return PanelLayout(
        graph_rect=graph_rect,
        controls_top=controls_top,
        x=x,
        width=width,
        half_width=half_width,
        row_height=int(control_row_height),
        gap=gap,
    )
