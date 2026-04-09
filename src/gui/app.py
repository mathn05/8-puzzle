# src/gui/app.py

import pygame
import sys
import os
from src.core.puzzle import is_solvable, GOAL_STATE
from src.core.solver import a_star
from src.heuristics.functions import *
from src.utils.board import generate_random_solvable, parse_board_input

# Màu sắc
WHITE      = (255, 255, 255)
BLACK      = (20,  20,  20)
GRAY       = (200, 200, 200)
LIGHT_GRAY = (240, 240, 240)
BLUE       = (70,  130, 180)
DARK_BLUE  = (40,  90,  140)
GREEN      = (60,  179, 113)
RED        = (220, 80,  80)
ORANGE     = (255, 165, 0)
BG_COLOR   = (245, 245, 250)

# Kích thước
WINDOW_W   = 700
WINDOW_H   = 600
TILE_SIZE  = 120
BOARD_X    = 50     # vị trí bảng trên màn hình
BOARD_Y    = 100
FONT_TILE  = 48     # cỡ chữ số trong ô
FONT_UI    = 22     # cỡ chữ giao diện


def load_unicode_font(size, bold=False):
    """Ưu tiên font có hỗ trợ tiếng Việt tốt trên Windows."""
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


def draw_input_box(screen, font_ui, text, x, y, w, h, active=True):
    """Vẽ ô nhập liệu cho chế độ manual."""
    border = BLUE if active else GRAY
    rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(screen, WHITE, rect, border_radius=8)
    pygame.draw.rect(screen, border, rect, width=2, border_radius=8)

    text_surface = font_ui.render(text or "Nhập 9 số...", True, BLACK if text else GRAY)
    screen.blit(text_surface, (x + 10, y + h // 2 - text_surface.get_height() // 2))

def draw_board(screen, state, font_tile, solving=False):
    """Vẽ bảng 3x3 lên màn hình."""
    for r in range(3):
        for c in range(3):
            val  = state[r][c]
            x    = BOARD_X + c * TILE_SIZE
            y    = BOARD_Y + r * TILE_SIZE

            rect = pygame.Rect(x + 4, y + 4, TILE_SIZE - 8, TILE_SIZE - 8)

            if val == 0:
                # Ô trống
                pygame.draw.rect(screen, LIGHT_GRAY, rect, border_radius=12)
                pygame.draw.rect(screen, GRAY, rect, width=2, border_radius=12)
            else:
                # Ô số — xanh nếu đang giải, xanh đậm nếu đúng vị trí
                goal_val = GOAL_STATE[r][c]
                color = GREEN if val == goal_val else BLUE
                pygame.draw.rect(screen, color, rect, border_radius=12)
                pygame.draw.rect(screen, DARK_BLUE, rect, width=2, border_radius=12)

                # Vẽ số
                text = font_tile.render(str(val), True, WHITE)
                tx   = x + TILE_SIZE // 2 - text.get_width()  // 2
                ty   = y + TILE_SIZE // 2 - text.get_height() // 2
                screen.blit(text, (tx, ty))

def draw_info(screen, font_ui, steps, nodes, time_ms, current_step, total_steps):
    """Vẽ thông tin kết quả bên phải bảng."""
    info_x = BOARD_X + 3 * TILE_SIZE + 40

    labels = [
        ("Số bước:",        str(steps)         if steps  else "-"),
        ("Node mở rộng:",   str(nodes)         if nodes  else "-"),
        ("Thời gian:",      f"{time_ms} ms"    if time_ms else "-"),
        ("Bước hiện tại:",  f"{current_step}/{total_steps}" if total_steps else "-"),
    ]

    for i, (label, value) in enumerate(labels):
        y = 120 + i * 60
        lbl = font_ui.render(label, True, BLACK)
        val = font_ui.render(value, True, BLUE)
        screen.blit(lbl, (info_x, y))
        screen.blit(val, (info_x, y + 26))


def draw_button(screen, font_ui, text, x, y, w, h, color, hover_color, mouse_pos):
    """Vẽ nút bấm, đổi màu khi hover."""
    rect    = pygame.Rect(x, y, w, h)
    is_over = rect.collidepoint(mouse_pos)
    pygame.draw.rect(screen, hover_color if is_over else color, rect, border_radius=8)
    pygame.draw.rect(screen, DARK_BLUE, rect, width=2, border_radius=8)
    label = font_ui.render(text, True, WHITE)
    screen.blit(label, (x + w//2 - label.get_width()//2, y + h//2 - label.get_height()//2))
    return is_over


def run():
    pygame.init()
    screen  = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("8-Puzzle — A* Solver")

    font_tile = load_unicode_font(FONT_TILE, bold=True)
    font_ui   = load_unicode_font(FONT_UI)
    font_title = load_unicode_font(28, bold=True)
    clock     = pygame.time.Clock()

    # Trạng thái ứng dụng: mode_select -> manual_input -> solver_view
    app_mode = "mode_select"
    start = GOAL_STATE
    pending_state = None
    current_mode_label = ""
    message = "Chọn chế độ để bắt đầu."
    manual_text = ""

    # Kết quả giải
    solution_path  = []
    current_step   = 0
    result_info    = {}
    is_playing     = False
    play_timer     = 0
    PLAY_INTERVAL  = 600  # ms mỗi bước khi auto-play
    text_input_enabled = False

    input_rect = pygame.Rect(100, 210, 500, 52)

    def solve_from_start(state, heuristic_fn):
        """Giải puzzle từ trạng thái đầu vào và cập nhật trạng thái UI."""
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

        result = a_star(start, heuristic_fn)
        if not result:
            solution_path = []
            result_info = {}
            message = "Không tìm thấy lời giải."
            return False

        solution_path = result["path"]
        result_info = result
        message = ""
        return True

    while True:
        dt         = clock.tick(60)
        mouse_pos  = pygame.mouse.get_pos()
        screen.fill(BG_COLOR)

        # Bật/tắt text input theo màn hình để IME (UniKey) hoạt động ổn định.
        if app_mode == "manual_input" and not text_input_enabled:
            pygame.key.start_text_input()
            pygame.key.set_text_input_rect(input_rect)
            text_input_enabled = True
        elif app_mode != "manual_input" and text_input_enabled:
            pygame.key.stop_text_input()
            text_input_enabled = False

        # --- Tiêu đề ---
        title = font_title.render("8-Puzzle  —  A* Solver", True, BLACK)
        screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 30))

        prev_hover = next_hover = play_hover = reset_hover = False
        random_hover = manual_mode_hover = solve_manual_hover = back_hover = menu_hover = False
        mt_hover = manhattan_hover = mlc_hover = id_hover = max_hover = gaschnig_hover = back_h_hover = False
        change_heuris_hover = menu_hover = False

        if app_mode == "mode_select":
            hint = font_ui.render("Chọn chế độ chơi:", True, BLACK)
            screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, 120))

            random_hover = draw_button(
                screen, font_ui, "Random Case", 200, 210, 300, 56, BLUE, DARK_BLUE, mouse_pos
            )
            manual_mode_hover = draw_button(
                screen, font_ui, "Nhập thủ công", 200, 290, 300, 56, GREEN, (30, 140, 80), mouse_pos
            )

            if message:
                msg_color = RED if "không" in message.lower() else BLACK
                msg = font_ui.render(message, True, msg_color)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, 380))

        elif app_mode == "manual_input":
            guide = font_ui.render("Nhập 9 số (0..8), ví dụ: 1 2 3 4 5 6 7 8 0", True, BLACK)
            screen.blit(guide, (WINDOW_W // 2 - guide.get_width() // 2, 140))

            draw_input_box(screen, font_ui, manual_text, 100, 210, 500, 52, active=True)

            solve_manual_hover = draw_button(
                screen, font_ui, "Giải", 200, 300, 130, 46, BLUE, DARK_BLUE, mouse_pos
            )
            back_hover = draw_button(
                screen, font_ui, "Quay lại", 360, 300, 130, 46, ORANGE, (230, 140, 0), mouse_pos
            )

            if message:
                msg = font_ui.render(message, True, RED)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, 380))

        elif app_mode == "heuristic_select":
            hint = font_ui.render("Chọn hàm Heuristic để giải:", True, BLACK)
            screen.blit(hint, (WINDOW_W // 2 - hint.get_width() // 2, 80))

            mt_hover = draw_button(
                screen, font_ui, "Misplaced Tiles", 80, 130, 250, 56, RED, (153, 0, 0), mouse_pos
            )
            gaschnig_hover = draw_button(
                screen, font_ui, "Gaschnig", 370, 130, 250, 56, RED, (153, 0, 0), mouse_pos
            )

            manhattan_hover = draw_button(
                screen, font_ui, "Manhattan Distance", 370, 200, 250, 56, GREEN, (30, 140, 80), mouse_pos
            )
            id_hover = draw_button(
                screen, font_ui, "Inversion Distance", 80, 200, 250, 56, GREEN, (30, 140, 80), mouse_pos
            )

            tmp = draw_button(
                screen, font_ui, "temp", 80, 270, 250, 56, (70, 130, 180), (40, 90, 140), mouse_pos
            )
            mlc_hover = draw_button(
                screen, font_ui, "Manhat + Linear Conf", 370, 270, 250, 56, (70, 130, 180), (40, 90, 140), mouse_pos
            )

            max_hover = draw_button(
                screen, font_ui, "Max Heuristic", 80, 350, 540, 56, (128, 90, 213), (85, 60, 154), mouse_pos
            )

            back_h_hover = draw_button(
                screen, font_ui, "Quay lại", 285, 430, 130, 46, ORANGE, (230, 140, 0), mouse_pos
            )

            if message:
                msg = font_ui.render(message, True, BLACK)
                screen.blit(msg, (WINDOW_W // 2 - msg.get_width() // 2, 510))

        else:
            # --- Bảng hiện tại ---
            current_state = (
                solution_path[current_step]
                if solution_path else start
            )
            draw_board(screen, current_state, font_tile)

            mode_text = font_ui.render(f"Chế độ: {current_mode_label}", True, BLACK)
            screen.blit(mode_text, (BOARD_X, 70))

            # --- Thông tin ---
            draw_info(
                screen, font_ui,
                result_info.get("steps"),
                result_info.get("nodes_expanded"),
                result_info.get("time_ms"),
                current_step,
                len(solution_path) - 1 if solution_path else 0
            )

            # --- Các nút bấm ---
            btn_y = WINDOW_H - 80
            prev_hover = draw_button(screen, font_ui, "< Prev",  35,  btn_y, 90, 44, BLUE, DARK_BLUE, mouse_pos)
            next_hover = draw_button(screen, font_ui, "Next >",  135, btn_y, 90, 44, BLUE, DARK_BLUE, mouse_pos)
            play_label = "Pause" if is_playing else "Play"
            play_hover = draw_button(screen, font_ui, play_label, 235, btn_y, 90, 44, GREEN, (30, 140, 80), mouse_pos)
            reset_hover = draw_button(screen, font_ui, "Reset",  335, btn_y, 90, 44, RED, (180, 50, 50), mouse_pos)
            change_heuris_hover = draw_button(screen, font_ui, "Đổi Heuris", 435, btn_y, 130, 44, ORANGE, (230, 140, 0), mouse_pos)
            menu_hover = draw_button(screen, font_ui, "Menu", 575, btn_y, 90, 44, ORANGE, (230, 140, 0), mouse_pos)

        # --- Auto-play ---
        if app_mode == "solver_view" and is_playing and solution_path:
            play_timer += dt
            if play_timer >= PLAY_INTERVAL:
                play_timer = 0
                if current_step < len(solution_path) - 1:
                    current_step += 1
                else:
                    is_playing = False

        # --- Xử lý sự kiện ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if app_mode == "mode_select":
                    if random_hover:
                        current_mode_label = "Random"
                        pending_state = generate_random_solvable()
                        app_mode = "heuristic_select"
                        message = "Chọn Heuristic"
                    elif manual_mode_hover:
                        app_mode = "manual_input"
                        manual_text = ""
                        message = ""

                elif app_mode == "manual_input":
                    if solve_manual_hover:
                        parsed_state, error = parse_board_input(manual_text)
                        if error:
                            message = error
                        elif not is_solvable(parsed_state):
                            message = "Trạng thái nhập vào không giải được."
                        else:
                            current_mode_label = "Người chơi nhập"
                            pending_state = parsed_state
                            app_mode = "heuristic_select"
                            message = "Chọn Heuristic"
                    elif back_hover:
                        app_mode = "mode_select"
                        message = "Chọn chế độ để bắt đầu."

                elif app_mode == "heuristic_select":
                    if mt_hover:
                        if solve_from_start(pending_state, misplaced_tiles):
                            app_mode = "solver_view"

                    elif manhattan_hover:
                        if solve_from_start(pending_state, manhattan):
                            app_mode = "solver_view"

                    elif mlc_hover:
                        if solve_from_start(pending_state, manhattan_linear_conflict):
                            app_mode = "solver_view"

                    elif id_hover:
                        if solve_from_start(pending_state, inversion_distance):
                            app_mode = "solver_view"

                    elif gaschnig_hover:
                        if solve_from_start(pending_state, gaschnig):
                            app_mode = "solver_view"

                    elif max_hover:
                        if solve_from_start(pending_state, max_heuristic):
                            app_mode = "solver_view"

                    elif back_h_hover:
                        if current_mode_label == "Random":
                            app_mode = "mode_select"
                        else:
                            app_mode = "manual_input"
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

                    if change_heuris_hover:
                        pending_state = start
                        app_mode = "heuristic_select"
                        is_playing = False
                        message = "Chọn lại hàm Heuristic"

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
                        current_mode_label = "Người chơi nhập"
                        pending_state = parsed_state
                        app_mode = "heuristic_select"
                        message = "Chọn Heuristic"
                elif event.key == pygame.K_BACKSPACE:
                    manual_text = manual_text[:-1]

            if event.type == pygame.TEXTINPUT and app_mode == "manual_input":
                filtered = "".join(ch for ch in event.text if ch.isdigit() or ch in {" ", ","})
                if filtered:
                    manual_text += filtered
                    if len(manual_text) > 40:
                        manual_text = manual_text[:40]

        pygame.display.flip()