from rw import WarehouseEnv

env = WarehouseEnv(render=False)
states = env.reset()
actions = [0] * env.num_agents
ns, rewards, done, cols, _ = env.step(actions)
print('states:', len(states), 'state-size:', len(states[0]))
print('next_states:', len(ns), 'rewards-sum:', sum(rewards), 'collisions:', cols, 'done:', done)
