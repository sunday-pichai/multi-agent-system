from main import run_verify_refine
from dqn import DQN
from env import WarehouseEnv
import torch


def test_verify_refine_loop_one_iteration(tmp_path):
    # create a simple env with two head-on robots and a policy that moves forward
    env = WarehouseEnv(render=False)
    env.robots = []
    from agent import Robot, Direction
    r0 = Robot(0, 5, 5)
    r1 = Robot(1, 6, 5)
    r0.dir = Direction.RIGHT
    r1.dir = Direction.LEFT
    env.robots.append(r0)
    env.robots.append(r1)

    # create two small DQNs and save them to tmp dir
    p = tmp_path
    d0 = DQN(len(env.get_state(env.robots[0])))
    d1 = DQN(len(env.get_state(env.robots[0])))
    torch.save(d0.state_dict(), p / 'dqn_agent_0.pth')
    torch.save(d1.state_dict(), p / 'dqn_agent_1.pth')

    args = type('A', (), {})()
    args.save_dir = str(p)
    args.iterations = 1
    args.refine_steps = 5
    args.refine_batch = 4

    # run one iteration of verify-refine (should complete without error)
    run_verify_refine(args)

    # also ensure prioritized replay updates (indirect test): create buffer and update priorities
    from replay import PrioritizedReplayBuffer
    buf = PrioritizedReplayBuffer(capacity=10)
    buf.push(('a', 0), priority=1.0)
    idxs, items = buf.sample(1, return_indices=True)
    buf.update_priorities(idxs, [5.0])
    assert buf.priorities[idxs[0]] >= 5.0
    # expect models written back
    import os
    assert os.path.exists(os.path.join(str(p), 'dqn_agent_0.pth'))
    assert os.path.exists(os.path.join(str(p), 'dqn_agent_1.pth'))


if __name__ == '__main__':
    import pathlib
    test_verify_refine_loop_one_iteration(pathlib.Path('.'))
    print('verify-refine integration test passed')