from src.heuristics.common import flatten_wd_state, wd_goal_pos
from src.heuristics.walking_distance_table import get_wd_tables


def walking_distance(state, goal):
    wd_table, _, wd_tuple_lookup = get_wd_tables()

    flat_state = flatten_wd_state(state)
    flat_goal = flatten_wd_state(goal)
    goal_positions = wd_goal_pos(goal)

    goal_blank_index = flat_goal.index(0)
    goal_blank_row = goal_blank_index // 3
    goal_blank_col = goal_blank_index % 3

    row_puzzle = [[0 for _ in range(3)] for _ in range(3)]
    col_puzzle = [[0 for _ in range(3)] for _ in range(3)]

    for index, tile in enumerate(flat_state):
        if tile == 0:
            continue

        current_row = index // 3
        current_col = index % 3
        tile_goal_row, tile_goal_col = goal_positions[tile]

        row_puzzle[current_row][tile_goal_row] += 1
        col_puzzle[current_col][tile_goal_col] += 1

    row_key = tuple(value for row in row_puzzle for value in row)
    col_key = tuple(value for row in col_puzzle for value in row)

    row_wd_id = wd_tuple_lookup[goal_blank_row][row_key]
    col_wd_id = wd_tuple_lookup[goal_blank_col][col_key]

    row_wd = wd_table[goal_blank_row][row_wd_id]
    col_wd = wd_table[goal_blank_col][col_wd_id]
    return row_wd + col_wd
