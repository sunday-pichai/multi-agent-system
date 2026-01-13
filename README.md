# Warehouse Multi-Agent System (MAS)

A scalable multi-agent reinforcement learning system for warehouse automation. This project implements a grid-based warehouse environment where multiple robots learn to pick up shelves, deliver requested items to goals, and avoid collisions using Deep Q-Networks (DQN).

## 🎯 Features

- **Multi-Agent DQN Training**: Independent DQN policies for each agent with experience replay
- **Symmetry-Aware Verification**: Quotient model construction for efficient safety verification
- **Counterexample-Guided Refinement**: Automatic policy improvement using failure cases
- **Prioritized Experience Replay**: Focus training on important failure cases
- **Comprehensive Testing**: Full test suite covering all components
- **Configurable**: YAML-based configuration for easy hyperparameter tuning

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Training](#training)
- [Evaluation](#evaluation)
- [Verification & Refinement](#verification--refinement)
- [Configuration](#configuration)
- [Testing](#testing)
- [Architecture](#architecture)
- [Reward System](#reward-system)
- [Troubleshooting](#troubleshooting)

## 🚀 Installation

### Prerequisites

- Python 3.8+
- pip

### Setup

1. **Create and activate a virtual environment:**

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -U pip
pip install -r requirements.txt
```

**Dependencies:**
- `torch` - PyTorch for neural networks
- `numpy` - Numerical operations
- `pygame` - Visualization (optional, for rendering)
- `matplotlib` - Plotting
- `pyyaml` - Configuration file support

3. **Verify installation:**

```bash
python tests/run_tests.py
```

All tests should pass. If you see any errors, check the [Troubleshooting](#troubleshooting) section.

## 🏃 Quick Start

### Basic Training

Train agents to learn warehouse navigation and item delivery:

```bash
python main.py --mode train --episodes 200 --steps-per-episode 1000 --save-dir models
```

### Evaluate Trained Models

```bash
python main.py --mode eval --eval-episodes 20 --save-dir models
```

### Interactive Mode (Watch Agents)

```bash
python main.py --mode interactive --render
```

## 📁 Project Structure

```
.
├── main.py                 # CLI entry point and training/eval loops
├── env.py                  # Warehouse environment implementation
├── agent.py                # Robot agent with actions (move, turn, pick, drop)
├── dqn.py                  # Deep Q-Network neural network
├── config.py               # Configuration constants and YAML loader
├── config.yaml             # YAML configuration overrides
├── eval_utils.py           # Evaluation utilities and seed setting
├── utils.py                # Model saving utilities
├── verification.py         # Safety verification (quotient model)
├── refinement.py           # Counterexample-guided fine-tuning
├── symmetry_reduction.py   # Symmetry detection and quotient building
├── replay.py               # Experience replay buffers
├── requirements.txt        # Python dependencies
├── tests/                  # Comprehensive test suite
│   ├── test_rewards.py     # Reward structure tests
│   ├── test_env.py         # Environment tests
│   ├── test_agent.py       # Agent action tests
│   ├── test_training.py    # Training component tests
│   ├── test_integration.py # Integration tests
│   └── run_tests.py        # Test runner
├── experiments/            # Experiment scripts and results
│   ├── run_verify_refine_experiment.py
│   └── results.csv
└── README.md               # This file
```

## 🎓 Training

### Basic Training Command

```bash
python main.py --mode train \
    --episodes 200 \
    --steps-per-episode 1000 \
    --save-dir models \
    --batch-size 128 \
    --seed 42
```

### Key Training Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--episodes` | 200 | Number of training episodes |
| `--steps-per-episode` | 1000 | Maximum steps per episode |
| `--batch-size` | 128 | Minibatch size for DQN updates |
| `--warmup-steps` | 5000 | Steps before training starts |
| `--target-update` | 500 | Steps between target network updates |
| `--save-interval` | 20000 | Steps between model checkpoints |
| `--save-dir` | models | Directory to save models |
| `--seed` | None | Random seed for reproducibility |
| `--gamma` | 0.99 | Discount factor |
| `--render` | False | Enable visualization during training |

### Training Process

1. **Initialization**: Creates DQN networks for each agent (8 agents by default)
2. **Exploration**: Agents explore using epsilon-greedy policy (starts at 100% random, decays to 10%)
3. **Experience Collection**: Transitions stored in per-agent replay buffers
4. **Learning**: After warmup, agents learn from random batches of experience
5. **Target Updates**: Target networks updated every 500 steps for stable learning
6. **Checkpointing**: Models saved periodically to `--save-dir`

### Expected Training Behavior

- **Early Episodes**: Rewards around -20 to -30 (agents exploring)
- **Mid Training**: Rewards improve as agents learn to pick items
- **Late Training**: Rewards continue improving, agents learn efficient delivery
- **Collision Rate**: Should decrease over time

### Monitoring Training

- **Console Logs**: Episode rewards and statistics printed every `--log-interval` episodes
- **TensorBoard**: Logs saved to `<save-dir>/runs/` (if TensorBoard available)
- **Model Checkpoints**: Saved every `--save-interval` steps

## 📊 Evaluation

### Evaluate Trained Models

```bash
python main.py --mode eval \
    --eval-episodes 20 \
    --save-dir models \
    --render  # Optional: visualize trajectories
```

### Robust Evaluation (Multiple Runs)

```bash
python main.py --mode eval \
    --eval-episodes 20 \
    --eval-robust \
    --eval-runs 3 \
    --save-dir models
```

This runs evaluation 3 times and reports mean ± std collision rate.

### Evaluation Metrics

- **Collision Rate**: Percentage of steps with collisions (lower is better)
- **Trajectory Visualization**: Optional plotting of agent paths

## 🔍 Verification & Refinement

### Verify-Refine Loop

This workflow finds safety violations and improves policies:

```bash
python main.py --verify-refine \
    --iterations 3 \
    --refine-steps 200 \
    --save-dir models
```

### How It Works

1. **Verification**: Runs verification on quotient model (symmetry-reduced)
2. **Counterexample Extraction**: Finds failure cases (collisions)
3. **Case Storage**: Stores failure cases in prioritized replay buffer
4. **Fine-Tuning**: Fine-tunes models on failure cases
5. **Iteration**: Repeats until safe or max iterations

### Experiment Runner

```bash
python experiments/run_verify_refine_experiment.py \
    --save-dir experiments/models \
    --iterations 2 \
    --refine-steps 50 \
    --seed 42
```

Results saved to `experiments/results.csv`.

## ⚙️ Configuration

### YAML Configuration

Edit `config.yaml` to customize settings:

```yaml
grid:
  width: 20
  height: 20
  cell_size: 30

agents:
  num_agents: 8
  num_shelves: 20
  goals:
    - [9, 18]
    - [10, 18]

training:
  lr: 0.0005          # Learning rate
  gamma: 0.99         # Discount factor
  batch_size: 128     # Batch size
  target_update: 500  # Target network update frequency
  memory_size: 100000 # Replay buffer size
  warmup_steps: 5000  # Steps before training
  save_interval: 20000 # Checkpoint frequency
  eps_start: 1.0      # Initial exploration
  eps_end: 0.1        # Final exploration
  eps_decay: 0.9999   # Exploration decay rate
```

### Command-Line Overrides

Most parameters can be overridden via command-line:

```bash
python main.py --mode train \
    --episodes 500 \
    --batch-size 64 \
    --gamma 0.95 \
    --seed 123
```

## 🧪 Testing

### Run All Tests

```bash
python tests/run_tests.py
```

### Test Coverage

- **Reward Structure** (6 tests): Verifies reward values and calculations
- **Environment** (6 tests): Tests reset, step, state shape, collisions
- **Agent** (9 tests): Tests all agent actions (move, turn, pick, drop)
- **Training Components** (7 tests): DQN, gradients, replay buffers
- **Integration** (4 tests): End-to-end system tests

### Run Individual Test Modules

```bash
python -m tests.test_rewards
python -m tests.test_env
python -m tests.test_agent
python -m tests.test_training
python -m tests.test_integration
```

## 🏗️ Architecture

### Environment (`env.py`)

- **Grid World**: 20x20 grid with obstacles (goals)
- **Agents**: 8 robots with position, direction, carrying state
- **Shelves**: 20 shelves, 40% requested initially
- **Goals**: 2 delivery points
- **State**: Normalized positions, directions, shelf states, other agents

### Agent (`agent.py`)

- **Actions**: FORWARD, TURN_LEFT, TURN_RIGHT, PICK_DROP, WAIT
- **Movement**: Collision detection (boundaries and other agents)
- **Pick/Drop**: Shelf management with delivery logic

### DQN (`dqn.py`)

- **Architecture**: Fully connected: `state_size → 512 → 512 → 256 → action_size`
- **Activation**: ReLU
- **Output**: Q-values for each action

### Training Loop (`main.py`)

- **Experience Replay**: Per-agent buffers (100k capacity)
- **Target Networks**: Updated every 500 steps
- **Epsilon-Greedy**: Decays from 1.0 to 0.1
- **Gradient Clipping**: Max norm 1.0 for stability

## 🎁 Reward System

The reward system is carefully tuned to encourage desired behavior:

### Reward Components

| Action | Reward | Description |
|--------|--------|-------------|
| **Step** | -0.005 | Small time penalty |
| **Forward (success)** | +0.01 | Bonus for successful movement |
| **Collision** | -0.2 | Penalty for collisions |
| **Pick Requested** | +5.0 | Reward for picking requested shelf |
| **Pick Non-Requested** | +0.5 | Small reward (neutral) |
| **Deliver** | +20.0 | Large reward for delivery |
| **Drop** | -0.2 | Small penalty for dropping |
| **Distance Improvement** | +0.15 × Δdistance | Reward for moving closer to target |
| **Carrying Non-Requested** | -0.05 | Small penalty per step |

### Reward Design Principles

1. **Balanced**: Positive rewards outweigh penalties for good behavior
2. **Progress-Based**: Distance rewards encourage movement toward goals
3. **Action-Specific**: Different rewards for different actions
4. **Collision-Aware**: Penalties discourage unsafe behavior

## 🔧 Troubleshooting

### Common Issues

#### Training Collapse (Rewards Degrading)

**Symptoms**: Rewards start around -50, degrade to -150

**Solution**: Already fixed! The reward structure has been optimized. If you still see issues:
- Check that you're using the latest code
- Verify `config.yaml` has correct epsilon decay (0.9999)
- Ensure learning rate is 0.0005

#### Pygame Warnings on Windows

**Symptoms**: Warnings about `pkg_resources` or SDL

**Solution**: Usually benign. To suppress:
- Update setuptools: `pip install --upgrade setuptools`
- For headless: Set `SDL_VIDEODRIVER=dummy` (Linux/macOS)

#### Out of Memory

**Symptoms**: CUDA out of memory errors

**Solution**:
- Reduce `--batch-size` (e.g., 64 instead of 128)
- Reduce `NUM_AGENTS` in config
- Use CPU: The code auto-detects, but you can force CPU by not installing CUDA PyTorch

#### Tests Failing

**Symptoms**: Test failures

**Solution**:
- Ensure all dependencies installed: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Run tests individually to isolate issues

#### Models Not Saving

**Symptoms**: No model files in `--save-dir`

**Solution**:
- Check `--save-interval` (default 20000 steps)
- Ensure directory exists and is writable
- Check console for save messages

### Getting Help

1. **Run Tests**: `python tests/run_tests.py` to verify setup
2. **Check Logs**: Look for error messages in console output
3. **Verify Config**: Ensure `config.yaml` is valid YAML
4. **Check Dependencies**: `pip list` to verify packages

## 📈 Performance Tips

### Faster Training

- **GPU**: Install CUDA-enabled PyTorch for 5-10x speedup
- **Batch Size**: Increase to 256 if memory allows
- **Parallel Agents**: Already parallelized, but reduce `NUM_AGENTS` if needed

### Better Results

- **More Episodes**: Train for 500+ episodes for better policies
- **Longer Episodes**: Increase `--steps-per-episode` to 2000+
- **Hyperparameter Tuning**: Adjust learning rate, epsilon decay in `config.yaml`

### Memory Optimization

- **Reduce Replay Buffer**: Lower `memory_size` in config
- **Smaller Networks**: Reduce `HIDDEN` size in `config.py`
- **Fewer Agents**: Reduce `NUM_AGENTS`

## 📝 License

This project is provided as-is for research and educational purposes.

## 🤝 Contributing

To contribute:
1. Add tests for new features
2. Ensure all tests pass: `python tests/run_tests.py`
3. Update this README if needed
4. Follow existing code style

## 📚 References

- **DQN**: Mnih et al., "Human-level control through deep reinforcement learning" (Nature, 2015)
- **Experience Replay**: Lin, "Reinforcement Learning for Robots Using Neural Networks" (1993)
- **Prioritized Replay**: Schaul et al., "Prioritized Experience Replay" (ICLR, 2016)

---

**Happy Training! 🚀**

For questions or issues, check the [Troubleshooting](#troubleshooting) section or review the test suite for usage examples.
