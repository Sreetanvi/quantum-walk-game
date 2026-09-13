export type GameStatus = "playing" | "won" | "lost";

export type GameState = {
  session_id: string;
  level_id: string;
  mode: string;
  width: number;
  height: number;
  cells: {
    walls: number[];
    traps: number[];
    goals: number[];
    observations?: number[];
    phase_gates?: number[];
  };
  probabilities: number[];
  probabilities_2d: number[][] | null;
  step: number;
  step_limit: number;
  status: GameStatus;
  collapsed_cell: number | null;
  p_goal: number;
  p_trap: number;
  p_observation?: number;
  target_p_goal: number;
  objective_met: boolean;
  last_op: string | null;
  explanation: string | null;
  allowed_ops: string[];
  ops_used: number;
  op_limit: number | null;
  history: string[];
  message: string | null;
  score: number | null;
  quantum_outcome?: "goal" | "trap" | "other" | null;
  beginner_assist?: "success" | "unlucky" | "off";
  assist_seed?: number | null;
};

export type LevelSummary = {
  id: string;
  title: string;
  order: number;
};

export type LevelDetail = {
  id: string;
  title: string;
  order: number;
  copy?: { short?: string; detail?: string };
};

export type CircuitView = {
  supported: boolean;
  message: string;
  session_id: string | null;
  diagram: string | null;
  qasm: string | null;
  steps_shown: number | null;
  n_qubits: number | null;
  n_sites: number | null;
  history?: string[];
};

export type CoinGate = "H" | "X" | "Z" | "S";
