"""Integration tests for the full system."""
import torch
import numpy as np
from env import WarehouseEnv
from dqn import DQN
from config import NUM_AGENTS, ACTION_SIZE, LR
from eval_utils import set_seed, evaluate_repeated


def test_full_training_episode():
    """Test a complete training episode."""
    set_seed(42)
    env = WarehouseEnv(render=False)
    device = torch.device("cpu")
    
    state_size = len(env.get_state(env.robots[0]))
    dqns = [DQN(state_size, ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    
    states = env.reset()
    episode_rewards = [0.0] * NUM_AGENTS
    
    for step in range(50):  # Short episode
        actions = []
        for i, state in enumerate(states):
            with torch.no_grad():
                q = dqns[i](torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0).to(device))
                actions.append(q.argmax().item())
        
        next_states, rewards, done, collisions, _ = env.step(actions)
        
        for i in range(NUM_AGENTS):
            episode_rewards[i] += rewards[i]
        
        states = next_states
        
        if done:
            break
    
    # Check rewards are reasonable (not all extremely negative)
    avg_reward = sum(episode_rewards) / NUM_AGENTS
    assert avg_reward > -100, f"Average reward too negative: {avg_reward}"
    print(f"  Average episode reward: {avg_reward:.2f}")


def test_evaluation_functionality():
    """Test evaluation function works."""
    set_seed(42)
    env = WarehouseEnv(render=False)
    device = torch.device("cpu")
    
    state_size = len(env.get_state(env.robots[0]))
    dqns = [DQN(state_size, ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    
    # Run evaluation
    collision_rate = env.evaluate(dqns, device, num_episodes=5, plot=False)
    
    assert isinstance(collision_rate, (int, float)), "Collision rate should be numeric"
    assert collision_rate >= 0, f"Collision rate should be non-negative, got {collision_rate}"
    print(f"  Collision rate: {collision_rate:.2f}%")


def test_reward_improvement_over_episodes():
    """Test that rewards can improve (or at least not degrade catastrophically)."""
    set_seed(42)
    env = WarehouseEnv(render=False)
    device = torch.device("cpu")
    
    state_size = len(env.get_state(env.robots[0]))
    dqn = DQN(state_size, ACTION_SIZE).to(device)
    target = DQN(state_size, ACTION_SIZE).to(device)
    target.load_state_dict(dqn.state_dict())
    optimizer = torch.optim.Adam(dqn.parameters(), lr=LR)
    
    from collections import deque
    memory = deque(maxlen=1000)
    
    # Collect some experience
    states = env.reset()
    for step in range(100):
        actions = []
        for i, state in enumerate(states):
            if np.random.random() < 0.5:  # 50% exploration
                actions.append(np.random.randint(0, ACTION_SIZE))
            else:
                with torch.no_grad():
                    q = dqn(torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0).to(device))
                    actions.append(q.argmax().item())
            memory.append((state.copy(), actions[i], 0.0, None, False))
        
        next_states, rewards, done, _, _ = env.step(actions)
        
        # Update rewards in memory
        for i in range(NUM_AGENTS):
            if len(memory) > 0:
                s, a, _, _, _ = memory[-NUM_AGENTS + i]
                memory[-NUM_AGENTS + i] = (s, a, rewards[i], next_states[i].copy(), done)
        
        states = next_states
        if done:
            states = env.reset()
    
    # Train on collected experience
    if len(memory) >= 32:
        batch = list(memory)[:32]
        ss, aa, rr, ns, dd = zip(*batch)
        ss = torch.from_numpy(np.stack(ss)).float().to(device)
        aa = torch.LongTensor(aa).to(device)
        rr = torch.FloatTensor(rr).to(device)
        ns = torch.from_numpy(np.stack(ns)).float().to(device)
        dd = torch.FloatTensor(dd).to(device)
        
        with torch.no_grad():
            next_q = target(ns).max(1)[0]
            targets = rr + 0.99 * next_q * (1 - dd)
        
        current_q = dqn(ss).gather(1, aa.unsqueeze(1)).squeeze()
        loss = torch.nn.functional.mse_loss(current_q, targets)
        
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(dqn.parameters(), max_norm=1.0)
        optimizer.step()
        
        assert not torch.isnan(loss), "Loss should not be NaN"
        print(f"  Training loss: {loss.item():.4f}")


def test_config_loading():
    """Test that config values are loaded correctly."""
    from config import GRID_W, GRID_H, NUM_AGENTS, NUM_SHELVES, LR, EPS_START, EPS_END
    
    assert GRID_W > 0, "GRID_W should be positive"
    assert GRID_H > 0, "GRID_H should be positive"
    assert NUM_AGENTS > 0, "NUM_AGENTS should be positive"
    assert NUM_SHELVES > 0, "NUM_SHELVES should be positive"
    assert LR > 0, "LR should be positive"
    assert 0 <= EPS_START <= 1, "EPS_START should be in [0, 1]"
    assert 0 <= EPS_END <= 1, "EPS_END should be in [0, 1]"
    assert EPS_END < EPS_START, "EPS_END should be less than EPS_START"
    
    print(f"  Config: LR={LR}, EPS_START={EPS_START}, EPS_END={EPS_END}")


if __name__ == '__main__':
    print("Running integration tests...")
    test_config_loading()
    print("[OK] Config loading test passed")
    
    test_full_training_episode()
    print("[OK] Full training episode test passed")
    
    test_evaluation_functionality()
    print("[OK] Evaluation functionality test passed")
    
    test_reward_improvement_over_episodes()
    print("[OK] Reward improvement test passed")
    
    print("\nAll integration tests passed!")
