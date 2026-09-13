import { useCallback, useEffect, useState } from "react";
import { Board1D } from "./Board1D";
import { Board2D } from "./Board2D";
import { CircuitSidebar } from "./CircuitSidebar";
import { EducationPanel } from "./EducationPanel";
import { HowItWorks } from "./HowItWorks";
import { applyAction, fetchCircuit, fetchLevel, listLevels, measure, quantumWalk, startGame } from "./gameApi";
import {
  RESULT_OVERLAY_DELAY_MS,
  ResultOverlay,
  firstLevelId,
  levelLabel,
  nextLevelId,
} from "./ResultOverlay";
import type { CircuitView, CoinGate, GameState, LevelDetail, LevelSummary } from "./types";

type Screen = "landing" | "play" | "how";

const GATE_HELP: Record<CoinGate, string> = {
  H: "Mix / superposition",
  X: "Flip heading",
  Z: "Flip phase",
  S: "Quarter-turn phase",
};

function titleFor(levels: LevelSummary[], levelId: string): string {
  return levelLabel(levels, levelId);
}

export default function App() {
  const [screen, setScreen] = useState<Screen>("landing");
  const [levels, setLevels] = useState<LevelSummary[]>([]);
  const [state, setState] = useState<GameState | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [levelEnter, setLevelEnter] = useState(0);

  const loadLevels = useCallback(async () => {
    try {
      setLevels(await listLevels());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to list levels");
    }
  }, []);

  useEffect(() => {
    void loadLevels();
  }, [loadLevels]);

  async function run<T>(work: () => Promise<T>): Promise<T | undefined> {
    setBusy(true);
    setError(null);
    try {
      return await work();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      return undefined;
    } finally {
      setBusy(false);
    }
  }

  async function onPlay(levelId?: string) {
    const id = levelId ?? firstLevelId(levels) ?? "01_superposition";
    const next = await run(() => startGame(id));
    if (next) {
      setState(next);
      setScreen("play");
      setLevelEnter((n) => n + 1);
    }
  }

  async function onGate(gate: CoinGate) {
    if (!state || state.status !== "playing") return;
    const next = await run(() => applyAction(state.session_id, gate));
    if (next) setState(next);
  }

  async function onWalk() {
    if (!state || state.status !== "playing") return;
    const next = await run(() => quantumWalk(state.session_id));
    if (next) setState(next);
  }

  async function onMeasure() {
    if (!state || state.status !== "playing") return;
    const next = await run(() => measure(state.session_id));
    if (next) setState(next);
  }

  async function onRestart() {
    if (!state) {
      await onPlay();
      return;
    }
    await onPlay(state.level_id);
  }

  async function onNextLevel() {
    if (!state) return;
    const nxt = nextLevelId(levels, state.level_id);
    if (!nxt) return;
    await onPlay(nxt);
  }

  return (
    <div className="min-h-screen bg-ink text-slate-100">
      <header className="flex items-center justify-between border-b border-line px-6 py-4">
        <button type="button" className="text-left" onClick={() => setScreen("landing")}>
          <p className="font-mono text-xs tracking-[0.2em] text-cyan">QUANTUM WALK</p>
          <h1 className="text-lg font-medium">You are a wave until something looks.</h1>
        </button>
        <nav className="flex gap-3 text-sm">
          <button type="button" className="hover:text-cyan" onClick={() => setScreen("how")}>
            How it works
          </button>
          <button
            type="button"
            className="rounded-md bg-cyan px-3 py-1.5 font-medium text-ink hover:opacity-90"
            onClick={() => void onPlay()}
            disabled={busy}
          >
            Play
          </button>
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {error ? (
          <p className="mb-4 rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}

        {screen === "landing" ? (
          <Landing levels={levels} onPlay={(id) => void onPlay(id)} busy={busy} />
        ) : null}
        {screen === "how" ? <HowItWorks /> : null}
        {screen === "play" && state ? (
          <div key={levelEnter} className="level-enter">
            <Play
              state={state}
              levels={levels}
              busy={busy}
              onGate={(g) => void onGate(g)}
              onWalk={() => void onWalk()}
              onMeasure={() => void onMeasure()}
              onRestart={() => void onRestart()}
              onNextLevel={() => void onNextLevel()}
              onPlayAgain={() => void onPlay(firstLevelId(levels) ?? undefined)}
              onBackToLevels={() => {
                setScreen("landing");
                setState(null);
              }}
            />
          </div>
        ) : null}
      </main>
    </div>
  );
}

function Landing({
  levels,
  onPlay,
  busy,
}: {
  levels: LevelSummary[];
  onPlay: (id: string) => void;
  busy: boolean;
}) {
  return (
    <section className="space-y-8">
      <p className="max-w-2xl text-lg text-slate-300">
        You pick the coin. Then the wave walks. Interference is complex addition. You only
        become one tile when you measure.
      </p>
      <div>
        <h2 className="mb-3 font-mono text-xs tracking-widest text-slate-400">LEVELS</h2>
        <ul className="space-y-2">
          {levels.map((level) => (
            <li key={level.id}>
              <button
                type="button"
                disabled={busy}
                onClick={() => onPlay(level.id)}
                className="w-full max-w-md rounded-lg border border-line bg-panel px-4 py-3 text-left hover:border-cyan"
              >
                <span className="font-mono text-xs text-cyan">{String(level.order).padStart(2, "0")}</span>
                <span className="ml-3">{level.title}</span>
              </button>
            </li>
          ))}
        </ul>
        {levels.length === 0 ? (
          <p className="text-sm text-slate-400">No levels loaded. Is the API running on port 8000?</p>
        ) : null}
      </div>
    </section>
  );
}

function Play({
  state,
  levels,
  busy,
  onGate,
  onWalk,
  onMeasure,
  onRestart,
  onNextLevel,
  onPlayAgain,
  onBackToLevels,
}: {
  state: GameState;
  levels: LevelSummary[];
  busy: boolean;
  onGate: (gate: CoinGate) => void;
  onWalk: () => void;
  onMeasure: () => void;
  onRestart: () => void;
  onNextLevel: () => void;
  onPlayAgain: () => void;
  onBackToLevels: () => void;
}) {
  const playing = state.status === "playing";
  const canMeasure = playing && state.step > 0;
  const [circuit, setCircuit] = useState<CircuitView | null>(null);
  const [level, setLevel] = useState<LevelDetail | null>(null);
  const [showResultOverlay, setShowResultOverlay] = useState(false);
  const gates = (state.allowed_ops ?? []) as CoinGate[];

  useEffect(() => {
    if (playing) {
      setShowResultOverlay(false);
      return;
    }
    setShowResultOverlay(false);
    let timer = 0;
    let raf2 = 0;
    const raf1 = window.requestAnimationFrame(() => {
      raf2 = window.requestAnimationFrame(() => {
        timer = window.setTimeout(() => {
          setShowResultOverlay(true);
        }, RESULT_OVERLAY_DELAY_MS);
      });
    });
    return () => {
      window.cancelAnimationFrame(raf1);
      window.cancelAnimationFrame(raf2);
      window.clearTimeout(timer);
    };
  }, [playing, state.session_id, state.status, state.collapsed_cell]);

  useEffect(() => {
    let cancelled = false;
    void fetchLevel(state.level_id).then((detail) => {
      if (!cancelled) setLevel(detail);
    });
    return () => {
      cancelled = true;
    };
  }, [state.level_id]);

  useEffect(() => {
    let cancelled = false;
    void fetchCircuit(state.session_id)
      .then((view) => {
        if (!cancelled) setCircuit(view);
      })
      .catch(() => {
        if (!cancelled) {
          setCircuit({
            supported: false,
            message: "Could not load the Qiskit circuit.",
            session_id: state.session_id,
            diagram: null,
            qasm: null,
            steps_shown: null,
            n_qubits: null,
            n_sites: null,
            history: state.history,
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [state.session_id, state.step, state.last_op, state.history]);

  const target = state.target_p_goal ?? 0;
  const met = target > 0 && state.p_goal >= target - 1e-12;

  return (
    <section className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="font-mono text-xs text-cyan">{state.level_id}</p>
          <h2 className="text-2xl">{titleFor(levels, state.level_id)}</h2>
        </div>
        <dl className="flex flex-wrap gap-5 font-mono text-sm">
          <div>
            <dt className="text-slate-400">Walks</dt>
            <dd>
              {state.step}/{state.step_limit}
            </dd>
          </div>
          {state.op_limit != null ? (
            <div>
              <dt className="text-slate-400">Gates</dt>
              <dd>
                {state.ops_used}/{state.op_limit}
              </dd>
            </div>
          ) : null}
          <div>
            <dt className="text-slate-400">Current gate</dt>
            <dd className="text-cyan">{state.last_op ?? "—"}</dd>
          </div>
          {target > 0 ? (
            <div>
              <dt className="text-slate-400">Goal</dt>
              <dd className={met ? "text-gold" : ""}>
                ≥ {(target * 100).toFixed(0)}%
              </dd>
            </div>
          ) : null}
          <div>
            <dt className="text-slate-400">Current</dt>
            <dd className={met ? "text-gold" : "text-cyan"}>{(state.p_goal * 100).toFixed(1)}%</dd>
          </div>
          <div>
            <dt className="text-slate-400">P(trap)</dt>
            <dd>{(state.p_trap * 100).toFixed(1)}%</dd>
          </div>
          {state.score !== null ? (
            <div>
              <dt className="text-slate-400">Score</dt>
              <dd>{state.score}</dd>
            </div>
          ) : null}
        </dl>
      </div>

      <div className="grid items-start gap-6 lg:grid-cols-[1fr_20rem]">
        <div className="space-y-4">
          <div className={state.status === "playing" ? "" : "collapse-flash"}>
            {state.height > 1 ? <Board2D state={state} /> : <Board1D state={state} />}
            <p className="mt-2 font-mono text-[11px] text-slate-500">
              Gold dashed = goal · red hatch = trap · violet dotted = camera · cyan ring = phase ·
              bright outline = peak P
              {state.height > 1 ? " · hover a cell for exact P" : ""}
            </p>
          </div>

          <div className="space-y-3">
            <p className="font-mono text-xs tracking-widest text-slate-400">QUANTUM CONTROLS</p>
            <div className="flex flex-wrap gap-2">
              {(["H", "X", "Z", "S"] as CoinGate[]).map((gate) => {
                const allowed = gates.includes(gate);
                const active = state.last_op === gate;
                return (
                  <button
                    key={gate}
                    type="button"
                    title={GATE_HELP[gate]}
                    disabled={busy || !playing || !allowed || showResultOverlay}
                    onClick={() => onGate(gate)}
                    className={`min-w-[3rem] rounded-md border px-3 py-2 font-mono text-sm disabled:opacity-30 ${
                      active ? "border-cyan bg-cyan/15 text-cyan" : "border-line hover:border-cyan"
                    }`}
                  >
                    {gate}
                    {state.mode === "2d" && gate === "H" ? " / G" : ""}
                  </button>
                );
              })}
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                disabled={busy || !playing || showResultOverlay}
                onClick={onWalk}
                className="rounded-md bg-cyan px-4 py-2 font-medium text-ink disabled:opacity-40"
              >
                Quantum Walk →
              </button>
              <button
                type="button"
                disabled={busy || !canMeasure || showResultOverlay}
                onClick={onMeasure}
                className="rounded-md border border-gold px-4 py-2 font-medium text-gold disabled:opacity-40"
              >
                Measure (collapse)
              </button>
              <button
                type="button"
                disabled={busy || !playing || showResultOverlay}
                onClick={onRestart}
                className="rounded-md border border-line px-4 py-2 hover:border-slate-400"
              >
                Restart
              </button>
            </div>
          </div>

          <p className="text-sm text-slate-300">{state.message ?? "Choose a gate, walk the wave, then look."}</p>
          {state.status !== "playing" ? (
            <p className="font-medium" data-testid="result" data-overlay-visible={showResultOverlay ? "true" : "false"}>
              {state.status === "won" ? "Game: win." : "Game: loss."}
              {state.collapsed_cell !== null
                ? ` Measured cell ${state.collapsed_cell} (${state.quantum_outcome ?? "sample"}).`
                : ""}
              {` P(goal) ${ (state.p_goal * 100).toFixed(1)}% before collapse.`}
              {state.beginner_assist === "success" ? " Beginner Assist: Success." : ""}
              {state.beginner_assist === "unlucky" ? " Beginner Assist: Unlucky this time." : ""}
            </p>
          ) : null}
        </div>
        <div className="space-y-4">
          <EducationPanel level={level} state={state} />
          <CircuitSidebar circuit={circuit} />
        </div>
      </div>

      <ResultOverlay
        state={state}
        levels={levels}
        busy={busy}
        visible={showResultOverlay}
        onNext={onNextLevel}
        onReplay={onRestart}
        onPlayAgain={onPlayAgain}
        onBackToLevels={onBackToLevels}
      />
    </section>
  );
}
