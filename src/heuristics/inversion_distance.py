from src.heuristics.common import count_inversion


def inversion_distance(state, goal):
    goal_row_map = {}
    goal_col_map = {}

    for row in range(3):
        for col in range(3):
            value = goal[row][col]
            goal_row_map[value] = row * 3 + col
            goal_col_map[value] = col * 3 + row

    flat_row = []
    for row in range(3):
        for col in range(3):
            value = state[row][col]
            if value != 0:
                flat_row.append(goal_row_map[value])

    flat_col = []
    for col in range(3):
        for row in range(3):
            value = state[row][col]
            if value != 0:
                flat_col.append(goal_col_map[value])

    row_inversions = count_inversion(flat_row)
    col_inversions = count_inversion(flat_col)
    return (row_inversions + 1) // 2 + (col_inversions + 1) // 2
