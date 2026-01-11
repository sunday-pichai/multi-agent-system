# Scalable Warehouse MAS — Usage & Training Guide

This repository implements a compact multi-agent warehouse environment with DQN policies, symmetry-aware verification, and counterexample-guided refinement.

This README focuses on how to set up, run, and *train* models in this project.

---

## 1) Quick setup (local)

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows (cmd)
.venv\Scripts\activate
# Windows (PowerShell)
$env:VIRTUAL_ENV = "${PWD}\\.venv"; . .venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -U pip
pip install -r requirements.txt
```

Tip: If you have a GPU and PyTorch configured, training will be faster; the code auto-selects `cuda` when available.

---

## 2) Quick smoke checks

Run small helper scripts to ensure the environment and model code load correctly:

```bash
python test_env.py     # simple env reset/step smoke check
python eval_test.py    # small eval smoke check (constructs DQNs and runs a short eval)
```

---

## 3) Training (basic usage)

Start a training run with sensible defaults:

```bash
python main.py --mode train --episodes 200 --steps-per-episode 1000 --save-dir models
```

Key flags:
- `--mode train` — start training
- `--episodes`, `--steps-per-episode` — episodes and per-episode length
- `--batch-size` — minibatch size for DQN updates
- `--save-dir` — directory for models and logs

Checkpointing:
- Models are saved as `dqn_agent_<i>.pth` in `--save-dir` using `save_models()`.
- TensorBoard logs (if enabled) are saved to `<save-dir>/runs`.

Tuning:
- Hyperparameters live near the top of `main.py` and `dqn.py` (learning rate, epsilon schedule, target update frequency). Adjust these for larger runs.

---

## 4) Verify → Refine loop (counterexample-guided)

This workflow runs a verifier to find counterexamples, extracts failure cases, and fine-tunes agents on them.

Run the loop via `main.py`:

```bash
python main.py --verify-refine --iterations 3 --refine-steps 200 --save-dir models
```

Or use the example experiment runner:

```bash
python experiments/run_verify_refine_experiment.py --save-dir experiments/models --iterations 2 --refine-steps 50
```

The experiment script saves results and writes a small CSV summary under `experiments/results.csv`.

---

## 5) Evaluation

Evaluate models with the CLI:

```bash
python main.py --mode eval --eval-episodes 20 --save-dir models
```

You can also call `env.evaluate(models, device, num_episodes=N)` for scripted evaluation in Python.

---

## 6) Headless / CI tips

- In headless CI set `SDL_VIDEODRIVER=dummy` (Linux/macOS) or set the equivalent for Windows.
- Use small `--iterations`/`--refine-steps` in tests to keep runs quick.

---

## 7) Tests & development notes

- Add focused unit tests to `tests/` or `archive/backup_contents/tests/`.
- The archive test runner is a handy smoke script:

```bash
$env:PYTHONPATH='D:\hhhh'; python archive/backup_contents/tests/run_tests.py
```

---

## 8) Troubleshooting (common issues)

- Missing dependencies: ensure you're in the virtualenv and re-run `pip install -r requirements.txt`.
- Pygame warnings on Windows: often benign; ensure compatible versions.
- If verification or training behaves unexpectedly, run the small smoke scripts and capture tracebacks for debugging.

---