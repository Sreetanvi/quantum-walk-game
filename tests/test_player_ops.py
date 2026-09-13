import numpy as np
import pytest

from quantum_engine.coin import GATES_1D, PAULI_X_2D, apply_coin_gate
from quantum_engine.errors import QuantumEngineError
from quantum_engine.walk import QuantumWalk


def test_h_then_propagate_matches_textbook_step() -> None:
    a = QuantumWalk(grid_size=10, mode="1d")
    a.initialize(position=5, coin="R")
    a.step()
    b = QuantumWalk(grid_size=10, mode="1d")
    b.initialize(position=5, coin="R")
    b.apply_gate("H")
    np.testing.assert_allclose(b.probabilities(), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
    b.propagate()
    np.testing.assert_allclose(a.probabilities(), b.probabilities())


def test_x_flips_heading_then_shift_is_left() -> None:
    walk = QuantumWalk(grid_size=10, mode="1d")
    walk.initialize(position=5, coin="R")
    walk.apply_gate("X")
    walk.propagate()
    probs = walk.probabilities()
    assert probs[4] == pytest.approx(1.0)
    assert probs[6] == pytest.approx(0.0)


def test_z_is_unitary_and_changes_later_interference() -> None:
    ident = GATES_1D["Z"].conj().T @ GATES_1D["Z"]
    assert np.allclose(ident, np.eye(2), atol=1e-12)
    mixed = QuantumWalk(grid_size=21, mode="1d")
    mixed.initialize(position=10, coin="R")
    mixed.apply_gate("H")
    mixed.propagate()
    mixed.apply_gate("Z")
    mixed.apply_gate("H")
    mixed.propagate()
    mixed.apply_gate("H")
    mixed.propagate()
    plain = QuantumWalk(grid_size=21, mode="1d")
    plain.initialize(position=10, coin="R")
    for _ in range(3):
        plain.apply_gate("H")
        plain.propagate()
    assert not np.allclose(mixed.probabilities(), plain.probabilities())


def test_2d_x_is_unitary() -> None:
    ident = PAULI_X_2D.conj().T @ PAULI_X_2D
    assert np.allclose(ident, np.eye(4), atol=1e-12)


def test_phase_tile_multiplies_amplitude() -> None:
    walk = QuantumWalk(grid_size=6, mode="1d", phase_tiles={(4, 0): -1 + 0j})
    walk.initialize(position=3, coin="R")
    walk.propagate()
    assert walk.amplitudes[4, 0] == pytest.approx(-1 + 0j)


def test_unknown_gate_rejected() -> None:
    walk = QuantumWalk(grid_size=6, mode="1d")
    walk.initialize(position=2)
    with pytest.raises(QuantumEngineError):
        apply_coin_gate(walk.amplitudes, "Q", "1d")
