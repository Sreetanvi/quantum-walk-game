from __future__ import annotations

from typing import Any

import numpy as np

from quantum_engine.coin import (
    PHASE_FACTORS,
    apply_coin_gate,
    apply_position_phase,
)
from quantum_engine.errors import QuantumEngineError
from quantum_engine.measurement import MeasurementResult, measure_1d, measure_2d
from quantum_engine.shift import apply_shift_1d, apply_shift_2d
from quantum_engine.state import (
    allocate_1d,
    allocate_2d,
    enforce_normalization,
    flatten_grid,
    initialize_1d,
    initialize_2d,
    probabilities_1d,
    probabilities_2d,
)


def _wall_set(raw: Any) -> set[tuple[int, int]]:
    walls: set[tuple[int, int]] = set()
    for item in raw or []:
        if isinstance(item, dict):
            walls.add((int(item["x"]), int(item.get("y", 0))))
        else:
            walls.add((int(item[0]), int(item[1])))
    return walls


def _phase_tiles(raw: Any) -> dict[tuple[int, int], complex]:
    tiles: dict[tuple[int, int], complex] = {}
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        x = int(item["x"])
        y = int(item.get("y", 0))
        label = str(item.get("gate") or item.get("phase") or "Z").strip()
        if label in PHASE_FACTORS:
            tiles[(x, y)] = PHASE_FACTORS[label]
        else:
            tiles[(x, y)] = np.exp(1j * float(label))
    return tiles


class QuantumWalk:
    """Discrete-time quantum walk: 1D Hadamard or 2D Grover with reflecting walls."""

    def __init__(
        self,
        grid_size: int = 10,
        mode: str = "1d",
        width: int | None = None,
        height: int = 1,
        walls: set[tuple[int, int]] | None = None,
        phase_tiles: dict[tuple[int, int], complex] | None = None,
    ) -> None:
        if mode not in {"1d", "2d"}:
            raise QuantumEngineError("mode must be '1d' or '2d'.")
        self.mode = mode
        self.walls = walls or set()
        self.phase_tiles = phase_tiles or {}
        self._initialized = False
        self.step_count = 0
        self.collapsed_cell: int | None = None
        self.history: list[str] = []
        self.last_gate: str | None = None
        if mode == "1d":
            self.width = width if width is not None else grid_size
            self.height = 1
            self.grid_size = self.width
            self.amplitudes = allocate_1d(self.width)
        else:
            self.width = width if width is not None else grid_size
            self.height = height
            self.grid_size = self.width
            self.amplitudes = allocate_2d(self.height, self.width)

    @classmethod
    def from_level(cls, level: dict[str, Any]) -> QuantumWalk:
        mode = level.get("mode", "1d")
        width = int(level["width"])
        height = int(level.get("height", 1))
        walls = _wall_set(level.get("walls"))
        walk = cls(
            mode=mode,
            width=width,
            height=height,
            walls=walls,
            phase_tiles=_phase_tiles(level.get("phase_gates")),
        )
        start = level.get("start") or {}
        if mode == "1d":
            walk.initialize(position=int(start.get("x", width // 2)), coin=str(start.get("coin", "R")))
        else:
            walk.initialize(
                x=int(start.get("x", 1)),
                y=int(start.get("y", 1)),
                coin=str(start.get("coin", "E")),
            )
        return walk

    def initialize(
        self,
        position: int | None = None,
        coin: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> None:
        if self.mode == "1d":
            if position is None:
                raise QuantumEngineError("1D initialize needs position.")
            initialize_1d(self.amplitudes, position=position, coin=coin or "R")
        else:
            if x is None or y is None:
                raise QuantumEngineError("2D initialize needs x and y.")
            initialize_2d(self.amplitudes, x=x, y=y, coin=coin or "E", walls=self.walls)
        self._initialized = True
        self.step_count = 0
        self.collapsed_cell = None
        self.history = []
        self.last_gate = None

    def apply_gate(self, gate: str) -> None:
        if not self._initialized:
            raise QuantumEngineError("Call initialize() before apply_gate().")
        name = gate.upper()
        apply_coin_gate(self.amplitudes, name, self.mode)
        enforce_normalization(self.amplitudes)
        self.history.append(name)
        self.last_gate = name

    def propagate(self) -> None:
        """Reflecting shift only, then phase tiles. Does not apply H/Grover."""
        if not self._initialized:
            raise QuantumEngineError("Call initialize() before propagate().")
        if self.mode == "1d":
            self.amplitudes = apply_shift_1d(self.amplitudes)
        else:
            self.amplitudes = apply_shift_2d(self.amplitudes, self.walls)
        apply_position_phase(self.amplitudes, self.mode, self.phase_tiles)
        enforce_normalization(self.amplitudes)
        self.history.append("SHIFT")
        self.step_count += 1

    def step(self) -> None:
        """Textbook DTQW step U = S C (Hadamard 1D / Grover 2D). Used by physics tests."""
        self.apply_gate("H")
        self.propagate()

    def probabilities(self) -> np.ndarray:
        if not self._initialized:
            raise QuantumEngineError("Call initialize() before probabilities().")
        if self.mode == "1d":
            return probabilities_1d(self.amplitudes)
        return flatten_grid(probabilities_2d(self.amplitudes))

    def probabilities_grid(self) -> np.ndarray:
        if self.mode != "2d":
            raise QuantumEngineError("probabilities_grid is 2D only.")
        if not self._initialized:
            raise QuantumEngineError("Call initialize() before probabilities_grid().")
        return probabilities_2d(self.amplitudes)

    def measure(self, seed: int | None = None) -> MeasurementResult:
        if not self._initialized:
            raise QuantumEngineError("Call initialize() before measure().")
        if self.mode == "1d":
            result = measure_1d(self.amplitudes, seed=seed)
        else:
            result = measure_2d(self.amplitudes, seed=seed)
        self.collapsed_cell = result.cell
        return result

    def amplitudes_copy(self) -> np.ndarray:
        return self.amplitudes.copy()
