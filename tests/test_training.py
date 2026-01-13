"""Test training components: DQN, optimizer, replay buffer."""
import torch
import numpy as np
from dqn import DQN
from config import ACTION_SIZE, LR
from replay import ReplayBuffer, PrioritizedReplayBuffer
from env import WarehouseEnv


def test_dqn_forward():
    """Test DQN forward pass."""
    state_size = 100
    model = DQN(state_size, ACTION_SIZE)
    
    x = torch.randn(2, state_size)
    y = model(x)
    
    assert y.shape == (2, ACTION_SIZE), f"Expected shape (2, {ACTION_SIZE}), got {y.shape}"
    assert not torch.isnan(y).any(), "Output should not contain NaN"
    assert not torch.isinf(y).any(), "Output should not contain Inf"


def test_dqn_gradient_flow():
    """Test DQN gradients flow correctly."""
    state_size = 100
    model = DQN(state_size, ACTION_SIZE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    x = torch.randn(1, state_size)
    y = model(x)
    loss = y.sum()
    
    optimizer.zero_grad()
    loss.backward()
    
    # Check gradients exist
    has_grad = False
    for param in model.parameters():
        if param.grad is not None:
            has_grad = True
            assert not torch.isnan(param.grad).any(), "Gradients should not contain NaN"
            break
    
    assert has_grad, "At least one parameter should have gradients"


def test_dqn_gradient_clipping():
    """Test gradient clipping works."""
    state_size = 100
    model = DQN(state_size, ACTION_SIZE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    x = torch.randn(1, state_size)
    y = model(x)
    loss = y.sum()
    
    optimizer.zero_grad()
    loss.backward()
    
    # Clip gradients
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    
    # Check gradients are clipped
    total_norm = 0
    for param in model.parameters():
        if param.grad is not None:
            param_norm = param.grad.data.norm(2)
            total_norm += param_norm.item() ** 2
    total_norm = total_norm ** (1. / 2)
    
    assert total_norm <= 1.1, f"Gradient norm should be <= 1.0, got {total_norm}"  # Small tolerance


def test_replay_buffer():
    """Test basic replay buffer functionality."""
    buffer = ReplayBuffer(capacity=100)
    
    # Add transitions
    for i in range(50):
        buffer.push((i, i+1, i+2))
    
    assert len(buffer) == 50, f"Expected 50 items, got {len(buffer)}"
    
    # Sample
    batch = buffer.sample(10)
    assert len(batch) == 10, f"Expected batch size 10, got {len(batch)}"
    
    # Test capacity
    for i in range(100):
        buffer.push((i, i+1, i+2))
    
    assert len(buffer) == 100, f"Expected capacity 100, got {len(buffer)}"


def test_prioritized_replay_buffer():
    """Test prioritized replay buffer."""
    buffer = PrioritizedReplayBuffer(capacity=100)
    
    # Add transitions with priorities
    for i in range(50):
        buffer.push((i, i+1, i+2), priority=float(i))
    
    assert len(buffer) == 50, f"Expected 50 items, got {len(buffer)}"
    
    # Sample with indices
    indices, batch = buffer.sample(10, return_indices=True)
    assert len(batch) == 10, f"Expected batch size 10, got {len(batch)}"
    assert len(indices) == 10, f"Expected 10 indices, got {len(indices)}"
    
    # Update priorities
    new_priorities = [1.0] * 10
    buffer.update_priorities(indices, new_priorities)
    
    # Verify priorities updated
    assert buffer.priorities[indices[0]] > 0, "Priority should be updated"


def test_dqn_training_step():
    """Test a single DQN training step."""
    env = WarehouseEnv(render=False)
    states = env.reset()
    state_size = len(states[0])
    
    model = DQN(state_size, ACTION_SIZE)
    target = DQN(state_size, ACTION_SIZE)
    target.load_state_dict(model.state_dict())
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    # Create a batch of transitions
    batch_size = 32
    states_batch = torch.randn(batch_size, state_size)
    actions_batch = torch.randint(0, ACTION_SIZE, (batch_size,))
    rewards_batch = torch.randn(batch_size)
    next_states_batch = torch.randn(batch_size, state_size)
    dones_batch = torch.zeros(batch_size)
    
    # Compute targets
    with torch.no_grad():
        next_q = target(next_states_batch).max(1)[0]
        targets = rewards_batch + 0.99 * next_q * (1 - dones_batch)
    
    # Compute current Q values
    current_q = model(states_batch).gather(1, actions_batch.unsqueeze(1)).squeeze()
    
    # Compute loss
    loss = torch.nn.functional.mse_loss(current_q, targets)
    
    # Backward pass
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()
    
    assert not torch.isnan(loss), "Loss should not be NaN"
    assert loss.item() >= 0, "Loss should be non-negative"


def test_optimizer_uses_config_lr():
    """Test optimizer uses the correct learning rate from config."""
    model = DQN(100, ACTION_SIZE)
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    
    # Check optimizer has correct LR
    assert optimizer.param_groups[0]['lr'] == LR, f"Expected LR {LR}, got {optimizer.param_groups[0]['lr']}"


if __name__ == '__main__':
    print("Testing training components...")
    test_dqn_forward()
    print("✓ DQN forward test passed")
    
    test_dqn_gradient_flow()
    print("✓ DQN gradient flow test passed")
    
    test_dqn_gradient_clipping()
    print("✓ DQN gradient clipping test passed")
    
    test_replay_buffer()
    print("✓ Replay buffer test passed")
    
    test_prioritized_replay_buffer()
    print("✓ Prioritized replay buffer test passed")
    
    test_dqn_training_step()
    print("✓ DQN training step test passed")
    
    test_optimizer_uses_config_lr()
    print("✓ Optimizer LR test passed")
    
    print("\nAll training component tests passed! ✓")
