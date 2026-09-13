from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from quantum_engine.errors import QuantumEngineError
from quantum_engine.state import COIN_E, COIN_R, flatten_grid, probabilities_1d, probabilities_2d

POST_MEASURE_COIN_1D = COIN_R
POST_MEASURE_COIN_2D = COIN_E


@dataclass(frozen=True)
class MeasurementResult:
    """Born-rule position sample and the distribution that produced it."""

    cell: int
    probabilities_before: np.ndarray
    seed_used: int


def _generator(seed: int | None) -> tuple[np.random.Generator, int]:
    if seed is None:
        seed_used = int(np.random.SeedSequence().generate_state(1)[0])
    else:
        seed_used = int(seed)
    return np.random.default_rng(seed_used), seed_used


def sample_position(probabilities: np.ndarray, seed: int | None = None) -> tuple[int, int]:
    """Draw one site index from P(x). RNG lives only in this module."""
    total = float(probabilities.sum())
    if total <= 0:
        raise QuantumEngineError("Cannot measure a zero state.")
    weights = probabilities / total
    rng, seed_used = _generator(seed)
    cell = int(rng.choice(len(weights), p=weights))
    return cell, seed_used


def collapse_1d(amplitudes: np.ndarray, cell: int) -> None:
    """Replace |ψ⟩ with |cell⟩ ⊗ |R⟩."""
    n_sites = amplitudes.shape[0]
    if not 0 <= cell < n_sites:
        raise QuantumEngineError(f"Collapse cell {cell} is outside [0, {n_sites}).")
    amplitudes.fill(0)
    amplitudes[cell, POST_MEASURE_COIN_1D] = 1.0 + 0.0j


def collapse_2d(amplitudes: np.ndarray, cell: int) -> tuple[int, int]:
    """Replace |ψ⟩ with |x,y⟩ ⊗ |E⟩. `cell` is row-major y * width + x."""
    height, width, _ = amplitudes.shape
    if not 0 <= cell < height * width:
        raise QuantumEngineError(f"Collapse cell {cell} is outside the grid.")
    y, x = divmod(cell, width)
    amplitudes.fill(0)
    amplitudes[y, x, POST_MEASURE_COIN_2D] = 1.0 + 0.0j
    return x, y


def measure_1d(amplitudes: np.ndarray, seed: int | None = None) -> MeasurementResult:
    probabilities_before = probabilities_1d(amplitudes)
    cell, seed_used = sample_position(probabilities_before, seed=seed)
    collapse_1d(amplitudes, cell)
    return MeasurementResult(
        cell=cell,
        probabilities_before=probabilities_before,
        seed_used=seed_used,
    )


def measure_2d(amplitudes: np.ndarray, seed: int | None = None) -> MeasurementResult:
    grid = probabilities_2d(amplitudes)
    flat = flatten_grid(grid)
    cell, seed_used = sample_position(flat, seed=seed)
    collapse_2d(amplitudes, cell)
    return MeasurementResult(
        cell=cell,
        probabilities_before=flat,
        seed_used=seed_used,
    )
