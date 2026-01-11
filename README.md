# Scalable Warehouse MAS — Symmetry-aware Verification & Refinement

A compact research-style project demonstrating partial symmetry reduction, bounded verification, and counterexample-guided refinement for neural policies controlling a multi-agent warehouse environment.

## Features
- Modular simulation (`env.py`, `agent.py`) with a small grid warehouse and simple robot actions  
- DQN agents (`dqn.py`) and a lightweight training/evaluation harness (`main.py`, `eval_utils.py`)  
- Symmetry detection heuristic and quotient-model checks (`symmetry_reduction.py`)  
- Lightweight falsifiers and deterministic verifiers (`verification.py`) with quotient-based checks  
- Counterexample extraction and targeted fine-tuning (`refinement.py`) using prioritized replay (`replay.py`)  
- Visualization helpers for trajectories, heatmaps and refinement metrics (`viz.py`)  
- Small, focused test cases as top-level `test_*.py` files (run with Python's unittest)  

## Quick start
1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -U pip
pip install -r requirements.txt
```

2. Run the test suite (sanity check):
```bash
python -m unittest discover -v
```

3. Train a small smoke model (headless):
```bash
python main.py --mode train --episodes 20 --steps-per-episode 200 --save-dir models
```

4. Run a verify→refine loop (checkpointed + visualizations):
```bash
python main.py --verify-refine --iterations 5 --refine-steps 200 --save-dir models
```

5. Visualize training and refinement logs (if producing TensorBoard logs):
```bash
tensorboard --logdir models/runs
```

## Running headless / CI tips 🔧
- In headless environments set `SDL_VIDEODRIVER=dummy` (useful for CI).  
- Use small `--iterations` and `--refine-steps` during experiments to keep runs short while debugging.

## Project structure (key files)
- `env.py` — Warehouse environment, observations and step logic  
- `agent.py` — Robot data structures and actions  
- `dqn.py` — Simple DQN network and helpers  
- `symmetry_reduction.py` — Heuristic orbit detection + quotient building  
- `verification.py` — Falsifiers + quotient-based verification  
- `refinement.py` — Counterexample extraction + targeted fine-tuning  
- `replay.py` — Replay buffers (basic and prioritized)  
- `viz.py` — Plots for trajectories, heatmaps and metrics  
- `test_*.py` — Small unit tests and integration checks (top-level files)

## Reproducibility and experiments 📊
- Use `--seed` in `main.py` for deterministic runs.  
- Save models with `--save-dir` and inspect `models/runs` for logs and artifacts.  
- For reproducible experiments use `experiments/run_verify_refine_experiment.py` and the demo notebook `experiments/notebooks/verify_refine_demo.ipynb`.

## Contributing & License ✅
- Add tests for new features and keep PRs small and focused.  
- License: MIT (if included)

---

If you'd like, I can also open a PR with this change, or apply the edit directly and commit it — which would you prefer?
