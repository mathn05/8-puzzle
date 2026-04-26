def gaschnig(state, goal):
    flat_state = [value for row in state for value in row]
    flat_goal = [value for row in goal for value in row]

    swaps = 0
    while flat_state != flat_goal:
        blank_index = flat_state.index(0)

        if flat_goal[blank_index] != 0:
            target_tile = flat_goal[blank_index]
            target_index = flat_state.index(target_tile)
            flat_state[target_index], flat_state[blank_index] = (
                flat_state[blank_index],
                flat_state[target_index],
            )
        else:
            for index in range(9):
                if flat_goal[index] != flat_state[index]:
                    flat_state[index], flat_state[blank_index] = (
                        flat_state[blank_index],
                        flat_state[index],
                    )
                    break

        swaps += 1

    return swaps
