from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

import numpy as np
from fastapi import HTTPException

from backend.levels import linear_cells, load_level
from backend.models import CellSets, CircuitResponse, GameStateDTO
from quantum_engine import QuantumWalk
from quantum_engine.coin import COIN_GATES
from quantum_engine.errors import QuantumEngineError
from quantum_engine.qiskit_circuit import circuit_view

SESSIONS: dict[str, "GameSession"] = {}

# Game-layer only. Does not touch amplitudes or Born sampling.
BEGINNER_ASSIST_P = 0.75

DEFAULT_OPS = ["H", "X", "Z", "S"]

EXPLANATIONS = {
    "H": "H applied: the coin was mixed into superposition (1D Hadamard, 2D Grover). Cell probabilities did not move yet.",
    "X": "X applied: direction labels flipped. Probability on each cell is unchanged until you walk.",
    "Z": "Z applied: relative phases flipped, which can change future interference.",
    "S": "S applied: a +i phase on part of the coin. Later overlapping paths can add differently.",
    "quantum_walk": "Quantum Walk: amplitudes propagated to neighboring cells (shift). Phase tiles, if any, were applied.",
    "measure": "Measurement: the wavefunction collapsed to one physical cell.",
}


@dataclass
class GameSession:
    session_id: str
    level: dict
    walk: QuantumWalk
    status: str = "playing"
    collapsed_cell: int | None = None
    p_goal: float = 0.0
    p_trap: float = 0.0
    p_observation: float = 0.0
    message: str | None = None
    score: int | None = None
    frozen_probabilities: list[float] | None = None
    cells: dict[str, list[int]] = field(default_factory=dict)
    last_op: str | None = None
    explanation: str | None = None
    ops_used: int = 0
    quantum_outcome: str | None = None
    beginner_assist: str = "off"
    assist_seed: int | None = None


def _floats(values) -> list[float]:
    return [float(v) for v in values]


def _mass_on(probabilities: list[float], indices: list[int]) -> float:
    return float(sum(probabilities[i] for i in indices if 0 <= i < len(probabilities)))


def _allowed_ops(level: dict) -> list[str]:
    raw = level.get("allowed_ops")
    if not raw:
        return list(DEFAULT_OPS)
    return [str(op).upper() for op in raw if str(op).upper() in COIN_GATES]


def _target_p(level: dict) -> float:
    return float(level.get("target_p_goal", 0.0))


def _op_limit(level: dict) -> int | None:
    raw = level.get("op_limit")
    return int(raw) if raw is not None else None


def _obs_threshold(level: dict) -> float:
    return float(level.get("observation_threshold", 0.51))


def _refresh_skill(session: GameSession, probabilities: list[float]) -> None:
    session.p_goal = _mass_on(probabilities, session.cells["goals"])
    session.p_trap = _mass_on(probabilities, session.cells.get("traps", []))
    session.p_observation = _mass_on(probabilities, session.cells.get("observations", []))


def _to_dto(session: GameSession) -> GameStateDTO:
    height = int(session.level["height"])
    width = int(session.level["width"])
    probabilities = session.frozen_probabilities
    if probabilities is None:
        probabilities = _floats(session.walk.probabilities())
        _refresh_skill(session, probabilities)
    probabilities_2d = None
    if session.walk.mode == "2d":
        probabilities_2d = [
            probabilities[row * width : (row + 1) * width] for row in range(height)
        ]
    target = _target_p(session.level)
    return GameStateDTO(
        session_id=session.session_id,
        level_id=session.level["id"],
        mode=session.level.get("mode", "1d"),
        width=width,
        height=height,
        cells=CellSets(**session.cells),
        probabilities=probabilities,
        probabilities_2d=probabilities_2d,
        step=session.walk.step_count,
        step_limit=int(session.level["step_limit"]),
        status=session.status,  # type: ignore[arg-type]
        collapsed_cell=session.collapsed_cell,
        p_goal=session.p_goal,
        p_trap=session.p_trap,
        p_observation=session.p_observation,
        target_p_goal=target,
        objective_met=session.p_goal + 1e-12 >= target if target > 0 else False,
        last_op=session.last_op,
        explanation=session.explanation,
        allowed_ops=_allowed_ops(session.level),
        ops_used=session.ops_used,
        op_limit=_op_limit(session.level),
        history=list(session.walk.history),
        message=session.message,
        score=session.score,
        quantum_outcome=session.quantum_outcome,  # type: ignore[arg-type]
        beginner_assist=session.beginner_assist,  # type: ignore[arg-type]
        assist_seed=session.assist_seed,
    )


def _get(session_id: str) -> GameSession:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session.")
    return session


def start_game(level_id: str) -> GameStateDTO:
    try:
        level = load_level(level_id)
        walk = QuantumWalk.from_level(level)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown level: {level_id}") from None
    except QuantumEngineError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session_id = str(uuid4())
    session = GameSession(
        session_id=session_id,
        level=level,
        walk=walk,
        cells=linear_cells(level),
        message=level.get("copy", {}).get("short"),
        explanation="Choose a coin gate, then Quantum Walk. Probabilities come from |amplitude|².",
    )
    SESSIONS[session_id] = session
    return _to_dto(session)


def apply_move(session_id: str, action: str) -> GameStateDTO:
    session = _get(session_id)
    if session.status != "playing":
        raise HTTPException(status_code=400, detail="This run already ended. Start a new game.")

    name = action.upper() if action != "quantum_walk" else "quantum_walk"
    if name in COIN_GATES:
        allowed = _allowed_ops(session.level)
        if name not in allowed:
            raise HTTPException(status_code=400, detail=f"Gate {name} is locked on this level.")
        limit = _op_limit(session.level)
        if limit is not None and session.ops_used >= limit:
            raise HTTPException(status_code=400, detail="No coin operations remaining.")
        session.walk.apply_gate(name)
        session.ops_used += 1
        session.last_op = name
        session.explanation = EXPLANATIONS[name]
        session.message = None
        return _to_dto(session)

    if name != "quantum_walk":
        raise HTTPException(status_code=400, detail="Unknown action.")

    if session.walk.step_count >= int(session.level["step_limit"]):
        raise HTTPException(status_code=400, detail="No steps remaining.")

    session.walk.propagate()
    session.last_op = "SHIFT"
    session.explanation = EXPLANATIONS["quantum_walk"]
    session.message = None

    probs = _floats(session.walk.probabilities())
    _refresh_skill(session, probs)
    obs = session.cells.get("observations") or []
    if obs and session.p_observation >= _obs_threshold(session.level):
        return _collapse(session, seed=None, forced=True, reason="observation")
    if session.walk.step_count >= int(session.level["step_limit"]):
        return _collapse(session, seed=None, forced=True, reason="limit")
    return _to_dto(session)


def apply_measure(session_id: str, seed: int | None = None) -> GameStateDTO:
    session = _get(session_id)
    if session.status != "playing":
        raise HTTPException(status_code=400, detail="This run already ended. Start a new game.")
    if session.walk.step_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Measure is disabled until you make at least one Quantum Walk.",
        )
    return _collapse(session, seed=seed, forced=False, reason="player")


def _assist_seed(measure_seed: int) -> int:
    return int((int(measure_seed) + 9176) * 2654435761 % 2**32)


def _assist_roll(assist_seed: int) -> bool:
    rng = np.random.default_rng(assist_seed)
    return float(rng.random()) < BEGINNER_ASSIST_P


def _quantum_outcome(session: GameSession, cell: int) -> str:
    if cell in set(session.cells["goals"]):
        return "goal"
    if cell in set(session.cells.get("traps") or []):
        return "trap"
    return "other"


def _collapse(session: GameSession, seed: int | None, forced: bool, reason: str) -> GameStateDTO:
    before = _floats(session.walk.probabilities())
    _refresh_skill(session, before)
    result = session.walk.measure(seed=seed)
    session.frozen_probabilities = before
    session.collapsed_cell = result.cell
    session.last_op = "MEASURE"
    session.explanation = EXPLANATIONS["measure"]
    session.quantum_outcome = _quantum_outcome(session, result.cell)

    target = _target_p(session.level)
    target_met = target > 0 and session.p_goal + 1e-12 >= target
    quantum_won = session.quantum_outcome == "goal"

    target = _target_p(session.level)
    target_met = target > 0 and session.p_goal + 1e-12 >= target
    quantum_won = session.quantum_outcome == "goal"

    if quantum_won:
        # If the quantum measurement landed on the goal, the player WON fair and square!
        session.status = "won"
        session.beginner_assist = "success" if target_met else "off"
    elif target_met:
        # The player missed the goal, but met the required skill target.
        # Beginner assist gives a 75% second chance to win anyway.
        if seed is not None:
            a_seed = _assist_seed(seed)
        else:
            a_seed = int(np.random.default_rng().integers(0, 2**31))

        session.assist_seed = a_seed
        assist_won = _assist_roll(a_seed)

        if assist_won:
            session.beginner_assist = "success"
            session.status = "won"
        else:
            session.beginner_assist = "unlucky"
            session.status = "lost"
    else:
        # Missed goal and missed target -> lost
        session.beginner_assist = "off"
        session.assist_seed = None
        session.status = "lost"

    steps_used = session.walk.step_count
    step_limit = int(session.level["step_limit"])
    session.score = int(round(100 * session.p_goal))
    if session.status == "won":
        session.score += 10
    if target_met:
        session.score += 25
    session.score += max(0, step_limit - steps_used)

    if reason == "observation":
        prefix = "An observation tile looked. Forced measure. "
    elif reason == "limit" or forced:
        prefix = "Step limit reached. Forced measure. "
    else:
        prefix = ""

    outcome_label = {"goal": "Goal", "trap": "Trap", "other": f"Cell {result.cell}"}[
        session.quantum_outcome
    ]
    skill = (
        f" Measured cell: {outcome_label} ({result.cell})."
        f" P(goal) before collapse: {session.p_goal:.1%} (target {target:.0%})."
    )
    if target_met:
        skill += " Target reached."
        if session.beginner_assist == "success":
            skill += " Beginner Assist: Success (game-level, not a change to Born-rule P)."
        else:
            skill += " Beginner Assist: Unlucky this time (game-level roll missed)."
    else:
        skill += " Target not reached."

    if session.status == "won":
        session.message = f"{prefix}Level complete.{skill}"
        if not target_met and quantum_won:
            session.message += f" You got lucky: P(goal) was under the {target:.0%} target."
    elif session.quantum_outcome == "trap":
        session.message = f"{prefix}Collapsed on a trap.{skill}"
    else:
        session.message = f"{prefix}Collapsed off the goal.{skill}"
    return _to_dto(session)


def get_state(session_id: str) -> GameStateDTO:
    return _to_dto(_get(session_id))


def get_circuit(session_id: str) -> CircuitResponse:
    session = _get(session_id)
    history = list(session.walk.history)
    if session.walk.mode != "1d":
        return CircuitResponse(
            supported=False,
            message=(
                "Grid walk uses a 4-direction Grover coin; a full 2D Qiskit circuit is not drawn. "
                f"Operations so far: {', '.join(history) if history else '(none)'}."
            ),
            session_id=session_id,
            history=history,
        )
    view = circuit_view(
        n_sites=session.walk.grid_size,
        steps=session.walk.step_count,
        step_limit=int(session.level["step_limit"]),
        ops=history,
    )
    return CircuitResponse(
        supported=True,
        message=view.message,
        session_id=session_id,
        diagram=view.diagram,
        qasm=view.qasm,
        steps_shown=view.steps_shown,
        n_qubits=view.n_qubits,
        n_sites=view.n_sites,
        history=history,
    )
