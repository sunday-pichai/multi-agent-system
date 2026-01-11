import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.run_verify_refine_experiment import run_experiment

if __name__ == '__main__':
    res = run_experiment(save_dir='experiments/models_demo_run', seed=42, iterations=2, refine_steps=30, refine_batch=8, eval_episodes=10)
    print('RETURNED:', res)
