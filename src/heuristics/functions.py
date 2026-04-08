# src/heuristics/basic.py
from functools import lru_cache


@lru_cache(maxsize=1)
def get_goal_pos(goal):
    return {
        goal[r][c]: (r, c)
        for r in range(3)
        for c in range(3)
    }

def manhattan(state, goal):
    goal_pos = get_goal_pos(goal)

    dist = 0
    for r in range(3):
        for c in range(3):
            val = state[r][c]
            if val != 0:
                gr, gc = goal_pos[val]
                dist += abs(r - gr) + abs(c - gc)
    return dist

"""
Heuristic nâng cao: Manhattan + 2 * Linear Conflict.
Xung đột xảy ra khi 2 ô (A, B) cùng nằm trên một hàng (hoặc cột) đích,
nhưng vị trí của chúng bị ngược nhau, buộc một ô phải đi vòng để nhường đường
"""
def linear_conflict(state, goal):
    goal_pos = get_goal_pos(goal)
    conflicts = 0

    # check all hàng
    for row in range(3):
        for left_col in range(3):
            for right_col in range(left_col + 1, 3):
                left_val = state[row][left_col]
                right_val = state[row][right_col]

                if left_val != 0 and right_val != 0:
                    left_goal_row, left_goal_col = goal_pos[left_val]
                    right_goal_row, right_goal_col = goal_pos[right_val]

                    # check thuộc đúng hàng đích
                    if left_goal_row == row and right_goal_row == row:
                        # check vị trị ngược nhau
                        if left_goal_col > right_goal_col:
                            conflicts += 1


    # check all cột
    for col in range(3):
        for top_row in range(3):
            for bottom_row in range(top_row + 1, 3):
                top_val = state[top_row][col]
                bottom_val = state[bottom_row][col]

                if top_val != 0 and bottom_val != 0:
                    top_goal_row, top_goal_col = goal_pos[top_val]
                    bottom_goal_row, bottom_goal_col = goal_pos[bottom_val]

                    # check thuộc đúng cột đích
                    if top_goal_col == col and bottom_goal_col == col:
                        if top_goal_row > bottom_goal_row:
                            conflicts += 1

    return conflicts

def manhattan_linear_conflict(state, goal):
    return manhattan(state, goal) + 2 * linear_conflict(state, goal)

