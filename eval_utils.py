import random
import numpy as np
import torch
from typing import List, Tuple
from env import WarehouseEnv


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    try:
        torch.cuda.manual_seed_all(seed)
    except Exception:
        pass


def evaluate_repeated(dqns: List, device, episodes: int = 10, runs: int = 3) -> Tuple[float, float]:
    """Run evaluation multiple times and return (mean_collision_rate, std).

    This helps get a robust estimate across different random seeds.
    """
    env = WarehouseEnv(render=False)
    rates = []
    for r in range(runs):
        rate = env.evaluate(dqns, device, num_episodes=episodes, plot=False)
        rates.append(rate)
    return float(np.mean(rates)), float(np.std(rates))


def plot_trajectory_comparison(baseline_traj, repaired_traj, out_path=None):
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(8, 8))

    colors = plt.cm.rainbow(np.linspace(0, 1, len(baseline_traj)))
    for i, traj in enumerate(baseline_traj):
        x, y = zip(*traj)
        ax.plot(x, y, marker='o', markersize=3, linewidth=1, color=colors[i], alpha=0.6)
    for i, traj in enumerate(repaired_traj):
        x, y = zip(*traj)
        ax.plot(x, y, marker='x', markersize=4, linewidth=1.5, color='k', alpha=0.9)

    ax.set_xlim(0, 20)
    ax.set_ylim(0, 20)
    ax.set_title('Baseline (color) vs Repaired (black X) Trajectories')
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    plt.tight_layout()
    if out_path:
        plt.savefig(out_path)
    else:
        plt.show()
