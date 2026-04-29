import random
import time
import os
import pickle

from typing import Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict, deque

from src.core.puzzle import GOAL_STATE, get_neighbors
from src.utils.board import generate_random_solvable
from src.heuristics.walking_distance_table import get_wd_tables

_STATES_BY_DEPTH_CACHE = None
STATES_BY_DEPTH_FILE = "states_by_depth_8puzzle.pkl"

def get_states_by_depth(goal=GOAL_STATE):
    global _STATES_BY_DEPTH_CACHE

    if _STATES_BY_DEPTH_CACHE is not None:
        return _STATES_BY_DEPTH_CACHE

    if os.path.exists(STATES_BY_DEPTH_FILE):
        with open(STATES_BY_DEPTH_FILE, "rb") as f:
            _STATES_BY_DEPTH_CACHE = pickle.load(f)
    else:
        _STATES_BY_DEPTH_CACHE = build_states_by_depth(goal)
        with open(STATES_BY_DEPTH_FILE, "wb") as f:
            pickle.dump(_STATES_BY_DEPTH_CACHE, f)

    return _STATES_BY_DEPTH_CACHE

def build_states_by_depth(goal=GOAL_STATE):
    states_by_depth = defaultdict(list)
    visited = {goal: 0}
    queue = deque([goal])

    while queue:
        state = queue.popleft()
        depth = visited[state]
        states_by_depth[depth].append(state)

        for neighbor in get_neighbors(state):
            if neighbor not in visited:
                visited[neighbor] = depth + 1
                queue.append(neighbor)
    return states_by_depth

def generate_stratified_cases(goal=GOAL_STATE, seed=42):
    rng = random.Random(seed)
    states_by_depth = get_states_by_depth(goal)

    depth_counts = {
        5: 1,
        6: 1,
        7: 1,
        8: 1,
        9: 1,
        10: 2,

        11: 2,
        12: 2,
        13: 2,
        14: 2,
        15: 2,

        16: 2,
        17: 2,
        18: 2,
        19: 3,
        20: 3,

        21: 3,
        22: 3,
        23: 3,
        24: 3,
        25: 2,

        26: 2,
        27: 1,
        28: 1,
        29: 1,
        30: 1,
        31: 1,
    }

    cases = []

    for depth, count in depth_counts.items():
        candidates = states_by_depth.get(depth, [])
        if not candidates:
            raise ValueError(f"Không có state ở depth {depth}")

        selected = rng.sample(candidates, min(count, len(candidates)))
        cases.extend(selected)

    rng.shuffle(cases)
    return cases


@dataclass(frozen=True)
class AlgorithmSpec:
    key: str
    label: str
    solver: Callable


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


def benchmark_average_random_cases(algorithms, heuristic_specs, goal=GOAL_STATE, num_cases=50, use_stratified=True, seed=42):
    if use_stratified:
        starts = generate_stratified_cases(goal=goal, seed=seed)
    else:
        starts = [generate_random_solvable() for _ in range(num_cases)]

    aggregated_results = {}
    max_workers = max(1, (os.cpu_count() or 2) - 1)

    with ProcessPoolExecutor(max_workers=max_workers, initializer=get_wd_tables) as executor:
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

