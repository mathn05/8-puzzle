from dataclasses import dataclass

from src.heuristics.gaschnig import gaschnig
from src.heuristics.inversion_distance import inversion_distance
from src.heuristics.linear_conflict import linear_conflict
from src.heuristics.manhattan import manhattan
from src.heuristics.manhattan_linear_conflict import manhattan_linear_conflict
from src.heuristics.misplaced_tiles import misplaced_tiles
from src.heuristics.walking_distance import walking_distance


@dataclass(frozen=True)
class HeuristicSpec:
    key: str
    label: str
    fn: callable


HEURISTIC_SPECS = [
    HeuristicSpec("misplaced_tiles", "Misplaced Tiles", misplaced_tiles),
    HeuristicSpec("gaschnig", "Gaschnig", gaschnig),
    HeuristicSpec("walking_distance", "Walking Distance", walking_distance),
    HeuristicSpec("inversion_distance", "Inversion Distance", inversion_distance),
    HeuristicSpec("manhattan", "Manhattan Distance", manhattan),
    HeuristicSpec(
        "manhattan_linear_conflict",
        "Manhattan + Linear Conflict",
        manhattan_linear_conflict,
    ),
]

HEURISTIC_BY_KEY = {spec.key: spec for spec in HEURISTIC_SPECS}

__all__ = [
    "HeuristicSpec",
    "HEURISTIC_SPECS",
    "HEURISTIC_BY_KEY",
    "gaschnig",
    "inversion_distance",
    "linear_conflict",
    "manhattan",
    "manhattan_linear_conflict",
    "misplaced_tiles",
    "walking_distance",
]
