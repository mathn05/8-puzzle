import heapq
import time
from heapq import heappop

from src.core.metrics import estimate_memory_kb_from_nodes
from src.core.puzzle import GOAL_STATE, get_neighbors


class Node:
    __slots__ = ["state", "parent", "g", "h", "f", "priority", "direction"]

    def __init__(self, state, parent=None, g=0, h=0, direction=0, mm_epsilon=0):
        self.state = state
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h
        self.direction = direction
        self.priority = max(2 * g + mm_epsilon, g + h)


def reconstruct_path_from_root(node):
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return list(reversed(path))


def combine_bidirectional_path(forward_node, backward_node):
    path_start_to_meet = reconstruct_path_from_root(forward_node)
    path_goal_to_meet = reconstruct_path_from_root(backward_node)
    path_meet_to_goal = list(reversed(path_goal_to_meet))
    return path_start_to_meet + path_meet_to_goal[1:]


def _push_node(priority_heap, f_heap, g_heap, node, counter):
    heapq.heappush(priority_heap, (node.priority, node.g, node.f, counter, node))
    heapq.heappush(f_heap, (node.f, node.g, counter, node))
    heapq.heappush(g_heap, (node.g, node.f, counter, node))


def _is_current_open_node(node, open_map):
    return open_map.get(node.state) is node


def _peek_valid(heap, open_map):
    while heap:
        node = heap[0][-1]
        if _is_current_open_node(node, open_map):
            return node
        heapq.heappop(heap)
    return None


def _pop_valid(heap, open_map):
    while heap:
        node = heappop(heap)[-1]
        if _is_current_open_node(node, open_map):
            return node
    return None


def bidirectional_a_star_mim(start, heuristic_fn, goal=GOAL_STATE, mm_epsilon=0):
    start_time = time.time()

    if start == goal:
        return {
            "path": [start],
            "steps": 0,
            "nodes_expanded": 0,
            "nodes_in_open": 0,
            "time_ms": 0,
            "memory_kb": 0,
        }

    fwd = 0
    bwd = 1

    roots = {fwd: start, bwd: goal}
    targets = {fwd: goal, bwd: start}

    priority_heaps = {fwd: [], bwd: []}
    f_heaps = {fwd: [], bwd: []}
    g_heaps = {fwd: [], bwd: []}
    open_maps = {fwd: {}, bwd: {}}
    closed_maps = {fwd: {}, bwd: {}}
    best_nodes = {fwd: {}, bwd: {}}

    counter = 0

    for direction in (fwd, bwd):
        root_state = roots[direction]
        h0 = heuristic_fn(root_state, targets[direction])
        root_node = Node(
            state=root_state,
            parent=None,
            g=0,
            h=h0,
            direction=direction,
            mm_epsilon=mm_epsilon,
        )

        open_maps[direction][root_state] = root_node
        best_nodes[direction][root_state] = root_node
        _push_node(
            priority_heaps[direction],
            f_heaps[direction],
            g_heaps[direction],
            root_node,
            counter,
        )
        counter += 1

    best_path_cost = float("inf")
    best_forward_meet = None
    best_backward_meet = None
    nodes_expanded = 0

    while open_maps[fwd] and open_maps[bwd]:
        fwd_priority_node = _peek_valid(priority_heaps[fwd], open_maps[fwd])
        bwd_priority_node = _peek_valid(priority_heaps[bwd], open_maps[bwd])
        fwd_f_node = _peek_valid(f_heaps[fwd], open_maps[fwd])
        bwd_f_node = _peek_valid(f_heaps[bwd], open_maps[bwd])
        fwd_g_node = _peek_valid(g_heaps[fwd], open_maps[fwd])
        bwd_g_node = _peek_valid(g_heaps[bwd], open_maps[bwd])

        if (
            fwd_priority_node is None
            or bwd_priority_node is None
            or fwd_f_node is None
            or bwd_f_node is None
            or fwd_g_node is None
            or bwd_g_node is None
        ):
            break

        current_bound = min(fwd_priority_node.priority, bwd_priority_node.priority)
        stop_bound = max(
            current_bound,
            fwd_f_node.f,
            bwd_f_node.f,
            fwd_g_node.g + bwd_g_node.g + 1,
        )
        if best_path_cost <= stop_bound:
            break

        direction = fwd if fwd_priority_node.priority <= bwd_priority_node.priority else bwd
        opposite = 1 - direction
        current = _pop_valid(priority_heaps[direction], open_maps[direction])

        if current is None:
            break

        open_maps[direction].pop(current.state, None)
        closed_maps[direction][current.state] = current
        nodes_expanded += 1

        for neighbor_state in get_neighbors(current.state):
            new_g = current.g + 1

            old_open_node = open_maps[direction].get(neighbor_state)
            old_closed_node = closed_maps[direction].get(neighbor_state)

            if old_open_node is not None and old_open_node.g <= new_g:
                continue
            if old_closed_node is not None and old_closed_node.g <= new_g:
                continue

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
                mm_epsilon=mm_epsilon,
            )

            open_maps[direction][neighbor_state] = neighbor_node
            best_nodes[direction][neighbor_state] = neighbor_node
            _push_node(
                priority_heaps[direction],
                f_heaps[direction],
                g_heaps[direction],
                neighbor_node,
                counter,
            )
            counter += 1

            matched_node = best_nodes[opposite].get(neighbor_state)
            if matched_node is None:
                continue

            candidate_length = neighbor_node.g + matched_node.g
            if candidate_length < best_path_cost:
                best_path_cost = candidate_length
                if direction == fwd:
                    best_forward_meet = neighbor_node
                    best_backward_meet = matched_node
                else:
                    best_forward_meet = matched_node
                    best_backward_meet = neighbor_node

    if best_forward_meet is None or best_backward_meet is None:
        return None

    path = combine_bidirectional_path(best_forward_meet, best_backward_meet)
    elapsed = (time.time() - start_time) * 1000
    nodes_in_open = len(open_maps[fwd]) + len(open_maps[bwd])
    memory_kb = estimate_memory_kb_from_nodes(
        list(open_maps[fwd].values()) + list(open_maps[bwd].values()),
        list(closed_maps[fwd].values()) + list(closed_maps[bwd].values()),
    )

    return {
        "path": path,
        "steps": len(path) - 1,
        "nodes_expanded": nodes_expanded,
        "nodes_in_open": nodes_in_open,
        "time_ms": round(elapsed, 2),
        "memory_kb": memory_kb,
    }


mm_search = bidirectional_a_star_mim
