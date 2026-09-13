from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend import game as game_mod
from backend.levels import load_level, list_levels
from backend.models import (
    CircuitResponse,
    GameStateDTO,
    HealthResponse,
    LevelSummary,
    MeasureRequest,
    MoveRequest,
    StartRequest,
)

app = FastAPI(title="Quantum Walk Game API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)


@app.get("/levels", response_model=list[LevelSummary])
def levels() -> list[LevelSummary]:
    return [LevelSummary(**item) for item in list_levels()]


@app.get("/levels/{level_id}")
def level_detail(level_id: str) -> dict:
    try:
        return load_level(level_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown level: {level_id}") from None


@app.post("/game/start", response_model=GameStateDTO)
def game_start(body: StartRequest) -> GameStateDTO:
    return game_mod.start_game(body.level_id)


@app.post("/game/move", response_model=GameStateDTO)
def game_move(body: MoveRequest) -> GameStateDTO:
    return game_mod.apply_move(body.session_id, body.action)


@app.post("/game/measure", response_model=GameStateDTO)
def game_measure(body: MeasureRequest) -> GameStateDTO:
    return game_mod.apply_measure(body.session_id, seed=body.seed)


@app.get("/game/state", response_model=GameStateDTO)
def game_state(session_id: str = Query(...)) -> GameStateDTO:
    return game_mod.get_state(session_id)


@app.get("/game/circuit", response_model=CircuitResponse)
def game_circuit(session_id: str = Query(...)) -> CircuitResponse:
    return game_mod.get_circuit(session_id)
