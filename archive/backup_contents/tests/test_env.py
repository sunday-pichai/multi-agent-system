from env import WarehouseEnv

def test_env_reset_step():
    env = WarehouseEnv(render=False)
    states = env.reset()
    assert len(states) == env.num_agents
    actions = [0] * env.num_agents
    ns, rewards, done, cols, _ = env.step(actions)
    assert len(ns) == env.num_agents

if __name__ == '__main__':
    test_env_reset_step()
    print('Env reset/step smoke test passed')