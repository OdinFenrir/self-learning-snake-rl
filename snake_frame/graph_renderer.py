from __future__ import annotations

import pygame

from .theme import DesignTokens, ThemePalette, get_design_tokens, get_theme


class ScoreGraphRenderer:
    _PLOT_PAD_RIGHT = 8
    _PLOT_PAD_LEFT = 6

    def __init__(self, small_font: pygame.font.Font, theme: ThemePalette | None = None) -> None:
        self.small_font = small_font
        self.theme = theme or get_theme(None)
        self.tokens: DesignTokens = get_design_tokens(self.theme.name)
        self._points_cache: dict[
            tuple[tuple[int, int, int, int], tuple[int, ...]],
            tuple[list[tuple[int, int]], list[tuple[int, int]], list[tuple[int, int]], int, float, float],
        ] = {}

    def clear_cache(self) -> None:
        self._points_cache.clear()

    def draw(
        self,
        surface: pygame.Surface,
        graph_rect: pygame.Rect,
        episode_scores: list[int],
        empty_message: str = "Train PPO to build graph.",
    ) -> None:
        try:
            self._draw_safe(surface, graph_rect, episode_scores, empty_message)
        except Exception:
            fallback = self.small_font.render("Graph unavailable", True, self.theme.banner_warn)
            surface.blit(fallback, (graph_rect.x + 10, graph_rect.y + 12))

    def _draw_safe(
        self,
        surface: pygame.Surface,
        graph_rect: pygame.Rect,
        episode_scores: list[int],
        empty_message: str,
    ) -> None:
        scores = [int(v) for v in episode_scores]
        line_h = max(16, int(self.small_font.get_linesize()))
        plot_pad_top = int(line_h + 12)
        plot_pad_bottom = int(line_h + 18)
        if len(scores) < 2:
            text = self._fit_text(str(empty_message), self.theme.badge_text, max(40, graph_rect.width - 20))
            surface.blit(text, (graph_rect.x + 10, graph_rect.y + 12))
            return

        plot_rect = pygame.Rect(
            int(graph_rect.x + self._PLOT_PAD_LEFT),
            int(graph_rect.y + plot_pad_top),
            max(10, int(graph_rect.width - self._PLOT_PAD_LEFT - self._PLOT_PAD_RIGHT)),
            max(10, int(graph_rect.height - plot_pad_top - plot_pad_bottom)),
        )
        cache_key = (
            (int(plot_rect.x), int(plot_rect.y), int(plot_rect.width), int(plot_rect.height)),
            tuple(scores),
        )
        cached = self._points_cache.get(cache_key)
        if cached is None:
            smoothing_window = max(3, min(12, max(3, len(scores) // 6)))
            smoothed = self._moving_average(scores, smoothing_window)
            best = self._cumulative_best(scores)
            min_score = min(min(scores), min(smoothed), min(best))
            max_score = max(max(scores), max(smoothed), max(best))
            span = max(1.0, float(max_score - min_score))
            raw_points = self._series_to_points([float(v) for v in scores], plot_rect, min_score, span)
            avg_points = self._series_to_points(smoothed, plot_rect, min_score, span)
            best_points = self._series_to_points(best, plot_rect, min_score, span)
            cached = (raw_points, avg_points, best_points, smoothing_window, min_score, max_score)
            self._points_cache[cache_key] = cached
            if len(self._points_cache) > 64:
                self._points_cache.clear()
        raw_points, avg_points, best_points, smoothing_window, min_score, max_score = cached
        if len(raw_points) >= 2:
            pygame.draw.lines(surface, self.theme.load_bg, False, raw_points, 2)
        if len(avg_points) >= 2:
            pygame.draw.lines(surface, self.theme.toggle_positive_hover, False, avg_points, 3)
        if len(best_points) >= 2:
            pygame.draw.lines(surface, self.theme.banner_warn, False, best_points, 2)

        legend_y = graph_rect.y + 8
        raw_text = self.small_font.render("Raw", True, self.theme.status_color)
        avg_text = self.small_font.render(f"Avg({smoothing_window})", True, self.theme.toggle_positive_hover)
        best_text = self.small_font.render("Best", True, self.theme.banner_warn)
        x = int(graph_rect.x + 8)
        surface.blit(raw_text, (x, legend_y))
        x += int(raw_text.get_width() + 10)
        surface.blit(avg_text, (x, legend_y))
        x += int(avg_text.get_width() + 10)
        surface.blit(best_text, (x, legend_y))
        surface.blit(
            self.small_font.render(f"max {int(max_score)}", True, self.theme.badge_text),
            (graph_rect.right - 96, legend_y),
        )
        # Keep range labels separate from the stats line to avoid overlap.
        surface.blit(
            self.small_font.render(f"min {int(min_score)}", True, self.theme.badge_text),
            (graph_rect.right - 96, graph_rect.bottom - line_h - 6),
        )
        latest_score = int(scores[-1])
        latest_avg = self._moving_average(scores, smoothing_window)[-1]
        best_score = int(max(scores))
        stats_line = f"Last {latest_score}  Avg {latest_avg:.2f}  Best {best_score}"
        stats = self._fit_text(stats_line, self.theme.badge_text, max(30, graph_rect.width - 118))
        surface.blit(
            stats,
            (graph_rect.x + 8, graph_rect.bottom - line_h - 6),
        )

    @staticmethod
    def _moving_average(values: list[int | float], window: int) -> list[float]:
        lookback = max(1, int(window))
        out: list[float] = []
        rolling = 0.0
        for i, value in enumerate(values):
            rolling += float(value)
            if i >= lookback:
                rolling -= float(values[i - lookback])
            out.append(rolling / float(min(i + 1, lookback)))
        return out

    @staticmethod
    def _cumulative_best(values: list[int | float]) -> list[float]:
        out: list[float] = []
        best = float("-inf")
        for value in values:
            best = max(best, float(value))
            out.append(best)
        return out

    @staticmethod
    def _series_to_points(
        series: list[float],
        graph_rect: pygame.Rect,
        min_score: float,
        span: float,
    ) -> list[tuple[int, int]]:
        points: list[tuple[int, int]] = []
        denom = max(1, len(series) - 1)
        for i, value in enumerate(series):
            x = graph_rect.x + int((graph_rect.width - 1) * (i / denom))
            norm = (float(value) - float(min_score)) / span
            y = graph_rect.y + graph_rect.height - 1 - int((graph_rect.height - 1) * norm)
            points.append((x, y))
        return points

    def _fit_text(self, text: str, color: tuple[int, int, int], max_width: int) -> pygame.Surface:
        candidate = str(text)
        rendered = self.small_font.render(candidate, True, color)
        if rendered.get_width() <= int(max_width):
            return rendered
        ellipsis = "..."
        while candidate:
            candidate = candidate[:-1]
            clipped = candidate.rstrip() + ellipsis
            rendered = self.small_font.render(clipped, True, color)
            if rendered.get_width() <= int(max_width):
                return rendered
        return self.small_font.render(ellipsis, True, color)
