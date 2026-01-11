"""viz module removed — plotting disabled per user request."""

raise ModuleNotFoundError("viz module has been removed from this project")


def plot_trajectories(trace: List[List[Tuple[int, int]]], env, save_path: str = None, title: str = "Trajectories"):
    """Plot agent trajectories from a counterexample trace.

    trace: list of timesteps, each entry is a list of (x,y) tuples for each agent
    env: WarehouseEnv instance (for grid size and goals)
    save_path: if provided, save the figure to this path
    """
    if not trace or not trace[0]:
        raise ValueError("Empty trace provided")

    num_agents = len(trace[0])
    # build per-agent trajectory lists
    trajectories = [[] for _ in range(num_agents)]
    for t in trace:
        for i, pos in enumerate(t):
            trajectories[i].append(pos)

    fig, ax = plt.subplots(figsize=(6, 6))
    colors = plt.cm.tab10(np.linspace(0, 1, num_agents))
    for i, traj in enumerate(trajectories):
        xs, ys = zip(*traj)
        ax.plot(xs, ys, marker='o', linewidth=2, markersize=4, color=colors[i], label=f'Agent {i+1}')
        ax.scatter(xs[0], ys[0], marker='s', color=colors[i], s=80, label=f'Start {i+1}')
        ax.scatter(xs[-1], ys[-1], marker='X', color=colors[i], s=80, label=f'End {i+1}')

    # Goals
    if hasattr(env, 'GOALS'):
        for gx, gy in env.GOALS:
            ax.scatter(gx, gy, marker='*', color='gold', s=120, edgecolor='k')

    ax.set_xlim(-0.5, env.grid_w - 0.5)
    ax.set_ylim(-0.5, env.grid_h - 0.5)
    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    if save_path:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        fig.savefig(save_path)
        plt.close(fig)
    else:
        plt.show()


def plot_collision_heatmap(trace: List[List[Tuple[int, int]]], env, save_path: str = None, title: str = "Collision Heatmap"):
    """Plot a heatmap of visit counts across the grid and mark collision steps."""
    if not trace or not trace[0]:
        raise ValueError("Empty trace provided")

    grid = np.zeros((env.grid_h, env.grid_w), dtype=np.int32)
    collisions = []
    for t_idx, t in enumerate(trace):
        for pos in t:
            x, y = pos
            if 0 <= x < env.grid_w and 0 <= y < env.grid_h:
                grid[env.grid_h - 1 - y, x] += 1  # flip y for plotting
        # detect collisions (same pos by multiple agents)
        seen = {}
        for i, pos in enumerate(t):
            seen.setdefault(pos, []).append(i)
        for pos, agents in seen.items():
            if len(agents) > 1:
                collisions.append((t_idx, pos))

    fig, ax = plt.subplots(figsize=(6, 6))
    im = ax.imshow(grid, cmap='Reds')
    ax.set_title(title)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # overlay collisions
    for t_idx, (x, y) in collisions:
        ay = env.grid_h - 1 - y
        ax.scatter(x, ay, marker='X', color='black', s=80)

    if save_path:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        fig.savefig(save_path)
        plt.close(fig)
    else:
        plt.show()


def plot_refinement_metrics(losses: List[float], collision_rates: List[float], save_path: str = None, title: str = "Refinement Metrics"):
    fig, ax1 = plt.subplots(figsize=(8, 4))

    ax1.plot(losses, label='Loss', color='tab:blue')
    ax1.set_xlabel('Iteration')
    ax1.set_ylabel('Loss', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.plot(collision_rates, label='Collision Rate', color='tab:red')
    ax2.set_ylabel('Collision Rate (%)', color='tab:red')
    ax2.tick_params(axis='y', labelcolor='tab:red')

    ax1.legend(loc='upper left')
    ax2.legend(loc='upper right')
    plt.title(title)
    plt.tight_layout()

    if save_path:
        dirpath = os.path.dirname(save_path)
        if dirpath:
            os.makedirs(dirpath, exist_ok=True)
        fig.savefig(save_path)
        plt.close(fig)
    else:
        plt.show()