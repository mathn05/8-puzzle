import heapq
import sys
import time
from heapq import heappop

from src.core.puzzle import GOAL_STATE, get_neighbors

class Node:
    """
    Node dùng cho Bidirectional A* + Meet in the Middle.
    """
    __slots__ = ["state", "parent", "g", "h", "f", "priority", "direction"]

    def __init__(self, state, parent=None, g=0, h=0, direction=0, mm_epsilon=0):
        self.state  = state   # trạng thái bảng 3x3
        self.parent = parent  # node cha (để truy vết)
        self.g      = g       # g          : số bước từ gốc của hướng đó đến node này
                              # - hướng forward: g = khoảng cách từ start đến node
                              # - hướng backward: g = khoảng cách từ goal đến node
        self.h      = h       # giá trị heuristic
        self.f      = g + h   # f(n) = g(n) + h(n)
        self.direction = direction # 0 = forward, 1 = backward
        self.priority = max(2 * g + mm_epsilon, g + h) #độ ưu tiên kiểu MM / MMε

def reconstruct_path_from_root(node):
    """
       Lấy đường đi từ gốc của hướng đó đến node.
       Nếu node thuộc forward:
           start -> ... -> meet
       Nếu node thuộc backward:
           goal -> ... -> meet
       Hàm này chỉ đi theo parent rồi đảo ngược.
       """
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return list(reversed(path))

def combine_bidirectional_path(forward_node, backward_node):
    """
    Nối đường đi của 2 phía.

    forward_node:
        start -> ... -> meet

    backward_node:
        goal -> ... -> meet
        vì backward search đi từ goal ngược về start.

    Cần kết quả cuối:
        start -> ... -> meet -> ... -> goal
    """
    path_start_to_meet = reconstruct_path_from_root(forward_node)
    path_goal_to_meet = reconstruct_path_from_root(backward_node)

    path_meet_to_goal = list(reversed(path_goal_to_meet))

    return path_start_to_meet + path_meet_to_goal[1:]

def _push_node(priority_heap, f_heap, g_heap, node, counter):
    """
       Đẩy node vào 3 heap khác nhau.

       priority_heap:
           dùng để chọn node mở rộng theo MM priority

       f_heap:
           dùng để lấy min f cho điều kiện dừng

       g_heap:
           dùng để lấy min g cho điều kiện dừng

       counter dùng để tránh lỗi khi heapq phải so sánh 2 Node.
    """
    heapq.heappush(priority_heap, (node.priority, node.g, node.f, counter, node))
    heapq.heappush(f_heap, (node.f, node.g, counter, node))
    heapq.heappush(g_heap, (node.g, node.f, counter, node))

def _is_current_open_node(node, open_map):
    """
    Kiểm tra node lấy ra từ heap có còn hợp lệ không.

    Vì heapq của Python không tiện xóa node ở giữa heap.
    Nên khi một node cũ bị thay bằng node tốt hơn, ta cứ để node cũ trong heap.
    Lúc pop/peek thì kiểm tra:
        open_map[state] is node

    Nếu không đúng, đó là node rác/stale.
    """
    return open_map.get(node.state) is node

def _peek_valid(heap, open_map):
    """
    Xem phần tử nhỏ nhất hợp lệ trong heap.
    Các node cũ/stale sẽ bị bỏ qua.
    """
    while heap:
        node = heap[0][-1]

        if _is_current_open_node(node, open_map):
            return node

        heapq.heappop(heap)

    return None

def _pop_valid(heap, open_map):
    """
    Pop phần tử nhỏ nhất hợp lệ trong heap.
    Các node cũ/stale sẽ bị bỏ qua.
    """
    while heap:
        node = heappop(heap)[-1]

        if _is_current_open_node(node, open_map):
            return node

    return None

def _estimate_memory_kb(open_maps, closed_maps):
    total_bytes = 0

    for direction in (0, 1):
        for node in open_maps[direction].values():
            total_bytes += sys.getsizeof(node)
            total_bytes += sys.getsizeof(node.state)
            total_bytes += sum(sys.getsizeof(row) for row in node.state)

        for node in closed_maps[direction].values():
            total_bytes += sys.getsizeof(node)
            total_bytes += sys.getsizeof(node.state)
            total_bytes += sum(sys.getsizeof(row) for row in node.state)

    return round(total_bytes / 1024, 2)

def bidirectional_a_star_mim(start, heuristic_fn, goal=GOAL_STATE, mm_epsilon=0):
    """
     Bidirectional A* + Meet in the Middle / MM.

     Tham số:
        start — trạng thái ban đầu (tuple 3x3)

        heuristic_fn — hàm h(state, goal)

        goal: trạng thái đích.

        mm_epsilon:
            dùng cho MMε.
            Để 0 là MM thường.
            Có thể thử 1, 2, ... nếu muốn biến thể MMε.

    Trả về dict gồm:
        path            — danh sách trạng thái từ đầu đến đích
        steps           — số bước di chuyển
        nodes_expanded  — số node đã mở rộng
        nodes_in_open   — số node còn trong open list lúc tìm ra đích
        time_ms         — thời gian chạy (ms)
        memory_kb       - bộ nhớ sử dụng (kb)
     """
    start_time = time.time()

    if start == goal:
        return {
            "path": [start],
            "steps": 0,
            "nodes_expanded": 0,
            "nodes_in_open": 0,
            "time_ms": 0,
            "memory_kb": 0
        }

    FWD = 0
    BWD = 1

    roots = {
        FWD: start,
        BWD: goal
    }

    targets = {
        FWD: goal,
        BWD: start
    }
    # Mỗi hướng có 3 heap:
    # - priority_heap: chọn node theo MM priority
    # - f_heap: lấy min f
    # - g_heap: lấy min g

    priority_heaps = {
        FWD: [],
        BWD: []
    }

    f_heaps = {
        FWD: [],
        BWD: []
    }

    g_heaps = {
        FWD: [],
        BWD: []
    }

    # Open map: các node đang chờ mở rộng
    open_maps = {
        FWD: {},
        BWD: {}
    }

    # Closed map: các node đã mở rộng
    closed_maps = {
        FWD: {},
        BWD: {}
    }

    # Best discovered: node tốt nhất đã biết cho mỗi state ở mỗi hướng
    best_nodes = {
        FWD: {},
        BWD: {}
    }

    counter = 0

    # Khởi tạo 2 node gốc:
    # forward bắt đầu từ start
    # backward bắt đầu từ goal
    for direction in (FWD, BWD):
        root_state = roots[direction]
        h0 = heuristic_fn(root_state, targets[direction])

        root_node = Node(
            state=root_state,
            parent=None,
            g=0,
            h=h0,
            direction=direction,
            mm_epsilon=mm_epsilon
        )

        open_maps[direction][root_state] = root_node
        best_nodes[direction][root_state] = root_node

        _push_node(
            priority_heaps[direction],
            f_heaps[direction],
            g_heaps[direction],
            root_node,
            counter
        )

        counter += 1

        # U là độ dài đường đi tốt nhất hiện tìm được.
        # Ban đầu chưa có đường nên để vô cực.
    U = float("inf")

    best_forward_meet = None
    best_backward_meet = None

    nodes_expanded = 0

    while open_maps[FWD] and open_maps[BWD]:
        fwd_priority_node = _peek_valid(priority_heaps[FWD], open_maps[FWD])
        bwd_priority_node = _peek_valid(priority_heaps[BWD], open_maps[BWD])

        fwd_f_node = _peek_valid(f_heaps[FWD], open_maps[FWD])
        bwd_f_node = _peek_valid(f_heaps[BWD], open_maps[BWD])

        fwd_g_node = _peek_valid(g_heaps[FWD], open_maps[FWD])
        bwd_g_node = _peek_valid(g_heaps[BWD], open_maps[BWD])

        if (
                fwd_priority_node is None or
                bwd_priority_node is None or
                fwd_f_node is None or
                bwd_f_node is None or
                fwd_g_node is None or
                bwd_g_node is None
        ):
            break

        # C = min priority của 2 phía
        C = min(fwd_priority_node.priority, bwd_priority_node.priority)

        # Điều kiện dừng kiểu MM:
        # Nếu U đã đủ tốt và không còn khả năng tìm đường ngắn hơn nữa thì dừng.
        stop_bound = max(
            C,
            fwd_f_node.f,
            bwd_f_node.f,
            fwd_g_node.g + bwd_g_node.g + 1
        )
        if U <= stop_bound:
            break

        # Chọn hướng để mở rộng:
        # bên nào có priority nhỏ hơn thì mở rộng trước.
        if fwd_priority_node.priority <= bwd_priority_node.priority:
            direction = FWD
        else:
            direction = BWD

        opposite = 1 - direction
        current = _pop_valid(priority_heaps[direction], open_maps[direction])

        if current is None:
            break

        # Chuyển current từ open sang closed
        open_maps[direction].pop(current.state, None)
        closed_maps[direction][current.state] = current

        nodes_expanded += 1

        # Mở rộng hàng xóm
        for neighbor_state in get_neighbors(current.state):
            new_g = current.g + 1

            old_open_node = open_maps[direction].get(neighbor_state)
            old_closed_node = closed_maps[direction].get(neighbor_state)

            # Nếu đã có đường tốt hơn hoặc bằng tới neighbor_state thì bỏ qua
            if old_open_node is not None and old_open_node.g <= new_g:
                continue

            if old_closed_node is not None and old_closed_node.g <= new_g:
                continue

            # Nếu node cũ tệ hơn, xóa khỏi map.
            if old_open_node is not None:
                open_maps[direction].pop(neighbor_state, None)

            if old_closed_node is not None:
                closed_maps[direction].pop(neighbor_state, None)

            new_h = heuristic_fn(neighbor_state, targets[direction])

            neighbor_node = Node(
                state=neighbor_state,
                parent=current,
                g=new_g,
                h=new_h,
                direction=direction,
                mm_epsilon=mm_epsilon
            )

            open_maps[direction][neighbor_state] = neighbor_node
            best_nodes[direction][neighbor_state] = neighbor_node

            _push_node(
                priority_heaps[direction],
                f_heaps[direction],
                g_heaps[direction],
                neighbor_node,
                counter
            )

            counter += 1

            # Meet in the Middle:
            # Nếu trạng thái này đã được phía đối diện tìm thấy,
            # ta có một đường start -> ... -> meet -> ... -> goal.
            matched_node = best_nodes[opposite].get(neighbor_state)

            if matched_node is not None:
                candidate_length = neighbor_node.g + matched_node.g

                if candidate_length < U:
                    U = candidate_length

                    if direction == FWD:
                        best_forward_meet = neighbor_node
                        best_backward_meet = matched_node
                    else:
                        best_forward_meet = matched_node
                        best_backward_meet = neighbor_node

    # Nếu không tìm được điểm gặp
    if best_forward_meet is None or best_backward_meet is None:
        return None

    path = combine_bidirectional_path(best_forward_meet, best_backward_meet)

    elapsed = (time.time() - start_time) * 1000

    nodes_in_open = len(open_maps[FWD]) + len(open_maps[BWD])
    memory_kb = _estimate_memory_kb(open_maps, closed_maps)

    return {
        "path": path,
        "steps": len(path) - 1,
        "nodes_expanded": nodes_expanded,
        "nodes_in_open": nodes_in_open,
        "time_ms": round(elapsed, 2),
        "memory_kb": memory_kb
    }

# Alias cho dễ gọi trong giao diện
mm_search = bidirectional_a_star_mim
bi_a_star_mim = bidirectional_a_star_mim
