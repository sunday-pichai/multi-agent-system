import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.run_verify_refine_experiment import run_experiment

if __name__ == '__main__':
    res = run_experiment(save_dir='experiments/models_demo_run', seed=43, iterations=1, refine_steps=10, refine_batch=4, eval_episodes=5)
    print('RETURNED:', res)
