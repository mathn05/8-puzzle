from collections import deque

WD_CACHE = None

def _matrix_to_tuple(matrix):
    """
    Chuyển ma trận abstract 3x3 thành tuple 9 phần tử để làm key dict.
    """
    return tuple(x for row in matrix for x in row)

def generate_wd_tables():
    wd_table = []
    wd_neighbors = []
    wd_tuple_lookup = []

    for i in range(3):
        next_tuple_lookup, next_neighborhood, next_table = walking_distance_table(i)
        wd_tuple_lookup.append(next_tuple_lookup)
        wd_neighbors.append(next_neighborhood)
        wd_table.append(next_table)

    return wd_table, wd_neighbors, wd_tuple_lookup

def walking_distance_table(goal):
    state = [[3, 0, 0], [0, 3, 0], [0, 0, 3]]
    state[goal][goal] = 2

    # frontier item:
    #   state      : abstract matrix 3x3
    #   blank      : blank đang ở dòng/cột nào
    #   home_line  : loại quân vừa bị kéo
    #   depth      : khoảng cách WD hiện tại
    #   origin     : next_id của abstract state cha
    frontier = deque([(state, goal, -1, 0, -1)])

    tuple_ids = {}
    neighborhoods = []
    walking_distance = []

    next_id = 0

    while len(frontier) != 0:
        state, blank, home_line, depth, origin = frontier.popleft()

        key = _matrix_to_tuple(state)

        if key in tuple_ids:
            loc = tuple_ids[key]

            # Root ban đầu có home_line = -1, origin = -1
            # nên không ghi neighbor cho root.
            if home_line != -1 and origin != -1:
                neighborhoods[loc][home_line] = origin
                neighborhoods[origin][5 - home_line] = loc
        else:
            tuple_ids[key] = next_id
            neighborhoods.append([-1] * 6)
            walking_distance.append(depth)

            # Blank đi lên trong abstract state:
            # Một quân từ dòng blank - 1 bị kéo xuống dòng blank.
            # Blank chuyển lên dòng blank - 1
            if blank != 0:
                for home_line in range(3):
                    if state[blank - 1][home_line] != 0:
                        new_state = [row[:] for row in state]

                        new_state[blank][home_line] += 1
                        new_state[blank - 1][home_line] -= 1

                        frontier.append((new_state, blank - 1, home_line, depth + 1, next_id))

            # Blank đi xuống trong abstract state:
            # Một quân từ dòng blank + 1 bị kéo lên dòng blank.
            # Blank chuyển xuống dòng blank + 1.
            if blank != 2:
                for home_line in range(3):
                    if state[blank + 1][home_line] != 0:
                        new_state = [row[:] for row in state]

                        new_state[blank][home_line] += 1
                        new_state[blank + 1][home_line] -= 1

                        frontier.append((new_state, blank + 1, 5 - home_line, depth + 1, next_id))

            next_id += 1

    return tuple_ids, neighborhoods, walking_distance

def get_wd_tables():
    global WD_CACHE

    if WD_CACHE is None:
        WD_CACHE = generate_wd_tables()

    return WD_CACHE

def clear_wd_cache():
    global WD_CACHE
    WD_CACHE = None