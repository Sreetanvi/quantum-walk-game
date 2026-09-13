from fastapi.testclient import TestClient
import pytest

from backend.game import SESSIONS
from backend.main import app

client = TestClient(app)


def setup_function() -> None:
    SESSIONS.clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_list_and_get_level() -> None:
    listing = client.get("/levels")
    assert listing.status_code == 200
    ids = [item["id"] for item in listing.json()]
    assert "01_superposition" in ids
    assert "02_interference" in ids
    assert "03_measurement" in ids
    assert "04_strategy" in ids
    assert "05_quantum_strategy" in ids

    detail = client.get("/levels/01_superposition")
    assert detail.status_code == 200
    body = detail.json()
    assert body["mode"] == "1d"
    assert body["width"] == 11
    assert len(body["goals"]) == 2


def test_unknown_level() -> None:
    response = client.post("/game/start", json={"level_id": "does_not_exist"})
    assert response.status_code == 404


def test_start_move_measure() -> None:
    started = client.post("/game/start", json={"level_id": "01_superposition"}).json()
    session_id = started["session_id"]
    assert started["status"] == "playing"
    assert started["step"] == 0
    assert started["probabilities"][5] == 1.0
    assert started["collapsed_cell"] is None
    assert started["target_p_goal"] == pytest.approx(0.7)

    locked = client.post("/game/move", json={"session_id": session_id, "action": "S"})
    assert locked.status_code == 400

    gated = client.post("/game/move", json={"session_id": session_id, "action": "H"})
    assert gated.status_code == 200
    assert gated.json()["probabilities"][5] == pytest.approx(1.0)
    assert gated.json()["last_op"] == "H"

    moved = client.post(
        "/game/move",
        json={"session_id": session_id, "action": "quantum_walk"},
    )
    assert moved.status_code == 200
    after = moved.json()
    assert after["step"] == 1
    assert after["probabilities"][5] == 0.0
    assert abs(after["probabilities"][4] - 0.5) < 1e-9
    assert abs(after["probabilities"][6] - 0.5) < 1e-9

    measured = client.post("/game/measure", json={"session_id": session_id, "seed": 3})
    assert measured.status_code == 200
    ended = measured.json()
    assert ended["status"] in {"won", "lost"}
    assert ended["collapsed_cell"] in {4, 6}
    assert ended["score"] is not None
    assert abs(ended["probabilities"][4] - 0.5) < 1e-9


def test_measure_at_step_zero_rejected() -> None:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    response = client.post("/game/measure", json={"session_id": session_id})
    assert response.status_code == 400
    assert "disabled" in response.json()["detail"].lower()


def test_unknown_session() -> None:
    response = client.post(
        "/game/move",
        json={"session_id": "missing", "action": "quantum_walk"},
    )
    assert response.status_code == 404


def test_move_after_end_rejected() -> None:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    client.post("/game/move", json={"session_id": session_id, "action": "H"})
    client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    client.post("/game/measure", json={"session_id": session_id, "seed": 1})
    again = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    assert again.status_code == 400


def test_step_limit_auto_measures() -> None:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    last = None
    for _ in range(6):
        last = client.post(
            "/game/move",
            json={"session_id": session_id, "action": "quantum_walk"},
        )
        assert last.status_code == 200
    body = last.json()
    assert body["step"] == 6
    assert body["status"] in {"won", "lost"}
    assert body["collapsed_cell"] is not None
    extra = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    assert extra.status_code == 400


def test_get_state_and_circuit() -> None:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    state = client.get("/game/state", params={"session_id": session_id})
    assert state.status_code == 200
    assert state.json()["level_id"] == "01_superposition"

    circuit = client.get("/game/circuit", params={"session_id": session_id})
    assert circuit.status_code == 200
    body = circuit.json()
    assert body["supported"] is True
    assert body["n_qubits"] == 5
    assert body["steps_shown"] == 0
    client.post("/game/move", json={"session_id": session_id, "action": "H"})
    client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    after = client.get("/game/circuit", params={"session_id": session_id}).json()
    assert after["steps_shown"] == 1
    assert "H" in after["diagram"] or "h" in after["diagram"].lower()


def test_2d_level_start_move_and_circuit_unsupported() -> None:
    started = client.post("/game/start", json={"level_id": "03_measurement"})
    assert started.status_code == 200
    body = started.json()
    assert body["mode"] == "2d"
    assert body["height"] == 7
    assert body["width"] == 7
    assert body["probabilities_2d"] is not None
    assert len(body["probabilities_2d"]) == 7
    start_idx = 1 * 7 + 1
    assert body["probabilities"][start_idx] == pytest.approx(1.0)
    assert body["cells"]["walls"]

    session_id = body["session_id"]
    moved = client.post(
        "/game/move",
        json={"session_id": session_id, "action": "quantum_walk"},
    )
    assert moved.status_code == 200
    after = moved.json()
    assert after["step"] == 1
    assert after["probabilities"][start_idx] < 1.0
    assert abs(sum(after["probabilities"]) - 1.0) < 1e-8

    circuit = client.get("/game/circuit", params={"session_id": session_id}).json()
    assert circuit["supported"] is False


def test_observation_forces_measure_on_pawn_walk() -> None:
    session_id = client.post("/game/start", json={"level_id": "02_interference"}).json()[
        "session_id"
    ]
    walked = client.post(
        "/game/move",
        json={"session_id": session_id, "action": "quantum_walk"},
    )
    body = walked.json()
    assert body["status"] in {"won", "lost"}
    assert body["collapsed_cell"] == 11
    assert body["p_observation"] == pytest.approx(1.0)


def test_observation_does_not_trigger_below_threshold() -> None:
    """H then walk: P(camera) = 0.5, threshold 0.51 — still playing."""
    session_id = client.post("/game/start", json={"level_id": "02_interference"}).json()[
        "session_id"
    ]
    assert client.post("/game/move", json={"session_id": session_id, "action": "H"}).status_code == 200
    walked = client.post(
        "/game/move",
        json={"session_id": session_id, "action": "quantum_walk"},
    )
    body = walked.json()
    assert body["status"] == "playing"
    assert body["p_observation"] == pytest.approx(0.5)
    extra = client.post(
        "/game/move",
        json={"session_id": session_id, "action": "quantum_walk"},
    )
    assert extra.status_code == 200
    assert extra.json()["status"] == "playing"


def test_observation_triggers_when_p_is_above_threshold_not_only_one() -> None:
    """Three textbook H+walk steps put ~0.625 on the camera (not 1.0) and must force measure."""
    session_id = client.post("/game/start", json={"level_id": "02_interference"}).json()[
        "session_id"
    ]
    last = None
    for _ in range(3):
        assert client.post("/game/move", json={"session_id": session_id, "action": "H"}).status_code == 200
        last = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
        assert last.status_code == 200
        if last.json()["status"] != "playing":
            break
    body = last.json()
    assert body["status"] in {"won", "lost"}
    assert body["collapsed_cell"] is not None
    assert body["p_observation"] >= 0.51
    assert body["p_observation"] < 1.0 - 1e-9


def test_high_p_goal_does_not_auto_measure() -> None:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    for _ in range(5):
        walked = client.post(
            "/game/move",
            json={"session_id": session_id, "action": "quantum_walk"},
        )
        assert walked.status_code == 200
    body = walked.json()
    assert body["status"] == "playing"
    assert body["p_goal"] == pytest.approx(1.0)
    extra = client.post("/game/move", json={"session_id": session_id, "action": "H"})
    assert extra.status_code == 200
    assert extra.json()["status"] == "playing"


def test_move_rejected_after_camera_collapse() -> None:
    session_id = client.post("/game/start", json={"level_id": "02_interference"}).json()[
        "session_id"
    ]
    client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    again = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    assert again.status_code == 400


def test_level_five_h_then_ride_meets_target() -> None:
    session_id = client.post("/game/start", json={"level_id": "05_quantum_strategy"}).json()[
        "session_id"
    ]
    assert (
        client.post("/game/move", json={"session_id": session_id, "action": "H"}).status_code
        == 200
    )
    last = None
    for _ in range(5):
        last = client.post(
            "/game/move",
            json={"session_id": session_id, "action": "quantum_walk"},
        )
        assert last.status_code == 200
        if last.json()["status"] != "playing":
            break
    body = last.json()
    assert body["p_goal"] == pytest.approx(0.5, abs=1e-9)
    assert body["objective_met"] is True
    if body["status"] == "playing":
        ended = client.post("/game/measure", json={"session_id": session_id, "seed": 0}).json()
        assert ended["status"] in {"won", "lost"}
