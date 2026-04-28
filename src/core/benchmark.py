import time
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
import os

from src.core.puzzle import GOAL_STATE
from src.heuristics.walking_distance_table import clear_wd_cache
from src.utils.board import generate_random_solvable


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

def run_one_benchmark_case(case_index, start, algorithms, heuristic_specs, goal):
    case_results = benchmark_algorithms(
        start = start, 
        algorithms = algorithms, 
        heuristic_specs = heuristic_specs, 
        goal=goal)
    return case_index, case_results


def benchmark_average_random_cases(algorithms, heuristic_specs, goal=GOAL_STATE, num_cases=50):
    starts = [generate_random_solvable() for _ in range(num_cases)]
    aggregated_results = {}

    max_workers = max(1, (os.cpu_count() or 2) - 1)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                run_one_benchmark_case,
                case_index,
                start,
                algorithms,
                heuristic_specs,
                goal,
            )
            for case_index, start in enumerate(starts)
        ]

        for future in as_completed(futures):
            _, case_results = future.result()

            for result in case_results:
                result_key = (result["algorithm_key"], result["heuristic_key"])
                aggregate = aggregated_results.setdefault(
                    result_key,
                    {
                        "algorithm_key": result["algorithm_key"],
                        "algorithm_name": result["algorithm_name"],
                        "heuristic_key": result["heuristic_key"],
                        "heuristic_name": result["heuristic_name"],
                        "steps": 0.0,
                        "nodes_expanded": 0.0,
                        "nodes_in_open": 0.0,
                        "time_ms": 0.0,
                        "memory_kb": 0.0,
                        "heuristic_calls": 0.0,
                        "heuristic_time_ms": 0.0,
                        "cases_run": 0,
                        "cases_solved": 0,
                    },
                )

                aggregate["cases_run"] += 1
                if result.get("solved"):
                    aggregate["cases_solved"] += 1

                for metric_key in (
                    "steps",
                    "nodes_expanded",
                    "nodes_in_open",
                    "time_ms",
                    "memory_kb",
                    "heuristic_calls",
                    "heuristic_time_ms",
                ):
                    aggregate[metric_key] += result.get(metric_key, 0.0)

    averaged_results = []
    for aggregate in aggregated_results.values():
        cases_run = aggregate["cases_run"] or 1
        averaged_results.append(
            {
                "algorithm_key": aggregate["algorithm_key"],
                "algorithm_name": aggregate["algorithm_name"],
                "heuristic_key": aggregate["heuristic_key"],
                "heuristic_name": aggregate["heuristic_name"],
                "solved": aggregate["cases_solved"] == cases_run,
                "steps": round(aggregate["steps"] / cases_run, 2),
                "nodes_expanded": round(aggregate["nodes_expanded"] / cases_run, 2),
                "nodes_in_open": round(aggregate["nodes_in_open"] / cases_run, 2),
                "time_ms": round(aggregate["time_ms"] / cases_run, 2),
                "memory_kb": round(aggregate["memory_kb"] / cases_run, 2),
                "heuristic_calls": round(aggregate["heuristic_calls"] / cases_run, 2),
                "heuristic_time_ms": round(aggregate["heuristic_time_ms"] / cases_run, 2),
                "cases_run": cases_run,
                "cases_solved": aggregate["cases_solved"],
            }
        )

    return averaged_results

