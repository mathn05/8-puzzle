# src/core/puzzle.py

GOAL_STATE = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 0)  # 0 là ô trống
)

def is_solvable(state):
    """
    Kiểm tra trạng thái có giải được không.
    Đếm số nghịch thế (inversion)
    """
    flat = [x for row in state for x in row if x != 0]
    inversions = 0
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if flat[i] > flat[j]:
                inversions += 1
    return inversions % 2 == 0

def find_blank(state):
    """Trả về (row, col) của ô trống (giá trị 0)."""
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                return (r, c)


def get_neighbors(state):
    """
    Trả về danh sách các trạng thái có thể đi tiếp bằng cách di chuyển ô trống theo 4 hướng.
    """
    neighbors = []
    r, c = find_blank(state)

    # (delta_row, delta_col, tên hướng)
    directions = [(-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")]

    for dr, dc, direction in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            # Tạo bản sao và hoán đổi ô trống với ô kế bên
            new_state = [list(row) for row in state]
            new_state[r][c], new_state[nr][nc] = new_state[nr][nc], new_state[r][c]
            neighbors.append(tuple(tuple(row) for row in new_state))

    return neighbors