# Warehouse MAS Commands

## 1) Setup

```bash
python -m pip install -r requirements.txt
python main.py --help
```

## 2) Main Run Modes

```bash
# Interactive (default mode)
python main.py

# Interactive (explicit)
python main.py --mode interactive

# Batch simulation (no render)
python main.py --mode simulate --episodes 8 --steps-per-episode 200

# Batch simulation with rendering
python main.py --mode simulate --render --episodes 3 --steps-per-episode 120

# Evaluation mode
python main.py --mode eval --eval-episodes 3 --steps-per-episode 150
```

## 3) Verification and Refinement (Safety Check)

```bash
# Main verification/refinement command
python main.py --verify-refine --verify-horizon 30 --verify-trials 20

# More aggressive check
python main.py --verify-refine --verify-horizon 40 --verify-trials 30 --refine-iterations 3 --refine-max-constraints 150
```

## 4) Symmetry Check

```bash
python main.py --detect-symmetry
```

## 5) Reproducibility / Config Overrides

```bash
# Fixed random seed
python main.py --mode simulate --seed 42

# Use specific config file
python main.py --config config.yaml --mode simulate

# Override planner horizon from CLI
python main.py --mode eval --plan-horizon 35
```

## 6) Test Commands

```bash
# Main bundled test runner
python tests/run_tests.py

# Focused suites
python tests/test_refinement.py
python tests/test_verification_refinement.py
python tests/test_training.py
python tests/test_integration.py
```

## 7) Quick Sanity Check Flow

```bash
python main.py --help
python main.py --mode simulate --episodes 2 --steps-per-episode 80
python main.py --verify-refine --verify-horizon 30 --verify-trials 20
python tests/run_tests.py
```
