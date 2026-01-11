from viz import plot_trajectories, plot_collision_heatmap, plot_refinement_metrics
from env import WarehouseEnv
import tempfile
import os


def test_plot_trajectories_and_heatmap_creates_files():
    env = WarehouseEnv(render=False)
    # simple two-agent head-on collision
    env.robots = []
    from agent import Robot, Direction
    r0 = Robot(0, 2, 2)
    r1 = Robot(1, 3, 2)
    r0.dir = Direction.RIGHT
    r1.dir = Direction.LEFT
    env.robots.append(r0)
    env.robots.append(r1)

    trace = [ [(2,2), (3,2)], [(3,2), (2,2)] ]  # collision at step 1

    tmp = tempfile.mkdtemp()
    tpath = os.path.join(tmp, 'traj.png')
    hpath = os.path.join(tmp, 'heat.png')
    mpath = os.path.join(tmp, 'metrics.png')

    plot_trajectories(trace, env, save_path=tpath)
    plot_collision_heatmap(trace, env, save_path=hpath)
    plot_refinement_metrics([1.0, 0.5], [12.0, 4.0], save_path=mpath)

    assert os.path.exists(tpath)
    assert os.path.exists(hpath)
    assert os.path.exists(mpath)


if __name__ == '__main__':
    test_plot_trajectories_and_heatmap_creates_files()
    print('viz tests passed')