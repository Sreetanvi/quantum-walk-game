"""Helpers for checking the 1D Hadamard walk against known qualitative results."""

from __future__ import annotations

import numpy as np

from quantum_engine.walk import QuantumWalk


def hadamard_walk_probabilities(n_sites: int, start: int, steps: int, coin: str = "R") -> np.ndarray:
    walk = QuantumWalk(grid_size=n_sites, mode="1d")
    walk.initialize(position=start, coin=coin)
    for _ in range(steps):
        walk.step()
    return walk.probabilities()


def binomial_random_walk_probabilities(n_sites: int, start: int, steps: int) -> np.ndarray:
    """Classical symmetric random walk on a line (reflecting), for contrast tests."""
    probs = np.zeros(n_sites, dtype=np.float64)
    probs[start] = 1.0
    for _ in range(steps):
        nxt = np.zeros_like(probs)
        for x, p in enumerate(probs):
            if p == 0:
                continue
            left, right = x - 1, x + 1
            if left < 0:
                nxt[x] += p * 0.5
                nxt[right] += p * 0.5
            elif right >= n_sites:
                nxt[x] += p * 0.5
                nxt[left] += p * 0.5
            else:
                nxt[left] += p * 0.5
                nxt[right] += p * 0.5
        probs = nxt
    return probs
