"""Simple smoke test: run `rw.py` in train mode via subprocess with small settings."""
import subprocess
import sys
from pathlib import Path

script = Path(__file__).parent / "rw.py"
cmd = [sys.executable, str(script), "--mode", "train", "--episodes", "4", "--steps-per-episode", "150", "--save-dir", "models_test", "--log-interval", "1", "--save-interval", "1000000"]
print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Stdout:\n", res.stdout)
print("Stderr:\n", res.stderr)

