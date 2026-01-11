from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import torch
from eval_utils import set_seed
from main import run_verify_refine
# plotting removed per user request (viz module deleted)
from env import WarehouseEnv
from dqn import DQN

print('DEBUG: starting debug run')
set_seed(42)
print('DEBUG: seed set')

env = WarehouseEnv(render=False)
print('DEBUG: env created, num_agents=', env.num_agents)

save_dir = Path('experiments/models_debug')
save_dir.mkdir(parents=True, exist_ok=True)

# initialize and save
dqns = [DQN(len(env.get_state(env.robots[0]))).to('cpu') for _ in range(env.num_agents)]
for i, dqn in enumerate(dqns):
    torch.save(dqn.state_dict(), save_dir / f'dqn_agent_{i}.pth')
print('DEBUG: initial models saved to', save_dir)

pre_rate = env.evaluate(dqns, 'cpu', num_episodes=5)
print('DEBUG: pre_rate=', pre_rate)

class Args: pass
args = Args(); args.save_dir = str(save_dir); args.iterations=1; args.refine_steps=10; args.refine_batch=4
print('DEBUG: running verify_refine')
run_verify_refine(args)
print('DEBUG: run_verify_refine returned')

# load refined models
refined = [DQN(len(env.get_state(env.robots[0]))).to('cpu') for _ in range(env.num_agents)]
for i, dqn in enumerate(refined):
    p = save_dir / f'dqn_agent_{i}.pth'
    if p.exists():
        dqn.load_state_dict(torch.load(p, map_location='cpu'))
print('DEBUG: loaded refined models')

post_rate = env.evaluate(refined, 'cpu', num_episodes=5)
print('DEBUG: post_rate=', post_rate)

print('DEBUG: finished')