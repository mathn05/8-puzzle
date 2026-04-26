def misplaced_tiles(state, goal):
    count = 0
    for row in range(3):
        for col in range(3):
            value = state[row][col]
            if value != 0 and value != goal[row][col]:
                count += 1
    return count
