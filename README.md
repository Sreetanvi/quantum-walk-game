# Quantum Walk Game — Build Bible

This file is the **source of truth** for a **solo** build. There is no team. Divisions below are **modules and work phases**, not people. Every architecture, physics, product, and tooling choice that would otherwise be debated is **locked here** so implementation can start without re-deciding.

If a later change is needed, change this file first, then the code.

---

## Progress and work log

This is the running record of what already exists in the repo. New slices should append here.

### Status

| Slice | Status | Notes |
| --- | --- | --- |
| **A** — 1D NumPy walk | **Done** | `initialize`, `step` (`U = SC`), `probabilities()`, reflecting edges, pytest green |
| **B** — measure + collapse | **Done** | Born-rule `measure(seed)`, collapse to `|cell⟩⊗|R⟩`, replay + histogram tests |
| **C** — FastAPI game rules | **Done** | In-memory sessions, level 1 JSON, start/move/measure, win/lose, API tests |
| **D** — React UI | **Done** | Vite + React play screen, 1D canvas heatmap, three buttons, talks to API |
| **E** — Qiskit circuit + Aer | **Done** | 1D H+S circuit, Aer vs NumPy 1e-8, sidebar, `/game/circuit` live |
| **F** — 2D + maze walls | **Done** | Grover coin, reflecting walls/edges, level `03_measurement`, 2D canvas |
| **G** — campaign + polish | **Done** | Levels 2 and 4, LEARN panel, lucky-win copy, collapse flash |
| **I** — strategy controls | **Done** | Coin gates ≠ walk; P(goal) targets; cameras / phase tiles; Level 5; controls under the map; Vite proxy |
| **J** — win / campaign UX | **Done** | Win/loss/campaign overlays; Next Level from API order; camera threshold tests |
| **H** — deploy | Not started | |

**Next slice:** H — deploy if you want it online.

### This agent (skill redesign → layout → win UX)

The playable A–G game was “press Quantum Move, then hope.” The design question was: **where is the player’s skill?** Skill must be *choosing operations that causally change the complex state*, not extra RNG.

What shipped in this agent, in order: skill redesign (**I**), then **controls under the map**, then **win / campaign UX (J)**.

**Instructions the player-facing work followed**

- Keep an honest DTQW (NumPy amplitudes, FastAPI rules). Do not fake P with shaders or RNG heatmaps.
- Skill = choosing coin ops that change \(\psi\), then walking, then choosing when to Measure.
- Put Quantum Controls **directly under the map** (they were below the tall circuit column).
- After collapse, a strong win/loss/campaign modal and Next Level — **without** changing walk, camera, or measure math.

1. **Coin ≠ walk.** Panel: **H, X, Z, S**. Primary: **Quantum Walk →**. H is not auto-applied.
2. Gates are real matrices on the coin. Walk is shift only. \(P=\|\psi\|^2\).
3. Each level has a **target** (`target_p_goal`), shown as Goal ≥ N% vs Current.
4. **Measure** is the player’s look (off at step 0). Not fired just because P(goal) is high. Forced at `step_limit` or on **observation** tiles.
5. Tiles: goal, trap, wall (reflect), observation (camera), phase gate.
6. Short plain-English **explanation after every action**.
7. **Quantum Circuit** panel tracks the real 1D op history (Qiskit). 2D: text history, no fake Grover circuit.
8. Heatmap: brightness ∝ P; peak outline; gold goal; hatched trap; violet camera; cyan phase ring; ~260ms lerp.
9. HUD: current gate, walks, target, P(goal), P(trap), measure status, win/loss + pre-collapse P, score.
10. Five levels: Superposition → Interference → Measurement → Quantum Maze → Quantum Strategy.
11. **Play layout:** board, then **controls immediately under the map**; LEARN + circuit on the right (all levels).
12. Vite **proxies** `/levels`, `/game`, `/health` → `:8000` so `localhost:5173` is one origin (level list no longer empty while CORS waits).
13. Engine `step()` is still textbook \(U=SC\) for A–G physics tests.
14. **Win modal** after collapse on a goal: YOU WIN!, cell, P(goal), target ✓/✗, score, **Next Level →** / Replay.
15. **Next Level** starts the next id from `GET /levels` order (fresh session). Last level → **QUANTUM WALK COMPLETE**.
16. **Loss modal** (camera, trap, miss): why + cell + P(goal) + **Retry Level**. Gates/Walk stay off.
17. Camera rule re-checked and tested: force measure iff \(P(\mathrm{obs})\ge\) threshold (0.50 stays playing; 0.625 collapses). High P(goal) still does **not** auto-measure.

`pytest` **54 passed**.

**Still not done / out of v1 unless asked:** Slice H deploy; IBM QPU; accounts; editor; 3D; walls-as-measurement; Left/Right as the default move; rewriting the engine in the browser; 2D Qiskit Grover circuit.

### Work done before any code (planning)

1. **Concept.** Locked the game as a discrete-time quantum walk: the player is amplitudes on many tiles, not a classical pawn. Quantum Move = Hadamard (1D) or Grover (2D later) then a shift. Interference is complex addition. Position is unknown until measurement.
2. **Qiskit vs NumPy.** Gameplay uses **NumPy** (custom maze, speed, heatmap). **Qiskit + Aer** is for 1D circuit view and numerical agreement tests, not IBM hardware in v1, and not the HTTP backend.
3. **Architecture.** Not “frontend vs backend only.” Heart is `quantum_engine`. Layout: Frontend → FastAPI (rules, levels, session) → engine. Solo build: modules, not a five-person split.
4. **Rules that are easy to get wrong.** Walls **reflect** (unitary, coin flip); they do **not** measure. Traps/goals score **after** Measure (or forced at `step_limit`). Overlap with a trap does **not** auto-collapse. Level **ends** on measure. No Left/Right button in v1.
5. **v1 freeze (updated Slice I).** Five levels. Coin gates **H / X / Z / S** are separate from **Quantum Walk** (shift only). Measure is a player decision (still off at step 0; forced at `step_limit` or observation tiles). Skill = meet `target_p_goal` then collapse. Qiskit sidebar tracks the **actual** 1D gate history.

The rest of this file is that locked design. Code should follow it.

### Slice A (implemented)

Python package `quantum_engine/` simulates a **1D Hadamard walk** on a closed line.

| Path | Role |
| --- | --- |
| `quantum_engine/errors.py` | `QuantumEngineError` |
| `quantum_engine/state.py` | `(N, 2)` `complex128` state; \(P(x)=\sum_c\|\alpha_{x,c}\|^2\); norm check |
| `quantum_engine/coin.py` | Hadamard; \(\|R\rangle=\|0\rangle\), \(\|L\rangle=\|1\rangle\) |
| `quantum_engine/shift.py` | Conditional shift; edges reflect and flip the coin |
| `quantum_engine/walk.py` | `QuantumWalk`: `initialize`, `step`, `probabilities`, `from_level`, `measure` |
| `quantum_engine/validation.py` | Helpers: quantum vs classical random walk |
| `tests/test_walk_1d.py` | Unitary coin, first-step split, norm, edges, ballistic ≠ binomial |
| `tests/test_interference.py` | Opposite-phase amplitudes cancel; same phase constructs |
| `requirements.txt` | `numpy`, `pytest` |
| `pytest.ini` | `pythonpath = .` |

**How to run Slice A**

```bash
pip install -r requirements.txt
pytest
```

**Minimal API (works today)**

```python
from quantum_engine import QuantumWalk

walk = QuantumWalk(grid_size=10)
walk.initialize(position=5)
walk.step()
print(walk.probabilities())
```

**Checks that passed**

- After one step from site 5 with coin `R`, probability is `0.5` on sites 4 and 6 (split, no leftover at 5).
- \(\sum_x P(x)=1\) after many steps, including bounces at the left edge.
- After 10 steps on a 51-site line starting at 25, the peak is **not** at the origin (ballistic, right-biased Hadamard walk from \(\|R\rangle\)), unlike a classical random walk which piles up in the middle.
- Destructive / constructive interference on a single basis state.

**Not in Slice A (were added in Slice B)**

- `measure()` — now implemented. Still no FastAPI, React, Qiskit, 2D, or on-disk levels.

### Slice B (implemented)

Position measurement uses the **Born rule** on the current amplitudes. The engine samples one cell, then **collapses** the state. Game win/lose still belongs in Slice C.

| Path | Role |
| --- | --- |
| `quantum_engine/measurement.py` | `sample_position`, `collapse_1d`, `measure_1d`, `MeasurementResult` |
| `quantum_engine/walk.py` | `measure(seed=None)` facade; `collapsed_cell` |
| `tests/test_measurement.py` | Certain start, collapse to a delta, seeded replay, 10k-shot histogram |

**Minimal API (Slices A+B)**

```python
from quantum_engine import QuantumWalk

walk = QuantumWalk(grid_size=10)
walk.initialize(position=5)
walk.step()
result = walk.measure(seed=42)
print(result.cell, result.probabilities_before, walk.probabilities())
```

**Locked behaviour in code**

- Sample from \(P(x)=\sum_c|\alpha_{x,c}|^2\) with `numpy.random.Generator` (the only RNG in the library).
- Same `seed` → same cell (replay / tests).
- If `seed` is omitted, a seed is generated and returned as `seed_used`.
- After collapse, amplitude is only on that cell, coin **reset to `|R⟩`**.
- `probabilities_before` is the distribution **used to sample**, copied so it still matches after collapse.
- Measuring before `initialize()` raises `QuantumEngineError`.

**Checks that passed**

- Step 0, start at 5: measure always returns cell 5; state is a delta there.
- After one split: outcome is 4 or 6; afterwards \(P=1\) on that cell only.
- Two walks, six steps, `seed=7`: identical collapse cell.
- 10 000 independent shots after one split: frequencies within 0.03 of 0.5 / 0.5 on sites 4 and 6.

**Not in Slice B**

- FastAPI, React, Qiskit, 2D (backend game rules were added in Slice C).

### Slice C (implemented)

The **game master** is a FastAPI app. It does not recompute \(U\); it calls `QuantumWalk`. Sessions live in memory (lost on restart).

| Path | Role |
| --- | --- |
| `levels/01_superposition.json` | 1D line, 11 cells, start at 5, goals at both ends, `step_limit` 6 |
| `backend/levels.py` | Load / list / validate 1D JSON; linear cell indices |
| `backend/models.py` | Pydantic request and `GameStateDTO` |
| `backend/game.py` | Sessions, legal moves, measure rules, win/lose, score |
| `backend/main.py` | HTTP routes + CORS for `http://localhost:5173` |
| `tests/test_api.py` | Health, start/move/measure, step-0 measure rejected, auto-measure |

**Run the API**

```bash
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Example:

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/game/start -H "Content-Type: application/json" -d "{\"level_id\":\"01_superposition\"}"
```

**Rules encoded (Slice C — later replaced by Slice I)**

- Then: only action `quantum_move` (= H then shift).
- Now: see Slice I (`H`/`X`/`Z`/`S`/`quantum_walk`).
- **Measure disabled at step 0** (still true).
- After Measure, the run **ends** (`won` if cell is a goal, else `lost`). Further moves 400.
- Hitting `step_limit` **forces** a measure.
- `p_goal` / `p_trap` from current \(P\); after collapse they stay the **pre-measure** values and `probabilities` is that snapshot (for a later collapse animation).
- Score: `round(100 * p_goal)` + 10 on win + leftover steps.
- `GET /game/circuit` is live in Slice E (was a stub here).

**Checks that passed (24 tests total, A–C)**

- Start: \(P=1\) at cell 5.
- One move: 0.5 / 0.5 on 4 and 6 (same physics as Slice A, over HTTP).
- Measure with seed collapses and sets `status` / `collapsed_cell` / `score`.
- Unknown level/session → 404.

**Not in Slice C**

- React UI (added in Slice D), Qiskit, 2D mazes, levels 2–4 as playable files.

### Slice D (implemented)

The player-facing site is a **Vite + React + TypeScript** app with Tailwind. It talks to FastAPI at `http://127.0.0.1:8000` (`VITE_API_URL` to override). No Redux. No Three.js.

| Path | Role |
| --- | --- |
| `frontend/src/gameApi.ts` | `listLevels`, `startGame`, `quantumMove`, `measure`, `fetchCircuit` |
| `frontend/src/Board1D.tsx` | Canvas heatmap; brightness ∝ \(P\); gold dashed goals; lerp ~260ms |
| `frontend/src/App.tsx` | Landing, How it works, Play; three buttons; HUD |

**Run with the API**

```bash
# terminal 1
uvicorn backend.main:app --reload --port 8000
# terminal 2
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`. Vite proxies `/levels`, `/game`, and `/health` to `http://127.0.0.1:8000` so the browser stays on one origin. Set `VITE_API_URL` only for a split production deploy.

**UI behaviour**

- Landing lists levels from `GET /levels`.
- **Play** / Superposition starts a session.
- **Quantum Move**, **Measure (collapse)** (disabled at step 0), **Restart**.
- HUD: step, `P(goal)`, `P(trap)`, score after collapse.
- After measure: result copy + pawn on `collapsed_cell`; move/measure disabled.

**Verified in the browser**

- Levels load from the API.
- Measure is disabled before the first move.
- One Quantum Move, then Measure: collapse (example: cell 6, miss the ends — expected after one split).
- How it works screen.

**Not in Slice D**

- Qiskit circuit sidebar (added in Slice E), 2D maze canvas, levels 2–4, Framer Motion flash.

### Slice E (implemented)

Qiskit is the **circuit / validation layer**, not the gameplay loop. NumPy still runs every `POST /game/move`. Aer `statevector` must match NumPy \(P(x)\) within `1e-8`.

| Path | Role |
| --- | --- |
| `quantum_engine/qiskit_circuit.py` | 1D circuit: coin qubit + position qubits; `H` then reflecting shift `S`; Aer simulate |
| `tests/test_qiskit_agreement.py` | t = 1, 2, 3 on N=8 and N=11 vs NumPy |
| `backend/game.py` `get_circuit` | Fills `GET /game/circuit` |
| `frontend/src/CircuitSidebar.tsx` | Text diagram beside the heatmap |

**Encoding:** qubit 0 = coin (\(\|R\rangle=\|0\rangle\)), remaining bits = position. Unused basis states (when N is not a power of 2) stay idle. `S` is the **same reflecting permutation** as NumPy, wrapped as a Qiskit `UnitaryGate`.

**API:** `GET /game/circuit?session_id=` returns `supported`, `diagram`, `qasm` (when dumpable), `steps_shown`, `n_qubits`, `n_sites`. Slice I: empty history = empty/stub circuit (not a fake H+S preview). After ops it shows the real 1D gate+shift list.

**Checks that passed (31 tests total, A–E)**

- Aer vs NumPy after 1–3 steps on 8 and 11 sites.
- API circuit for Superposition: 5 qubits, 11 sites.
- Browser: sidebar title **QISKIT CIRCUIT**; after one move the copy updates to “1 walk step(s)”.

**Not in Slice E**

- IBM QPU, 2D Grover *circuit*, QASM as the main UI (diagram is). 2D **NumPy** walk is Slice F.

### Slice F (implemented)

The walker can leave the line. On a grid the coin is **Grover** on \(\{|N\rangle,|E\rangle,|S\rangle,|W\rangle\}\). Walls and map edges **reflect** (stay + flip N↔S or E↔W). They still do **not** measure.

Coordinates: origin top-left, **+x right, +y down**. **North is \(y-1\)** (up on screen), east \(x+1\), south \(y+1\), west \(x-1\).

| Path | Role |
| --- | --- |
| `quantum_engine/coin.py` | `GROVER = \tfrac12 J - I` |
| `quantum_engine/shift.py` | `apply_shift_2d` + wall set |
| `quantum_engine/state.py` | `(H, W, 4)` amplitudes; `probabilities_2d` |
| `quantum_engine/measurement.py` | Flattened Born sample; collapse onto `|E⟩` |
| `quantum_engine/walk.py` | `mode="2d"`, `from_level` with walls |
| `tests/test_walk_2d.py` | Unitary Grover, 4-way split, wall bounce, measure |
| `levels/03_measurement.json` | 7×7 maze, goal (5,5), trap (5,1) |
| `frontend/src/Board2D.tsx` | Maze heatmap |

**Locked Grover:** \(G=2|s\rangle\langle s|-I\) with \(|s\rangle=\frac12\sum_d|d\rangle\). First step from an interior `|E⟩` puts **0.25** on each of the four neighbors.

**API:** `probabilities` is row-major flat; `probabilities_2d` is nested rows. Circuit view stays **unsupported** on 2D (message already in Slice E).

**Checks that passed (38 tests total, A–F)**

- Empty 5×5, start center `|E⟩`, one step: four neighbors 0.25, origin 0.
- East into an internal wall becomes West on the same cell.
- 6 steps stay normalized; measure is a delta with coin `|E⟩`.
- `POST /game/start` on `03_measurement` returns a 7×7 grid; one move spreads probability.
- Browser: **Level 3: Measurement** loads; Measure stays disabled until a Quantum Move.

**Not in Slice F**

- Level 2 and 4 (added in Slice G), deploy (H).

### Slice G (implemented)

The campaign is four levels. Education sits next to the board. Collapse is a bit louder, and a lucky win is called luck.

| Path | Role |
| --- | --- |
| `levels/02_interference.json` | 21-cell line; trap at the start; goal at the ballistic peak (cell 16); 8 steps |
| `levels/04_strategy.json` | 9×7 maze; wall blocks the straight line; two paths around it; **10-walk** budget |
| `frontend/src/EducationPanel.tsx` | Level `copy.detail` + per-level lessons + luck/skill notes |
| `backend/game.py` | Win with \(P(\mathrm{goal})<0.2\) appends “You got lucky…” |
| `frontend/src/index.css` | `.collapse-flash` (skipped if reduced motion) |
| `tests/test_campaign.py` | Four levels in order; after 8 interference steps \(P(16)>P(10)\) |

**Checks that passed (41 tests total, A–G)**

- Level list is Superposition → Interference → Measurement → Quantum strategy.
- After 8 Hadamard steps, the peak beats the origin trap.
- Strategy maze starts on (1,3) and spreads after one Grover step.
- Browser: all four levels on the landing page; Interference shows **LEARN** plus Qiskit (6 qubits / 21 sites).

**Not in Slice G**

- Hosting (Slice H), IBM QPU, level editor.

### Slice I (implemented)

The player **chooses** coin unitaries. The walk no longer secretly applies Hadamard/Grover on every button. The product question this slice answers: *the player should think “what operation do I apply now so the interference later is the one I want?”* — not “press the same button five times and hope.”

| Path | Role |
| --- | --- |
| `quantum_engine/coin.py` | 1D `H,X,Z,S`; 2D Grover-as-H plus direction `X,Z,S`; phase-tile factors |
| `quantum_engine/walk.py` | `apply_gate`, `propagate` (shift + phase tiles); `step()` still `U=SC` for physics tests |
| `quantum_engine/qiskit_circuit.py` | `circuit_from_ops` — Qiskit diagram of the **actual** 1D history |
| `backend/game.py` | Actions `H`/`X`/`Z`/`S`/`quantum_walk`; observation collapse; targets; explanations |
| `backend/models.py` | DTO: `target_p_goal`, `last_op`, `explanation`, `allowed_ops`, `history`, cameras |
| `levels/01`–`04` JSON | Targets, `allowed_ops`, cameras on 02/03 |
| `levels/05_quantum_strategy.json` | `op_limit` 8, `target_p_goal` **0.5**, camera at cell 6, S phase tile |
| `frontend/src/App.tsx` | Quantum Controls **under the board**; HUD; 1D and 2D |
| `frontend/vite.config.ts` | Dev proxy `/levels` `/game` `/health` → `127.0.0.1:8000` |
| `tests/test_player_ops.py` | H then propagate ≡ `step()`; X heading; Z changes later P |
| `tests/test_api.py` | H then walk split; pawn-walk camera; L5 H-then-ride meets 50% |

**Design brief that is now locked (from the skill rewrite)**

- Do **not** replace the engine with fake/random probability animations.
- Separate **quantum operations** from **quantum walk movement**.
- Workflow: choose gate → it is applied to the state → **Quantum Walk →** → amplitudes propagate → P updates.
- Level objective is of the form “reach the goal with at least X% probability in N walks,” then Measure.
- Observation tiles may force measurement; walls still only reflect.
- After every action, one short sentence (H mixed the coin; Z flipped phase; walk propagated; measure collapsed).
- Circuit view corresponds to operations the sim used, not decoration.
- Win copy includes measured cell **and** P(goal) before collapse. Lucky win if P was under the target.
- Architecture stays **Frontend → FastAPI rules → NumPy engine**. Qiskit is circuit + Aer tests, not IBM hardware, not every animation frame.

**Intended solutions (so difficulty is fair, not 70% on an impossible Hadamard mash)**

| Level | Skill shot |
| --- | --- |
| 1 Superposition | Teach H (split: P stays on the start until Walk). **X** or a bare Walk to an **end** can hit the **70%** target (both ends are goals). Mixing is a choice, not always optimal. |
| 2 Interference | Bare Walk right hits the **camera at 11** and collapses. **H** then Walk sneaks past (\(P(\mathrm{cam})=0.5 < 0.51\)). Target **45%**. Z is unlocked for later interference; mashing H can pile onto the camera. |
| 3 Measurement | 2D. H = Grover. Camera in the top hall. Walls bounce. Target **20%**. |
| 4 Quantum Maze | Pillar; Grover to turn corners. File id still `04_strategy`. Target **20%**. `step_limit` **10**. |
| 5 Quantum Strategy | Camera at 6 blocks a 100% pawn-walk. **H once, then five Walks** (do not remash H) puts **50%** on the exit and 50% on the trap — target **50%**. S phase tile at 8 does not change P, only phase. |

**UI verified**

- Controls sit **directly under** the 1D line and the 2D maze (not below the tall circuit panel).
- Measure disabled at step 0; H then Walk on L1 splits 0.50 / 0.50 on cells 4 and 6; circuit shows `H → SHIFT`.
- Z/S greyed on L1; S greyed on L3; H labeled **H / G** on 2D.

### Slice J (implemented) — win / campaign UX

Instruction: make win and progression obvious **without** changing the NumPy walk, measure math, or FastAPI legal-move rules. In-page LEARN copy stays; the modal is the celebration.

| Path | Role |
| --- | --- |
| `frontend/src/ResultOverlay.tsx` | Win / loss / campaign-complete dialogs; `nextLevelId` / `firstLevelId` from API `order` |
| `frontend/src/App.tsx` | Overlay wiring; refuse gates/walk after `status !== playing`; level-enter fade |
| `frontend/src/index.css` | Overlay fade, win pulse; skipped if `prefers-reduced-motion` |
| `tests/test_api.py` | Camera ≥ threshold (not only P=1); P=0.5 does not trip; high P(goal) does not auto-measure |

**Locked UX**

- **Timing:** collapse paints first (pawn + in-page result). Wait **~1.5s**. Then the modal. No second measure.
- **Win:** **🎉 YOU WIN!** / You reached the goal! / live `P(goal)`. Lucky copy if target missed. **Next Level →**.
- **Next Level:** `POST /game/start` on the next campaign id. New session, empty history, walk count 0. Do not bounce to the landing list.
- **Last win:** **🏆 CAMPAIGN COMPLETE!** / You mastered the Quantum Walk. **Play Again** (first by `order`).
- **Loss:** **💥 YOU LOSE** / You collapsed somewhere else. / live `P(goal)`. **Try Again** = restart current id.
- Board still shows the existing result sentence under the controls. Overlay summarizes; it does not delete education.
- After collapse, Quantum Walk / coin gates stay disabled (UI + API 400).

**Camera (bug check, Slice J — no physics change)**

`backend/game.py` after each `quantum_walk`: if observation cells exist and \(P(\mathrm{obs})\ge\) `observation_threshold` (default **0.51**), forced full measure.

| P(obs) | Threshold 0.51 | Result |
| --- | --- | --- |
| 1.00 | ≥ | Force measure (pawn-walk into camera) |
| 0.625 | ≥ | Force measure (Hadamard mash on L2) |
| 0.51 | ≥ | Force measure |
| 0.50 | < | **No** force (H then one Walk on L2) |
| 0.20 | < | No force |

Do **not** require \(P=1\). Do **not** measure because amplitude is merely nonzero on a camera. Walls still only reflect. Phase tiles still only multiply. Goals/traps still score after a look. Player Measure still manual.

**Verified**

- Browser: L1 X + 5 walks + Measure → YOU WIN! (cell 0, 100% vs 70% ✓) → Next Level → Level 2 Interference.
- Browser: L2 bare Walk → camera cell 11 → Run over + Retry. Walk disabled.
- `pytest` 54.

---


## 0. Solo constraint (locked)

You are building **all parts**. That does **not** mean five parallel workstreams. It means:

- One repo, three packages: `quantum_engine` → `backend` → `frontend`
- Build **vertically in slices** (one playable loop at a time), not “finish all quantum then all backend then all UI”
- Cut anything that needs a second human (auth, editor v1, 3D, live QPU queues, multiplayer)

**Team-shaped design, solo execution:** the five “divisions” in the project brief become folders and checklists. You wear each hat **in sequence per slice**, not all week as five jobs.

| Brief “person” | Solo equivalent |
| --- | --- |
| Quantum simulation | `quantum_engine/` + pytest |
| Qiskit validation | `quantum_engine/qiskit_backend.py` after NumPy works |
| Game backend | `backend/` FastAPI, thin, no extra services |
| Frontend + viz | `frontend/` Vite + React |
| Education + testing + deploy | Levels JSON, copy in UI, tests, deploy last |

**Do not** hire a backend “because quantum.” Do not add a third web tier. The quantum engine is a **library the backend imports**.

---

## 1. What we are building (one sentence)

> An interactive quantum-walk maze where the player controls quantum operations, watches **amplitudes** spread and interfere, and learns how **measurement** changes the outcome.

Three things the demo must prove:

1. **Real simulation** — evolve complex amplitudes with a discrete-time quantum walk (DTQW), not a blur shader.
2. **Playable game** — levels, legal moves, traps, goals, win/loss.
3. **Education** — a watcher understands why this is not a classical pawn.

**Product name:** Quantum Walk Game  
**Genre:** Educational puzzle / maze  
**Scope (solo v1):** Polished **2D** maze + **1D tutorial**, NumPy engine, Qiskit circuit view, **5 levels**, player coin gates + walk, FastAPI + React. Not a full game studio engine.

---

## 2. Locked physics (do not “simplify” this away)

### 2.1 Amplitudes, not probabilities, are the state

The engine stores **complex amplitudes** \(\alpha_{p,c}\) for every position \(p\) and coin state \(c\).

\[
|\psi\rangle = \sum_{p,c} \alpha_{p,c}\, |p\rangle\otimes|c\rangle
\]

- **Evolution** uses \(\alpha\) (unitary \(U = SC\)).
- **Display** may show \(P(p)=\sum_c |\alpha_{p,c}|^2\).
- **Collapse** samples from \(P(p)\), then replaces \(|\psi\rangle\) with a localized state.

Probabilities are **derived**. They are never what you step forward in time (except after measurement).

### 2.2 Player actions (Slice I)

Coin and shift are **separate player actions**. Textbook `step()` in the engine is still \(U=SC\) for tests.

| Control | Physics |
| --- | --- |
| **H / X / Z / S** | Unitary on the **coin** register at every cell. \(P(x)\) unchanged. |
| **Quantum Walk** | Reflecting **shift** \(S\) only, then phase tiles if the level has them. |
| **Measure** | Born-rule collapse (unchanged). |

Default 1D mixer is Hadamard; default 2D mixer (the **H** button on mazes) is the **Grover coin**. The player does **not** pick a tile with WASD. They pick a **coin unitary**, then ask the wave to propagate.

A full textbook walk step is what you get if you press **H** then **Quantum Walk**. Pressing Walk with no mix is a directed shift of the current coin — that is a real (and sometimes losing) strategy.

### 2.3 Coin (locked)

| Mode | Coin space | Operator |
| --- | --- | --- |
| **1D** (tutorial, validation) | \(\{|L\rangle,|R\rangle\}\) | **Hadamard** \(H\) |
| **2D** (maze) | \(\{|N\rangle,|E\rangle,|S\rangle,|W\rangle\}\) | **Grover coin** on 4 directions |

Hadamard on 1D is the textbook walk (easy to validate). Grover on 2D is the standard grid walk (symmetric, interference is visible). Do **not** invent a random 4×4 matrix.

**Hadamard (1D):**

\[
H = \frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}
\]

Convention: \(|R\rangle = |0\rangle\), \(|L\rangle = |1\rangle\) (document in `coin.py` and never flip silently).

**Grover coin (2D):** \(G = 2|s\rangle\langle s| - I\) with \(|s\rangle = \frac12\sum_{d=N,E,S,W}|d\rangle\).

**Player coin gates (Slice I):** 1D uses the 2×2 matrices \(H,X,Z,S=\mathrm{diag}(1,i)\). 2D **H** is Grover; 2D **X** swaps N↔S and E↔W; 2D **Z** / **S** phase the S and W components. **Phase tiles** multiply the amplitudes on a cell after a shift (still unitary). No other gadgets.

### 2.4 Shift (locked)

- **1D:** \(|x,R\rangle \mapsto |x+1,R\rangle\), \(|x,L\rangle \mapsto |x-1,L\rangle\).
- **2D:** coin \(N/E/S/W\) steps **north \(y-1\)** (up on screen), east \(x+1\), south \(y+1\), west \(x-1\). Origin top-left; **+x right, +y down** (same as CSS). Engine and renderer must share this.

### 2.5 Walls vs measurement (locked — important)

These are **not** the same. Mixing them makes the science and the tutorial false.

| Object | Physics in v1 | Game feel |
| --- | --- | --- |
| **Empty floor** | Amplitude may sit here | Heatmap |
| **Wall / missing edge** | **Boundary of the graph.** Shift **reflects**: that amplitude stays on the cell and the **coin flips** to the opposite direction (1D: L↔R; 2D: N↔S, E↔W). **No collapse.** | Solid maze |
| **Map edge** | Same as wall (closed box). **No periodic wrap** in v1. | Board edge |
| **Trap** | **Position measurement** restricted to “did we hit a trap?” — see §2.6 | Death / fail |
| **Goal** | Measurement of position; win if outcome ∈ goal set | Exit |
| **Detector / observation** | After **Quantum Walk**, if \(P(\mathrm{obs})\ge\) level `observation_threshold`, **forced full** position measurement | Camera |
| **Phase tile** | After shift, multiply that cell’s amplitudes by \(Z\) or \(S\) | Interference gadget |
| **Player Measure** | Full position measurement on demand | Collapse button |

**v1 rule in one line:** *Walls shape unitary evolution. Traps and goals score after a look. Observation tiles can force that look. Phase tiles do not collapse.*

Do **not** make walls observation points in v1.

### 2.6 When measurement fires (locked)

After each **Quantum Walk**, the backend:

1. Gets new amplitudes from the engine.
2. Computes \(P(p)\) per cell.
3. **Does not** auto-collapse just because probability sits on a trap/goal (that would destroy superposition every time the cloud *touches* a special tile — unplayable and pedagogically wrong).

**Locked observation model (Slice I):**

- **Measure button:** player-controlled after at least one **Quantum Walk** (still **disabled at step 0**).
- **Do not** auto-collapse just because \(P(\mathrm{goal})\) is large.
- **Forced measure:** `step_limit` walks reached, **or** \(P(\mathrm{observation})\ge\) threshold after a walk.
- **Win:** collapsed cell is a **goal**.
- **Lose:** trap, or any non-goal (all puzzles require the goal).
- **Walls** never collapse you. **Phase tiles** never collapse you.
- **Skill:** \(P(\mathrm{goal})\ge\) `target_p_goal` at collapse. The sampled cell is luck.

### 2.7 Measurement math (locked)

1. \(P(p) = \sum_c |\alpha_{p,c}|^2\)
2. Sample \(p^\*\) with a **seeded** RNG (`numpy.random.Generator`)
3. Post-measurement state: all amplitude on \(p^\*\), coin **reset to a fixed state** \(|R\rangle\) (1D) or \(|E\rangle\) (2D) so the game can continue in “collapsed pawn” mode **or** end the level. **v1: level ends on measure.** No post-collapse walking. Cleaner demo.

4. Return `{ cell, probabilities_before, seed_used }`.

### 2.8 Normalization (locked)

After every `step()`, check \(\sum_{p,c}|\alpha|^2 = 1\) within `1e-10`. If drift, **renormalize** and log a warning (should not happen if \(S,C\) are unitary including reflections). Tests fail if drift \(> 1e-8\) before renormalize.

### 2.9 Validation targets (locked)

Must match textbook **1D Hadamard walk** on an infinite line (use a large enough line that boundaries don’t hit for small \(t\)):

- Start at the line centre, coin \(|R\rangle\) (**locked**; this is the usual *right-biased* Hadamard walk, not a symmetric two-sided peak).
- After \(t\) steps, distribution is **not** binomial; mass is **ballistic** (peak away from the origin). The origin may still hold some probability; the **argmax** is not the start cell.
- Destructive interference: two equal-magnitude opposite-phase amplitudes on the same basis state → \(P=0\).
- Qiskit Aer statevector on the **same 1D walk** (small \(n\)) agrees with NumPy within `1e-8`.

---

## 3. Architecture (locked)

Not “frontend vs backend only.” The **quantum engine is the heart**. Backend **coordinates**; it does not reimplement \(U\).

```text
Player
  → Frontend (React)     # see, click, animate, teach
      → Game API (FastAPI)   # rules, levels, session
          → Quantum Engine (NumPy)   # amplitudes, U, measure
          → Qiskit (optional path)  # circuit view + validation
```

This is a **normal** web app plus a **domain engine**:

> Frontend → Game API → Quantum Simulation Engine → NumPy / Qiskit

No extra “quantum microservice.” No database in v1.

### 3.1 Why FastAPI at all if you are solo?

**Locked: yes, keep a Python backend.** Reasons:

- Engine is Python (NumPy + Qiskit). Do not rewrite it in TypeScript for v1.
- Frontend stays dumb: JSON in, JSON out.
- Qiskit stays off the browser (heavy, painful).
- Same process: FastAPI imports `quantum_engine`. One deployable API + static frontend.

**Not locked as “scale.”** For local demo you run two processes (`uvicorn` + `vite`). That is enough.

### 3.2 Dual engine (locked)

| Backend | Role |
| --- | --- |
| **NumPy** | **Source of truth for gameplay.** Every `POST /game/move` uses this. |
| **Qiskit + Aer** | Build the **same** 1D (and later small 2D) walk as a circuit; `statevector` to **validate**; UI **Quantum Circuit View** for education. |

Gameplay **never** waits on IBM Quantum. No real QPU in v1.

If NumPy and Qiskit disagree, **NumPy is what the game uses**; that is a **bug** to fix until they match on 1D.

---

## 4. Repository layout (locked)

```text
quantum-walk-game/
  README.md                 # this file
  quantum_engine/           # no FastAPI, no React
    __init__.py
    state.py                # amplitudes ndarray
    coin.py                 # H, X, Z, S, Grover
    shift.py                # 1D / 2D + reflection
    walk.py                 # apply_gate, propagate, step()=SC
    measurement.py          # Born sample
    qiskit_circuit.py       # circuit for 1D walk + Aer
    validation.py           # known results helpers
  tests/
    test_walk_1d.py
    test_interference.py
    test_measurement.py
    test_qiskit_agreement.py
    test_api.py
    test_campaign.py
    test_walk_2d.py
    test_player_ops.py
  backend/
    main.py                 # FastAPI app
    models.py               # Pydantic
    game.py                 # session + rules
    levels.py               # load JSON
  levels/
    01_superposition.json
    02_interference.json
    03_measurement.json
    04_strategy.json
    05_quantum_strategy.json
  frontend/
    package.json
    src/
      App.tsx
      ResultOverlay.tsx
      Board1D.tsx / Board2D.tsx
      EducationPanel.tsx
      CircuitSidebar.tsx
      gameApi.ts
  requirements.txt
  .gitignore
```

Python 3.11+. Frontend Node 20+.

---

## 5. Module 1 — Quantum engine (what to implement first)

**Question this module answers:** *Given \(|\psi\rangle\) and the player’s operation, what is the new \(|\psi\rangle\)?*

Independent of HTTP and UI. `pytest` is the UI until the API exists.

### 5.1 Deliverable API (Python)

```python
from quantum_engine import QuantumWalk

walk = QuantumWalk.from_level(level_dict)  # or grid_size=10, mode="1d"
walk.initialize(position=5)                # 1D; or (x, y) for 2D
walk.apply_gate("H")                       # coin only
walk.propagate()                           # shift (+ phase tiles)
walk.step()                                # textbook U = S C (tests)
probs = walk.probabilities()               # P(p) flattened or 2D
amps = walk.amplitudes()                   # optional debug
outcome = walk.measure(seed=42)            # cell index / (x,y)
```

Frontend never sees Hadamard entries.

### 5.2 State representation (locked)

- **1D:** `amplitudes.shape == (N, 2)` complex128, axis 1 = coin R, L.
- **2D:** `amplitudes.shape == (H, W, 4)` complex128, coin order `N, E, S, W`.

Unwalkable cells (walls) have **zeros** and are never written except that reflection happens on the **walkable** neighbor.

### 5.3 Files

| File | Responsibility |
| --- | --- |
| `state.py` | Allocate, initialize, copy, norm |
| `coin.py` | Apply \(C\) in-place |
| `shift.py` | Apply \(S\) with reflection |
| `walk.py` | `step`, `probabilities`, facade |
| `measurement.py` | Sample + collapse |
| `qiskit_circuit.py` | 1D circuit, Aer statevector, circuit qasm/draw data |
| `validation.py` | Reference distributions / helpers |

### 5.4 Tools (engine)

- Python 3.11
- NumPy (complex arrays)
- Qiskit + Qiskit Aer (circuit + statevector)
- pytest

---

## 6. Module 2 — Game backend (rules, not physics)

**Question:** *Is the move legal, what level is this, did they win, what JSON does the UI need?*

Think: **game master**. Engine = physics.

### 6.1 Flow (locked)

```text
POST /game/move  { action: "H"|"X"|"Z"|"S"|"quantum_walk" }
  → coin: walk.apply_gate(action)  (does not consume step_limit)
  → walk: walk.propagate(); if steps hit limit or observation: measure
  → return GameStateDTO
```

```text
POST /game/measure
  → walk.measure()
  → set status won | lost
  → return cell + probabilities_before
```

### 6.2 Session (locked, v1)

**In-memory dict** `session_id → GameSession`. No SQLite, no Redis, no JWT.

Restarting the API wipes games. Fine for demo.

`session_id` = UUID issued by `POST /game/start`.

### 6.3 HTTP API (locked)

Base URL: `http://127.0.0.1:8000`

CORS: allow `http://localhost:5173`.

| Method | Path | Body | Meaning |
| --- | --- | --- | --- |
| `GET` | `/health` | — | `{"ok": true}` |
| `GET` | `/levels` | — | list `{id, title, order}` |
| `GET` | `/levels/{id}` | — | full level JSON (no answers) |
| `POST` | `/game/start` | `{ "level_id": "01_superposition" }` | new session |
| `POST` | `/game/move` | `{ "session_id", "action": "H"\|"X"\|"Z"\|"S"\|"quantum_walk" }` | coin or shift |
| `POST` | `/game/measure` | `{ "session_id" }` | collapse |
| `GET` | `/game/state?session_id=` | — | current DTO |
| `GET` | `/game/circuit?session_id=` | — | Qiskit draw payload (1D or “unsupported”) |

**Actions:** coin gates and `quantum_walk`. No undo. Reset = `POST /game/start` again. Levels may set `allowed_ops` and `op_limit`.

### 6.4 GameState DTO (locked)

```json
{
  "session_id": "uuid",
  "level_id": "01_superposition",
  "mode": "1d",
  "width": 11,
  "height": 1,
  "cells": {
    "walls": [],
    "traps": [2],
    "goals": [8],
    "observations": [],
    "phase_gates": []
  },
  "probabilities": [0, 0.12, 0.38, ...],
  "probabilities_2d": null,
  "step": 3,
  "step_limit": 8,
  "status": "playing",
  "collapsed_cell": null,
  "p_goal": 0.41,
  "p_trap": 0.05,
  "p_observation": 0.0,
  "target_p_goal": 0.7,
  "objective_met": false,
  "last_op": "H",
  "explanation": "H applied: the coin was put into superposition.",
  "allowed_ops": ["H", "X"],
  "ops_used": 1,
  "op_limit": null,
  "history": ["H"],
  "message": null,
  "score": null
}
```

`status`: `playing` | `won` | `lost` | `measured` (if we ever need; v1 use won/lost only after measure).

`probabilities` for 1D length `N`. For 2D, `probabilities_2d` is row-major `height × width` nested arrays; `probabilities` may be flattened the same order.

**Always send `p_goal` and `p_trap` while playing** so the UI can teach skill vs luck. After collapse, those are the **pre-measure** values plus `collapsed_cell`.

### 6.5 Scoring (locked)

- **Primary skill metric:** `p_goal` at the moment of measure (show large).
- **Win/loss this run:** sampled cell ∈ goals / else lose if goals defined.
- **Score number:** `round(100 * p_goal)` + `+10` on goal collapse + leftover walks + **`+25` if `p_goal` met `target_p_goal`**. Luck is visible; skill is meeting the target.

No leaderboard v1.

### 6.6 Tools (backend)

- FastAPI
- Pydantic v2
- Uvicorn
- JSON files on disk for levels

---

## 7. Module 3 — Frontend (make the wave visible)

**Job:** maze + heatmap + controls + collapse animation + short explanations. Not a 3D quantum art piece.

### 7.1 Stack (locked)

- React 18 + TypeScript + Vite
- Tailwind CSS
- HTML **Canvas** for the grid heatmap (not Three.js, not SVG as the main board — SVG OK for icons)
- Framer Motion for HUD / collapse overlay only
- `fetch` to FastAPI; no Redux; React state + a small `gameApi.ts`

### 7.2 Screens (locked v1)

1. **Landing** — title, one sentence, Play, How it works  
2. **Level select** — 5 levels  
3. **Play** — board, **controls under the board**, HUD, LEARN + circuit sidebar; **win/loss/campaign overlay** after collapse  
4. **How it works** — static education (gates, walk, interference, collapse, walls ≠ cameras)

No accounts.

### 7.3 Play layout (locked)

```text
┌──────────────────────────────────────────────┐
│  QUANTUM WALK     Level title                │
│  Walks 1/6  Gate H  Goal ≥70%  Current 0%    │
│                                              │
│  [ canvas maze / 1D bars ]    [ LEARN      ] │
│                               [ circuit    ] │
│  QUANTUM CONTROLS                            │
│  [H][X][Z][S]                                │
│  [Quantum Walk →] [Measure] [Restart]        │
└──────────────────────────────────────────────┘
```

**Locked:** controls are **immediately under the map** on 1D and 2D. Do not put them under the tall circuit column.

- Tiles: brightness ∝ \(P(p)\); **cyan outline = current peak P**.
- Walls: solid, no glow.
- Goals: dashed gold.
- Traps: hatched, not only color.
- Observation: violet dotted.
- Phase tile: small cyan ring.
- After measure: pawn on `collapsed_cell`; other tiles dim.

### 7.4 Controls copy (locked)

| Button | Player-facing name | What happens |
| --- | --- | --- |
| H X Z S | **Quantum Controls** | Coin unitaries (level may hide some) |
| Quantum Walk | **Quantum Walk →** | Shift only |
| Measure | **Measure (collapse)** | Born sample, end level |
| Restart | **Restart** / Try Again | `POST /game/start` on the **current** id |
| Next Level | **Next Level →** | Fresh start on the next `order` |
| Play Again | **Play Again** | Fresh start on the first `order` |
| Back to Levels | **Back to Levels** | Landing list |

No WASD walking.

### 7.5 Animation (locked)

- After move: request new probabilities, **lerp tile intensities** 200–300ms.
- After measure: CSS collapse flash on the board, **in-page result stays visible**, then **~1.5s pause**, then fade/scale overlay (respect `prefers-reduced-motion`: skip flash, pulse, and overlay motion).
- Next level: short `level-enter` fade, then the new session.

### 7.5b Result overlay (locked, Slice J)

Centered modal appears **after** the collapse has been painted — not in the same frame as Measure. Variants: win, loss, campaign complete. Progression ids come from `GET /levels` sort by `order`. Never hard-code “level 5” in the overlay — last in that list is the campaign end. Controls stay off during the pause and while the modal is open.

### 7.6 Circuit view (locked)

On **1D levels**, sidebar shows the **accumulated Qiskit circuit of gates the player actually applied** (H/X/Z/S and shift \(S\)), capped for drawing.

2D: Grover coin; Qiskit grid circuit still unsupported; the sidebar lists the same op history in text.

### 7.7 Tools not used in v1

Three.js, next.js, auth, PWA mandatory, native apps.

---

## 8. Module 4 — Education & game design (solo, do this on paper first)

Without this, the site is “press button, squares glow.”

### 8.1 Learning outcomes (locked)

After 10 minutes the player should be able to say:

1. I am on **many tiles at once** (amplitudes).
2. Two paths can **cancel** (interference).
3. I only **know** the tile after **Measure**.
4. I try to make **P(goal)** large **before** I look (skill = meet the target).
5. I **chose gates** that changed the state (H mix, X flip, Z/S phase), then walked.

### 8.2 Levels (locked — ship these five)

Stored in `/levels/*.json`. Each file may set `target_p_goal`, `allowed_ops`, `op_limit`, `observations`, `phase_gates`, `observation_threshold`.

**Level 1 — Superposition** (`01_superposition`)  
Mode `1d`, 11 cells, start center, goals at both ends, `step_limit` 6. Teach **H** then **Quantum Walk** (the split). **X** is available so a directed heading can stack an end — mixing is a choice. Measure off until one walk.

**Level 2 — Interference** (`02_interference`)  
Mode `1d`, trap at the start, goal at cell 16, **Z** unlocked, cameras on the naive east path so a pawn-walk is looked at. Teach phase.

**Level 3 — Measurement** (`03_measurement`)  
Mode `2d`, 7×7 maze, walls, goal, trap, observation tile. Copy: *Walls bounce. Cameras look. Measure when P(goal) is high.*

**Level 4 — Quantum Maze** (`04_strategy`)  
Mode `2d`, pillar, two routes. Grover **H** to turn corners. Title in UI: Quantum Maze. `step_limit` **10** (shortest reflecting path around the pillar is 10 shifts; do not teleport).

**Level 5 — Quantum Strategy** (`05_quantum_strategy`)  
Tighter `op_limit` + `target_p_goal` (50% on this map; cameras block a 100% pawn-walk). Limited gates.

### 8.3 Difficulty

1 → 2 → 3 → 4 → 5 only. No branching campaign.

### 8.4 Demo script (2–3 min, locked outline)

1. Classical vs this: pawn vs cloud (10s).  
2. Level 1: one move, split (20s).  
3. Level 2: several moves, show origin dip; mention amplitudes add (40s).  
4. Measure: collapse (15s).  
5. Engine: NumPy is the walk; Qiskit circuit of 1D step (20s).  
6. Level 5: camera, limited gates, hit the P(goal) target (30s).

### 8.5 Design tools

Figma optional; a paper grid is enough. Do not block coding on Figma.

---

## 9. Module 5 — Tests, integration, deploy

### 9.1 Tests (locked minimum)

- `test_walk_1d.py` — norm 1; ballistic not binomial (e.g. after 10 steps on N=51, P(origin) < P near edge).
- `test_interference.py` — manual two-amplitude cancel.
- `test_measurement.py` — 10k samples vs P, chi-square or max-error; seeded replay identical.
- `test_qiskit_agreement.py` — 1D t=1,2,3 vs Aer; player-ops circuit has H, Z, shift.
- `test_api.py` — start, H, quantum_walk, measure, step-0 measure rejected, camera force-measure, L5 target.
- `test_player_ops.py` — H+propagate matches `step()`; X walks left; Z changes later P.
- `test_campaign.py` — five levels in order; after 8 textbook steps \(P(16)>P(10)\).

Frontend: no Cypress in v1; manual play of 5 levels. Measure off at step 0. Controls under the map.

### 9.2 Deploy (when local works)

- Frontend: Vercel or Netlify, `VITE_API_URL` to API.
- Backend: Render or Railway, `uvicorn backend.main:app`.
- CORS: add production frontend origin.

Do not deploy until Level 1 is playable locally.

---

## 10. Level JSON schema (locked)

```json
{
  "id": "01_superposition",
  "title": "Superposition",
  "order": 1,
  "mode": "1d",
  "width": 11,
  "height": 1,
  "step_limit": 6,
  "target_p_goal": 0.7,
  "allowed_ops": ["H", "X"],
  "start": { "x": 5, "y": 0, "coin": "R" },
  "walls": [],
  "traps": [],
  "goals": [ { "x": 0, "y": 0 }, { "x": 10, "y": 0 } ],
  "copy": {
    "short": "Move left and right at once.",
    "detail": "H mixes the coin; Quantum Walk shifts. X flips heading."
  }
}
```

2D: `"mode": "2d"`, `height` > 1, `walls` list of `{x,y}`, coin start `"E"`.

Coordinates: integers, `0 ≤ x < width`, `0 ≤ y < height`. Walls cannot overlap start/goal/trap. Engine validates on load.

---

## 11. Components map (8 pieces)

| # | Component | Lives in |
| --- | --- | --- |
| 1 | Quantum State Manager | `quantum_engine/state.py` |
| 2 | Walk operator \(SC\) | `coin.py` + `shift.py` + `walk.py` |
| 3 | Measurement & collapse | `measurement.py` + `backend/game.py` win/lose |
| 4 | Game rules | `backend/game.py` |
| 5 | Level manager | `backend/levels.py` + `levels/*.json` |
| 6 | Visualization | `frontend` canvas |
| 7 | API | `backend/main.py` |
| 8 | Tests & deploy | `tests/` + host config later |

---

## 12. v1 feature freeze

### Must have

- [x] NumPy 1D walk + tests  
- [x] NumPy 2D walk + walls reflect  
- [x] Measure (engine collapse; win/lose is Slice C)  
- [x] FastAPI session API + win/lose  
- [x] React play screen, heatmap, strategy controls  
- [x] Five levels + sidebar copy  
- [x] `P(goal)` / `P(trap)` / target HUD  
- [x] Qiskit 1D circuit view + Aer agreement test  
- [x] Collapse animation (pawn + dim + CSS flash)  
- [x] Player coin gates separate from walk (Slice I)  
- [x] Controls directly under the board (1D and 2D)  
- [x] Vite `/api`-style proxy of `/levels` `/game` `/health` → `:8000`  
- [x] Win / loss / campaign overlays + Next Level (Slice J)  

### Nice-to-have (after must-have only)

- Classical vs quantum comparison chart  
- Phase as hue  
- Probability-over-time graph  
- Decoherence slider  
- Level editor  
- Undo  
- IBM QPU button  
- SQLite scores  
- Detectors that auto-measure (done in Slice I as observation tiles, thresholded)  

### Explicitly out of v1

- Multiplayer, accounts, payments  
- Three.js  
- Rewriting the engine in the browser  
- Walls-as-measurement  
- Choosing Left/Right as the default move  

---

## 13. Slice plan (solo order — start here)

Do not “finish Qiskit” before a visible 1D line exists. After each slice, you should be able to **run something**.

| Slice | Done when |
| --- | --- |
| **A** | **Done.** `QuantumWalk` 1D: `initialize`, `step`, `probabilities`, pytest green |
| **B** | **Done.** `measure(seed)` + collapse tests |
| **C** | **Done.** FastAPI `/game/start` + `/game/move` + `/game/measure` on level 1 JSON |
| **D** | **Done.** Vite app: 1D canvas, three buttons, talks to API |
| **E** | **Done.** Qiskit 1D circuit + Aer agreement + sidebar |
| **F** | **Done.** 2D Grover walk + reflecting walls + playable 7×7 maze |
| **G** | **Done.** Levels 2 and 4, LEARN panel, collapse polish |
| **I** | **Done.** Coin vs walk, targets, cameras, phase tiles, level 5, controls under map, Vite proxy |
| **J** | **Done.** Win/loss/campaign overlays; Next Level from API order |
| **H** | Deploy if needed |

**Next action:** Slice H — deploy (optional).

---

## 14. Coding conventions (locked)

- Engine: no prints in library code; raise `QuantumEngineError`.
- Complex dtype: `np.complex128`.
- RNG only in `measurement.py` (and tests).
- API never returns raw complex numbers in v1 (optional later `debug=true`). Probabilities are floats 0–1, JSON-safe.
- TypeScript: strict.
- No secrets. No API keys required.

---

## 15. How this differs from a fake maze

| Fake | This project |
| --- | --- |
| Random teleport + CSS blur | \(U=SC\) on \(\alpha\) |
| Probabilities updated ad hoc | \(P=\|\psi\|^2\) only when needed |
| Wall = death | Wall = reflection |
| Qiskit-only slow loop | NumPy gameplay, Qiskit proof + teaching |
| “Frontend/backend” only | Engine is a first-class module |

---

## 16. Run

**Works now (Slices A–G + I + J)**

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest
uvicorn backend.main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

---

## 17. Decisions log (quick reference)

| Topic | Decision |
| --- | --- |
| Team | Solo; modules not people |
| Engine language | Python |
| Gameplay sim | NumPy |
| Quantum credibility | Qiskit Aer + circuit UI; no QPU v1 |
| Web | FastAPI + React + Vite + Tailwind + Canvas |
| DB | None v1 |
| 1D coin | Hadamard, R=\|0⟩, L=\|1⟩ |
| 2D coin | Grover 4-dir |
| Walls | Reflect + coin flip; no measure |
| Traps/goals | Scored **after** Measure (or forced at step_limit) |
| Auto-measure on overlap | **No** |
| Post-collapse play | **No**; level ends |
| Play layout | Board, then controls; LEARN + circuit sidebar |
| Dev browser | Vite proxies API paths; default `VITE_API_URL` empty |
| Default move | Coin gate(s), then Quantum Walk (shift) |
| Measure at step 0 | Disabled |
| Auto-measure on high P(goal) | **No** |
| Observation tiles | Force measure if \(P(\mathrm{obs})\ge\) threshold (not only \(P=1\)) |
| Post-collapse UI | Modal is primary; LEARN + in-page copy stay |
| Next level | Next id by `GET /levels` `order`; last win = campaign complete |
| Wraparound grid | **No** |
| 3D | **No** |
| Browser WASM engine | **No** v1 |

## 18. Backlog (confirm before a big rewrite)

1. **Deploy (H)** — Vercel/Netlify frontend + Render/Railway API; set `VITE_API_URL`; production CORS.
2. **README drift** — keep this log, §2.4 directions, and checkboxes in sync after every slice.
3. **2D Qiskit** — still unsupported on mazes by design. Add a Grover+shift circuit only if asked. NumPy stays source of truth.
4. **Level tuning** — if P(goal) feels unfair, change JSON targets / cameras, not the engine.
5. **UX** — phase-as-hue, classical-vs-quantum chart, undo, sound, mobile layout, blurbs from API `copy`.
6. **Python** — engine/API ran on 3.14 here; FastAPI `TestClient` may warn about httpx. Prefer versions in `requirements.txt`.
7. **Uvicorn `--reload`** has failed to pick up route changes; restart the API if `/game/circuit` looks stubbed.
8. Do **not** mix wall reflection with measurement, or put a Schrödinger solver on the server per frame.

Slices A–G, I, and J are in the repo. Next: Slice H (deploy) if you want it online.
