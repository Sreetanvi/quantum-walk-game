import numpy as np
import pytest

from quantum_engine.qiskit_circuit import circuit_from_ops, simulate_probabilities, walk_circuit
from quantum_engine.walk import QuantumWalk


@pytest.mark.parametrize("steps", [1, 2, 3])
def test_aer_matches_numpy_power_of_two_line(steps: int) -> None:
    n_sites, start = 8, 3
    walk = QuantumWalk(grid_size=n_sites)
    walk.initialize(position=start, coin="R")
    for _ in range(steps):
        walk.step()
    aer = simulate_probabilities(n_sites, start, "R", steps)
    np.testing.assert_allclose(aer, walk.probabilities(), atol=1e-8)


@pytest.mark.parametrize("steps", [1, 2, 3])
def test_aer_matches_numpy_level_width(steps: int) -> None:
    n_sites, start = 11, 5
    walk = QuantumWalk(grid_size=n_sites)
    walk.initialize(position=start, coin="R")
    for _ in range(steps):
        walk.step()
    aer = simulate_probabilities(n_sites, start, "R", steps)
    np.testing.assert_allclose(aer, walk.probabilities(), atol=1e-8)


def test_one_step_circuit_has_h_and_shift() -> None:
    qc = walk_circuit(11, steps=1)
    assert qc.num_qubits == 5
    labels = [inst.operation.name for inst in qc.data]
    assert "h" in labels
    assert any(name in {"S", "unitary"} for name in labels)


def test_player_ops_circuit_contains_z_and_shift() -> None:
    qc = circuit_from_ops(11, ["H", "Z", "SHIFT"])
    names = [inst.operation.name.lower() for inst in qc.data]
    assert "h" in names
    assert "z" in names
    assert any(name in {"s", "unitary"} for name in names)
