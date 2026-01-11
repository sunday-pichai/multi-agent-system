# Scalable Warehouse MAS — Symmetry-aware Verification & Refinement

A compact research-style project demonstrating partial symmetry reduction, bounded verification, and counterexample-guided refinement for neural policies controlling a multi-agent warehouse environment.

## Features

- Modular simulation (`env.py`, `agent.py`) with a small grid warehouse and simple robot actions
- DQN agents (`dqn.py`) and a lightweight training/evaluation harness (`main.py`, `eval_utils.py`)
- Symmetry detection heuristic and quotient-model checks (`symmetry_reduction.py`)
- Lightweight falsifiers and deterministic verifiers (`verification.py`) with quotient-based checks
- Counterexample extraction and targeted fine-tuning (`refinement.py`) using prioritized replay (`replay.py`)

- Test harness (`tests/run_tests.py`) for easy CI-friendly testing without pytest

## Quick start

1. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -U pip
pip install -r requirements.txt
```

2. Run the test suite (sanity check):

```bash
python tests/run_tests.py
```

3. Train a small smoke model (headless):

```bash
python main.py --mode train --episodes 20 --steps-per-episode 200 --save-dir models
```

4. Run verify → refine loop (checkpointed + visualizations):

```bash
python main.py --verify-refine --iterations 5 --refine-steps 200 --save-dir models
```

5. Visualize training and refinement logs with TensorBoard:

```bash
tensorboard --logdir models/runs
```

## Running headless / CI tips
- In headless environments ensure `SDL_VIDEODRIVER` is set to `dummy` (the GitHub Actions workflow does this).
- Use small `--iterations` and `--refine-steps` during experiments to avoid long runs while debugging.

## Project structure (key files)
- `env.py` — Warehouse environment, observations and step logic
- `agent.py` — Robot data structure and actions
- `dqn.py` — Simple DQN network
- `symmetry_reduction.py` — Heuristic orbit detection + quotient building
- `verification.py` — Falsifiers + quotient-based verification
- `refinement.py` — Counterexample extraction + targeted fine-tuning
- `replay.py` — Replay buffers (basic and prioritized)

- `tests/` — Small unit tests and integration checks

## Reproducibility and experiments
- Use `--seed` in `main.py` for deterministic runs
- Save models to `--save-dir` and inspect `models/runs` for TensorBoard logs and per-iteration images
- For publication-quality experiments: run multiple seeds and aggregate CSV results (use `experiments/run_verify_refine_experiment.py` and the demo notebook `experiments/notebooks/verify_refine_demo.ipynb`).

## Contributing & License
- Add tests for new features and keep PRs small and focused.
- License: MIT (if included)

---
Small, self-contained project intended for final-year demonstration and reproducible experiments. If you'd like, I can add a step-by-step experiment script and a short notebook that demonstrates a verify→refine example.
