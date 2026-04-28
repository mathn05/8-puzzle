import os
import sys

import pygame

from src.core.benchmark import (
    AlgorithmSpec,
    benchmark_average_random_cases,
    run_solver_with_metrics,
)
from src.core.puzzle import GOAL_STATE, is_solvable
from src.core.solver_a import a_star
from src.core.solver_mm_search import mm_search
from src.heuristics import HEURISTIC_BY_KEY, HEURISTIC_SPECS
from src.utils.board import generate_random_solvable, parse_board_input

WHITE = (255, 255, 255)
BLACK = (26, 26, 26)
GRAY = (180, 188, 198)
LIGHT_GRAY = (238, 242, 247)
BLUE = (69, 119, 194)
DARK_BLUE = (42, 76, 125)
GREEN = (80, 164, 122)
RED = (210, 92, 92)
ORANGE = (229, 157, 74)
BG_COLOR = (243, 246, 250)
PANEL_BG = (252, 253, 255)
TABLE_HEADER = (224, 233, 244)
PANEL_BORDER = (214, 221, 232)

WINDOW_W = 1080
WINDOW_H = 760
TILE_SIZE = 102
BOARD_X = 78
BOARD_Y = 224
FONT_TILE = 44
FONT_UI = 22
FONT_SMALL = 17
COMPARE_CASES = 50

ALGORITHMS = [
    AlgorithmSpec("A_STAR", "A*", a_star),
    AlgorithmSpec("MM_SEARCH", "A* hai đầu", mm_search),
]
ALGORITHM_BY_KEY = {algorithm.key: algorithm for algorithm in ALGORITHMS}


def load_unicode_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
    ]

    for path in candidates:
        if os.path.exists(path):
            font = pygame.font.Font(path, size)
            font.set_bold(bold)
            return font

    return pygame.font.SysFont("Arial", size, bold=bold)


def format_board_inline(state):
    return " | ".join(" ".join(str(value) for value in row) for row in state)


def draw_panel(screen, rect, radius=18):
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=radius)
    pygame.draw.rect(screen, PANEL_BORDER, rect, width=2, border_radius=radius)


def draw_state_banner(screen, font, label, state, x, y, width):
    banner_rect = pygame.Rect(x, y, width, 48)
    pygame.draw.rect(screen, TABLE_HEADER, banner_rect, border_radius=12)
    pygame.draw.rect(screen, PANEL_BORDER, banner_rect, width=2, border_radius=12)

    text = font.render(f"{label}: {format_board_inline(state)}", True, BLACK)
    text_x = banner_rect.x + 16
    text_y = banner_rect.y + banner_rect.height // 2 - text.get_height() // 2
    screen.blit(text, (text_x, text_y))


def draw_button(screen, font_ui, text, x, y, w, h, color, hover_color, mouse_pos):
    rect = pygame.Rect(x, y, w, h)
    is_over = rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, hover_color if is_over else color, rect, border_radius=10)
    pygame.draw.rect(screen, DARK_BLUE, rect, width=2, border_radius=10)
    label = font_ui.render(text, True, WHITE)
    screen.blit(label, (x + w // 2 - label.get_width() // 2, y + h // 2 - label.get_height() // 2))
    return is_over


def draw_input_box(screen, font_ui, text, x, y, w, h, active=True, cursor_pos=0):
    border = BLUE if active else GRAY
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, WHITE, rect, border_radius=10)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=10)

    text_x = x + 14
    dummy_surface = font_ui.render("0", True, BLACK)
    text_y = y + h // 2 - dummy_surface.get_height() // 2

    if text:
        text_surface = font_ui.render(text, True, BLACK)
        screen.blit(text_surface, (text_x, text_y))
    else:
        placeholder = font_ui.render("Nhập 9 số...", True, GRAY)
        screen.blit(placeholder, (text_x, text_y))

    if active:
        cursor_x_offset = font_ui.size(text[:cursor_pos])[0] if text else 0
        cursor_x = text_x + cursor_x_offset
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            pygame.draw.line(
                screen,
                BLACK,
                (cursor_x, text_y),
                (cursor_x, text_y + dummy_surface.get_height()),
                2,
            )


def draw_board(screen, state, font_tile):
    board_rect = pygame.Rect(BOARD_X - 18, BOARD_Y - 18, TILE_SIZE * 3 + 36, TILE_SIZE * 3 + 36)
    draw_panel(screen, board_rect, radius=22)

    for row in range(3):
        for col in range(3):
            value = state[row][col]
            x = BOARD_X + col * TILE_SIZE
            y = BOARD_Y + row * TILE_SIZE
            rect = pygame.Rect(x + 5, y + 5, TILE_SIZE - 10, TILE_SIZE - 10)

            if value == 0:
                pygame.draw.rect(screen, LIGHT_GRAY, rect, border_radius=14)
                pygame.draw.rect(screen, GRAY, rect, width=2, border_radius=14)
                continue

            color = GREEN if value == GOAL_STATE[row][col] else BLUE
            pygame.draw.rect(screen, color, rect, border_radius=14)
            pygame.draw.rect(screen, DARK_BLUE, rect, width=2, border_radius=14)

            text = font_tile.render(str(value), True, WHITE)
            tx = x + TILE_SIZE // 2 - text.get_width() // 2
            ty = y + TILE_SIZE // 2 - text.get_height() // 2
            screen.blit(text, (tx, ty))


def draw_info(screen, font_ui, result_info, current_step, total_steps):
    panel_rect = pygame.Rect(470, 214, 530, 376)
    draw_panel(screen, panel_rect)

    title = font_ui.render("Thông tin lời giải", True, BLACK)
    screen.blit(title, (panel_rect.x + 28, panel_rect.y + 18))

    labels = [
        ("Heuristic", result_info.get("heuristic_name", "-")),
        ("Thuật toán", result_info.get("algorithm_name", "-")),
        ("Số bước", str(result_info.get("steps", "-"))),
        ("Node mở rộng", str(result_info.get("nodes_expanded", "-"))),
        ("Thời gian", f'{result_info.get("time_ms", "-")} ms'),
        ("Bộ nhớ", f'{result_info.get("memory_kb", "-")} KB'),
        ("Lần gọi heuristic", str(result_info.get("heuristic_calls", "-"))),
        ("Thời gian heuristic", f'{result_info.get("heuristic_time_ms", "-")} ms'),
        ("Bước hiện tại", f"{current_step}/{total_steps}" if total_steps else "-"),
    ]

    for index, (label, value) in enumerate(labels):
        y = panel_rect.y + 52 + index * 34
        lbl = font_ui.render(f"{label}:", True, BLACK)
        val = font_ui.render(str(value), True, BLUE)
        screen.blit(lbl, (panel_rect.x + 28, y))
        screen.blit(val, (panel_rect.x + 280, y))


def draw_compare_summary(screen, font_ui, results, y_start):
    if not results:
        return

    best_time = min(results, key=lambda item: item.get("time_ms", float("inf")))
    best_nodes = min(results, key=lambda item: item.get("nodes_expanded", float("inf")))

    lines = [
        f"TB nhanh nhất: {best_time['algorithm_name']} + {best_time['heuristic_name']} ({best_time['time_ms']} ms)",
        f"TB it node nhất: {best_nodes['algorithm_name']} + {best_nodes['heuristic_name']} ({best_nodes['nodes_expanded']} node)",
    ]

    for index, line in enumerate(lines):
        surface = font_ui.render(line, True, BLACK)
        screen.blit(surface, (78, y_start + index * 32))


def draw_compare_table(screen, font_small, results, scroll_offset):
    outer_rect = pygame.Rect(68, 292, 944, 352)
    draw_panel(screen, outer_rect, radius=16)

    columns = [
        ("Thuật toán", 86, 135),
        ("Heuristic", 225, 252),
        ("Bước", 482, 55),
        ("Node", 548, 78),
        ("Thời gian", 632, 86),
        ("Bộ nhớ", 722, 84),
        ("Số lần gọi h", 810, 92),
        ("Thời gian h", 910, 84),
    ]
    row_height = 32
    table_y = 308

    header_rect = pygame.Rect(80, table_y, 920, row_height)
    pygame.draw.rect(screen, TABLE_HEADER, header_rect, border_radius=8)

    for label, x, _ in columns:
        surface = font_small.render(label, True, BLACK)
        screen.blit(surface, (x, table_y + 7))

    visible_results = results[scroll_offset : scroll_offset + 8]
    for index, result in enumerate(visible_results):
        y = table_y + row_height + 8 + index * row_height
        bg_color = PANEL_BG if index % 2 == 0 else WHITE
        pygame.draw.rect(screen, bg_color, pygame.Rect(80, y, 920, row_height), border_radius=4)

        values = [
            result.get("algorithm_name", "-"),
            result.get("heuristic_name", "-"),
            str(result.get("steps", "-")),
            str(result.get("nodes_expanded", "-")),
            f'{result.get("time_ms", "-")} ms',
            f'{result.get("memory_kb", "-")} KB',
            str(result.get("heuristic_calls", "-")),
            f'{result.get("heuristic_time_ms", "-")} ms',
        ]

        for (_, x, width), value in zip(columns, values):
            text = font_small.render(str(value), True, BLACK)
            clipped = text
            if text.get_width() > width - 10:
                clipped = font_small.render(str(value)[: max(3, (width // 8) - 1)] + "...", True, BLACK)
            screen.blit(clipped, (x, y + 8))


def shorten_heuristic_label(label):
    mapping = {
        "Misplaced Tiles": "Misplaced",
        "Gaschnig": "Gaschnig",
        "Walking Distance": "Walking",
        "Inversion Distance": "Inversion",
        "Manhattan Distance": "Manhattan",
        "Manhattan + Linear Conflict": "M + LC",
    }
    return mapping.get(label, label)


def format_chart_value(value, metric_key):
    numeric_value = float(value)
    if metric_key == "nodes_expanded":
        if numeric_value >= 1000:
            return f"{numeric_value:,.0f}".replace(",", ".")
        if numeric_value >= 100:
            return f"{numeric_value:.1f}"
        return f"{numeric_value:.2f}"

    if numeric_value >= 10:
        return f"{numeric_value:.1f}"
    return f"{numeric_value:.2f}"


def draw_statistics_chart_view(screen, font_ui, font_small, results, metric_key, metric_title, metric_suffix):
    heading = font_ui.render(f"Thống kê trung bình trên {COMPARE_CASES} case random", True, BLACK)
    screen.blit(heading, (WINDOW_W // 2 - heading.get_width() // 2, 104))

    subheading = font_ui.render(metric_title, True, BLUE)
    screen.blit(subheading, (WINDOW_W // 2 - subheading.get_width() // 2, 142))

    note = font_small.render(
        "Mỗi heuristic gồm 2 cột. Gia trị được đặt bên dưới để tránh chồng chéo.",
        True,
        BLACK,
    )
    screen.blit(note, (WINDOW_W // 2 - note.get_width() // 2, 178))

    chart_rect = pygame.Rect(68, 214, 944, 430)
    draw_panel(screen, chart_rect, radius=16)

    if not results:
        empty_surface = font_small.render("Chưa có dữ liệu để vẽ biểu đồ.", True, RED)
        screen.blit(empty_surface, (chart_rect.x + 24, chart_rect.y + 24))
        return

    algorithms = ALGORITHMS
    heuristics = HEURISTIC_SPECS
    values_by_pair = {
        (item["algorithm_key"], item["heuristic_key"]): float(item.get(metric_key, 0.0))
        for item in results
    }

    plot_left = chart_rect.x + 76
    plot_right = chart_rect.x + chart_rect.w - 34
    plot_top = chart_rect.y + 42
    plot_bottom = chart_rect.y + chart_rect.h - 146
    plot_width = plot_right - plot_left
    plot_height = plot_bottom - plot_top

    max_value = max(values_by_pair.values(), default=1.0)
    if max_value <= 0:
        max_value = 1.0

    axis_color = (120, 132, 148)
    grid_color = (225, 231, 239)
    label_color = BLACK
    bar_colors = [BLUE, GREEN]

    pygame.draw.line(screen, axis_color, (plot_left, plot_top), (plot_left, plot_bottom), 2)
    pygame.draw.line(screen, axis_color, (plot_left, plot_bottom), (plot_right, plot_bottom), 2)

    tick_count = 5
    for tick in range(tick_count):
        ratio = tick / (tick_count - 1)
        y = plot_bottom - int(plot_height * ratio)
        pygame.draw.line(screen, grid_color, (plot_left, y), (plot_right, y), 1)
        tick_value = round(max_value * ratio, 2)
        tick_label = font_small.render(f"{tick_value:g}", True, label_color)
        screen.blit(tick_label, (plot_left - tick_label.get_width() - 10, y - tick_label.get_height() // 2))

    group_width = plot_width / max(1, len(heuristics))
    bar_width = max(22, min(38, int(group_width * 0.26)))
    gap_inside_group = 14

    for index, heuristic_spec in enumerate(heuristics):
        group_center_x = plot_left + group_width * index + group_width / 2
        total_bars_width = bar_width * len(algorithms) + gap_inside_group * (len(algorithms) - 1)
        start_x = int(group_center_x - total_bars_width / 2)
        group_left = start_x - 14
        group_box_width = total_bars_width + 28

        info_box = pygame.Rect(group_left, plot_bottom + 8, group_box_width, 64)
        pygame.draw.rect(screen, LIGHT_GRAY, info_box, border_radius=10)
        pygame.draw.rect(screen, PANEL_BORDER, info_box, width=1, border_radius=10)

        for algo_index, algorithm in enumerate(algorithms):
            value = values_by_pair.get((algorithm.key, heuristic_spec.key), 0.0)
            bar_height = int((value / max_value) * (plot_height - 8))
            bar_x = start_x + algo_index * (bar_width + gap_inside_group)
            bar_y = plot_bottom - bar_height

            pygame.draw.rect(
                screen,
                bar_colors[algo_index % len(bar_colors)],
                pygame.Rect(bar_x, bar_y, bar_width, bar_height),
                border_radius=2,
            )

            short_name = "A*" if algo_index == 0 else "2 dau"
            value_text = f"{short_name}: {format_chart_value(value, metric_key)}"
            value_label = font_small.render(value_text, True, bar_colors[algo_index % len(bar_colors)])
            value_x = group_left + 10
            value_y = info_box.y + 8 + algo_index * 24
            screen.blit(value_label, (value_x, value_y))

        heuristic_label = font_small.render(shorten_heuristic_label(heuristic_spec.label), True, label_color)
        screen.blit(
            heuristic_label,
            (int(group_center_x - heuristic_label.get_width() // 2), info_box.y + info_box.h + 6),
        )

    legend_y = chart_rect.y + 12
    legend_x = chart_rect.x + 28
    for algo_index, algorithm in enumerate(algorithms):
        color = bar_colors[algo_index % len(bar_colors)]
        pygame.draw.rect(screen, color, pygame.Rect(legend_x, legend_y, 18, 18), border_radius=4)
        legend_text = font_small.render(algorithm.label, True, BLACK)
        screen.blit(legend_text, (legend_x + 28, legend_y - 1))
        legend_x += 180

    unit_text = font_small.render(f"Đơn vị: {metric_suffix}", True, BLACK)
    screen.blit(unit_text, (chart_rect.x + chart_rect.w - unit_text.get_width() - 24, chart_rect.y + 18))


def run():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("8-Puzzle - So sánh heuristic")

    font_tile = load_unicode_font(FONT_TILE, bold=True)
    font_ui = load_unicode_font(FONT_UI)
    font_title = load_unicode_font(30, bold=True)
    font_small = load_unicode_font(FONT_SMALL)
    clock = pygame.time.Clock()

    app_mode = "mode_select"
    start = GOAL_STATE
    pending_state = None
    current_mode_label = ""
    message = "Chọn chế độ để bắt đầu."
    manual_text = ""
    cursor_pos = 0
    selected_algo = "A_STAR"
    compare_origin = "mode_select"

    solution_path = []
    current_step = 0
    result_info = {}
    compare_results = []
    compare_scroll = 0
    is_playing = False
    play_timer = 0
    play_interval = 600
    text_input_enabled = False

    input_rect = pygame.Rect(275, 270, 530, 56)
    center_card = pygame.Rect(250, 156, 580, 396)
    heuristic_card = pygame.Rect(96, 118, 888, 560)

    heuristic_buttons = []
    button_w = 320
    button_h = 54
    left_x = heuristic_card.x + 56
    right_x = heuristic_card.x + heuristic_card.w - 56 - button_w
    top_y = heuristic_card.y + 210
    row_gap = 82
    for index, spec in enumerate(HEURISTIC_SPECS):
        x = left_x if index % 2 == 0 else right_x
        y = top_y + (index // 2) * row_gap
        heuristic_buttons.append((spec.key, pygame.Rect(x, y, button_w, button_h)))

    def solve_from_start(state, heuristic_key):
        nonlocal start, solution_path, current_step, result_info, is_playing, play_timer, message

        start = state
        current_step = 0
        is_playing = False
        play_timer = 0

        if not is_solvable(start):
            solution_path = []
            result_info = {}
            message = "Trạng thái này không giải được."
            return False

        algorithm = ALGORITHM_BY_KEY[selected_algo]
        heuristic_spec = HEURISTIC_BY_KEY[heuristic_key]
        result = run_solver_with_metrics(start, algorithm, heuristic_spec)

        if not result.get("solved"):
            solution_path = []
            result_info = {}
            message = "Không tìm thấy lời giải."
            return False

        solution_path = result["path"]
        result_info = result
        message = ""
        return True

    def run_comparison():
        nonlocal compare_results, compare_scroll, message

        compare_results = benchmark_average_random_cases(
            ALGORITHMS,
            HEURISTIC_SPECS,
            num_cases=COMPARE_CASES,
        )
        compare_results.sort(
            key=lambda item: (
                item.get("nodes_expanded", float("inf")),
                item.get("time_ms", float("inf")),
            )
        )
        compare_scroll = 0
        message = ""
        return True

    while True:
        dt = clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        if app_mode == "manual_input" and not text_input_enabled:
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(input_rect)
            text_input_enabled = True
        elif app_mode != "manual_input" and text_input_enabled:
            pygame.key.stop_text_input()
            text_input_enabled = False

        title = font_title.render("8-Puzzle: So sánh heuristic và thuật toán", True, BLACK)
        screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 34))

        prev_hover = next_hover = play_hover = reset_hover = False
        change_heuristic_hover = menu_hover = False
        random_hover = manual_mode_hover = solve_manual_hover = back_hover = False
        main_compare_hover = False
        algo_toggle_hover = compare_back_hover = compare_again_hover = False
        view_stats_hover = stats_back_hover = stats_switch_hover = False
        back_h_hover = False

        if app_mode == "mode_select":
            draw_panel(screen, center_card)
            hint = font_ui.render("Chọn cách tạo trạng thái đầu vào", True, BLACK)
            screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, center_card.y + 58))

            random_hover = draw_button(screen, font_ui, "Tạo trạng thái ngẫu nhiên", 360, 262, 360, 58, BLUE, DARK_BLUE, mouse_pos)
            manual_mode_hover = draw_button(screen, font_ui, "Nhập trạng thái thủ công", 360, 350, 360, 58, GREEN, (48, 138, 96), mouse_pos)

            main_compare_hover = draw_button(screen, font_ui, "So sánh chi phí", 360, 438, 360, 58, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg_color = RED if "không" in message.lower() else BLACK
                msg = font_ui.render(message, True, msg_color)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, center_card.y + 344))

        elif app_mode == "manual_input":
            draw_panel(screen, center_card)
            guide = font_ui.render("Nhập 9 số từ 0 đến 8", True, BLACK)
            screen.blit(guide, (WINDOW_W // 2 - guide.get_width() // 2, center_card.y + 56))

            draw_input_box(screen, font_ui, manual_text, input_rect.x, input_rect.y, input_rect.w, input_rect.h, True, cursor_pos)

            solve_manual_hover = draw_button(screen, font_ui, "Tiếp tục", 356, 376, 160, 48, BLUE, DARK_BLUE, mouse_pos)
            back_hover = draw_button(screen, font_ui, "Quay lại", 560, 376, 160, 48, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg = font_ui.render(message, True, RED)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, 456))

        elif app_mode == "heuristic_select":
            draw_panel(screen, heuristic_card)
            hint = font_ui.render("Chọn heuristic để giải hoặc benchmark", True, BLACK)
            screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, heuristic_card.y + 34))

            algo_text = "Thuật toán: A*" if selected_algo == "A_STAR" else "Thuật toán: A* hai đầu"
            algo_color = (98, 116, 196) if selected_algo == "A_STAR" else (192, 108, 96)
            algo_hover_color = (74, 92, 168) if selected_algo == "A_STAR" else (168, 86, 76)
            algo_toggle_hover = draw_button(
                screen,
                font_ui,
                algo_text,
                WINDOW_W // 2 - 190,
                heuristic_card.y + 76,
                380,
                48,
                algo_color,
                algo_hover_color,
                mouse_pos,
            )

            if pending_state is not None:
                draw_state_banner(
                    screen,
                    font_small,
                    "Trạng thái hiện tại",
                    pending_state,
                    heuristic_card.x + 54,
                    heuristic_card.y + 136,
                    heuristic_card.w - 108,
                )

            for spec_key, rect in heuristic_buttons:
                spec = HEURISTIC_BY_KEY[spec_key]
                is_primary = spec_key in {"misplaced_tiles", "gaschnig"}
                is_secondary = spec_key in {"walking_distance", "inversion_distance"}
                color = RED if is_primary else GREEN if is_secondary else BLUE
                hover = (181, 73, 73) if is_primary else (58, 142, 102) if is_secondary else DARK_BLUE
                draw_button(screen, font_ui, spec.label, rect.x, rect.y, rect.w, rect.h, color, hover, mouse_pos)

            back_h_hover = draw_button(screen, font_ui, "Quay lại", 450, heuristic_card.y + 468, 180, 46, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg = font_ui.render(message, True, BLACK)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, heuristic_card.y + 528))

        elif app_mode == "compare_view":
            heading = font_ui.render(f"Bảng so sánh trung bình trên {COMPARE_CASES} case random", True, BLACK)
            screen.blit(heading, (WINDOW_W // 2 - heading.get_width() // 2, 118))

            benchmark_note = font_small.render(
                "Các chỉ số là trung bình trên cùng số lượng case ngẫu nhiên cho mỗi tổ hợp.",
                True,
                BLACK,
            )
            screen.blit(benchmark_note, (68, 160))

            draw_compare_summary(screen, font_ui, compare_results, 214)
            draw_compare_table(screen, font_small, compare_results, compare_scroll)
            view_stats_hover = draw_button(screen, font_ui, "Xem thống kê", 560, 670, 148, 42, GREEN, (58, 142, 102), mouse_pos)

            compare_again_hover = draw_button(screen, font_ui, "Chạy lại", 720, 670, 130, 42, BLUE, DARK_BLUE, mouse_pos)
            compare_back_hover = draw_button(screen, font_ui, "Quay lại", 872, 670, 130, 42, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg = font_small.render(message, True, RED)
                screen.blit(msg, (78, 680))

        elif app_mode == "stats_nodes_view":
            draw_statistics_chart_view(
                screen,
                font_ui,
                font_small,
                compare_results,
                "nodes_expanded",
                "Biểu đồ so sánh số node mở rộng",
                "node",
            )
            stats_switch_hover = draw_button(screen, font_ui, "Bảng thời gian", 548, 676, 166, 42, GREEN, (58, 142, 102), mouse_pos)
            compare_again_hover = draw_button(screen, font_ui, "Chạy lại", 726, 676, 130, 42, BLUE, DARK_BLUE, mouse_pos)
            stats_back_hover = draw_button(screen, font_ui, "Quay lại", 868, 676, 130, 42, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg = font_small.render(message, True, RED)
                screen.blit(msg, (70, 706))

        elif app_mode == "stats_time_view":
            draw_statistics_chart_view(
                screen,
                font_ui,
                font_small,
                compare_results,
                "time_ms",
                "Biểu đồ so sánh thời gian chạy",
                "ms",
            )
            stats_switch_hover = draw_button(screen, font_ui, "Bảng số node", 548, 676, 166, 42, GREEN, (58, 142, 102), mouse_pos)
            compare_again_hover = draw_button(screen, font_ui, "Chạy lại", 726, 676, 130, 42, BLUE, DARK_BLUE, mouse_pos)
            stats_back_hover = draw_button(screen, font_ui, "Quay lại", 868, 676, 130, 42, ORANGE, (204, 130, 46), mouse_pos)

            if message:
                msg = font_small.render(message, True, RED)
                screen.blit(msg, (70, 706))

        else:
            current_state = solution_path[current_step] if solution_path else start
            draw_state_banner(screen, font_small, "Trạng thái hiện tại", current_state, 68, 104, 932)
            draw_board(screen, current_state, font_tile)

            mode_text = font_ui.render(
                f"Chế độ: {current_mode_label}  |  {result_info.get('algorithm_name', '-')}",
                True,
                BLACK,
            )
            screen.blit(mode_text, (BOARD_X, 182))

            draw_info(screen, font_ui, result_info, current_step, len(solution_path) - 1 if solution_path else 0)

            btn_y = 604
            prev_hover = draw_button(screen, font_ui, "< Prev", 78, btn_y, 110, 44, BLUE, DARK_BLUE, mouse_pos)
            next_hover = draw_button(screen, font_ui, "Next >", 200, btn_y, 110, 44, BLUE, DARK_BLUE, mouse_pos)
            play_label = "Pause" if is_playing else "Play"
            play_hover = draw_button(screen, font_ui, play_label, 322, btn_y, 126, 44, GREEN, (58, 142, 102), mouse_pos)
            reset_hover = draw_button(screen, font_ui, "Reset", 460, btn_y, 110, 44, RED, (181, 73, 73), mouse_pos)
            change_heuristic_hover = draw_button(screen, font_ui, "Đổi heuristic", 648, btn_y, 160, 44, ORANGE, (204, 130, 46), mouse_pos)
            menu_hover = draw_button(screen, font_ui, "Menu", 820, btn_y, 116, 44, ORANGE, (204, 130, 46), mouse_pos)

        if app_mode == "solver_view" and is_playing and solution_path:
            play_timer += dt
            if play_timer >= play_interval:
                play_timer = 0
                if current_step < len(solution_path) - 1:
                    current_step += 1
                else:
                    is_playing = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEWHEEL and app_mode == "compare_view":
                max_scroll = max(0, len(compare_results) - 8)
                compare_scroll = max(0, min(max_scroll, compare_scroll - event.y))

            if event.type == pygame.MOUSEBUTTONDOWN:
                if app_mode == "mode_select":
                    if random_hover:
                        current_mode_label = "Ngẫu nhiên"
                        pending_state = generate_random_solvable()
                        app_mode = "heuristic_select"
                        message = ""
                    elif manual_mode_hover:
                        app_mode = "manual_input"
                        manual_text = ""
                        cursor_pos = 0
                        message = ""
                    elif main_compare_hover:
                        compare_origin = "mode_select"
                        if run_comparison():
                            app_mode = "compare_view"

                elif app_mode == "manual_input":
                    if solve_manual_hover:
                        parsed_state, error = parse_board_input(manual_text)
                        if error:
                            message = error
                        elif not is_solvable(parsed_state):
                            message = "Trạng thái nhập vào không giải được."
                        else:
                            current_mode_label = "Nhập thủ công"
                            pending_state = parsed_state
                            app_mode = "heuristic_select"
                            message = ""
                    elif back_hover:
                        app_mode = "mode_select"
                        message = "Chọn chế độ để bắt đầu."
                    elif input_rect.collidepoint(event.pos):
                        click_x = event.pos[0] - (input_rect.x + 14)
                        if click_x <= 0:
                            cursor_pos = 0
                        else:
                            best_pos = 0
                            min_diff = float("inf")
                            for index in range(len(manual_text) + 1):
                                text_width = font_ui.size(manual_text[:index])[0]
                                diff = abs(text_width - click_x)
                                if diff < min_diff:
                                    min_diff = diff
                                    best_pos = index
                            cursor_pos = best_pos

                elif app_mode == "heuristic_select":
                    if algo_toggle_hover:
                        selected_algo = "MM_SEARCH" if selected_algo == "A_STAR" else "A_STAR"
                    elif back_h_hover:
                        app_mode = "mode_select" if current_mode_label == "Ngẫu nhiên" else "manual_input"
                        message = ""
                    else:
                        for heuristic_key, rect in heuristic_buttons:
                            if rect.collidepoint(event.pos) and solve_from_start(pending_state, heuristic_key):
                                app_mode = "solver_view"
                                break

                elif app_mode == "compare_view":
                    if view_stats_hover:
                        app_mode = "stats_nodes_view"
                        message = ""
                    elif compare_again_hover:
                        run_comparison()
                    elif compare_back_hover:
                        app_mode = compare_origin
                        message = ""

                elif app_mode == "stats_nodes_view":
                    if stats_switch_hover:
                        app_mode = "stats_time_view"
                        message = ""
                    elif compare_again_hover:
                        run_comparison()
                    elif stats_back_hover:
                        app_mode = "compare_view"
                        message = ""

                elif app_mode == "stats_time_view":
                    if stats_switch_hover:
                        app_mode = "stats_nodes_view"
                        message = ""
                    elif compare_again_hover:
                        run_comparison()
                    elif stats_back_hover:
                        app_mode = "compare_view"
                        message = ""

                else:
                    if prev_hover and current_step > 0:
                        current_step -= 1
                        is_playing = False
                    if next_hover and solution_path and current_step < len(solution_path) - 1:
                        current_step += 1
                        is_playing = False
                    if play_hover and solution_path:
                        is_playing = not is_playing
                        play_timer = 0
                    if reset_hover:
                        current_step = 0
                        is_playing = False
                    if change_heuristic_hover:
                        pending_state = start
                        app_mode = "heuristic_select"
                        is_playing = False
                        message = ""
                    if menu_hover:
                        app_mode = "mode_select"
                        is_playing = False
                        message = "Chọn chế độ để bắt đầu."

            if event.type == pygame.KEYDOWN and app_mode == "manual_input":
                if event.key == pygame.K_RETURN:
                    parsed_state, error = parse_board_input(manual_text)
                    if error:
                        message = error
                    elif not is_solvable(parsed_state):
                        message = "Trạng thái nhập vào không giải được."
                    else:
                        current_mode_label = "Nhập thủ công"
                        pending_state = parsed_state
                        app_mode = "heuristic_select"
                        message = ""
                elif event.key == pygame.K_BACKSPACE:
                    if cursor_pos > 0:
                        manual_text = manual_text[: cursor_pos - 1] + manual_text[cursor_pos:]
                        cursor_pos -= 1
                elif event.key == pygame.K_DELETE:
                    if cursor_pos < len(manual_text):
                        manual_text = manual_text[:cursor_pos] + manual_text[cursor_pos + 1 :]
                elif event.key == pygame.K_LEFT:
                    if cursor_pos > 0:
                        cursor_pos -= 1
                elif event.key == pygame.K_RIGHT:
                    if cursor_pos < len(manual_text):
                        cursor_pos += 1

            if event.type == pygame.TEXTINPUT and app_mode == "manual_input":
                filtered = "".join(char for char in event.text if char.isdigit() or char in {" ", ","})
                if filtered:
                    manual_text = manual_text[:cursor_pos] + filtered + manual_text[cursor_pos:]
                    cursor_pos += len(filtered)
                    if len(manual_text) > 40:
                        manual_text = manual_text[:40]
                        cursor_pos = min(cursor_pos, 40)

        pygame.display.flip()
