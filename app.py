"""
Bloch Sphere & Qubit State Evolution — Qiskit (math) + PyVista + Panel (3D)

Grounded in ~/薦家/布球/ distilled notes:
  - 布球_distilled.md     : Bloch geometry, PyVista Plotter API, evolution trail
  - 5布球態演化維問.py     : proven off-screen Plotter, sphere opacity, axes, trail
  - 總結邏輯閘.md         : |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩

Rule (qbit-viz / viz-dboard): 3D — including Bloch spheres — uses pyvista + panel
only. Qiskit supplies the state math; no matplotlib-backed renderer is used.

Start:  cd ~/薦家/布球/bloch-evolution-viz && panel serve app.py --show
"""
import os

os.environ.setdefault("PYVISTA_OFF_SCREEN", "true")  # before importing pyvista

import numpy as np
import panel as pn
import pyvista as pv
from qiskit import QuantumCircuit
from qiskit.quantum_info import Pauli, Statevector

pn.extension("vtk")

# ---------- Bloch math (Qiskit owns the state; PyVista only draws) ----------
SPECIAL_STATES = {
    "|0⟩  north": (0.0, 0.0),
    "|1⟩  south": (np.pi, 0.0),
    "|+⟩  +X": (np.pi / 2, 0.0),
    "|−⟩  -X": (np.pi / 2, np.pi),
    "|+i⟩ +Y": (np.pi / 2, np.pi / 2),
    "|−i⟩ -Y": (np.pi / 2, 3 * np.pi / 2),
}

ROTATIONS = {
    "Rx": lambda qc, angle: qc.rx(angle, 0),
    "Ry": lambda qc, angle: qc.ry(angle, 0),
    "Rz": lambda qc, angle: qc.rz(angle, 0),
}


def initial_state(theta, phi):
    """|ψ⟩ = cos(θ/2)|0⟩ + e^{iφ} sin(θ/2)|1⟩ as a normalized Statevector."""
    return Statevector(
        np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)], dtype=complex)
    )


def bloch_vector(state):
    """Expectation values of X/Y/Z — pure states give |r| = 1."""
    return np.array(
        [state.expectation_value(Pauli(p)).real for p in ("X", "Y", "Z")], dtype=float
    )


def evolution_path(gate, total_angle, frames=60, start=(0.0, 0.0)):
    """Apply the rotation in exactly `frames` equal steps (frames+1 samples).

    The old implementation applied U^(frames+1) and overshot by one step.
    Here step = total_angle / frames and the operator is applied only between
    samples, so the final sample is exactly the requested total angle.
    """
    state = initial_state(*start)
    step_qc = QuantumCircuit(1)
    ROTATIONS[gate](step_qc, total_angle / frames)

    points, states = [], []
    for i in range(frames + 1):
        states.append(state)
        points.append(bloch_vector(state))
        if i < frames:
            state = state.evolve(step_qc)
    return np.array(points), states


# ---------- PyVista scene ----------
_current_plotter = None


def make_scene(points, show_trail=True):
    """Build the Bloch sphere scene; close the previous Plotter to avoid leaks."""
    global _current_plotter
    if _current_plotter is not None:
        _current_plotter.close()
        _current_plotter = None

    p = pv.Plotter(off_screen=True, window_size=[700, 700])
    p.set_background("#0a0a1a")

    # translucent sphere + wireframe grid (per distilled notes)
    p.add_mesh(pv.Sphere(radius=1.0, theta_resolution=32, phi_resolution=24),
               color="lightblue", opacity=0.12)
    p.add_mesh(pv.Sphere(radius=1.001, theta_resolution=12, phi_resolution=6),
               style="wireframe", color="gray", opacity=0.25)

    # axes (length 1.5)
    for end, color in [((1.5, 0, 0), "red"), ((0, 1.5, 0), "green"), ((0, 0, 1.5), "blue")]:
        p.add_mesh(pv.Line((0, 0, 0), end), color=color, line_width=2)

    # equator
    t = np.linspace(0, 2 * np.pi, 100)
    ring = pv.PolyData(np.column_stack([np.cos(t), np.sin(t), np.zeros_like(t)]))
    ring.lines = np.hstack([[len(t)], np.arange(len(t)), [0]])
    p.add_mesh(ring, color="magenta", line_width=2, opacity=0.7)

    # evolution trail (orange per 布球Util.py)
    if show_trail and len(points) > 1:
        path = pv.PolyData(points)
        path.lines = np.hstack([[len(points)], np.arange(len(points))])
        p.add_mesh(path, color="orange", line_width=3)
        p.add_points(points, color="orange", point_size=6)

    # state vector: unit direction + magnitude, so add_arrows does not double-scale
    vec = points[-1]
    norm = float(np.linalg.norm(vec))
    if norm > 1e-9:
        direction = (vec / norm).reshape(1, 3)
        p.add_arrows(np.zeros((1, 3)), direction, mag=norm, color="gold")

    # camera setup proven in 5布球態演化維問.py
    p.camera.position = (2.5, 2.5, 2.0)
    p.camera.focal_point = (0.0, 0.0, 0.0)
    p.camera.up = (0.0, 0.0, 1.0)
    p.camera.zoom(1.1)
    p.add_axes()

    _current_plotter = p
    return p


# ---------- Panel UI ----------
FRAMES = 60
gate = pn.widgets.RadioButtonGroup(name="旋轉閘", options=list(ROTATIONS),
                                   value="Ry", button_type="primary")
angle = pn.widgets.FloatSlider(name="總旋轉角 θ (rad)", start=0, end=2 * np.pi,
                               step=0.05, value=np.pi / 2)
# Panel 1.10 Player supports name/start/end/value/interval only (no loop/button_type).
frame = pn.widgets.Player(name="演化幀", start=0, end=FRAMES, value=FRAMES,
                          interval=120)
start_state = pn.widgets.Select(name="起始態", options=list(SPECIAL_STATES),
                                value="|0⟩  north")
show_trail = pn.widgets.Checkbox(name="顯示演化軌跡", value=True)


@pn.depends(gate, angle, frame, start_state, show_trail)
def scene_view(g, a, f, s, trail):
    pts, _ = evolution_path(g, a, frames=FRAMES, start=SPECIAL_STATES[s])
    plotter = make_scene(pts[: f + 1], show_trail=trail)
    # Panel VTK pane takes the render window, not the Plotter (Panel 1.x)
    return pn.pane.VTK(plotter.ren_win, width=650, height=650)


@pn.depends(gate, angle, frame, start_state)
def state_view(g, a, f, s):
    pts, states = evolution_path(g, a, frames=FRAMES, start=SPECIAL_STATES[s])
    x, y, z = pts[f]
    alpha, beta = states[f].data
    theta = np.arccos(np.clip(z, -1.0, 1.0))
    phi = np.arctan2(y, x)
    p0, p1 = abs(alpha) ** 2, abs(beta) ** 2
    return pn.pane.Markdown(
        f"### 當前狀態 (frame {f}/{FRAMES})\n\n"
        f"- Bloch 向量: `({x:.3f}, {y:.3f}, {z:.3f})`, |r| = {np.linalg.norm(pts[f]):.3f}\n"
        f"- θ = {theta:.3f}, φ = {phi:.3f}\n"
        f"- α = {alpha:.4f}, β = {beta:.4f}\n"
        f"- P(|0⟩) = {p0:.3f}, P(|1⟩) = {p1:.3f}"
    )


template = pn.template.FastListTemplate(
    title="Bloch Sphere · Qubit Evolution (Qiskit + PyVista + Panel)",
    sidebar=[gate, angle, frame, start_state, show_trail],
    main=[scene_view, state_view],
    accent="#00d4aa",
)
template.servable()
