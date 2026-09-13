from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class StartRequest(BaseModel):
    level_id: str = "01_superposition"


class MoveRequest(BaseModel):
    session_id: str
    action: Literal["H", "X", "Z", "S", "quantum_walk"]


class MeasureRequest(BaseModel):
    session_id: str
    seed: int | None = None


class CellSets(BaseModel):
    walls: list[int] = Field(default_factory=list)
    traps: list[int] = Field(default_factory=list)
    goals: list[int] = Field(default_factory=list)
    observations: list[int] = Field(default_factory=list)
    phase_gates: list[int] = Field(default_factory=list)


class GameStateDTO(BaseModel):
    session_id: str
    level_id: str
    mode: str
    width: int
    height: int
    cells: CellSets
    probabilities: list[float]
    probabilities_2d: list[list[float]] | None = None
    step: int
    step_limit: int
    status: Literal["playing", "won", "lost"]
    collapsed_cell: int | None
    p_goal: float
    p_trap: float
    p_observation: float = 0.0
    target_p_goal: float = 0.0
    objective_met: bool = False
    last_op: str | None = None
    explanation: str | None = None
    allowed_ops: list[str] = Field(default_factory=list)
    ops_used: int = 0
    op_limit: int | None = None
    history: list[str] = Field(default_factory=list)
    message: str | None
    score: int | None = None
    quantum_outcome: Literal["goal", "trap", "other"] | None = None
    beginner_assist: Literal["success", "unlucky", "off"] = "off"
    assist_seed: int | None = None


class LevelSummary(BaseModel):
    id: str
    title: str
    order: int


class HealthResponse(BaseModel):
    ok: bool


class CircuitResponse(BaseModel):
    supported: bool
    message: str
    session_id: str | None = None
    diagram: str | None = None
    qasm: str | None = None
    steps_shown: int | None = None
    n_qubits: int | None = None
    n_sites: int | None = None
    history: list[str] = Field(default_factory=list)
