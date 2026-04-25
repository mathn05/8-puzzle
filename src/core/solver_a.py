# src/core/solver_a.py

import heapq
import sys
import time

from src.core.puzzle import GOAL_STATE, get_neighbors

class Node:
    """
    Đại diện cho một trạng thái trong cây tìm kiếm.
    Lưu trạng thái, chi phí g(n), và con trỏ về node cha để truy vết đường đi.
    """
    __slots__ = ['state', 'parent', 'g', 'h', 'f']

    def __init__(self, state, parent=None, g=0, h=0):
        self.state  = state   # trạng thái bảng 3x3
        self.parent = parent  # node cha (để truy vết)
        self.g      = g       # chi phí từ đầu đến đây
        self.h      = h       # giá trị heuristic
        self.f      = g + h   # f(n) = g(n) + h(n)

    def __lt__(self, other):
        # So sánh ưu tiên theo f(n), nếu hòa xét tiếp h(n), rồi đến g(n)
        return (self.f, self.h, self.g) < (other.f, other.h, other.g)

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
        time_ms         — thời gian chạy (ms)
        memory_kb       - bộ nhớ sử dụng (kb)
    """
    start_time = time.time()

    # Khởi tạo node đầu tiên
    h0         = heuristic_fn(start, goal)
    start_node = Node(state=start, parent=None, g=0, h=h0)

    # open_heap: Hàng đợi ưu tiên (Min-Heap).
    open_heap  = []
    heapq.heappush(open_heap, (start_node.f, start_node.h, start_node.g, 0, start_node))

    # best_g: Từ điển (Hash Map) lưu chi phí g(n) tốt nhất đã biết để đi đến một trạng thái.
    best_g = {
        start: 0
    }

    # Closed set: lưu các trạng thái đã xét
    closed_set = set()

    # Đếm số node mở rộng
    nodes_expanded = 0

    # Đếm thứ tự sinh ra của Node
    counter = 1

    while open_heap:
        # Lấy Node có độ ưu tiên cao nhất (f(n) nhỏ nhất) ra khỏi hàng đợi
        _, _, _, _, current = heapq.heappop(open_heap)

        # Nếu lấy ra một Node có chi phí g(n) lớn hơn kỷ lục đã ghi nhận trong best_g,
        # ta hiểu đây là một phiên bản cũ/tệ hơn và bỏ qua nó ngay lập tức
        if current.g != best_g.get(current.state):
            continue

        # Nếu trạng thái này đã được duyệt xong từ trước, bỏ qua
        if current.state in closed_set:
            continue

        # Đánh dấu trạng thái đã duyệt
        closed_set.add(current.state)
        nodes_expanded += 1

        # Tìm thấy đích
        if current.state == goal:
            elapsed = (time.time() - start_time) * 1000

            node_size = sys.getsizeof(current)
            state_size = sys.getsizeof(current.state) + sum(sys.getsizeof(row) for row in current.state)
            total_bytes = (len(open_heap) * node_size) + (len(closed_set) * state_size)

            return {
                "path":           reconstruct_path(current),
                "steps":          current.g,
                "nodes_expanded": nodes_expanded,
                "nodes_in_open":  len(open_heap),
                "time_ms":        round(elapsed, 2),
                "memory_kb":      round(total_bytes / 1024, 2)
            }

        # Mở rộng các trạng thái kế tiếp
        for neighbor_state in get_neighbors(current.state):
            new_g = current.g + 1

            #Nếu hàng xóm đã nằm trong tập đã duyệt, không quay lại
            if neighbor_state in closed_set:
                continue

            #Chỉ cho phép tiếp tục nếu tìm được đường đi có chi phí (g) nhỏ hơn kỷ lục cũ
            if new_g >= best_g.get(neighbor_state, float("inf")):
                continue

            best_g[neighbor_state] = new_g

            new_h = heuristic_fn(neighbor_state, goal)

            neighbor_node = Node(
                state=neighbor_state,
                parent=current,
                g=new_g,
                h=new_h
            )

            heapq.heappush(
                open_heap,
                (neighbor_node.f, neighbor_node.h, neighbor_node.g, counter, neighbor_node)
            )

            counter += 1

    # Không tìm được lời giải
    return None