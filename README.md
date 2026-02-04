# Warehouse MAS (Deterministic, Symmetry?Reduced Verification)

A clean, **non?ML** multi?agent warehouse simulator that uses deterministic path planning and symmetry?reduced verification with a verification?guided refinement loop. Robots pick requested shelves, deliver them to goals, and avoid collisions using classical algorithms only.

## Highlights

- Deterministic multi?agent planning (Cooperative A* + CBS)
- Symmetry reduction via role?orbits and canonicalization
- Bounded safety verification on the quotient model
- Verification?guided refinement using explicit constraints (no learning)
- Simple, fast interactive visualization

## Quick Start (Easy Commands)

```powershell
.\scripts\run.ps1
```

Menu options:
1. Interactive (render)
2. Simulate
3. Evaluate
4. Verify & Refine
5. Run Tests

If PowerShell blocks scripts:
```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## Documentation Website

Open `docs/index.html` in a browser to view the documentation site.

The demo video is embedded at `docs/demo.mp4`.

## Direct Commands

```bash
python main.py --mode interactive --render
python main.py --mode simulate --episodes 15 --steps-per-episode 300
python main.py --mode eval --eval-episodes 6 --steps-per-episode 150
python main.py --verify-refine --verify-horizon 50 --verify-trials 50
python tests/run_tests.py
```

## How It Works

### Planning
- **Cooperative A*** plans each agent path in a time?expanded grid.
- **CBS (Conflict?Based Search)** resolves collisions by adding constraints and replanning.

### Symmetry Reduction
- Agents are grouped into **role orbits** (idle vs carrying requested shelf).
- The system state is **canonicalized** so symmetric permutations map to the same quotient state.

### Verification
- Bounded verification checks for collisions and minimum separation on the quotient.
- If unsafe, a counterexample trace is returned.

### Refinement (No ML)
- Counterexamples are converted into **hard constraints**.
- Planner is re?verified with those constraints until safe or budget is exhausted.

## Configuration

Edit `config.yaml`:

```yaml
grid:
  width: 16
  height: 16
  cell_size: 30

agents:
  num_agents: 6
  num_shelves: 8
  goals:
    - [7, 14]
    - [8, 14]

planning:
  horizon: 40
  use_cbs: true
  cbs_max_nodes: 200

verification:
  min_separation: 1
  horizon: 50
  trials: 50

refinement:
  iterations: 3
  max_constraints: 100

render:
  fps: 0
```

## Project Structure

```
.
|-- main.py
|-- env.py
|-- agent.py
|-- pathfinding.py
|-- symmetry_reduction.py
|-- verification.py
|-- refinement.py
|-- config.py
|-- config.yaml
|-- scripts/
|   |-- run.ps1
|   |-- run_interactive.ps1
|   |-- run_sim.ps1
|   |-- run_eval.ps1
|   |-- run_verify_refine.ps1
|   |-- run_tests.ps1
|-- tests/
|   |-- test_rewards.py
|   |-- test_env.py
|   |-- test_agent.py
|   |-- test_training.py
|   |-- test_integration.py
|   |-- run_tests.py
|-- requirements.txt
|-- MAS.pdf
```

## Notes

- This project is **fully deterministic** and contains **no ML or neural components**.
- All removed ML artifacts (models, notebooks, torch code) are gone.
- Rendering FPS is uncapped by default (`render.fps: 0`) for responsiveness.
