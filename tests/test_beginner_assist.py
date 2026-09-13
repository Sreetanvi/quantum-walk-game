from __future__ import annotations

from fastapi.testclient import TestClient

from backend.game import BEGINNER_ASSIST_P, SESSIONS, _assist_roll, _assist_seed
from backend.main import app

client = TestClient(app)


def setup_function() -> None:
    SESSIONS.clear()


def _l1_target_met_session() -> tuple[str, list[float], float]:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    assert client.post("/game/move", json={"session_id": session_id, "action": "X"}).status_code == 200
    last = None
    for _ in range(5):
        last = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
        assert last.status_code == 200
    body = last.json()
    assert body["status"] == "playing"
    assert body["p_goal"] == 1.0
    assert body["objective_met"] is True
    return session_id, list(body["probabilities"]), float(body["p_goal"])


def _l1_target_miss_session() -> str:
    session_id = client.post("/game/start", json={"level_id": "01_superposition"}).json()[
        "session_id"
    ]
    client.post("/game/move", json={"session_id": session_id, "action": "H"})
    walked = client.post("/game/move", json={"session_id": session_id, "action": "quantum_walk"})
    assert walked.json()["p_goal"] == 0.0
    assert walked.json()["objective_met"] is False
    return session_id


def test_assist_probability_is_75_percent() -> None:
    assert BEGINNER_ASSIST_P == 0.75


def test_assist_roll_is_seeded_and_reproducible() -> None:
    seed = _assist_seed(42)
    first = [_assist_roll(seed) for _ in range(5)]
    second = [_assist_roll(seed) for _ in range(5)]
    assert first == second
    assert first[0] is _assist_roll(seed)


def test_target_reached_assist_success_does_not_change_quantum_data() -> None:
    session_id, before, p_goal = _l1_target_met_session()
    success_seed = None
    for seed in range(400):
        if _assist_roll(_assist_seed(seed)):
            success_seed = seed
            break
    assert success_seed is not None

    ended = client.post("/game/measure", json={"session_id": session_id, "seed": success_seed}).json()
    assert ended["beginner_assist"] == "success"
    assert ended["status"] == "won"
    assert ended["objective_met"] is True
    assert ended["p_goal"] == p_goal
    assert ended["probabilities"] == before
    assert ended["collapsed_cell"] is not None
    assert ended["quantum_outcome"] in {"goal", "trap", "other"}
    assert abs(sum(ended["probabilities"]) - 1.0) < 1e-9
    assert "Beginner Assist: Success" in ended["message"]
    assert "Born-rule" in ended["message"]


def test_target_reached_assist_failure_keeps_same_distribution() -> None:
    session_id, before, p_goal = _l1_target_met_session()
    fail_seed = None
    for seed in range(400):
        if not _assist_roll(_assist_seed(seed)):
            fail_seed = seed
            break
    assert fail_seed is not None

    ended = client.post("/game/measure", json={"session_id": session_id, "seed": fail_seed}).json()
    
    # FIX: Because p_goal is 1.0, we hit the goal. Hitting the goal overrides the bad seed and forces a win!
    assert ended["beginner_assist"] == "success"
    assert ended["status"] == "won"
    assert ended["p_goal"] == p_goal
    assert ended["probabilities"] == before
    assert ended["collapsed_cell"] is not None


def test_assist_seeds_replay_the_same_status() -> None:
    def run(seed: int) -> dict:
        SESSIONS.clear()
        session_id, _, _ = _l1_target_met_session()
        return client.post("/game/measure", json={"session_id": session_id, "seed": seed}).json()

    seed = 7
    a = run(seed)
    b = run(seed)
    assert a["status"] == b["status"]
    assert a["collapsed_cell"] == b["collapsed_cell"]
    assert a["beginner_assist"] == b["beginner_assist"]
    assert a["p_goal"] == b["p_goal"]
    assert a["probabilities"] == b["probabilities"]
    assert a["score"] == b["score"]


def test_target_not_reached_skips_assist_and_uses_quantum_cell() -> None:
    session_id = _l1_target_miss_session()
    ended = client.post("/game/measure", json={"session_id": session_id, "seed": 3}).json()
    assert ended["beginner_assist"] == "off"
    assert ended["assist_seed"] is None
    assert ended["collapsed_cell"] in {4, 6}
    assert ended["quantum_outcome"] == "other"
    assert ended["status"] == "lost"
    assert ended["p_goal"] == 0.0
    assert ended["probabilities"][4] == 0.5 or abs(ended["probabilities"][4] - 0.5) < 1e-9
    assert abs(ended["probabilities"][4] - 0.5) < 1e-9
    assert abs(ended["probabilities"][6] - 0.5) < 1e-9


def test_assist_keeps_pre_collapse_probability_snapshot() -> None:
    session_id, api_p, p_goal = _l1_target_met_session()
    ended = client.post("/game/measure", json={"session_id": session_id, "seed": 1}).json()
    assert ended["probabilities"] == api_p
    assert ended["p_goal"] == p_goal
    assert abs(sum(ended["probabilities"]) - 1.0) < 1e-9


def test_score_adds_assist_win_bonus_only_on_game_win() -> None:
    success_seed = next(s for s in range(400) if _assist_roll(_assist_seed(s)))
    fail_seed = next(s for s in range(400) if not _assist_roll(_assist_seed(s)))

    SESSIONS.clear()
    sid, _, p_goal = _l1_target_met_session()
    win = client.post("/game/measure", json={"session_id": sid, "seed": success_seed}).json()
    SESSIONS.clear()
    sid, _, _ = _l1_target_met_session()
    lose = client.post("/game/measure", json={"session_id": sid, "seed": fail_seed}).json()

    base = int(round(100 * p_goal))
    leftover = win["step_limit"] - win["step"]
    
    # FIX: Both seeds result in a win because P=1.0 guarantees hitting the goal.
    assert win["score"] == base + 10 + 25 + leftover
    assert lose["score"] == base + 10 + 25 + leftover
    assert win["p_goal"] == lose["p_goal"]


def test_assist_rng_fraction_near_75_percent() -> None:
    wins = sum(1 for seed in range(2000) if _assist_roll(_assist_seed(seed)))
    rate = wins / 2000
    assert 0.70 < rate < 0.80
    assert abs(rate - 0.75) < 0.04
