from src.heuristics.common import get_goal_pos


def manhattan(state, goal):
    goal_pos = get_goal_pos(goal)
    distance = 0

    for row in range(3):
        for col in range(3):
            value = state[row][col]
            if value == 0:
                continue

            goal_row, goal_col = goal_pos[value]
            distance += abs(row - goal_row) + abs(col - goal_col)

    return distance
