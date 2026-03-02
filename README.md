# Warehouse Multi-Agent System (MAS)

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Deterministic grid-based multi-agent warehouse coordination with explicit planning, bounded safety verification, and counterexample-driven refinement.

## What This Project Does

Robots operate on a 2D grid:

- pick requested shelves,
- deliver them to goal cells,
- avoid vertex and edge collisions,
- and optionally run verification/refinement loops to improve safety.

This is a non-ML system. Behavior is algorithmic and reproducible (optionally with `--seed`).

## Demo

![Warehouse MAS Demo](docs/demo-gif.gif)

Also available as video: `docs/demo.mp4`.

## Core Components

- `main.py`: CLI entry point and orchestration.
- `env.py`: warehouse environment dynamics, rewards, collisions, rendering hooks, evaluation loop.
- `agent.py`: robot state/action primitives (`FORWARD`, `TURN_LEFT`, `TURN_RIGHT`, `PICK_DROP`, `WAIT`).
- `pathfinding.py`: cooperative planner with:
  - time-aware A* on `(x, y, direction, t)`,
  - rolling reservations (position + edge),
  - assignment logic,
  - idle tracking and deadlock escape behavior,
  - injected hard constraints from refinement.
- `symmetry_reduction.py`: role-orbit detection and canonical quotient keys.
- `verification.py`: bounded quotient-state safety checks and counterexample extraction.
- `refinement.py`: conflict/trace-to-constraint conversion.
- `renderer.py`: pygame renderer (grid, robots, shelves, goals, conflict overlays).
- `config.py` + `config.yaml`: defaults + YAML overrides.

## Installation

```bash
pip install -r requirements.txt
```

Dependencies currently listed:

- `pygame`
- `pyyaml`

## Quick Start

Interactive mode (default mode):

```bash
python main.py
```

Batch simulation:

```bash
python main.py --mode simulate --episodes 8 --steps-per-episode 200
```

Evaluation:

```bash
python main.py --mode eval --eval-episodes 3 --steps-per-episode 150
```

Verification + refinement:

```bash
python main.py --verify-refine --verify-horizon 30 --verify-trials 20
```

Symmetry/orbit inspection:

```bash
python main.py --detect-symmetry
```

## CLI Reference

`main.py --help` exposes:

- `--mode {interactive,simulate,eval}` (default: `interactive`)
- `--render` (enables rendering in simulate mode; interactive always renders)
- `--config CONFIG` (default: `config.yaml`)
- `--seed SEED`
- `--cell-size CELL_SIZE`
- `--episodes EPISODES` (default: `8`)
- `--steps-per-episode STEPS_PER_EPISODE` (default: `200`)
- `--log-interval LOG_INTERVAL` (default: `1`)
- `--eval-episodes EVAL_EPISODES` (default: `3`)
- `--plan-horizon PLAN_HORIZON`
- `--detect-symmetry`
- `--verify-refine`
- `--verify-horizon VERIFY_HORIZON`
- `--verify-trials VERIFY_TRIALS`
- `--verify-include-shelves`
- `--verify-progress VERIFY_PROGRESS` (default: `1`)
- `--min-separation MIN_SEPARATION`
- `--refine-iterations REFINE_ITERATIONS`
- `--refine-max-constraints REFINE_MAX_CONSTRAINTS`

## Configuration (`config.yaml`)

The runtime loads `config.yaml` via `cfg.load_from_yaml(...)`. CLI flags override config values when provided.

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
  horizon: 30
  astar_max_nodes: 3500
  idle_limit: 4
  reservation_window: 8
  unplanned_hold_steps: 2
  escape_idle_steps: 6

render:
  fps: 1

verification:
  min_separation: 1
  horizon: 30
  trials: 20

refinement:
  iterations: 2
  max_constraints: 100

paths:
  model_dir: models
```

Note: `paths.model_dir` is present in YAML but is not consumed by the current runtime code.

## Controls (Interactive/Rendered)

- Close window or press `Q`: quit.
- Left click robot cell: select agent.
- `Tab`, `Right`, `.`: next agent.
- `Left`, `,`: previous agent.

## Testing

Run bundled suite runner:

```bash
python tests/run_tests.py
```

Run individual suites directly:

```bash
python tests/test_rewards.py
python tests/test_env.py
python tests/test_agent.py
python tests/test_training.py
python tests/test_integration.py
python tests/test_refinement.py
python tests/test_verification_refinement.py
```

## Documentation

- Web documentation site: `docs/index.html`
- Alternate reader view: `docs/reader.html`
- PDF/Markdown chapter library: `docs/pdf/`
  - includes architecture, planning, verification, refinement, CLI/config, and execution playbooks
- Full compiled documentation PDF:
  - `docs/pdf/Warehouse_MAS_Documentation.pdf`

## Repository Layout

Top-level runtime files are at the project root (`main.py`, `env.py`, `pathfinding.py`, etc.).

The repository also contains `src/warehouse_mas/...` package directories (algorithms, coordination, simulation, visualization, etc.) as a broader project structure scaffold.

## License

MIT License. See `LICENSE`.
