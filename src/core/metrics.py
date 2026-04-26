import sys


def estimate_memory_kb_from_nodes(open_nodes, closed_nodes):
    total_bytes = 0

    for node in open_nodes:
        total_bytes += sys.getsizeof(node)
        total_bytes += sys.getsizeof(node.state)
        total_bytes += sum(sys.getsizeof(row) for row in node.state)

    for node in closed_nodes:
        total_bytes += sys.getsizeof(node)
        total_bytes += sys.getsizeof(node.state)
        total_bytes += sum(sys.getsizeof(row) for row in node.state)

    return round(total_bytes / 1024, 2)
