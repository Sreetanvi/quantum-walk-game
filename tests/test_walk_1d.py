import numpy as np
import pytest

from quantum_engine import QuantumEngineError, QuantumWalk
from quantum_engine.coin import HADAMARD
from quantum_engine.validation import binomial_random_walk_probabilities, hadamard_walk_probabilities


def test_hadamard_is_unitary() -> None:
    ident = HADAMARD.conj().T @ HADAMARD
    assert np.allclose(ident, np.eye(2), atol=1e-12)


def test_initialize_and_first_step_splits() -> None:
    walk = QuantumWalk(grid_size=10, mode="1d")
    walk.initialize(position=5, coin="R")
    np.testing.assert_allclose(walk.probabilities(), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])

    walk.step()
    probs = walk.probabilities()
    assert walk.step_count == 1
    assert abs(probs.sum() - 1.0) < 1e-12
    # H|R⟩ then shift: mass on 4 (left) and 6 (right), none remains at 5.
    assert probs[5] == pytest.approx(0.0, abs=1e-12)
    assert probs[4] == pytest.approx(0.5, abs=1e-12)
    assert probs[6] == pytest.approx(0.5, abs=1e-12)


def test_norm_stays_one_for_many_steps() -> None:
    walk = QuantumWalk(grid_size=21, mode="1d")
    walk.initialize(position=10, coin="R")
    for _ in range(20):
        walk.step()
        assert abs(walk.probabilities().sum() - 1.0) < 1e-10


def test_reflecting_left_edge() -> None:
    walk = QuantumWalk(grid_size=5, mode="1d")
    walk.initialize(position=0, coin="L")
    walk.step()
    assert abs(walk.probabilities().sum() - 1.0) < 1e-12
    assert walk.probabilities()[-1] == pytest.approx(0.0, abs=1e-12)


def test_ballistic_not_binomial() -> None:
    """Textbook Hadamard walk: mass near the edges, dip near the origin — not a Gaussian."""
    n_sites, start, steps = 51, 25, 10
    quantum = hadamard_walk_probabilities(n_sites, start, steps)
    classical = binomial_random_walk_probabilities(n_sites, start, steps)

    assert abs(quantum.sum() - 1.0) < 1e-10
    assert quantum[0] == pytest.approx(0.0, abs=1e-12)
    assert quantum[-1] == pytest.approx(0.0, abs=1e-12)

    origin = start
    peak = int(quantum.argmax())
    # After even t, only same-parity-as-(start+t) sites are occupied. ±7 is the wrong slot.
    # |R⟩ start makes the usual right-biased Hadamard walk: peak away from the origin.
    assert peak != origin
    assert abs(peak - origin) >= 4
    assert quantum[origin] < quantum[peak]
    assert quantum[origin] < classical[origin]


def test_step_before_initialize_raises() -> None:
    walk = QuantumWalk(grid_size=8)
    with pytest.raises(QuantumEngineError):
        walk.step()


def test_from_level() -> None:
    walk = QuantumWalk.from_level(
        {
            "mode": "1d",
            "width": 11,
            "start": {"x": 5, "y": 0, "coin": "R"},
        }
    )
    assert walk.grid_size == 11
    assert walk.probabilities()[5] == pytest.approx(1.0)
