from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from quantum_engine.errors import QuantumEngineError

LEVELS_DIR = Path(__file__).resolve().parent.parent / "levels"


def _index(x: int, y: int, width: int) -> int:
    return y * width + x


def _as_points(raw: Any) -> list[dict[str, int]]:
    if not raw:
        return []
    points: list[dict[str, int]] = []
    for item in raw:
        if isinstance(item, dict):
            points.append({"x": int(item["x"]), "y": int(item.get("y", 0))})
        else:
            points.append({"x": int(item), "y": 0})
    return points


def validate_level(level: dict[str, Any]) -> None:
    width = int(level["width"])
    height = int(level["height"])
    mode = level.get("mode", "1d")
    start = level.get("start") or {}
    sx, sy = int(start.get("x", 0)), int(start.get("y", 0))
    if not (0 <= sx < width and 0 <= sy < height):
        raise QuantumEngineError("Start is off the board.")
    walls = {(p["x"], p["y"]) for p in _as_points(level.get("walls"))}
    if (sx, sy) in walls:
        raise QuantumEngineError("Start cannot be a wall.")
    if mode == "1d":
        if width < 2 or height != 1:
            raise QuantumEngineError("1D levels need width >= 2 and height 1.")
    elif mode == "2d":
        if width < 2 or height < 2:
            raise QuantumEngineError("2D levels need width and height of at least 2.")
    else:
        raise QuantumEngineError("mode must be '1d' or '2d'.")
    for group in ("walls", "traps", "goals", "observations", "phase_gates"):
        for pt in _as_points(level.get(group)):
            if not (0 <= pt["x"] < width and 0 <= pt["y"] < height):
                raise QuantumEngineError(f"{group} contain a cell off the board.")
    blocked = {(p["x"], p["y"]) for p in _as_points(level.get("walls"))}
    for pt in (
        _as_points(level.get("goals"))
        + _as_points(level.get("traps"))
        + _as_points(level.get("observations"))
        + _as_points(level.get("phase_gates"))
    ):
        if (pt["x"], pt["y"]) in blocked:
            raise QuantumEngineError("Special tiles cannot sit on walls.")
    if not _as_points(level.get("goals")):
        raise QuantumEngineError("Level needs at least one goal.")


def linear_cells(level: dict[str, Any]) -> dict[str, list[int]]:
    width = int(level["width"])
    return {
        "walls": [_index(p["x"], p["y"], width) for p in _as_points(level.get("walls"))],
        "traps": [_index(p["x"], p["y"], width) for p in _as_points(level.get("traps"))],
        "goals": [_index(p["x"], p["y"], width) for p in _as_points(level.get("goals"))],
        "observations": [_index(p["x"], p["y"], width) for p in _as_points(level.get("observations"))],
        "phase_gates": [_index(p["x"], p["y"], width) for p in _as_points(level.get("phase_gates"))],
    }


def load_level(level_id: str) -> dict[str, Any]:
    path = LEVELS_DIR / f"{level_id}.json"
    if not path.is_file():
        raise FileNotFoundError(level_id)
    with path.open(encoding="utf-8") as handle:
        level = json.load(handle)
    validate_level(level)
    return level


def list_levels() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    if not LEVELS_DIR.is_dir():
        return summaries
    for path in sorted(LEVELS_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
        try:
            validate_level(data)
        except QuantumEngineError:
            continue
        summaries.append(
            {
                "id": data["id"],
                "title": data["title"],
                "order": int(data.get("order", 0)),
            }
        )
    summaries.sort(key=lambda item: item["order"])
    return summaries
