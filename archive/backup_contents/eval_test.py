from rw import WarehouseEnv, DQN, NUM_AGENTS, ACTION_SIZE
import torch
from pathlib import Path

env = WarehouseEnv(render=False)
device = torch.device("cpu")
dqns = [DQN(env.get_state(env.robots[0]).shape[0], ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
for i, dqn in enumerate(dqns):
    p = Path('models_test') / f'dqn_agent_{i}.pth'
    if p.exists():
        dqn.load_state_dict(torch.load(p, map_location=device))
        print('Loaded', p)

rate = env.evaluate(dqns, device, num_episodes=2, plot=False)
print('Eval rate:', rate)
