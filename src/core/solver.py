# src/core/solver.py

import heapq
import time
from src.core.puzzle import GOAL_STATE, get_neighbors

class Node:
    """
    Đại diện cho một trạng thái trong cây tìm kiếm.
    Lưu trạng thái, chi phí g(n), và con trỏ về node cha để truy vết đường đi.
    """
    def __init__(self, state, parent=None, g=0, h=0):
        self.state  = state   # trạng thái bảng 3x3
        self.parent = parent  # node cha (để truy vết)
        self.g      = g       # chi phí từ đầu đến đây
        self.h      = h       # giá trị heuristic
        self.f      = g + h   # f(n) = g(n) + h(n)

    def __lt__(self, other):
        return (self.f, self.h) < (other.f, other.h)

def reconstruct_path(node):
        """Đi ngược từ node đích về node gốc để lấy đường đi."""
        path = []
        while node is not None:
            path.append(node.state)
            node = node.parent
        return list(reversed(path))

def a_star(start, heuristic_fn, goal=GOAL_STATE):
    """
    Tham số:
        start — trạng thái ban đầu (tuple 3x3)
        heuristic_fn — hàm h(state, goal)
        goal — trạng thái đích

    Trả về dict gồm:
        path            — danh sách trạng thái từ đầu đến đích
        steps           — số bước di chuyển
        nodes_expanded  — số node đã mở rộng
        nodes_in_open   — số node còn trong open list lúc tìm ra đích
        time_ms         — thời gian chạy (milliseconds)
    """
    start_time = time.time()

    # Khởi tạo node đầu tiên
    h0         = heuristic_fn(start, goal)
    start_node = Node(state=start, parent=None, g=0, h=h0)

    # Open list: min-heap theo f(n)
    open_heap  = [start_node]

    # Closed set: lưu các trạng thái đã xét
    closed_set = set()

    # Đếm số node mở rộng
    nodes_expanded = 0

    while open_heap:
        current = heapq.heappop(open_heap)

        # Bỏ qua nếu đã xét trạng thái này rồi
        if current.state in closed_set:
            continue

        closed_set.add(current.state)
        nodes_expanded += 1

        # Tìm thấy đích
        if current.state == goal:
            elapsed = (time.time() - start_time) * 1000
            return {
                "path":           reconstruct_path(current),
                "steps":          current.g,
                "nodes_expanded": nodes_expanded,
                "nodes_in_open":  len(open_heap),
                "time_ms":        round(elapsed, 2)
            }

        # Mở rộng các trạng thái kế tiếp
        for neighbor_state in get_neighbors(current.state):
            if neighbor_state not in closed_set:
                new_g = current.g + 1
                new_h = heuristic_fn(neighbor_state, goal)
                neighbor_node = Node(
                    state  = neighbor_state,
                    parent = current,
                    g      = new_g,
                    h      = new_h
                )
                heapq.heappush(open_heap, neighbor_node)

    # Không tìm được lời giải
    return None