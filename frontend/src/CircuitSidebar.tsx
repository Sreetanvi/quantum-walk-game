import type { CircuitView } from "./types";

export function CircuitSidebar({ circuit }: { circuit: CircuitView | null }) {
  if (!circuit) {
    return (
      <aside className="rounded-lg border border-line bg-panel p-4 text-sm text-slate-400">
        Loading circuit…
      </aside>
    );
  }
  return (
    <details className="rounded-lg border border-line bg-panel p-4" open>
      <summary className="cursor-pointer font-mono text-xs tracking-widest text-cyan">
        QUANTUM CIRCUIT
      </summary>
      <p className="mt-2 text-sm text-slate-300">{circuit.message}</p>
      {circuit.history && circuit.history.length > 0 ? (
        <p className="mt-2 font-mono text-xs text-slate-400">
          {circuit.history.join(" → ")}
        </p>
      ) : (
        <p className="mt-2 font-mono text-xs text-slate-500">No gates yet.</p>
      )}
      {circuit.supported && circuit.diagram ? (
        <>
          <p className="mt-1 font-mono text-xs text-slate-500">
            {circuit.n_qubits} qubits · {circuit.n_sites} sites · {circuit.steps_shown ?? 0}{" "}
            {(circuit.steps_shown ?? 0) === 1 ? "shift" : "shifts"}
          </p>
          <pre className="mt-3 max-h-72 overflow-auto text-[11px] leading-4 text-cyan">{circuit.diagram}</pre>
        </>
      ) : null}
    </details>
  );
}
