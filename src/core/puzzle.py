# src/core/puzzle.py

GOAL_STATE = (
    (1, 2, 3),
    (4, 5, 6),
    (7, 8, 0)  # 0 là ô trống
)

def count_inversions(state):
    flat = [x for row in state for x in row if x != 0]
    inversions = 0
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if flat[i] > flat[j]:
                inversions += 1
    return inversions

def is_solvable(state, goal = GOAL_STATE):
    start_inversions = count_inversions(state)
    goal_inversions = count_inversions(goal)
    return  (start_inversions % 2) == (goal_inversions % 2)

def find_blank(state):
    for r in range(3):
        for c in range(3):
            if state[r][c] == 0:
                return (r, c)


def get_neighbors(state):
    neighbors = []
    r, c = find_blank(state)

    # (delta_row, delta_col, tên hướng)
    directions = [(-1, 0, "up"), (1, 0, "down"), (0, -1, "left"), (0, 1, "right")]

    for dr, dc, direction in directions:
        nr = r + dr
        nc = c + dc
        if 0 <= nr < 3 and 0 <= nc < 3:
            # Tạo bản sao và hoán đổi ô trống với ô kế bên
            new_state = [list(row) for row in state]
            new_state[r][c], new_state[nr][nc] = new_state[nr][nc], new_state[r][c]
            neighbors.append(tuple(tuple(row) for row in new_state))

    return neighbors