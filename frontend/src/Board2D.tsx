import { useEffect, useRef, useState } from "react";
import type { GameState } from "./types";

const DURATION_MS = 260;
const PAD = 12;
const GAP = 3;

export function formatCellProbability(p: number): string {
  const pct = p * 100;
  if (p <= 0) return "0.0%";
  if (pct > 0 && pct < 0.05) return `${pct.toExponential(1)}%`;
  return `${pct.toFixed(1)}%`;
}

function cellSize(canvas: HTMLCanvasElement, cols: number, rows: number): number {
  const { width: cw, height: ch } = canvas;
  return Math.min(
    (cw - PAD * 2 - GAP * (cols - 1)) / cols,
    (ch - PAD * 2 - GAP * (rows - 1)) / rows,
  );
}

function cellFromPointer(
  canvas: HTMLCanvasElement,
  clientX: number,
  clientY: number,
  cols: number,
  rows: number,
): { x: number; y: number; i: number } | null {
  const rect = canvas.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return null;
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  const px = (clientX - rect.left) * scaleX;
  const py = (clientY - rect.top) * scaleY;
  const size = cellSize(canvas, cols, rows);
  const x = Math.floor((px - PAD) / (size + GAP));
  const y = Math.floor((py - PAD) / (size + GAP));
  if (x < 0 || y < 0 || x >= cols || y >= rows) return null;
  const ox = PAD + x * (size + GAP);
  const oy = PAD + y * (size + GAP);
  if (px < ox || py < oy || px > ox + size || py > oy + size) return null;
  return { x, y, i: y * cols + x };
}

export function Board2D({ state }: { state: GameState }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const displayRef = useRef<number[]>(state.probabilities);
  const fromRef = useRef<number[]>(state.probabilities);
  const toRef = useRef<number[]>(state.probabilities);
  const animRef = useRef<number | null>(null);
  const startedRef = useRef(0);
  const stateRef = useRef(state);
  stateRef.current = state;
  const [hover, setHover] = useState<{
    x: number;
    y: number;
    i: number;
    left: number;
    top: number;
  } | null>(null);

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
      const mixed = to.map((p, i) => (from[i] ?? 0) + (p - (from[i] ?? 0)) * t);
      displayRef.current = mixed;
      drawGrid(canvas, stateRef.current, mixed);
      if (t < 1) animRef.current = requestAnimationFrame(tick);
    };

    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current !== null) cancelAnimationFrame(animRef.current);
    };
  }, [state.probabilities, state.collapsed_cell, state.status]);

  function placeTooltip(clientX: number, clientY: number, cell: { x: number; y: number; i: number }) {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const rect = wrap.getBoundingClientRect();
    const pad = 12;
    let left = clientX - rect.left + 14;
    let top = clientY - rect.top - 36;
    const maxL = Math.max(pad, rect.width - 118);
    const maxT = Math.max(pad, rect.height - 40);
    left = Math.min(Math.max(pad, left), maxL);
    top = Math.min(Math.max(pad, top), maxT);
    setHover({ ...cell, left, top });
  }

  function onMove(event: React.MouseEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const cell = cellFromPointer(canvas, event.clientX, event.clientY, state.width, state.height);
    if (!cell) {
      setHover(null);
      return;
    }
    placeTooltip(event.clientX, event.clientY, cell);
  }

  const pHover = hover ? (state.probabilities[hover.i] ?? 0) : 0;

  return (
    <div ref={wrapRef} className="relative w-full max-w-lg">
      <canvas
        ref={canvasRef}
        className="w-full rounded-lg border border-line bg-ink"
        width={448}
        height={448}
        role="img"
        aria-label="Probability on each maze cell. Hover a cell to read P."
        onMouseMove={onMove}
        onMouseLeave={() => setHover(null)}
      />
      {hover ? (
        <div
          className="cell-tooltip"
          data-testid="cell-prob-tooltip"
          style={{ left: hover.left, top: hover.top }}
        >
          P = {formatCellProbability(pHover)}
        </div>
      ) : null}
    </div>
  );
}

function drawGrid(canvas: HTMLCanvasElement, state: GameState, probs: number[]) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  const { width: cw, height: ch } = canvas;
  ctx.fillStyle = "#071018";
  ctx.fillRect(0, 0, cw, ch);

  const cols = state.width;
  const rows = state.height;
  const cell = cellSize(canvas, cols, rows);
  const goals = new Set(state.cells.goals);
  const traps = new Set(state.cells.traps);
  const walls = new Set(state.cells.walls);
  const observations = new Set(state.cells.observations ?? []);
  const phaseGates = new Set(state.cells.phase_gates ?? []);
  const collapsed = state.collapsed_cell;
  const peak = Math.max(0, ...probs);

  for (let y = 0; y < rows; y += 1) {
    for (let x = 0; x < cols; x += 1) {
      const i = y * cols + x;
      const px = PAD + x * (cell + GAP);
      const py = PAD + y * (cell + GAP);
      const p = probs[i] ?? 0;
      const dim = collapsed !== null && i !== collapsed;
      if (walls.has(i)) {
        ctx.fillStyle = "#243444";
      } else {
        const glow = 0.08 + p * 0.92;
        ctx.fillStyle = `rgba(94, 234, 212, ${dim ? glow * 0.18 : glow})`;
      }
      ctx.fillRect(px, py, cell, cell);
      if (goals.has(i)) {
        ctx.strokeStyle = "#e8c547";
        ctx.setLineDash([4, 3]);
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 2, py + 2, cell - 4, cell - 4);
        ctx.setLineDash([]);
      }
      if (traps.has(i)) {
        ctx.strokeStyle = "#f07167";
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 2, py + 2, cell - 4, cell - 4);
        ctx.beginPath();
        ctx.moveTo(px + 3, py + 3);
        ctx.lineTo(px + cell - 3, py + cell - 3);
        ctx.stroke();
      }
      if (observations.has(i)) {
        ctx.strokeStyle = "#c084fc";
        ctx.setLineDash([2, 2]);
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 2, py + 2, cell - 4, cell - 4);
        ctx.setLineDash([]);
      }
      if (phaseGates.has(i)) {
        ctx.strokeStyle = "#7dd3fc";
        ctx.beginPath();
        ctx.arc(px + cell / 2, py + 6, 3, 0, Math.PI * 2);
        ctx.stroke();
      }
      if (!walls.has(i) && peak > 0.02 && p >= peak - 1e-9 && collapsed === null) {
        ctx.strokeStyle = "#5eead4";
        ctx.lineWidth = 2;
        ctx.strokeRect(px + 1, py + 1, cell - 2, cell - 2);
      }
      if (collapsed === i) {
        ctx.fillStyle = "#f8fafc";
        ctx.beginPath();
        ctx.arc(px + cell / 2, py + cell / 2, cell * 0.18, 0, Math.PI * 2);
        ctx.fill();
      }
    }
  }
}
