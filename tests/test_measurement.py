import numpy as np
import pytest

from quantum_engine import QuantumEngineError, QuantumWalk
from quantum_engine.state import COIN_L, COIN_R


def test_measure_before_initialize_raises() -> None:
    walk = QuantumWalk(grid_size=8)
    with pytest.raises(QuantumEngineError):
        walk.measure(seed=1)


def test_measure_at_step_zero_is_certain() -> None:
    walk = QuantumWalk(grid_size=10)
    walk.initialize(position=5, coin="R")
    result = walk.measure(seed=0)
    assert result.cell == 5
    assert result.seed_used == 0
    np.testing.assert_allclose(result.probabilities_before[5], 1.0)
    np.testing.assert_allclose(walk.probabilities(), [0, 0, 0, 0, 0, 1, 0, 0, 0, 0])
    assert walk.collapsed_cell == 5
    assert walk.amplitudes[5, COIN_R] == pytest.approx(1.0 + 0.0j)
    assert walk.amplitudes[5, COIN_L] == pytest.approx(0.0)


def test_collapse_is_a_delta_after_a_split() -> None:
    walk = QuantumWalk(grid_size=10)
    walk.initialize(position=5, coin="R")
    walk.step()
    before = walk.probabilities().copy()
    result = walk.measure(seed=3)
    assert result.cell in (4, 6)
    np.testing.assert_allclose(result.probabilities_before, before)
    after = walk.probabilities()
    assert after[result.cell] == pytest.approx(1.0)
    assert after.sum() == pytest.approx(1.0)
    assert np.count_nonzero(after > 1e-12) == 1


def test_same_seed_replays() -> None:
    def collapse_once() -> int:
        walk = QuantumWalk(grid_size=21)
        walk.initialize(position=10, coin="R")
        for _ in range(6):
            walk.step()
        return walk.measure(seed=7).cell

    assert collapse_once() == collapse_once()


def test_histogram_matches_born_rule() -> None:
    n_trials = 10_000
    seed = 123
    walk = QuantumWalk(grid_size=10)
    walk.initialize(position=5, coin="R")
    walk.step()
    expected = walk.probabilities()

    counts = np.zeros(10, dtype=np.int64)
    rng_master = np.random.default_rng(seed)
    for _ in range(n_trials):
        trial = QuantumWalk(grid_size=10)
        trial.initialize(position=5, coin="R")
        trial.step()
        trial_seed = int(rng_master.integers(0, 2**31 - 1))
        counts[trial.measure(seed=trial_seed).cell] += 1

    frequencies = counts / n_trials
    # Two-site 50/50 split after one step; 10k shots should stay close.
    assert frequencies[4] == pytest.approx(expected[4], abs=0.03)
    assert frequencies[6] == pytest.approx(expected[6], abs=0.03)
    assert frequencies[4] + frequencies[6] == pytest.approx(1.0, abs=1e-12)
