# qaco/domain/solution.py
from __future__ import annotations
from typing import Sequence

Route = list[int]
Solution = list[Route]

def solution_key(s: Solution) -> tuple[tuple[int, ...], ...]: 
    return tuple(tuple(r) for r in s)

def edge_set(s: Solution) -> set[tuple[int, int]]: 
    return {tuple(sorted((i, j))) for r in s for i, j in zip(r[:-1], r[1:])}