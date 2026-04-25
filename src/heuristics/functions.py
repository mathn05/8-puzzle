# src/heuristics/basic.py
from functools import lru_cache

from src.heuristics.walking_distance_table import *

@lru_cache(maxsize=1)
def get_goal_pos(goal):
    return {
        goal[r][c]: (r, c)
        for r in range(3)
        for c in range(3)
    }
"""
Đếm số lượng ô (trừ ô 0) nằm sai vị trí so với đích.
"""
def misplaced_tiles(state, goal):

    count = 0
    for row in range(3):
        for col in range(3):
            val = state[row][col]
            if val != 0 and val != goal[row][col]:
                count += 1

    return count

"""
Tính số lần hoán đổi (swap) tối thiểu 
để đưa bàn cờ về đích, nếu cho phép ô trống đổi chỗ với BẤT KỲ ô nào.
Nguyên lý: tìm số 0 nếu hiện tại sai so với đích thì đảo 0 với số đáng lẽ phải ở đó.
nếu 0 đúng đích nhưng vẫn lộn xộn thì đảo 0 với 1 số đang sai vị trí bất kì
"""
def gaschnig(state, goal):
    flat_state = [val for row in state for val in row]
    flat_goal = [val for row in goal for val in row]

    res = 0
    while flat_state != flat_goal:
        #tìm vị trí của 0
        blank_idx = flat_state.index(0)
        # 0 nằm sai vị trí
        if flat_goal[blank_idx] != 0:
            # tìm số nằm ở vị trí này tại đích
            target_tile = flat_goal[blank_idx]
            # tìm số đó ở đâu hiện tại
            target_tile_idx = flat_state.index(target_tile)
            # đảo 0 với số đó
            flat_state[target_tile_idx], flat_state[blank_idx] = flat_state[blank_idx], flat_state[target_tile_idx]
        else:
            #tìm 1 số đang ở sai chỗ
            for i in range(9):
                # đảo 0 với số đó
                if flat_goal[i] != flat_state[i]:
                    flat_state[i], flat_state[blank_idx] = flat_state[blank_idx], flat_state[i]
                    break
        res += 1
    return  res


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
Xung đột xảy ra khi 2 ô (A, B) cùng nằm trên một hàng (hoặc cột) đích,
nhưng vị trí của chúng bị ngược nhau, buộc một ô phải đi vòng để nhường đường
"""
def linear_conflict(state, goal):
    # Tìm viên gạch cản đường nhiều nhất, nhấc ra ngoài, và lặp lại
    def count_conflicts(cur_line, goal_line, ans=0):
        conficts = [0 for x in range(3)]

        for cur_idx, cur_tile in enumerate(cur_line):

            if cur_tile in goal_line and cur_tile != 0:
                goal_cur_idx = goal_line.index(cur_tile)

                # so với ô khác cùng hàng/cột
                for other_idx, other_tile in enumerate(cur_line):
                    if other_tile in goal_line and other_tile != 0 and cur_idx != other_idx:
                        goal_other_idx = goal_line.index(other_tile)

                        # nếu ô hiện tại đứng trước ô khác nhưng đích lại ở sau
                        if goal_cur_idx > goal_other_idx and cur_idx < other_idx:
                            conficts[cur_idx] += 1

                        elif goal_cur_idx < goal_other_idx and cur_idx > other_idx:
                            conficts[cur_idx] += 1

        # nếu hết xung đột
        if max(conficts) == 0:
            return ans
        else:
            # vị trí ô nhiều xung đột nhất
            worst_tile_idx = conficts.index(max(conficts))

            cur_line[worst_tile_idx] = -1
            ans += 1

            return count_conflicts(cur_line, goal_line, ans)

    flat_state = [val for row in state for val in row]
    flat_goal = [val for row in goal for val in row]

    res = 0

    cur_rows = [[] for _ in range(3)]
    cur_cols = [[] for _ in range(3)]
    goal_rows = [[] for _ in range(3)]
    goal_cols = [[] for _ in range(3)]

    # Trải phẳng
    for row in range(3):
        for col in range(3):
            idx = row * 3 + col
            cur_rows[row].append(flat_state[idx])
            cur_cols[col].append(flat_state[idx])
            goal_rows[row].append(flat_goal[idx])
            goal_cols[col].append(flat_goal[idx])

    # tính bước phạt cho row
    for i in range(3):
        res += count_conflicts(cur_rows[i], goal_rows[i])
    # tính bước phạt cho col
    for i in range(3):
        res += count_conflicts(cur_cols[i], goal_cols[i])

    return res

def manhattan_linear_conflict(state, goal):
    return manhattan(state, goal) + 2 * linear_conflict(state, goal)

"""
trải phảng thành hàng dọc: tìm số lỗi mà só trước lớn hơn số sau
tương tự với hàng ngang. Kết quả heuris sẽ bằng tổng cả 2
"""
def count_inversion(arr):
    inversion = 0

    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] > arr[j]:
                inversion += 1
    return inversion

"""
Khoảng cách nghịch đảo (Inversion Distance).
Trải phẳng bàn cờ ra mảng 1 chiều, đếm xem có bao nhiêu cặp gạch đang nằm ngược thứ tự so với đích (Inversion).
Đếm tách biệt theo chiều ngang và chiều dọc. 
Vì mỗi bước đi lên/xuống chỉ có thể "nhảy" qua 2 viên gạch (giúp sửa tối đa 2 lỗi nghịch đảo), 
nên ta lấy tổng số lỗi chia 2 để ra số bước đi ước lượng tối thiểu.
"""
def inversion_distance(state, goal):
    goal_row_map = {}
    goal_col_map = {}

    # map vị trí của từng giá trị đích khi trải phẳng
    for row in range(3):
        for col in range(3):
            val = goal[row][col]
            goal_row_map[val] = row * 3 + col
            goal_col_map[val] = col * 3 + row

    # trải phẳng
    flat_row = []
    for row in range(3):
        for col in range(3):
            val = state[row][col]
            if val != 0:
                flat_row.append(goal_row_map[val])

    flat_col = []
    for col in range(3):
        for row in range(3):
            val = state[row][col]
            if val != 0:
                flat_col.append(goal_col_map[val])

    inv_row = count_inversion(flat_row)
    inv_col = count_inversion(flat_col)

    return (inv_row + 1) // 2 + (inv_col + 1) // 2

def flatten_wd_state(state):
    """
    Chuyển đổi trạng thái bảng (ma trận 2D hoặc mảng 1D) thành một tuple 1D.
    """
    if len(state) == 9 and not isinstance(state[0], (list, tuple)):
        return tuple(state)

    return tuple(x for row in state for x in row)

def wd_goal_pos(goal):
    """
    Tạo bảng băm (Hash Map) lưu trữ tọa độ (dòng, cột) của từng viên gạch trong trạng thái đích.
    """
    flat_goal = flatten_wd_state(goal)

    return {
        # divmod(idx, 3) trả về (idx // 3, idx % 3) tương đương với (dòng, cột) trong bảng 3x3
        tile: divmod(idx, 3)
        for idx, tile in enumerate(flat_goal)
    }

def walking_distance(state, goal):
    """
    Tính toán giá trị Heuristic Walking Distance (WD) giữa trạng thái hiện tại và đích.
    Thuật toán tách bài toán thành 2 phần độc lập (Hàng và Cột), sau đó xây dựng
    "ma trận trừu tượng" để tra cứu số bước di chuyển tối thiểu từ các bảng đã tính trước (Cache).
    Tổng số bước tối thiểu (Walking Distance) = Khoảng cách Hàng + Khoảng cách Cột.
    """
    # Lấy dữ liệu đệm (Cache) chứa bảng khoảng cách và từ điển tra cứu
    wd_table, wd_neighbors, wd_tuple_lookup = get_wd_tables()

    # Chuẩn hóa trạng thái hiện tại và đích về dạng tuple 1 chiều
    flat_state = flatten_wd_state(state)
    flat_goal = flatten_wd_state(goal)

    # Lấy từ điển tọa độ đích của từng viên gạch
    goal_pos = wd_goal_pos(goal)

    # Xác định vị trí của ô trống (Blank - số 0) trong trạng thái đích
    goal_blank_index = flat_goal.index(0)
    goal_blank_row = goal_blank_index // 3
    goal_blank_col = goal_blank_index % 3

    # Khởi tạo ma trận trừu tượng 3x3 toàn số 0 cho Hàng và Cột
    # Cấu trúc: ma_trận[i][j] = Số lượng viên gạch đang ở vị trí i nhưng cần về vị trí j
    row_puzzle = [[0 for _ in range(3)] for _ in range(3)]
    col_puzzle = [[0 for _ in range(3)] for _ in range(3)]

    for idx, tile in enumerate(flat_state):
        if tile == 0: # Bỏ qua ô trống, chỉ tính gạch
            continue

        # Tọa độ hiện tại của viên gạch
        current_row = idx // 3
        current_col = idx % 3

        # Tọa độ đích của viên gạch
        tile_goal_row, tile_goal_col = goal_pos[tile]

        # Có 1 viên gạch ở hàng/cột hiện tại cần phải di chuyển về hàng/cột đích
        row_puzzle[current_row][tile_goal_row] += 1
        col_puzzle[current_col][tile_goal_col] += 1

    # Chuyển ma trận trừu tượng thành Tuple (Key) để tra cứu
    row_key = tuple(x for row in row_puzzle for x in row)
    col_key = tuple(x for row in col_puzzle for x in row)

    # Tra cứu ID của trạng thái trừu tượng
    # Cần dùng goal_blank_row/col vì số bước đi phụ thuộc vào vị trí ô trống ở đích nằm ở đâu
    row_wd_id = wd_tuple_lookup[goal_blank_row][row_key]
    col_wd_id = wd_tuple_lookup[goal_blank_col][col_key]

    # Tra cứu số bước đi ngắn nhất (Distance) từ ID vừa tìm được
    row_wd = wd_table[goal_blank_row][row_wd_id]
    col_wd = wd_table[goal_blank_col][col_wd_id]

    return row_wd + col_wd

def max_heuristic(state, goal):
    id_heu = inversion_distance(state, goal)
    mlc_heu = manhattan_linear_conflict(state, goal)
    return max(id_heu, mlc_heu)