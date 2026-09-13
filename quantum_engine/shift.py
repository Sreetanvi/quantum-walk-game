"""Conditional shift with reflecting edges (closed box, no wrap)."""

from __future__ import annotations

import numpy as np

from quantum_engine.state import COIN_E, COIN_L, COIN_N, COIN_R, COIN_S, COIN_W

# Coin order N, E, S, W. +x right, +y down (CSS). North is up (y-1).
DELTA_2D = (
    (0, -1),  # N
    (1, 0),  # E
    (0, 1),  # S
    (-1, 0),  # W
)
OPPOSITE_2D = (COIN_S, COIN_W, COIN_N, COIN_E)


def apply_shift_1d(amplitudes: np.ndarray) -> np.ndarray:
    """
    |x, R⟩ → |x+1, R⟩ if x+1 is on the line, else stay at x and flip to L.
    |x, L⟩ → |x-1, L⟩ if x-1 is on the line, else stay at x and flip to R.
    """
    n_sites = amplitudes.shape[0]
    nxt = np.zeros_like(amplitudes)

    for x in range(n_sites):
        amp_r = amplitudes[x, COIN_R]
        amp_l = amplitudes[x, COIN_L]

        if x + 1 < n_sites:
            nxt[x + 1, COIN_R] += amp_r
        else:
            nxt[x, COIN_L] += amp_r

        if x - 1 >= 0:
            nxt[x - 1, COIN_L] += amp_l
        else:
            nxt[x, COIN_R] += amp_l

    return nxt


def _walkable(
    x: int,
    y: int,
    width: int,
    height: int,
    walls: set[tuple[int, int]],
) -> bool:
    return 0 <= x < width and 0 <= y < height and (x, y) not in walls


def apply_shift_2d(amplitudes: np.ndarray, walls: set[tuple[int, int]] | None = None) -> np.ndarray:
    """
    Move each coin component one step. Off-board or wall: stay and flip N↔S or E↔W.
    """
    blocked = walls or set()
    height, width, _ = amplitudes.shape
    nxt = np.zeros_like(amplitudes)
    for y in range(height):
        for x in range(width):
            if (x, y) in blocked:
                continue
            for coin, (dx, dy) in enumerate(DELTA_2D):
                amp = amplitudes[y, x, coin]
                if amp == 0:
                    continue
                nx, ny = x + dx, y + dy
                if _walkable(nx, ny, width, height, blocked):
                    nxt[ny, nx, coin] += amp
                else:
                    nxt[y, x, OPPOSITE_2D[coin]] += amp
    return nxt
