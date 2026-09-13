from quantum_engine.state import COIN_R, probabilities_1d
from quantum_engine.walk import QuantumWalk


def test_opposite_phase_on_same_site_cancels() -> None:
    walk = QuantumWalk(grid_size=5, mode="1d")
    walk.initialize(position=2, coin="R")
    walk.amplitudes[2, COIN_R] = 0.5 + 0.0j
    walk.amplitudes[2, COIN_R] += -0.5 + 0.0j
    probs = probabilities_1d(walk.amplitudes)
    assert probs[2] == 0.0


def test_same_phase_constructs() -> None:
    walk = QuantumWalk(grid_size=5, mode="1d")
    walk.initialize(position=2, coin="R")
    walk.amplitudes.fill(0)
    walk.amplitudes[2, COIN_R] = 0.5 + 0.0j
    walk.amplitudes[2, COIN_R] += 0.5 + 0.0j
    probs = probabilities_1d(walk.amplitudes)
    assert probs[2] == 1.0
