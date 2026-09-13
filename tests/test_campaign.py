from fastapi.testclient import TestClient

from backend.game import SESSIONS
from backend.levels import list_levels, load_level
from backend.main import app
from quantum_engine.walk import QuantumWalk

client = TestClient(app)


def setup_function() -> None:
    SESSIONS.clear()


def test_five_campaign_levels_in_order() -> None:
    summaries = list_levels()
    ids = [item["id"] for item in summaries]
    assert ids == [
        "01_superposition",
        "02_interference",
        "03_measurement",
        "04_strategy",
        "05_quantum_strategy",
    ]
    assert ids[ids.index("01_superposition") + 1] == "02_interference"


def test_interference_peak_beats_the_origin_trap() -> None:
    level = load_level("02_interference")
    walk = QuantumWalk.from_level(level)
    for _ in range(int(level["step_limit"])):
        walk.step()
    probs = walk.probabilities()
    origin = 10
    goal = 16
    assert probs[goal] > probs[origin]
    assert abs(probs.sum() - 1.0) < 1e-10


def test_strategy_level_starts_and_moves() -> None:
    started = client.post("/game/start", json={"level_id": "04_strategy"})
    assert started.status_code == 200
    body = started.json()
    assert body["mode"] == "2d"
    assert body["step_limit"] == 15
    idx = 3 * 9 + 1
    assert body["probabilities"][idx] == 1.0
    grover = client.post(
        "/game/move",
        json={"session_id": body["session_id"], "action": "H"},
    )
    assert grover.status_code == 200
    moved = client.post(
        "/game/move",
        json={"session_id": body["session_id"], "action": "quantum_walk"},
    )
    assert moved.status_code == 200
    assert moved.json()["probabilities"][idx] < 1.0
