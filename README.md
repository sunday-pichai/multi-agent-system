# Warehouse Multi-Agent System (MAS)

[![GitHub Repository](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/sunday-pichai/multi-agent-system)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](#license)

A deterministic multi-agent warehouse simulator featuring symmetry-reduced verification and verification-guided refinement. This system implements classical path planning algorithms for autonomous robots that collaboratively pick and deliver shelves while avoiding collisions.

**Repository**: [https://github.com/sunday-pichai/multi-agent-system](https://github.com/sunday-pichai/multi-agent-system)

## Features

- **Deterministic Multi-Agent Planning**: Cooperative A* with Conflict-Based Search (CBS)
- **Symmetry Reduction**: Role-orbit grouping and state canonicalization
- **Bounded Safety Verification**: Quotient model verification with collision detection
- **Verification-Guided Refinement**: Explicit constraint-based refinement (no machine learning)
- **Interactive Visualization**: Real-time rendering and simulation monitoring

## Table of Contents

- [Features](#features)
- [Documentation](#documentation)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Technical Notes](#technical-notes)

## Documentation

Interactive documentation is available at [docs/index.html](docs/index.html). Open this file in your web browser to access:
- System architecture overview
- Algorithm explanations
- Demo video (`docs/demo.mp4`)
- API documentation

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone or download this repository
2. Navigate to the project directory:
   ```bash
   cd multi-agent-system
   ```
3. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode

Run the simulator with real-time visualization:
```bash
python main.py --mode interactive --render
```

### Simulation Mode

Execute multiple episodes without rendering:
```bash
python main.py --mode simulate --episodes 8 --steps-per-episode 200
```

### Evaluation Mode

Run evaluation episodes with performance metrics:
```bash
python main.py --mode eval --eval-episodes 3 --steps-per-episode 150
```

### Verification and Refinement

Perform bounded safety verification with refinement:
```bash
python main.py --verify-refine --verify-horizon 30 --verify-trials 20
```

## How It Works

### Path Planning

The system employs a two-tier planning approach:

- **Cooperative A\***: Plans individual agent paths in a time-expanded grid, accounting for temporal constraints
- **Conflict-Based Search (CBS)**: Resolves multi-agent collisions by iteratively adding constraints and replanning conflicting paths

### Symmetry Reduction

To improve verification efficiency, the system reduces state space through:

- **Role Orbits**: Agents are grouped by operational role (idle vs. carrying requested shelf)
- **State Canonicalization**: Symmetric permutations of agent configurations are mapped to identical quotient states

### Symmetry Reduction: Before vs After

| Aspect | Full System | Symmetry-Reduced (Quotient) |
| --- | --- | --- |
| Agents represented | All N agents explicitly modeled | k role orbits (k <= 3 in this project) |
| State size | O(N * d) full agent state | O(k * d) representative state |
| Verification cost | Cver(n) over full dimension n = N * d | Cver(m) with m << n |
| Counterexamples | Full traces over all agents | Lifted from quotient representatives |
| Memory | O(n) full-state storage | O(m) reduced storage |

### Bounded Safety Verification

The verification module ensures collision-free operation:

- Performs bounded-horizon checks on the quotient model
- Validates minimum separation requirements between agents
- Generates counterexample traces when safety violations are detected

### Refinement Loop

When verification detects unsafe behaviors:

1. Counterexample traces are analyzed
2. Hard constraints are extracted and added to the planning system
3. The planner is re-executed with updated constraints
4. Verification is repeated until the system is safe or the iteration budget is exhausted

**Note**: This refinement process uses explicit constraint programming—no machine learning is involved.

## Configuration

The system behavior can be customized by editing [config.yaml](config.yaml):

### Grid Settings
```yaml
grid:
  width: 16          # Grid width in cells
  height: 16         # Grid height in cells
  cell_size: 30      # Pixel size for rendering
```

### Agent Configuration
```yaml
agents:
  num_agents: 6      # Number of robots
  num_shelves: 8     # Number of shelves in warehouse
  goals:             # Goal locations (delivery points)
    - [7, 14]
    - [8, 14]
```

### Planning Parameters
```yaml
planning:
  horizon: 40              # Planning horizon (time steps)
  use_cbs: true           # Enable Conflict-Based Search
  cbs_max_nodes: 200      # CBS node expansion limit
  astar_max_nodes: 6000   # A* node expansion limit
  idle_limit: 6           # Maximum idle time for agents
```

### Verification Settings
```yaml
verification:
  min_separation: 1    # Minimum required distance between agents
  horizon: 30         # Verification time horizon
  trials: 20          # Number of verification trials
```

### Refinement Configuration
```yaml
refinement:
  iterations: 2         # Maximum refinement iterations
  max_constraints: 100  # Maximum number of constraints to add
```

### Rendering Options
```yaml
render:
  fps: 0    # Frames per second (0 = uncapped for maximum responsiveness)
```

## Project Structure

```
MAS_FinalProject/
├── main.py                    # Entry point and CLI interface
├── env.py                     # Warehouse environment implementation
├── agent.py                   # Agent logic and behavior
├── pathfinding.py            # Cooperative A* and CBS algorithms
├── symmetry_reduction.py     # State canonicalization and orbit computation
├── verification.py           # Safety verification module
├── refinement.py             # Constraint-based refinement loop
├── config.py                 # Configuration loader
├── config.yaml               # System configuration file
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── docs/                     # Documentation website
│   ├── index.html
│   ├── script.js
│   ├── styles.css
│   └── demo.mp4
└── tests/                    # Test suite
    ├── __init__.py
    ├── run_tests.py         # Test runner
    ├── test_agent.py        # Agent unit tests
    ├── test_env.py          # Environment tests
    ├── test_rewards.py      # Reward system tests
    ├── test_training.py     # Planning tests
    └── test_integration.py  # Integration tests
```

## Testing

Run the complete test suite:

```bash
python tests/run_tests.py
```

Individual test modules can be run directly:
```bash
python -m pytest tests/test_agent.py
python -m pytest tests/test_env.py
python -m pytest tests/test_integration.py
```

## Technical Notes

- **Fully Deterministic**: This system uses classical algorithms exclusively—no machine learning or neural network components
- **No ML Dependencies**: All ML-related code and artifacts have been removed for clarity and simplicity
- **Performance**: Rendering FPS is uncapped by default (`render.fps: 0`) for optimal responsiveness
- **Scalability**: The symmetry reduction technique significantly improves verification performance for systems with many identical agents

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests to the [GitHub repository](https://github.com/sunday-pichai/multi-agent-system).

## License

This project is available under the MIT License. See the LICENSE file for more details.

## Author

**Sunday Pichai**
- GitHub: [@sunday-pichai](https://github.com/sunday-pichai)
- Repository: [multi-agent-system](https://github.com/sunday-pichai/multi-agent-system)

## Acknowledgments

This project implements classical multi-agent path planning algorithms including:
- Cooperative A* (CA*)
- Conflict-Based Search (CBS)
- Symmetry reduction techniques for formal verification

---

For questions, issues, or feature requests, please visit the [GitHub Issues](https://github.com/sunday-pichai/multi-agent-system/issues) page.
