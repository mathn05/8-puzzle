from src.heuristics.linear_conflict import linear_conflict
from src.heuristics.manhattan import manhattan


def manhattan_linear_conflict(state, goal):
    return manhattan(state, goal) + 2 * linear_conflict(state, goal)
