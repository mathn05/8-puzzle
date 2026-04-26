from functools import lru_cache


@lru_cache(maxsize=8)
def get_goal_pos(goal):
    return {
        goal[row][col]: (row, col)
        for row in range(3)
        for col in range(3)
    }


def count_inversion(values):
    inversion = 0
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if values[i] > values[j]:
                inversion += 1
    return inversion


def flatten_wd_state(state):
    if len(state) == 9 and not isinstance(state[0], (list, tuple)):
        return tuple(state)
    return tuple(value for row in state for value in row)


def wd_goal_pos(goal):
    flat_goal = flatten_wd_state(goal)
    return {
        tile: divmod(index, 3)
        for index, tile in enumerate(flat_goal)
    }
