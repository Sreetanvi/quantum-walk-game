import type { GameState, LevelSummary } from "./types";

export const RESULT_OVERLAY_DELAY_MS = 1500;

export function sortedLevels(levels: LevelSummary[]): LevelSummary[] {
  return [...levels].sort((a, b) => a.order - b.order);
}

export function nextLevelId(levels: LevelSummary[], currentId: string): string | null {
  const ordered = sortedLevels(levels);
  const index = ordered.findIndex((item) => item.id === currentId);
  if (index < 0 || index >= ordered.length - 1) return null;
  return ordered[index + 1].id;
}

export function firstLevelId(levels: LevelSummary[]): string | null {
  return sortedLevels(levels)[0]?.id ?? null;
}

export function levelLabel(levels: LevelSummary[], id: string): string {
  const found = levels.find((item) => item.id === id);
  if (!found) return id;
  return `Level ${found.order}: ${found.title}`;
}

function measuredCellLabel(state: GameState): string {
  const cell = state.collapsed_cell;
  if (cell === null) return "—";
  if (state.quantum_outcome === "goal" || state.cells.goals.includes(cell)) return "Goal";
  if (state.quantum_outcome === "trap" || state.cells.traps.includes(cell)) return "Trap";
  if (state.cells.observations?.includes(cell)) return "Camera";
  return `Cell ${cell}`;
}

// Added forceUnlucky to override any weird backend assist messages
function ResultFacts({ state, forceUnlucky }: { state: GameState; forceUnlucky?: boolean }) {
  const pGoal = `${(state.p_goal * 100).toFixed(1)}%`;
  const target = `${((state.target_p_goal ?? 0) * 100).toFixed(0)}%`;
  const assist = forceUnlucky ? "unlucky" : (state.beginner_assist ?? "off");
  
  return (
    <dl className="mt-4 space-y-1 font-mono text-sm">
      <div className="flex justify-between gap-4">
        <dt className="text-slate-400">Measured cell</dt>
        <dd>
          {measuredCellLabel(state)}
          {state.collapsed_cell !== null ? ` (${state.collapsed_cell})` : ""}
        </dd>
      </div>
      <div className="flex justify-between gap-4">
        <dt className="text-slate-400">P(goal) before collapse</dt>
        <dd className="text-gold">{pGoal}</dd>
      </div>
      <div className="flex justify-between gap-4">
        <dt className="text-slate-400">Target</dt>
        <dd>{target}</dd>
      </div>
      <div className="flex justify-between gap-4">
        <dt className="text-slate-400">Target reached</dt>
        <dd>{state.objective_met ? "yes" : "no"}</dd>
      </div>
      {assist === "success" ? (
        <div className="flex justify-between gap-4 text-cyan">
          <dt>Beginner Assist</dt>
          <dd>Success</dd>
        </div>
      ) : null}
      {assist === "unlucky" ? (
        <div className="flex justify-between gap-4 text-gold">
          <dt>Beginner Assist</dt>
          <dd>Unlucky this time</dd>
        </div>
      ) : null}
    </dl>
  );
}

type Props = {
  state: GameState;
  levels: LevelSummary[];
  busy: boolean;
  visible: boolean;
  onNext: () => void;
  onReplay: () => void;
  onPlayAgain: () => void;
  onBackToLevels: () => void;
};

export function ResultOverlay({
  state,
  levels,
  busy,
  visible,
  onNext,
  onReplay,
  onPlayAgain,
  onBackToLevels,
}: Props) {
  if (state.status === "playing" || !visible) return null;

  // We completely ignore state.status here and calculate the truth ourselves
  const hitGoal = state.quantum_outcome === "goal";
  const nextId = nextLevelId(levels, state.level_id);
  const campaignDone = hitGoal && nextId === null;
  const pGoal = `${(state.p_goal * 100).toFixed(1)}%`;

  // --- 1. Campaign Complete ---
  if (campaignDone) {
    return (
      <div className="result-overlay" role="dialog" aria-labelledby="campaign-title" data-testid="campaign-complete">
        <div className="result-card border-cyan/50">
          <h2 id="campaign-title" className="text-3xl font-medium text-cyan">
            CAMPAIGN COMPLETE!
          </h2>
          <p className="mt-3 text-slate-200">You mastered the Quantum Walk.</p>
          <p className="mt-3 font-mono text-sm text-gold">P(goal): {pGoal}</p>
          <ResultFacts state={state} />
          <div className="mt-6 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={busy}
              onClick={onPlayAgain}
              className="rounded-md bg-cyan px-4 py-2 font-medium text-ink disabled:opacity-40"
            >
              Play Again
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={onBackToLevels}
              className="rounded-md border border-line px-4 py-2 hover:border-slate-400"
            >
              Back to Levels
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- 2. Win (Hit the Goal) ---
  if (hitGoal) {
    return (
      <div className="result-overlay" role="dialog" aria-labelledby="win-title" data-testid="win-modal">
        <div className="result-card win-glow border-cyan/60">
          <h2 id="win-title" className="text-4xl font-medium text-cyan">
            YOU WIN!
          </h2>
          <p className="mt-3 text-slate-200">
            You reached the goal!
          </p>
          <ResultFacts state={state} />
          {!state.objective_met ? (
            <p className="mt-4 text-sm text-slate-300">
              You got lucky: P(goal) was under the target. This shot still landed on a goal.
            </p>
          ) : null}
          <div className="mt-6">
            <button
              type="button"
              disabled={busy}
              onClick={onNext}
              className="rounded-md bg-cyan px-4 py-2 font-medium text-ink disabled:opacity-40"
            >
              Next Level →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- 3. Mercy Pass (Missed Goal, Met Target) ---
  if (!hitGoal && state.objective_met) {
    return (
      <div className="result-overlay" role="dialog" aria-labelledby="mercy-title" data-testid="mercy-modal">
        <div className="result-card border-gold/50">
          <h2 id="mercy-title" className="text-3xl font-medium text-gold">
            UNLUCKY THIS TIME
          </h2>
          <p className="mt-3 text-slate-200">
            You met the target probability, but the quantum wave collapsed off the goal. We'll give you a pass!
          </p>
          {/* forceUnlucky ensures it never says "Assist Success" here */}
          <ResultFacts state={state} forceUnlucky={true} />
          <div className="mt-6">
            <button
              type="button"
              disabled={busy}
              onClick={onNext}
              className="rounded-md bg-cyan px-4 py-2 font-medium text-ink disabled:opacity-40"
            >
              Next Level →
            </button>
          </div>
        </div>
      </div>
    );
  }

  // --- 4. True Loss (Missed Goal, Missed Target) ---
  return (
    <div className="result-overlay" role="dialog" aria-labelledby="loss-title" data-testid="loss-modal">
      <div className="result-card border-danger/50">
        <h2 id="loss-title" className="text-3xl font-medium text-danger">
          YOU LOSE
        </h2>
        <p className="mt-3 text-slate-200">
          You missed the target and the wave collapsed somewhere else.
        </p>
        <ResultFacts state={state} forceUnlucky={true} />
        <div className="mt-6">
          <button
            type="button"
            disabled={busy}
            onClick={onReplay}
            className="rounded-md border border-gold px-4 py-2 font-medium text-gold disabled:opacity-40"
          >
            Try Again
          </button>
        </div>
      </div>
    </div>
  );
}