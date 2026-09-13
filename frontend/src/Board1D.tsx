import { useEffect, useRef } from "react";
import type { GameState } from "./types";

type Props = {
  state: GameState;
};

const DURATION_MS = 260;

export function Board1D({ state }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const displayRef = useRef<number[]>(state.probabilities);
  const fromRef = useRef<number[]>(state.probabilities);
  const toRef = useRef<number[]>(state.probabilities);
  const animRef = useRef<number | null>(null);
  const startedRef = useRef(0);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    fromRef.current = displayRef.current.slice();
    toRef.current = state.probabilities.slice();
    startedRef.current = performance.now();
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const tick = (now: number) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const t = reduced ? 1 : Math.min(1, (now - startedRef.current) / DURATION_MS);
      const from = fromRef.current;
      const to = toRef.current;
      const n = to.length;
      const mixed = new Array<number>(n);
      for (let i = 0; i < n; i += 1) {
        const a = from[i] ?? 0;
        mixed[i] = a + (to[i] - a) * t;
      }
      displayRef.current = mixed;
      drawBoard(canvas, stateRef.current, mixed);
      if (t < 1) animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current !== null) cancelAnimationFrame(animRef.current);
    };
  }, [state.probabilities, state.collapsed_cell, state.status]);

  return (
    <canvas
      ref={canvasRef}
      className="w-full max-w-3xl rounded-lg border border-line bg-ink"
      width={880}
      height={168}
      role="img"
      aria-label="Probability on each cell of the line"
    />
  );
}

function drawBoard(canvas: HTMLCanvasElement, state: GameState, probs: number[]) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const { width: w, height: h } = canvas;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#071018";
  ctx.fillRect(0, 0, w, h);

  const n = state.width;
  const pad = 16;
  const gap = 6;
  const cellW = (w - pad * 2 - gap * (n - 1)) / n;
  const cellH = 88;
  const y = 36;
  const goals = new Set(state.cells.goals);
  const traps = new Set(state.cells.traps);
  const walls = new Set(state.cells.walls);
  const observations = new Set(state.cells.observations ?? []);
  const phaseGates = new Set(state.cells.phase_gates ?? []);
  const collapsed = state.collapsed_cell;
  const peak = Math.max(0, ...probs);

  ctx.font = "12px 'IBM Plex Mono', monospace";
  ctx.textAlign = "center";

  for (let i = 0; i < n; i += 1) {
    const x = pad + i * (cellW + gap);
    const p = probs[i] ?? 0;
    const dim = collapsed !== null && i !== collapsed;
    const glow = 0.08 + p * 0.92;
    ctx.fillStyle = walls.has(i)
      ? "#243444"
      : `rgba(94, 234, 212, ${dim ? glow * 0.18 : glow})`;
    ctx.fillRect(x, y, cellW, cellH);

    if (goals.has(i)) {
      ctx.strokeStyle = "#e8c547";
      ctx.setLineDash([5, 4]);
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 2, y + 2, cellW - 4, cellH - 4);
      ctx.setLineDash([]);
    }
    if (traps.has(i)) {
      ctx.strokeStyle = "#f07167";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 2, y + 2, cellW - 4, cellH - 4);
      ctx.beginPath();
      ctx.moveTo(x + 4, y + 4);
      ctx.lineTo(x + cellW - 4, y + cellH - 4);
      ctx.stroke();
    }

    if (observations.has(i)) {
      ctx.strokeStyle = "#c084fc";
      ctx.setLineDash([2, 3]);
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 2, y + 2, cellW - 4, cellH - 4);
      ctx.setLineDash([]);
    }
    if (phaseGates.has(i)) {
      ctx.strokeStyle = "#7dd3fc";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(x + cellW / 2, y + 12, 4, 0, Math.PI * 2);
      ctx.stroke();
    }
    if (!walls.has(i) && peak > 0.02 && p >= peak - 1e-9 && collapsed === null) {
      ctx.strokeStyle = "#5eead4";
      ctx.lineWidth = 2;
      ctx.strokeRect(x + 1, y + 1, cellW - 2, cellH - 2);
    }
    if (collapsed === i) {
      ctx.fillStyle = "#f8fafc";
      ctx.beginPath();
      ctx.arc(x + cellW / 2, y + cellH / 2, Math.min(cellW, cellH) * 0.18, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.fillStyle = "#9fb3c4";
    ctx.fillText(String(i), x + cellW / 2, y + cellH + 18);
    ctx.fillStyle = "#e2f6f1";
    ctx.fillText(p.toFixed(2), x + cellW / 2, y - 8);
  }
}
