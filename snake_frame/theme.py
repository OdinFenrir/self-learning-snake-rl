from __future__ import annotations

from dataclasses import dataclass

Color = tuple[int, int, int]


@dataclass(frozen=True)
class ThemePalette:
    name: str
    surface_bg: Color
    panel_bg: Color
    panel_bg_accent: Color
    panel_border: Color
    panel_split_highlight: Color
    title_color: Color
    graph_bg: Color
    status_color: Color
    status_secondary: Color
    badge_bg: Color
    badge_border: Color
    badge_text: Color
    section_header: Color
    divider: Color
    frame_outer: Color
    frame_inner: Color
    board_frame_bg: Color
    board_frame_border: Color
    board_frame_inner: Color
    board_frame_highlight: Color
    banner_warn: Color
    perf_text: Color
    train_start_bg: Color
    train_start_hover: Color
    save_bg: Color
    save_hover: Color
    load_bg: Color
    load_hover: Color
    delete_bg: Color
    delete_hover: Color
    restart_bg: Color
    restart_hover: Color
    game_start_bg: Color
    game_start_hover: Color
    game_stop_bg: Color
    game_stop_hover: Color
    debug_off_bg: Color
    debug_off_hover: Color
    reach_off_bg: Color
    reach_off_hover: Color
    toggle_positive_bg: Color
    toggle_positive_hover: Color
    toggle_negative_bg: Color
    toggle_negative_hover: Color
    toggle_info_bg: Color
    toggle_info_hover: Color
    toggle_warm_bg: Color
    toggle_warm_hover: Color
    board_grad_top: Color
    board_grad_bottom: Color
    grid_line: Color
    food_base: Color
    food_dark: Color
    food_light: Color
    snake_head_base: Color
    snake_head_dark: Color
    snake_head_light: Color
    snake_body_start: Color
    snake_body_end: Color
    snake_body_dark_start: Color
    snake_body_dark_end: Color
    snake_body_light_start: Color
    snake_body_light_end: Color
    hud_shadow: Color
    hud_text: Color
    game_over_text: Color


@dataclass(frozen=True)
class TypographyTokens:
    title_family: str = "Segoe UI"
    body_family: str = "Segoe UI"
    title_size: int = 24
    body_size: int = 19
    title_bold: bool = True
    body_bold: bool = True
    section_title_gap: int = 2
    status_line_min_height: int = 24


@dataclass(frozen=True)
class SpacingTokens:
    input_top_offset: int = 1
    input_to_buttons_gap: int = 8
    section_gap: int = 10
    section_gap_large: int = 24
    right_options_y: int = 12
    right_options_gap: int = 8
    right_header_block_gap: int = 6
    badge_gap_x: int = 7
    badge_gap_y: int = 5
    left_controls_top_padding: int = 18
    left_controls_raise_px: int = 48
    status_top_gap: int = 12
    right_graph_bottom_reserve: int = 0
    panel_inner_pad_x: int = 18
    graph_margin_compact_threshold: int = 820
    compact_gap_scale_num: int = 3
    compact_gap_scale_den: int = 4


@dataclass(frozen=True)
class ComponentTokens:
    input_height: int = 36
    button_row_height: int = 40
    right_options_height: int = 32
    badge_min_height: int = 26
    badge_padding_x: int = 8
    badge_padding_y: int = 4
    border_radius_button: int = 8
    border_radius_badge: int = 7
    max_badge_rows: int = 3
    graph_min_height: int = 120
    graph_min_height_large: int = 140


@dataclass(frozen=True)
class DesignTokens:
    typography: TypographyTokens
    spacing: SpacingTokens
    components: ComponentTokens


_THEMES: dict[str, ThemePalette] = {
    "retro_forest_noir": ThemePalette(
        name="retro_forest_noir",
        surface_bg=(16, 24, 30),
        panel_bg=(19, 30, 34),
        panel_bg_accent=(28, 46, 42),
        panel_border=(78, 115, 108),
        panel_split_highlight=(128, 182, 166),
        title_color=(230, 246, 236),
        graph_bg=(15, 28, 34),
        status_color=(189, 216, 205),
        status_secondary=(156, 184, 172),
        badge_bg=(30, 52, 52),
        badge_border=(102, 146, 136),
        badge_text=(224, 240, 232),
        section_header=(221, 240, 232),
        divider=(67, 98, 92),
        frame_outer=(34, 66, 62),
        frame_inner=(87, 132, 124),
        board_frame_bg=(26, 48, 46),
        board_frame_border=(96, 152, 142),
        board_frame_inner=(70, 118, 112),
        board_frame_highlight=(166, 214, 196),
        banner_warn=(238, 198, 112),
        perf_text=(214, 234, 224),
        train_start_bg=(156, 100, 54),
        train_start_hover=(186, 124, 70),
        save_bg=(58, 110, 78),
        save_hover=(78, 142, 102),
        load_bg=(64, 104, 128),
        load_hover=(84, 130, 158),
        delete_bg=(122, 66, 66),
        delete_hover=(154, 84, 84),
        restart_bg=(112, 98, 54),
        restart_hover=(138, 122, 70),
        game_start_bg=(52, 116, 78),
        game_start_hover=(72, 146, 100),
        game_stop_bg=(132, 68, 68),
        game_stop_hover=(162, 88, 88),
        debug_off_bg=(68, 98, 118),
        debug_off_hover=(88, 124, 146),
        reach_off_bg=(92, 72, 108),
        reach_off_hover=(114, 92, 134),
        toggle_positive_bg=(58, 112, 84),
        toggle_positive_hover=(78, 142, 108),
        toggle_negative_bg=(106, 70, 54),
        toggle_negative_hover=(134, 90, 70),
        toggle_info_bg=(62, 120, 96),
        toggle_info_hover=(82, 148, 120),
        toggle_warm_bg=(122, 94, 56),
        toggle_warm_hover=(148, 114, 74),
        board_grad_top=(22, 36, 42),
        board_grad_bottom=(14, 22, 28),
        grid_line=(56, 78, 82),
        food_base=(238, 92, 86),
        food_dark=(148, 44, 40),
        food_light=(255, 162, 146),
        snake_head_base=(96, 232, 178),
        snake_head_dark=(42, 126, 98),
        snake_head_light=(184, 255, 224),
        snake_body_start=(58, 182, 212),
        snake_body_end=(34, 88, 118),
        snake_body_dark_start=(26, 114, 144),
        snake_body_dark_end=(18, 50, 72),
        snake_body_light_start=(138, 234, 252),
        snake_body_light_end=(88, 166, 208),
        hud_shadow=(10, 18, 20),
        hud_text=(236, 248, 242),
        game_over_text=(255, 188, 158),
    ),
    "crt_ocean_amber": ThemePalette(
        name="crt_ocean_amber",
        surface_bg=(12, 20, 34),
        panel_bg=(12, 24, 42),
        panel_bg_accent=(18, 40, 66),
        panel_border=(72, 108, 142),
        panel_split_highlight=(122, 166, 206),
        title_color=(234, 244, 255),
        graph_bg=(10, 18, 34),
        status_color=(190, 208, 228),
        status_secondary=(160, 180, 202),
        badge_bg=(20, 38, 58),
        badge_border=(82, 128, 170),
        badge_text=(220, 236, 248),
        section_header=(220, 236, 250),
        divider=(52, 76, 104),
        frame_outer=(16, 40, 62),
        frame_inner=(64, 102, 140),
        board_frame_bg=(20, 42, 66),
        board_frame_border=(82, 132, 176),
        board_frame_inner=(52, 90, 126),
        board_frame_highlight=(140, 188, 228),
        banner_warn=(242, 188, 96),
        perf_text=(212, 228, 242),
        train_start_bg=(178, 108, 52),
        train_start_hover=(208, 130, 66),
        save_bg=(48, 102, 88),
        save_hover=(66, 132, 114),
        load_bg=(50, 90, 132),
        load_hover=(68, 114, 162),
        delete_bg=(116, 58, 64),
        delete_hover=(146, 76, 84),
        restart_bg=(102, 92, 52),
        restart_hover=(128, 114, 66),
        game_start_bg=(48, 112, 90),
        game_start_hover=(66, 142, 114),
        game_stop_bg=(128, 66, 70),
        game_stop_hover=(156, 84, 90),
        debug_off_bg=(56, 90, 128),
        debug_off_hover=(72, 112, 156),
        reach_off_bg=(84, 66, 118),
        reach_off_hover=(106, 84, 144),
        toggle_positive_bg=(46, 110, 86),
        toggle_positive_hover=(64, 140, 110),
        toggle_negative_bg=(98, 66, 50),
        toggle_negative_hover=(124, 84, 66),
        toggle_info_bg=(52, 104, 134),
        toggle_info_hover=(70, 126, 160),
        toggle_warm_bg=(120, 90, 52),
        toggle_warm_hover=(146, 110, 66),
        board_grad_top=(12, 24, 40),
        board_grad_bottom=(8, 16, 30),
        grid_line=(44, 62, 90),
        food_base=(248, 102, 84),
        food_dark=(152, 52, 38),
        food_light=(255, 176, 144),
        snake_head_base=(86, 228, 196),
        snake_head_dark=(32, 122, 102),
        snake_head_light=(170, 255, 236),
        snake_body_start=(64, 176, 232),
        snake_body_end=(28, 76, 124),
        snake_body_dark_start=(20, 104, 156),
        snake_body_dark_end=(14, 42, 82),
        snake_body_light_start=(140, 228, 255),
        snake_body_light_end=(86, 158, 216),
        hud_shadow=(8, 14, 22),
        hud_text=(238, 246, 255),
        game_over_text=(255, 190, 160),
    ),
    "terminal_sunset": ThemePalette(
        name="terminal_sunset",
        surface_bg=(20, 20, 28),
        panel_bg=(24, 24, 34),
        panel_bg_accent=(36, 30, 48),
        panel_border=(112, 94, 122),
        panel_split_highlight=(166, 138, 178),
        title_color=(244, 238, 250),
        graph_bg=(22, 20, 32),
        status_color=(214, 204, 224),
        status_secondary=(184, 172, 198),
        badge_bg=(42, 34, 56),
        badge_border=(126, 104, 148),
        badge_text=(236, 226, 246),
        section_header=(236, 226, 246),
        divider=(80, 66, 96),
        frame_outer=(44, 36, 62),
        frame_inner=(98, 84, 126),
        board_frame_bg=(44, 36, 58),
        board_frame_border=(128, 108, 154),
        board_frame_inner=(94, 80, 116),
        board_frame_highlight=(188, 164, 210),
        banner_warn=(244, 184, 110),
        perf_text=(228, 220, 240),
        train_start_bg=(176, 108, 66),
        train_start_hover=(206, 132, 84),
        save_bg=(70, 114, 88),
        save_hover=(90, 144, 110),
        load_bg=(74, 102, 142),
        load_hover=(94, 126, 172),
        delete_bg=(132, 72, 76),
        delete_hover=(160, 90, 96),
        restart_bg=(128, 104, 62),
        restart_hover=(154, 126, 80),
        game_start_bg=(76, 130, 96),
        game_start_hover=(98, 158, 120),
        game_stop_bg=(140, 76, 82),
        game_stop_hover=(166, 94, 102),
        debug_off_bg=(76, 102, 144),
        debug_off_hover=(96, 126, 172),
        reach_off_bg=(100, 74, 130),
        reach_off_hover=(124, 94, 158),
        toggle_positive_bg=(68, 126, 92),
        toggle_positive_hover=(90, 154, 116),
        toggle_negative_bg=(116, 74, 58),
        toggle_negative_hover=(142, 94, 76),
        toggle_info_bg=(82, 122, 150),
        toggle_info_hover=(104, 144, 176),
        toggle_warm_bg=(136, 102, 66),
        toggle_warm_hover=(160, 124, 84),
        board_grad_top=(24, 22, 36),
        board_grad_bottom=(16, 14, 26),
        grid_line=(68, 60, 86),
        food_base=(244, 104, 88),
        food_dark=(156, 56, 44),
        food_light=(255, 178, 150),
        snake_head_base=(116, 226, 190),
        snake_head_dark=(56, 122, 98),
        snake_head_light=(194, 255, 232),
        snake_body_start=(108, 170, 236),
        snake_body_end=(64, 82, 134),
        snake_body_dark_start=(70, 108, 170),
        snake_body_dark_end=(40, 50, 98),
        snake_body_light_start=(182, 224, 255),
        snake_body_light_end=(128, 154, 216),
        hud_shadow=(12, 10, 18),
        hud_text=(246, 240, 252),
        game_over_text=(255, 194, 166),
    ),
}

_DEFAULT_TOKENS = DesignTokens(
    typography=TypographyTokens(),
    spacing=SpacingTokens(),
    components=ComponentTokens(),
)


def available_themes() -> list[str]:
    return sorted(_THEMES.keys())


def normalize_theme_name(name: str | None) -> str:
    key = str(name or "").strip().lower()
    if key in _THEMES:
        return key
    return "retro_forest_noir"


def get_theme(name: str | None) -> ThemePalette:
    theme_name = normalize_theme_name(name)
    if theme_name not in _THEMES:
        # Fallback to default theme if requested theme is not found
        theme_name = "retro_forest_noir"
    return _THEMES[theme_name]


def get_design_tokens(name: str | None = None, *, compact: bool = False) -> DesignTokens:
    _ = normalize_theme_name(name)
    if not compact:
        return _DEFAULT_TOKENS
    spacing = SpacingTokens(
        section_gap=max(0, int((_DEFAULT_TOKENS.spacing.section_gap * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        section_gap_large=max(0, int((_DEFAULT_TOKENS.spacing.section_gap_large * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        input_top_offset=max(0, int((_DEFAULT_TOKENS.spacing.input_top_offset * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        input_to_buttons_gap=max(0, int((_DEFAULT_TOKENS.spacing.input_to_buttons_gap * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        right_options_y=_DEFAULT_TOKENS.spacing.right_options_y,
        right_options_gap=_DEFAULT_TOKENS.spacing.right_options_gap,
        right_header_block_gap=max(0, int((_DEFAULT_TOKENS.spacing.right_header_block_gap * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        badge_gap_x=max(0, int((_DEFAULT_TOKENS.spacing.badge_gap_x * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        badge_gap_y=max(0, int((_DEFAULT_TOKENS.spacing.badge_gap_y * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        left_controls_top_padding=_DEFAULT_TOKENS.spacing.left_controls_top_padding,
        left_controls_raise_px=_DEFAULT_TOKENS.spacing.left_controls_raise_px,
        status_top_gap=_DEFAULT_TOKENS.spacing.status_top_gap,
        right_graph_bottom_reserve=_DEFAULT_TOKENS.spacing.right_graph_bottom_reserve,
        panel_inner_pad_x=_DEFAULT_TOKENS.spacing.panel_inner_pad_x,
        graph_margin_compact_threshold=_DEFAULT_TOKENS.spacing.graph_margin_compact_threshold,
        compact_gap_scale_num=_DEFAULT_TOKENS.spacing.compact_gap_scale_num,
        compact_gap_scale_den=_DEFAULT_TOKENS.spacing.compact_gap_scale_den,
    )
    components = ComponentTokens(
        input_height=max(30, int((_DEFAULT_TOKENS.components.input_height * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        button_row_height=max(32, int((_DEFAULT_TOKENS.components.button_row_height * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        right_options_height=max(26, int((_DEFAULT_TOKENS.components.right_options_height * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        badge_min_height=_DEFAULT_TOKENS.components.badge_min_height,
        badge_padding_x=_DEFAULT_TOKENS.components.badge_padding_x,
        badge_padding_y=_DEFAULT_TOKENS.components.badge_padding_y,
        border_radius_button=_DEFAULT_TOKENS.components.border_radius_button,
        border_radius_badge=_DEFAULT_TOKENS.components.border_radius_badge,
        max_badge_rows=_DEFAULT_TOKENS.components.max_badge_rows,
        graph_min_height=max(96, int((_DEFAULT_TOKENS.components.graph_min_height * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
        graph_min_height_large=max(110, int((_DEFAULT_TOKENS.components.graph_min_height_large * _DEFAULT_TOKENS.spacing.compact_gap_scale_num) / _DEFAULT_TOKENS.spacing.compact_gap_scale_den)),
    )
    return DesignTokens(
        typography=_DEFAULT_TOKENS.typography,
        spacing=spacing,
        components=components,
    )
