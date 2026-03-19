from __future__ import annotations

from dataclasses import dataclass

import pygame

from .settings import Settings


@dataclass(frozen=True)
class RightPanelLayout:
    """Responsive grid layout for the right panel KPI dashboard."""
    utility_row_y: int
    utility_row_height: int

    # Training KPIs section anchors (used by Train tab)
    training_header_y: int
    training_header_height: int
    training_badges_y: int
    training_badges_height: int
    training_graph_y: int

    # Run KPIs section anchors (used by Run tab)
    run_header_y: int
    run_header_height: int
    run_badges_y: int
    run_badges_height: int
    run_graph_y: int

    # Dimensions
    panel_width: int
    inner_x: int
    inner_width: int

    # Graph rectangles (calculated)
    training_graph_rect: pygame.Rect
    run_graph_rect: pygame.Rect


def build_right_panel_layout(
    settings: Settings,
    *,
    panel_width: int | None = None,
    panel_x: int | None = None,
) -> RightPanelLayout:
    """Build a responsive, non-overlapping grid for the right panel."""
    p_width = int(panel_width if panel_width is not None else settings.right_panel_px)
    p_x = int(panel_x if panel_x is not None else settings.right_panel_offset_x)
    window_h = int(settings.window_height_px or settings.window_px)

    ui_scale = float(getattr(settings, "ui_scale", 1.0))
    ui_scale = max(0.85, min(1.4, ui_scale))
    inner_margin = max(12, int(round(18 * ui_scale)))
    inner_x = p_x + inner_margin
    inner_width = max(120, int(p_width - (inner_margin * 2)))

    outer_top = max(8, int(round(10 * ui_scale)))
    outer_bottom = max(8, int(round(12 * ui_scale)))

    utility_y = outer_top
    utility_h = max(30, int(round(34 * ui_scale)))

    header_h = max(18, int(round(24 * ui_scale)))
    badges_h = max(34, int(round(58 * ui_scale)))
    header_to_badge = max(4, int(round(8 * ui_scale)))
    badge_to_graph = max(6, int(round(10 * ui_scale)))
    graph_to_text_reserve = max(92, int(round(190 * ui_scale)))
    min_graph_h = max(72, int(round(110 * ui_scale)))

    content_top = utility_y + utility_h + max(6, int(round(10 * ui_scale)))
    content_bottom = max(content_top + 80, window_h - outer_bottom)

    training_header_y = content_top
    training_header_h = header_h
    training_badges_y = training_header_y + training_header_h + header_to_badge
    training_badges_h = badges_h
    training_graph_y = training_badges_y + training_badges_h + badge_to_graph

    graph_space = max(40, content_bottom - training_graph_y)
    if graph_space <= min_graph_h + 48:
        training_graph_h = max(36, graph_space - 32)
    else:
        training_graph_h = max(min_graph_h, graph_space - graph_to_text_reserve)
    max_graph_ratio_h = max(80, int(round(window_h * 0.40)))
    training_graph_h = max(36, min(training_graph_h, graph_space, max_graph_ratio_h))

    training_graph_rect = pygame.Rect(inner_x, training_graph_y, inner_width, training_graph_h)

    # Tabbed right panel: run tab reuses the same content grid for consistency.
    run_header_y = training_header_y
    run_header_h = training_header_h
    run_badges_y = training_badges_y
    run_badges_h = training_badges_h
    run_graph_y = training_graph_y
    run_graph_rect = pygame.Rect(training_graph_rect)

    return RightPanelLayout(
        utility_row_y=utility_y,
        utility_row_height=utility_h,
        training_header_y=training_header_y,
        training_header_height=training_header_h,
        training_badges_y=training_badges_y,
        training_badges_height=training_badges_h,
        training_graph_y=training_graph_y,
        run_header_y=run_header_y,
        run_header_height=run_header_h,
        run_badges_y=run_badges_y,
        run_badges_height=run_badges_h,
        run_graph_y=run_graph_y,
        panel_width=p_width,
        inner_x=inner_x,
        inner_width=inner_width,
        training_graph_rect=training_graph_rect,
        run_graph_rect=run_graph_rect,
    )


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
