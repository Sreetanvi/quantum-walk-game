"""Coin unitaries. 1D: |R⟩ = |0⟩, |L⟩ = |1⟩. 2D: |N⟩,|E⟩,|S⟩,|W⟩."""

from __future__ import annotations

import numpy as np

from quantum_engine.errors import QuantumEngineError

INV_SQRT2 = 1.0 / np.sqrt(2.0)

# H |R⟩ = (|R⟩ + |L⟩)/√2,  H |L⟩ = (|R⟩ − |L⟩)/√2
HADAMARD = np.array(
    [[INV_SQRT2, INV_SQRT2], [INV_SQRT2, -INV_SQRT2]],
    dtype=np.complex128,
)
PAULI_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
PHASE_S = np.array([[1, 0], [0, 1j]], dtype=np.complex128)

GATES_1D = {"H": HADAMARD, "X": PAULI_X, "Z": PAULI_Z, "S": PHASE_S}

# G = 2|s⟩⟨s| − I, |s⟩ = (1/2) Σ_d |d⟩  →  G_ii = −1/2, G_ij = 1/2 (i≠j)
GROVER = (0.5 * np.ones((4, 4)) - np.eye(4)).astype(np.complex128)

# X: N↔S, E↔W. Z/S phase the south and west components.
PAULI_X_2D = np.array(
    [
        [0, 0, 1, 0],
        [0, 0, 0, 1],
        [1, 0, 0, 0],
        [0, 1, 0, 0],
    ],
    dtype=np.complex128,
)
PAULI_Z_2D = np.diag([1, 1, -1, -1]).astype(np.complex128)
PHASE_S_2D = np.diag([1, 1, 1j, 1j]).astype(np.complex128)

GATES_2D = {"H": GROVER, "X": PAULI_X_2D, "Z": PAULI_Z_2D, "S": PHASE_S_2D}

COIN_GATES = ("H", "X", "Z", "S")
PHASE_FACTORS = {
    "Z": np.complex128(-1 + 0j),
    "S": np.complex128(1j),
    "-1": np.complex128(-1 + 0j),
    "i": np.complex128(1j),
}


def apply_hadamard(amplitudes: np.ndarray) -> None:
    """Apply H to the coin of every site. `amplitudes` is (N, 2) with columns (R, L)."""
    amplitudes[:] = amplitudes @ HADAMARD.T


def apply_grover(amplitudes: np.ndarray) -> None:
    """Apply the 4-direction Grover coin on every cell. `amplitudes` is (H, W, 4)."""
    amplitudes[:] = amplitudes @ GROVER.T


def apply_coin_gate(amplitudes: np.ndarray, gate: str, mode: str) -> None:
    """Apply a named coin unitary on every cell. Does not move probability between cells."""
    name = gate.upper()
    if mode == "1d":
        matrix = GATES_1D.get(name)
        if matrix is None:
            raise QuantumEngineError(f"Unknown 1D coin gate: {gate}")
        amplitudes[:] = amplitudes @ matrix.T
        return
    if mode == "2d":
        matrix = GATES_2D.get(name)
        if matrix is None:
            raise QuantumEngineError(f"Unknown 2D coin gate: {gate}")
        amplitudes[:] = amplitudes @ matrix.T
        return
    raise QuantumEngineError("mode must be '1d' or '2d'.")


def apply_position_phase(
    amplitudes: np.ndarray,
    mode: str,
    phases: dict[tuple[int, int], complex],
) -> None:
    """Multiply amplitudes on phase-tile cells (unitary, no collapse)."""
    if not phases:
        return
    if mode == "1d":
        for (x, _y), factor in phases.items():
            if 0 <= x < amplitudes.shape[0]:
                amplitudes[x] *= factor
        return
    height, width, _ = amplitudes.shape
    for (x, y), factor in phases.items():
        if 0 <= x < width and 0 <= y < height:
            amplitudes[y, x] *= factor
