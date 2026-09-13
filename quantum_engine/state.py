from __future__ import annotations

import numpy as np

from quantum_engine.errors import QuantumEngineError

COIN_R = 0
COIN_L = 1
COIN_N = 0
COIN_E = 1
COIN_S = 2
COIN_W = 3
COIN_2D = {"N": COIN_N, "E": COIN_E, "S": COIN_S, "W": COIN_W}
NORM_WARN = 1e-10
NORM_FAIL = 1e-8


def allocate_1d(n_sites: int) -> np.ndarray:
    if n_sites < 2:
        raise QuantumEngineError("1D walk needs at least 2 sites.")
    return np.zeros((n_sites, 2), dtype=np.complex128)


def initialize_1d(amplitudes: np.ndarray, position: int, coin: str = "R") -> None:
    n_sites = amplitudes.shape[0]
    if not 0 <= position < n_sites:
        raise QuantumEngineError(f"Start position {position} is outside [0, {n_sites}).")
    amplitudes.fill(0)
    label = coin.upper()
    if label not in {"R", "L"}:
        raise QuantumEngineError("1D coin must be 'R' or 'L'.")
    coin_index = COIN_R if label == "R" else COIN_L
    amplitudes[position, coin_index] = 1.0 + 0.0j


def total_probability(amplitudes: np.ndarray) -> float:
    return float(np.real(np.vdot(amplitudes, amplitudes)))


def probabilities_1d(amplitudes: np.ndarray) -> np.ndarray:
    return np.sum(np.abs(amplitudes) ** 2, axis=1).real.astype(np.float64)


def allocate_2d(height: int, width: int) -> np.ndarray:
    if height < 2 or width < 2:
        raise QuantumEngineError("2D walk needs height and width of at least 2.")
    return np.zeros((height, width, 4), dtype=np.complex128)


def initialize_2d(
    amplitudes: np.ndarray,
    x: int,
    y: int,
    coin: str = "E",
    walls: set[tuple[int, int]] | None = None,
) -> None:
    height, width, _ = amplitudes.shape
    if not (0 <= x < width and 0 <= y < height):
        raise QuantumEngineError(f"Start ({x}, {y}) is outside the grid.")
    blocked = walls or set()
    if (x, y) in blocked:
        raise QuantumEngineError("Cannot start inside a wall.")
    label = coin.upper()
    if label not in COIN_2D:
        raise QuantumEngineError("2D coin must be N, E, S, or W.")
    amplitudes.fill(0)
    amplitudes[y, x, COIN_2D[label]] = 1.0 + 0.0j


def probabilities_2d(amplitudes: np.ndarray) -> np.ndarray:
    return np.sum(np.abs(amplitudes) ** 2, axis=2).real.astype(np.float64)


def flatten_grid(grid: np.ndarray) -> np.ndarray:
    return grid.reshape(-1)


def enforce_normalization(amplitudes: np.ndarray) -> None:
    norm_sq = total_probability(amplitudes)
    if abs(norm_sq - 1.0) > NORM_FAIL:
        raise QuantumEngineError(f"State left the unit sphere: ‖ψ‖² = {norm_sq}.")
    if abs(norm_sq - 1.0) > NORM_WARN:
        amplitudes /= np.sqrt(norm_sq)
