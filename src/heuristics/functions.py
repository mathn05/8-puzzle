# src/heuristics/basic.py

def manhattan(state, goal):
    goal_pos = {
        goal[r][c]: (r, c)
        for r in range(3)
        for c in range(3)
    }
    dist = 0
    for r in range(3):
        for c in range(3):
            val = state[r][c]
            if val != 0:
                gr, gc = goal_pos[val]
                dist += abs(r - gr) + abs(c - gc)
    return dist