"""1D Hadamard walk as a Qiskit circuit. Gameplay still uses NumPy; this is validation + teaching."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister
from qiskit.circuit.library import UnitaryGate
from qiskit_aer import AerSimulator

from quantum_engine.errors import QuantumEngineError
from quantum_engine.state import COIN_L, COIN_R

COIN_QUBITS = 1


@dataclass(frozen=True)
class CircuitView:
    supported: bool
    message: str
    diagram: str
    qasm: str | None
    steps_shown: int
    n_qubits: int
    n_sites: int


def position_qubits(n_sites: int) -> int:
    if n_sites < 2:
        raise QuantumEngineError("Need at least 2 sites for a circuit.")
    return math.ceil(math.log2(n_sites))


def n_qubits_1d(n_sites: int) -> int:
    return position_qubits(n_sites) + COIN_QUBITS


def basis_index(position: int, coin: int) -> int:
    """Qubit 0 = coin, remaining bits = position (little-endian)."""
    return int(coin) + (int(position) << 1)


def numpy_amplitudes_to_vector(amplitudes: np.ndarray) -> np.ndarray:
    n_sites = amplitudes.shape[0]
    vec = np.zeros(2 ** n_qubits_1d(n_sites), dtype=np.complex128)
    for x in range(n_sites):
        vec[basis_index(x, COIN_R)] = amplitudes[x, COIN_R]
        vec[basis_index(x, COIN_L)] = amplitudes[x, COIN_L]
    return vec


def vector_to_probabilities(vector: np.ndarray, n_sites: int) -> np.ndarray:
    probs = np.zeros(n_sites, dtype=np.float64)
    for x in range(n_sites):
        amp_r = vector[basis_index(x, COIN_R)]
        amp_l = vector[basis_index(x, COIN_L)]
        probs[x] = float(np.abs(amp_r) ** 2 + np.abs(amp_l) ** 2)
    return probs


def shift_unitary(n_sites: int) -> np.ndarray:
    """Permutation matching NumPy reflecting shift, padded to 2^{n_qubits}."""
    dim = 2 ** n_qubits_1d(n_sites)
    matrix = np.zeros((dim, dim), dtype=np.complex128)
    used = set()
    for x in range(n_sites):
        src_r = basis_index(x, COIN_R)
        src_l = basis_index(x, COIN_L)
        dst_r = basis_index(x + 1, COIN_R) if x + 1 < n_sites else basis_index(x, COIN_L)
        dst_l = basis_index(x - 1, COIN_L) if x - 1 >= 0 else basis_index(x, COIN_R)
        matrix[dst_r, src_r] = 1.0
        matrix[dst_l, src_l] = 1.0
        used.add(src_r)
        used.add(src_l)
    for i in range(dim):
        if i not in used:
            matrix[i, i] = 1.0
    return matrix


def walk_circuit(n_sites: int, steps: int) -> QuantumCircuit:
    """`steps` applications of U = S H. steps=0 yields an empty circuit (initial |ψ⟩)."""
    if steps < 0:
        raise QuantumEngineError("steps must be >= 0.")
    return circuit_from_ops(n_sites, ["H", "SHIFT"] * steps)


def circuit_from_ops(n_sites: int, ops: list[str]) -> QuantumCircuit:
    """Build the 1D circuit that matches player coin gates + reflecting shift."""
    n_pos = position_qubits(n_sites)
    coin = QuantumRegister(1, "coin")
    pos = QuantumRegister(n_pos, "pos")
    qc = QuantumCircuit(coin, pos, name="dtqw")
    shift = UnitaryGate(shift_unitary(n_sites), label="S")
    for raw in ops:
        op = raw.upper()
        if op == "H":
            qc.h(coin[0])
        elif op == "X":
            qc.x(coin[0])
        elif op == "Z":
            qc.z(coin[0])
        elif op == "S":
            qc.s(coin[0])
        elif op == "SHIFT":
            qc.append(shift, list(coin) + list(pos))
        else:
            raise QuantumEngineError(f"Unknown circuit op: {raw}")
    return qc


def one_step_circuit(n_sites: int) -> QuantumCircuit:
    return walk_circuit(n_sites, steps=1)


def _qasm(circuit: QuantumCircuit) -> str | None:
    try:
        from qiskit.qasm2 import dumps

        return dumps(circuit)
    except Exception:
        try:
            return circuit.qasm()
        except Exception:
            return None


def simulate_probabilities(n_sites: int, start: int, coin: str, steps: int) -> np.ndarray:
    """Aer statevector simulation of the same walk NumPy implements."""
    coin_bit = 0 if coin.upper() == "R" else 1
    dim = 2 ** n_qubits_1d(n_sites)
    initial = np.zeros(dim, dtype=np.complex128)
    initial[basis_index(start, coin_bit)] = 1.0 + 0.0j

    qc = QuantumCircuit(n_qubits_1d(n_sites))
    qc.initialize(initial, qc.qubits)
    if steps:
        qc.compose(walk_circuit(n_sites, steps), inplace=True)
    qc.save_statevector()

    result = AerSimulator(method="statevector").run(qc).result()
    vector = np.asarray(result.get_statevector(), dtype=np.complex128)
    return vector_to_probabilities(vector, n_sites)


def circuit_view(
    n_sites: int,
    steps: int,
    step_limit: int,
    ops: list[str] | None = None,
) -> CircuitView:
    history = list(ops) if ops is not None else (["H", "SHIFT"] * max(0, steps))
    cap = max(step_limit * 3, 12)
    shown_ops = history[-cap:] if len(history) > cap else history
    shifts = sum(1 for op in history if op.upper() == "SHIFT")
    if not shown_ops:
        n_pos = position_qubits(n_sites)
        coin = QuantumRegister(1, "coin")
        pos = QuantumRegister(n_pos, "pos")
        circuit = QuantumCircuit(coin, pos, name="dtqw")
        message = (
            "Empty circuit: apply a coin gate (H, X, Z, S), then Quantum Walk (shift S). "
            "This diagram tracks the gates you actually use."
        )
    else:
        circuit = circuit_from_ops(n_sites, shown_ops)
        message = (
            f"Your 1D circuit so far ({shifts} shift(s)). "
            "Coin gates act on qubit 0; S is the reflecting walk shift."
        )
    diagram = str(circuit.draw(output="text", fold=-1))
    return CircuitView(
        supported=True,
        message=message,
        diagram=diagram,
        qasm=_qasm(circuit),
        steps_shown=shifts if history else 0,
        n_qubits=n_qubits_1d(n_sites),
        n_sites=n_sites,
    )
