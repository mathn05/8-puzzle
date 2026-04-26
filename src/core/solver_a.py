import heapq
import time

from src.core.metrics import estimate_memory_kb_from_nodes
from src.core.puzzle import GOAL_STATE, get_neighbors


class Node:
    __slots__ = ["state", "parent", "g", "h", "f"]

    def __init__(self, state, parent=None, g=0, h=0):
        self.state = state
        self.parent = parent
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, other):
        return (self.f, self.h, self.g) < (other.f, other.h, other.g)


def reconstruct_path(node):
    path = []
    while node is not None:
        path.append(node.state)
        node = node.parent
    return list(reversed(path))


def a_star(start, heuristic_fn, goal=GOAL_STATE):
    start_time = time.time()

    h0 = heuristic_fn(start, goal)
    start_node = Node(state=start, parent=None, g=0, h=h0)

    open_heap = []
    heapq.heappush(open_heap, (start_node.f, start_node.h, start_node.g, 0, start_node))

    best_g = {start: 0}
    open_nodes = {start: start_node}
    closed_nodes = {}

    nodes_expanded = 0
    counter = 1

    while open_heap:
        _, _, _, _, current = heapq.heappop(open_heap)

        if current.g != best_g.get(current.state):
            continue

        if current.state in closed_nodes:
            continue

        open_nodes.pop(current.state, None)
        closed_nodes[current.state] = current
        nodes_expanded += 1

        if current.state == goal:
            elapsed = (time.time() - start_time) * 1000
            return {
                "path": reconstruct_path(current),
                "steps": current.g,
                "nodes_expanded": nodes_expanded,
                "nodes_in_open": len(open_nodes),
                "time_ms": round(elapsed, 2),
                "memory_kb": estimate_memory_kb_from_nodes(
                    open_nodes.values(),
                    closed_nodes.values(),
                ),
            }

        for neighbor_state in get_neighbors(current.state):
            new_g = current.g + 1

            if neighbor_state in closed_nodes:
                continue

            if new_g >= best_g.get(neighbor_state, float("inf")):
                continue

            best_g[neighbor_state] = new_g
            new_h = heuristic_fn(neighbor_state, goal)

            neighbor_node = Node(
                state=neighbor_state,
                parent=current,
                g=new_g,
                h=new_h,
            )
            open_nodes[neighbor_state] = neighbor_node

            heapq.heappush(
                open_heap,
                (neighbor_node.f, neighbor_node.h, neighbor_node.g, counter, neighbor_node),
            )
            counter += 1

    return None
