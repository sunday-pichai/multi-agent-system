"""Run a small reproducible verify -> refine experiment and save results.

Provides `run_experiment(args)` for programmatic use and a CLI.
"""
import argparse
import os
import csv
import time
from pathlib import Path

import torch

from eval_utils import set_seed
from main import run_verify_refine
from viz import plot_refinement_metrics
from env import WarehouseEnv
from dqn import DQN


def run_experiment(save_dir: str = 'experiments/models', seed: int = 42, iterations: int = 2, refine_steps: int = 50, refine_batch: int = 8, eval_episodes: int = 20):
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)

    set_seed(seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    env = WarehouseEnv(render=False)

    # initialize and save random models so run_verify_refine will load them
    dqns = [DQN(len(env.get_state(env.robots[0]))).to(device) for _ in range(env.num_agents)]
    for i, dqn in enumerate(dqns):
        torch.save(dqn.state_dict(), save_dir / f'dqn_agent_{i}.pth')

    # baseline evaluation
    pre_rate = env.evaluate(dqns, device, num_episodes=eval_episodes)

    # run the verify->refine loop via main.run_verify_refine
    class Args:
        pass

    args = Args()
    args.save_dir = str(save_dir)
    args.iterations = iterations
    args.refine_steps = refine_steps
    args.refine_batch = refine_batch

    run_verify_refine(args)

    # load refined models
    refined = [DQN(len(env.get_state(env.robots[0]))).to(device) for _ in range(env.num_agents)]
    for i, dqn in enumerate(refined):
        p = save_dir / f'dqn_agent_{i}.pth'
        if p.exists():
            dqn.load_state_dict(torch.load(p, map_location=device))

    post_rate = env.evaluate(refined, device, num_episodes=eval_episodes)

    # write CSV result
    results_dir = Path('experiments')
    results_dir.mkdir(exist_ok=True)
    out = results_dir / 'results.csv'
    first = not out.exists()
    with open(out, 'a', newline='') as fh:
        writer = csv.writer(fh)
        if first:
            writer.writerow(['timestamp', 'seed', 'iterations', 'refine_steps', 'pre_rate', 'post_rate', 'delta'])
        writer.writerow([int(time.time()), seed, iterations, refine_steps, pre_rate, post_rate, post_rate - pre_rate])

    # create a small metrics plot (only pre/post available here)
    metrics_path = results_dir / f'metrics_seed_{seed}.png'
    plot_refinement_metrics([0.0, 0.0], [pre_rate, post_rate], save_path=str(metrics_path), title='Refinement: pre vs post')

    print(f'Experiment complete. pre_rate={pre_rate:.2f}%, post_rate={post_rate:.2f}%')
    print('Results saved to', out)
    print('Metrics image saved to', metrics_path)

    return {'seed': seed, 'pre_rate': pre_rate, 'post_rate': post_rate}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-dir', type=str, default='experiments/models')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--iterations', type=int, default=2)
    parser.add_argument('--refine-steps', type=int, default=50)
    parser.add_argument('--refine-batch', type=int, default=8)
    parser.add_argument('--eval-episodes', type=int, default=20)
    args = parser.parse_args()

    run_experiment(save_dir=args.save_dir, seed=args.seed, iterations=args.iterations, refine_steps=args.refine_steps, refine_batch=args.refine_batch, eval_episodes=args.eval_episodes)


if __name__ == '__main__':
    main()