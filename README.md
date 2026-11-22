> **RETIRED — 已整合進單一 app。** 本獨立 demo 的 3D Bloch 態演化已併入
> `~/薦家/布球/qbit-gate-viz/app.py`（Streamlit + PyVista + Panel VTK pane → `st.iframe`）。
> 請勿再將本目錄視為有效 demo 或從它複製骨架；保留僅供歷史對照。

# Bloch Sphere · Qubit Evolution (PyVista + Panel)

3D Bloch sphere and single-qubit state evolution, implemented with **Qiskit (state math)
+ PyVista + Panel (3D rendering)** (per `viz-dboard` rule: 3D → pyvista + panel).
Grounded in `~/薦家/布球/布球_distilled.md` and its **key PyVista source
`5布球態演化維問.py`**. (`10態演化布球.py` is legacy matplotlib `plot_surface` and is NOT
the 3D backend reference.)

## Features

- Bloch sphere: opacity 0.12 surface, 12-meridian / 6-parallel wireframe, 1.5 axes, equator
- Evolution trail (orange) + current state vector (gold arrow)
- Rx / Ry / Rz rotations with adjustable total angle, frame scrubbing and `Player` animation
- Special states: |0⟩, |1⟩, |+⟩, |−⟩, |+i⟩, |−i⟩
- Live |r| / θ / φ / α / β / P(|0⟩), P(|1⟩) readout
- States computed by Qiskit `Statevector.expectation_value`; exactly `frames` rotation steps (no off-by-one)

## Location & Startup

- **Location**: `~/薦家/布球/bloch-evolution-viz/app.py`
- **Startup**:
  ```bash
  cd ~/薦家/布球/bloch-evolution-viz
  panel serve app.py --show
  ```
  (headless: `panel serve app.py --port 5006`)

## Key API note

Panel's VTK pane takes the **render window**, not the Plotter:

```python
pn.extension("vtk")
plotter = pv.Plotter(off_screen=True)
...
pn.pane.VTK(plotter.ren_win, width=650, height=650)
```

Closing the previous Plotter before rebuilding avoids native memory accumulation.
