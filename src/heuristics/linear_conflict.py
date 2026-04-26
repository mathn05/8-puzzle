def _count_conflicts(current_line, goal_line, total=0):
    conflicts = [0, 0, 0]

    for current_index, current_tile in enumerate(current_line):
        if current_tile not in goal_line or current_tile == 0:
            continue

        goal_current_index = goal_line.index(current_tile)

        for other_index, other_tile in enumerate(current_line):
            if other_index == current_index or other_tile not in goal_line or other_tile == 0:
                continue

            goal_other_index = goal_line.index(other_tile)
            if goal_current_index > goal_other_index and current_index < other_index:
                conflicts[current_index] += 1
            elif goal_current_index < goal_other_index and current_index > other_index:
                conflicts[current_index] += 1

    worst_conflict = max(conflicts)
    if worst_conflict == 0:
        return total

    worst_tile_index = conflicts.index(worst_conflict)
    current_line[worst_tile_index] = -1
    return _count_conflicts(current_line, goal_line, total + 1)


def linear_conflict(state, goal):
    flat_state = [value for row in state for value in row]
    flat_goal = [value for row in goal for value in row]

    current_rows = [[] for _ in range(3)]
    current_cols = [[] for _ in range(3)]
    goal_rows = [[] for _ in range(3)]
    goal_cols = [[] for _ in range(3)]

    for row in range(3):
        for col in range(3):
            index = row * 3 + col
            current_rows[row].append(flat_state[index])
            current_cols[col].append(flat_state[index])
            goal_rows[row].append(flat_goal[index])
            goal_cols[col].append(flat_goal[index])

    penalty = 0
    for index in range(3):
        penalty += _count_conflicts(current_rows[index], goal_rows[index])
        penalty += _count_conflicts(current_cols[index], goal_cols[index])

    return penalty
