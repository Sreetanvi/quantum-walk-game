import numpy as np
import pytest

from quantum_engine.coin import GROVER
from quantum_engine.errors import QuantumEngineError
from quantum_engine.shift import apply_shift_2d
from quantum_engine.state import COIN_E, COIN_W
from quantum_engine.walk import QuantumWalk


def test_grover_is_unitary() -> None:
    ident = GROVER.conj().T @ GROVER
    assert np.allclose(ident, np.eye(4), atol=1e-12)


def test_first_step_spreads_to_four_neighbors() -> None:
    walk = QuantumWalk(mode="2d", width=5, height=5)
    walk.initialize(x=2, y=2, coin="E")
    walk.step()
    grid = walk.probabilities_grid()
    assert abs(grid.sum() - 1.0) < 1e-12
    assert grid[2, 2] == pytest.approx(0.0, abs=1e-12)
    for y, x in ((1, 2), (2, 3), (3, 2), (2, 1)):
        assert grid[y, x] == pytest.approx(0.25, abs=1e-12)


def test_map_edge_keeps_unit_norm() -> None:
    walk = QuantumWalk(mode="2d", width=3, height=3)
    walk.initialize(x=0, y=0, coin="W")
    walk.step()
    assert abs(walk.probabilities().sum() - 1.0) < 1e-12


def test_internal_wall_reflects() -> None:
    walls = {(2, 1)}
    walk = QuantumWalk(mode="2d", width=4, height=3, walls=walls)
    walk.initialize(x=1, y=1, coin="E")
    walk.amplitudes.fill(0)
    walk.amplitudes[1, 1, COIN_E] = 1.0 + 0.0j
    walk.amplitudes = apply_shift_2d(walk.amplitudes, walls)
    assert walk.amplitudes[1, 2, COIN_E] == pytest.approx(0.0)
    assert walk.amplitudes[1, 1, COIN_W] == pytest.approx(1.0 + 0.0j)


def test_norm_and_measure_on_grid() -> None:
    walk = QuantumWalk(mode="2d", width=5, height=4)
    walk.initialize(x=1, y=1, coin="N")
    for _ in range(6):
        walk.step()
        assert abs(walk.probabilities().sum() - 1.0) < 1e-10
    before = walk.probabilities().copy()
    result = walk.measure(seed=4)
    assert 0 <= result.cell < 20
    after = walk.probabilities()
    assert after[result.cell] == pytest.approx(1.0)
    np.testing.assert_allclose(result.probabilities_before, before)
    y, x = divmod(result.cell, 5)
    assert walk.amplitudes[y, x, COIN_E] == pytest.approx(1.0 + 0.0j)


def test_from_level_2d() -> None:
    walk = QuantumWalk.from_level(
        {
            "mode": "2d",
            "width": 5,
            "height": 4,
            "walls": [{"x": 2, "y": 1}],
            "start": {"x": 1, "y": 1, "coin": "E"},
        }
    )
    assert walk.mode == "2d"
    assert walk.walls == {(2, 1)}
    assert walk.probabilities_grid()[1, 1] == pytest.approx(1.0)


def test_cannot_start_in_wall() -> None:
    walk = QuantumWalk(mode="2d", width=3, height=3, walls={(1, 1)})
    with pytest.raises(QuantumEngineError):
        walk.initialize(x=1, y=1, coin="E")
