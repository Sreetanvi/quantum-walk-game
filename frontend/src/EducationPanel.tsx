import type { GameState, LevelDetail } from "./types";

type Lesson = {
  title: string;
  goal: string;
  points: string[];
};

const LESSONS: Record<string, Lesson> = {
  "01_superposition": {
    title: "Superposition",
    goal: "Learn how H creates a superposition, then walk, then look.",
    points: [
      "H mixes the coin (left/right). It does not move the wave yet.",
      "Quantum Walk is what actually shifts probability to neighboring cells.",
      "X flips heading so a packet can march toward an end.",
      "Both ends are goals. Watch P(goal) in the HUD.",
      "Target ≥ 70%: stack enough probability on a goal before Measure.",
      "Measure is off until you have walked at least once.",
    ],
  },
  "02_interference": {
    title: "Interference",
    goal: "Sneak past the camera and grow P(goal) without collapsing early.",
    points: [
      "The violet tile is a camera. If enough probability sits on it after a walk, it looks and the level ends.",
      "Walking right with no H is a pawn-walk into the camera.",
      "H first, then Walk, splits the wave so the camera often sees only half.",
      "Z flips phase. That may not change the heatmap immediately, but later overlaps can cancel or pile up.",
      "Mashing H every step can dump probability onto the camera.",
      "Target ≥ 45%. Measure when Current is at or above the target — if you still can.",
    ],
  },
  "03_measurement": {
    title: "Measurement",
    goal: "Steer a 2D wave through a maze and look when P(goal) is ready.",
    points: [
      "This is a grid. H is the Grover coin: it mixes north, east, south, and west.",
      "Walls bounce. They flip the coin; they do not measure you.",
      "A violet camera still looks if P(camera) is high enough after a Walk.",
      "Hover a cell to read its exact P from the current state.",
      "Watch P(goal) in the HUD. High P means a better Born-rule chance there, not a guarantee.",
      "Target ≥ 20%. Measure yourself, or a camera / step limit will force a look.",
    ],
  },
  "04_strategy": {
    title: "Quantum Maze",
    goal: "Take the wave around the pillar; you cannot go through it.",
    points: [
      "A wall pillar blocks the straight line from start to goal.",
      "There are two routes around it. Mixing with H/G lets the wave try both.",
      "On 2D mazes, H is Grover mixing, not a 1D Hadamard.",
      "X reverses N↔S and E↔W if you need to turn a packet around.",
      "You have 10 Quantum Walks — the shortest bounce path around the pillar needs that many shifts.",
      "Target ≥ 20%. Hover cells to see which route actually holds probability.",
    ],
  },
  "05_quantum_strategy": {
    title: "Quantum Strategy",
    goal: "Spend a small gate budget, sneak past the camera, then ride to the exit.",
    points: [
      "Coin gates are limited. Do not mash H.",
      "A bare walk into the camera collapses you.",
      "Intended idea: H once, then several Walks — one packet toward the exit, one toward the trap.",
      "That split can hit the 50% target without a 100% pawn-walk.",
      "The S phase tile changes phase, not P, until paths overlap later.",
      "Target ≥ 50%. Measure when Current is green.",
    ],
  },
};

export function EducationPanel({
  level,
  state,
}: {
  level: LevelDetail | null;
  state: GameState;
}) {
  const lesson = LESSONS[state.level_id];
  const title = lesson?.title ?? level?.title ?? state.level_id;
  const fallback = [
    "Pick a coin gate, then Quantum Walk.",
    "Read P(goal) against the target before you Measure.",
    "Walls bounce; cameras look; only Measure (or a camera) collapses.",
  ];

  return (
    <aside className="rounded-lg border border-line bg-panel p-4">
      <h3 className="font-mono text-xs tracking-widest text-gold">LEARN</h3>
      <p className="mt-1 font-mono text-[11px] tracking-widest text-cyan">
        {title.toUpperCase()}
      </p>
      <p className="mt-2 text-sm text-slate-200">{lesson?.goal ?? level?.copy?.detail}</p>
      <ul className="mt-3 list-disc space-y-1.5 pl-4 text-sm text-slate-400">
        {(lesson?.points ?? fallback).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {state.explanation ? (
        <p className="mt-3 border-t border-line pt-3 text-sm text-cyan">{state.explanation}</p>
      ) : null}
      {state.status !== "playing" ? <AssistNote state={state} /> : null}
    </aside>
  );
}

function AssistNote({ state }: { state: GameState }) {
  if (state.beginner_assist === "success") {
    return (
      <p className="mt-3 text-sm text-cyan">
        Beginner Assist succeeded. That is a game roll after you met the target — not a change
        to the quantum probabilities.
      </p>
    );
  }
  if (state.beginner_assist === "unlucky") {
    return (
      <p className="mt-3 text-sm text-gold">
        You met the target, but Beginner Assist missed this time. The measured cell is still the
        real collapse.
      </p>
    );
  }
  if (state.status === "won" && state.target_p_goal > 0 && !state.objective_met) {
    return (
      <p className="mt-3 text-sm text-gold">
        Lucky quantum sample — P(goal) was under the target, but the collapsed cell was a goal.
      </p>
    );
  }
  return null;
}
