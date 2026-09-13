export function HowItWorks() {
  return (
    <article className="max-w-2xl space-y-6 text-slate-300">
      <header>
        <h2 className="text-xl text-slate-100">How it works</h2>
        <p className="mt-2 text-sm text-slate-400">
          This page is the general tutorial. Puzzle hints live in LEARN on each level.
        </p>
      </header>

      <section>
        <h3 className="font-mono text-xs tracking-widest text-cyan">YOUR OBJECTIVE</h3>
        <p className="mt-2">
          You are controlling a <strong className="text-slate-100">quantum wave</strong>, not a
          classical pawn. Your job is to change the coin, then walk the wave, until enough
          probability sits on the goal.
        </p>
        <p className="mt-2">
          Each level shows a target such as <span className="font-mono text-gold">Goal ≥ 50%</span>.
          Steer the state until <span className="font-mono text-cyan">P(goal) ≥ target</span>, then
          Measure. The P(goal) number is computed from the amplitudes, not guessed.
        </p>
      </section>

      <section>
        <h3 className="font-mono text-xs tracking-widest text-cyan">HOW TO PLAY</h3>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm">
          <li>Look at the map: gold goal, red trap, walls, violet cameras, cyan phase tiles.</li>
          <li>Choose a gate if you want to change the coin (H, X, Z, or S).</li>
          <li>Press Quantum Walk → to propagate the wave.</li>
          <li>Watch P(goal) in the HUD.</li>
          <li>On 2D mazes, hover a cell to read its exact P.</li>
          <li>Try to get P(goal) above the target.</li>
          <li>When ready, Measure. The wave collapses and the level ends.</li>
        </ol>
      </section>

      <details className="how-details" open>
        <summary>H — SUPERPOSITION / MIXING</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>H changes the coin (direction) state. It does not move the wave.</p>
          <p>
            <strong className="text-slate-100">1D:</strong> Hadamard mixes left and right.
          </p>
          <p>
            <strong className="text-slate-100">2D:</strong> the H button is the Grover coin over
            N/E/S/W. It is not a 1D Hadamard drawn on a grid.
          </p>
          <p>
            Usual pair: <span className="font-mono text-cyan">H → Quantum Walk</span>. H can split
            probability across directions so the wave explores more than one path. Timing matters —
            mashing H is not automatically better, because later steps can interfere.
          </p>
        </div>
      </details>

      <details className="how-details">
        <summary>X — DIRECTION FLIP</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>X flips the coin labels. Probability on each cell stays put until you walk.</p>
          <p>
            <strong className="text-slate-100">1D:</strong> swaps left and right.
          </p>
          <p>
            <strong className="text-slate-100">2D:</strong> swaps N↔S and E↔W.
          </p>
          <p>
            Use <span className="font-mono text-cyan">X → Quantum Walk</span> to send a packet the
            other way. Used at the wrong time, it can walk probability away from the goal.
          </p>
        </div>
      </details>

      <details className="how-details">
        <summary>Z — PHASE</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>
            Z is like changing the sign of part of the wave so that when paths meet again, they can
            reinforce or cancel.
          </p>
          <p>
            The heatmap may not jump when you press Z. Phase shows up later, when amplitudes overlap.
          </p>
          <p>
            <strong className="text-slate-100">2D:</strong> Z phases the south and west components
            (this project&apos;s convention).
          </p>
        </div>
      </details>

      <details className="how-details">
        <summary>S — PHASE ROTATION</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>
            S is another phase gate (a quarter-turn, +i, on part of the coin). Like Z, it usually
            does not change P at the moment you press it.
          </p>
          <p>
            It is a strategy tool for later interference, not a movement key. On 2D, S phases south
            and west, matching Z&apos;s pair of directions.
          </p>
        </div>
      </details>

      <details className="how-details" open>
        <summary>QUANTUM WALK — MOVE THE WAVE</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>
            Quantum Walk is the shift. It is not a coin gate. Each coin component steps to a
            neighbor: N north (up), E east, S south, W west. Walls and edges reflect (stay and flip
            the coin). They do not collapse you.
          </p>
        </div>
      </details>

      <details className="how-details" open>
        <summary>MEASURE — LOOK AT THE WAVE</summary>
        <div className="mt-2 space-y-2 text-sm">
          <p>
            Before Measure you do not have one classical tile. The board is a probability cloud.
            Measure samples a cell from the real distribution and collapses the wave.
          </p>
          <p>High probability means a higher chance of being measured there. It does not guarantee the result.</p>
          <p>
            <strong className="text-gold">Beginner Assist</strong> (game only): if P(goal) has
            reached the level target, you get an extra 75% game-level chance to complete the level.
            That roll does not change amplitudes, P(goal), or the Born-rule sample. The measured
            cell stays genuine.
          </p>
        </div>
      </details>

      <section>
        <h3 className="font-mono text-xs tracking-widest text-cyan">HOW PROBABILITY WORKS</h3>
        <p className="mt-2 text-sm">
          Each cell&apos;s probability is the squared size of its amplitudes, added over coin
          directions:
        </p>
        <p className="mt-2 font-mono text-sm text-gold">P(cell) = Σ |amplitude|² over directions</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          <li>All cell probabilities add to 100%.</li>
          <li>A brighter cell holds more probability.</li>
          <li>P(goal) is the total currently on goal tiles.</li>
          <li>P(trap) is the total currently on trap tiles.</li>
        </ul>
      </section>

      <section>
        <h3 className="font-mono text-xs tracking-widest text-cyan">INTERFERENCE</h3>
        <p className="mt-2 text-sm">
          Paths can meet again. Their amplitudes can reinforce (constructive) or cancel
          (destructive). That is why a gate can look quiet now and matter several walks later.
        </p>
      </section>
    </article>
  );
}
