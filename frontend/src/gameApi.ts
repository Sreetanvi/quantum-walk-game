import type { CircuitView, GameState, LevelDetail, LevelSummary } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
    });
  } catch {
    throw new Error("Cannot reach the game API. Start it with: uvicorn backend.main:app --reload --port 8000");
  }

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function listLevels(): Promise<LevelSummary[]> {
  return request("/levels");
}

export function fetchLevel(levelId: string): Promise<LevelDetail> {
  return request(`/levels/${encodeURIComponent(levelId)}`);
}

export function startGame(levelId = "01_superposition"): Promise<GameState> {
  return request("/game/start", {
    method: "POST",
    body: JSON.stringify({ level_id: levelId }),
  });
}

export function applyAction(sessionId: string, action: string): Promise<GameState> {
  return request("/game/move", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, action }),
  });
}

export function quantumWalk(sessionId: string): Promise<GameState> {
  return applyAction(sessionId, "quantum_walk");
}

export function measure(sessionId: string): Promise<GameState> {
  return request("/game/measure", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export function fetchCircuit(sessionId: string): Promise<CircuitView> {
  return request(`/game/circuit?session_id=${encodeURIComponent(sessionId)}`);
}
