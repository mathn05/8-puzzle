import time
from dataclasses import dataclass

from src.core.puzzle import GOAL_STATE
from src.heuristics.walking_distance_table import clear_wd_cache


@dataclass(frozen=True)
class AlgorithmSpec:
    key: str
    label: str
    solver: callable


def instrument_heuristic(heuristic_fn):
    stats = {
        "heuristic_calls": 0,
        "heuristic_time_ms": 0.0,
    }

    def wrapped(state, goal):
        started_at = time.perf_counter()
        value = heuristic_fn(state, goal)
        stats["heuristic_calls"] += 1
        stats["heuristic_time_ms"] += (time.perf_counter() - started_at) * 1000
        return value

    wrapped.__name__ = getattr(heuristic_fn, "__name__", "heuristic")
    return wrapped, stats


def run_solver_with_metrics(start, algorithm, heuristic_spec, goal=GOAL_STATE):
    clear_wd_cache()
    wrapped_heuristic, heuristic_stats = instrument_heuristic(heuristic_spec.fn)
    result = algorithm.solver(start, wrapped_heuristic, goal)

    if result is None:
        return {
            "algorithm_key": algorithm.key,
            "algorithm_name": algorithm.label,
            "heuristic_key": heuristic_spec.key,
            "heuristic_name": heuristic_spec.label,
            "solved": False,
            "heuristic_calls": heuristic_stats["heuristic_calls"],
            "heuristic_time_ms": round(heuristic_stats["heuristic_time_ms"], 2),
        }

    enriched_result = dict(result)
    enriched_result.update(
        {
            "algorithm_key": algorithm.key,
            "algorithm_name": algorithm.label,
            "heuristic_key": heuristic_spec.key,
            "heuristic_name": heuristic_spec.label,
            "solved": True,
            "heuristic_calls": heuristic_stats["heuristic_calls"],
            "heuristic_time_ms": round(heuristic_stats["heuristic_time_ms"], 2),
        }
    )
    return enriched_result


def benchmark_algorithms(start, algorithms, heuristic_specs, goal=GOAL_STATE):
    results = []
    for algorithm in algorithms:
        for heuristic_spec in heuristic_specs:
            results.append(
                run_solver_with_metrics(
                    start=start,
                    algorithm=algorithm,
                    heuristic_spec=heuristic_spec,
                    goal=goal,
                )
            )
    return results
