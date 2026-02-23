# MAS Final Project: Overview and Architecture

## 1. Project Purpose

This project implements a deterministic multi-agent warehouse system where robots:

- navigate on a 2D grid,
- pick requested shelves,
- deliver requested shelves to goal cells,
- avoid collisions through cooperative planning,
- improve safety through verification-guided refinement.

The system is intentionally algorithmic (not ML-policy-driven).  
Core claim: practical multi-agent coordination can be built with explicit planning + symmetry-reduced verification + constraint refinement.

## 2. What the System Contains

Core runtime modules:

- `main.py`: CLI entrypoint and orchestration.
- `env.py`: environment dynamics, reward/collision handling, rendering, evaluation.
- `agent.py`: robot/action primitives and pick/drop semantics.
- `pathfinding.py`: cooperative planner and assignment logic.
- `symmetry_reduction.py`: role-orbit detection and canonical state mapping.
- `verification.py`: bounded safety verification over quotient states.
- `refinement.py`: conversion of unsafe traces into planner constraints.
- `config.py` + `config.yaml`: defaults and runtime overrides.

Support:

- `tests/`: module and integration tests.
- `docs/`: documentation site and written docs.

## 3. Architectural Style

The architecture is a deterministic closed loop:

1. Planner computes one action per robot.
2. Environment executes actions simultaneously with conflict resolution.
3. Verification optionally runs bounded trials on symmetry-reduced state keys.
4. Refinement optionally injects hard constraints back into planner.

This forms a CEGAR-like pattern:

- generate behavior,
- detect violations,
- refine constraints,
- repeat.

## 4. Execution Modes (from `main.py`)

The CLI supports:

- `interactive`: continuous render + planning loop.
- `simulate`: episode loop with optional rendering.
- `eval`: collision-rate evaluation over episodes.
- `--detect-symmetry`: print detected orbits and quotient metadata.
- `--verify-refine`: run verification and apply refinement iteratively.

Main orchestration functions:

- `run_interactive(...)`
- `run_simulation(...)`
- `run_eval(...)`
- `run_verify_refine(...)`

Default resolution:

- `_apply_defaults(...)` binds CLI omissions to values from `config.py`.

## 5. Environment Model (`env.py`)

### 5.1 State Variables

`WarehouseEnv` manages:

- grid dimensions (`grid_w`, `grid_h`),
- goal cells (`GOALS`),
- robots (`self.robots`),
- shelves (`self.shelves`),
- step counters and statistics,
- planner debug payloads:
  - `_planner_allowed_shelf_entries`,
  - `_planner_last_actions`,
  - `_planner_debug_by_agent`,
- conflict/event telemetry:
  - `last_conflicts`,
  - `event_log`,
  - `traffic_heat`,
  - `collision_heat`.

### 5.2 Reset and Spawn

`reset()`:

- places robots randomly on free cells (excluding goals),
- places shelves randomly on free cells,
- initializes metrics/log buffers,
- returns per-robot normalized state vectors.

### 5.3 Step Semantics

`step(actions, record_trajectories=False)` performs one simultaneous timestep:

1. Decode integer actions into `Action` enum.
2. Record intent-level conflicts (`boundary`, `vertex`, `edge`) for diagnostics.
3. Apply non-forward actions (`TURN_LEFT`, `TURN_RIGHT`, `PICK_DROP`, `WAIT`).
4. Collect forward intents.
5. Reject forward moves that violate:
   - boundary,
   - shelf occupancy rules,
   - static occupied targets,
   - same-target contention,
   - edge swap conflicts.
6. Apply valid forward moves simultaneously.
7. Compute shaping rewards from distance-to-target delta.
8. Apply delivery team bonus and penalties.
9. Update episode/global counters and logs.

`done` is currently bounded by `self.steps > 1000`.

### 5.4 Rendering and Observability

`render()` draws:

- grid, goals, shelves, robots,
- orbit-color indicator using symmetry detection,
- conflict overlays.

Rendering is presentation-only and does not alter simulation logic.

### 5.5 Evaluation

`evaluate(planner, num_episodes, max_steps_per_episode, ...)` runs no-render episodes and returns:

- average collisions per agent per episode.

## 6. Agent Semantics (`agent.py`)

### 6.1 Enums

- `Direction`: `UP`, `RIGHT`, `DOWN`, `LEFT`.
- `Action`: `FORWARD`, `TURN_LEFT`, `TURN_RIGHT`, `PICK_DROP`, `WAIT`.

### 6.2 Robot State

Each `Robot` has:

- `id`, `x`, `y`, `dir`,
- optional `carrying` shelf dict.

### 6.3 Motion and Interaction Rules

- `forward(env)`: moves one cell if inside bounds and not blocked by robot/shelf.
- `pick_or_drop(env)`:
  - picks shelf on same cell if empty-handed,
  - delivers requested shelf at goal,
  - otherwise drops carried shelf.

Shelf-blocking policy is planner-aware:

- `_occupied_by_shelf(...)` allows entry to assigned requested shelf cell only,
- reads allowed entries from `env._planner_allowed_shelf_entries`.

This is a key planner-environment contract.

## 7. Cooperative Planning (`pathfinding.py`)

`CooperativePlanner` is the central policy module.

### 7.1 Internal Components

- `ReservationTable`: time-indexed vertex and edge occupancy reservations.
- `ConstraintTable`: hard forbidden vertex/edge constraints.
- `AssignmentManager`: robot-to-shelf and shelf-to-robot matching.
- `IdleTracker`: starvation/deadlock mitigation through idle monitoring.

### 7.2 Planning Strategy

Per timestep:

1. Track idleness and update assignments.
2. Build planning order with rotating priority offset.
3. Plan robots sequentially in that order.
4. For each robot:
   - decide immediate `PICK_DROP` if applicable,
   - else run time-aware A* (`astar_time`) to target,
   - fallback to deterministic local escape action if stuck.
5. Reserve trajectory prefixes for already-planned robots.
6. Sanitize first-step conflicts (same target/swap/invalid forward).

### 7.3 A* Search Space

Space-time node key:

- `(x, y, dir, t)`.

Transition constraints include:

- grid bounds,
- blocked shelf cells,
- reservations (vertex + both edge directions),
- dynamic blocked occupancy assumptions,
- refinement constraints.

### 7.4 Assignment Logic

`minimum_cost_matching(...)` (Hungarian algorithm) is used for:

- free robot -> requested shelf assignment,
- carrier -> delivery goal slot assignment.

This reduces assignment churn and keeps delivery flow balanced.

## 8. Symmetry Reduction (`symmetry_reduction.py`)

Symmetry reduction maps many labeled states into one quotient representative.

### 8.1 Role-Orbit Detection

Robots are grouped by compact role:

- `(0,0)`: carrying nothing,
- `(1,1)`: carrying requested shelf,
- `(1,0)`: carrying non-requested shelf.

Robots with same role belong to same orbit.

### 8.2 Canonicalization

For each orbit:

- encode each member as `(x, y, dir, carrying_requested)`,
- sort tuples lexicographically,
- store orbit tuple.

State key is tuple of orbit tuples (plus optional shelf key).

Optional shelf inclusion:

- include uncarried shelf tuples `(x, y, requested_flag)` sorted.

### 8.3 Quotient Metadata

`build_quotient_model(env)` provides:

- `orbits`,
- representative index per orbit,
- agent index -> orbit index mapping.

## 9. Verification (`verification.py`)

`verify_on_quotient(...)` performs bounded trial-based safety checking.

### 9.1 Trial Loop

For each trial:

1. Reset environment.
2. Maintain `visited` set of canonical quotient keys.
3. At each step:
   - canonicalize current state,
   - stop trial if key repeated (cycle in quotient space),
   - execute planner action,
   - detect collisions/conflicts,
   - evaluate minimum pairwise Manhattan separation.

### 9.2 Safety Outputs

Returns dict with fields such as:

- `safe` (bool),
- `delta_q` (minimum margin relative to required separation),
- `avg_collision_rate`,
- when unsafe:
  - `conflicts`,
  - `counterexample`,
  - `actions`.

`delta_q` interpretation:

- `delta_q >= 0`: maintained separation requirement,
- `delta_q < 0`: violated required separation.

## 10. Refinement (`refinement.py`)

`refine_planner_with_conflicts(...)` converts verification conflicts into hard planner constraints.

Mapping:

- `vertex` conflict -> forbid that position at `t+1`,
- `edge` conflict -> forbid both edge directions at `t+1`,
- `boundary` conflict -> forbid out-of-bounds target position at `t+1`,
- `separation` currently ignored.

Fallback path:

- if no explicit conflicts but trace exists, add coarse position constraint from:
  - first same-cell collision if present,
  - else closest pair anchor at time 1.

Result:

- returns count of applied constraints.

## 11. Configuration System (`config.py` + `config.yaml`)

`config.py` contains typed defaults for:

- grid size and goals,
- planner horizon and node caps,
- idleness and reservation windows,
- rendering FPS and visuals,
- verification thresholds and trial sizes,
- refinement iteration/constraint limits.

`load_from_yaml(...)` optionally overrides these values at startup.

`main.py` then applies CLI overrides on top.

Precedence is effectively:

1. hardcoded defaults,
2. YAML overrides,
3. CLI overrides.

## 12. Data Contracts Between Modules

Critical contracts:

- Planner expects `env` fields:
  - `robots`, `shelves`, `GOALS`, grid size.
- Environment expects planner outputs:
  - list of integer action IDs aligned with `env.robots`.
- Agent shelf blocking depends on planner-provided:
  - `env._planner_allowed_shelf_entries`.
- Verification expects planner API:
  - `compute_actions(env)`.
- Refinement expects planner API:
  - `add_constraint_position(...)`,
  - `add_constraint_edge(...)`.

## 13. End-to-End Safety Loop

During `--verify-refine`:

1. Run `verify_on_quotient(...)`.
2. If `safe=True`, stop and report.
3. If unsafe:
   - extract conflicts/counterexample,
   - inject constraints via refinement,
   - rerun verification for next iteration.

This loop improves safety by hardening planner search space over iterations.

## 14. Determinism and Reproducibility

- Seed control via `--seed` in `main.py`.
- Given same seed/config and deterministic code paths, execution is reproducible.
- Symmetry reduction is deterministic because canonicalization uses sorted tuples.

## 15. Complexity and Scalability Notes

Major computational costs:

- Planner:
  - one bounded A* per robot per timestep,
  - plus assignment matching.
- Verification:
  - `trials * horizon` worst-case steps,
  - each step calls planner and environment dynamics.
- Symmetry:
  - canonicalization overhead is small relative to planning,
  - potential benefit depends on how frequently symmetric permutations occur.

## 16. Failure Modes and Limits

Current design limitations:

- Bounded verification, not full proof of global safety.
- Symmetry reduction is role-based, not geometric-map automorphism-based.
- Refinement currently translates a limited conflict vocabulary.
- Performance sensitivity to congestion, horizon, and node caps.

These are engineering tradeoffs for tractability and transparency.

## 17. Testing Posture

Existing tests include:

- unit/integration coverage across environment, agent, refinement, and verification flow.
- integration case for verification+refinement (`tests/test_verification_refinement.py`).

Recommended additions:

- dedicated symmetry canonicalization unit tests,
- regression tests for quotient-key invariance under same-orbit permutations,
- performance baselines for quotient compression on selected seeded scenarios.

## 18. Architecture Summary

The project is a layered deterministic MAS stack:

- execution substrate (`env.py`, `agent.py`),
- coordination policy (`pathfinding.py`),
- state-space reduction (`symmetry_reduction.py`),
- bounded safety analysis (`verification.py`),
- corrective feedback (`refinement.py`),
- orchestration/config (`main.py`, `config.py`).

The core value is not one isolated algorithm; it is the integrated pipeline that couples planning with formalized safety feedback under a symmetry-aware state abstraction.
