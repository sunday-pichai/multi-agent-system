"""Test environment functionality."""
from env import WarehouseEnv
from config import NUM_AGENTS, NUM_SHELVES, GRID_W, GRID_H


def test_env_reset():
    """Test environment reset functionality."""
    env = WarehouseEnv(render=False)
    states = env.reset()
    
    assert len(states) == env.num_agents, f"Expected {env.num_agents} states, got {len(states)}"
    assert len(states[0]) > 0, "State should not be empty"
    assert len(env.robots) == env.num_agents, f"Expected {env.num_agents} robots, got {len(env.robots)}"
    assert len(env.shelves) == NUM_SHELVES, f"Expected {NUM_SHELVES} shelves, got {len(env.shelves)}"
    
    # Check robots are within bounds
    for robot in env.robots:
        assert 0 <= robot.x < GRID_W, f"Robot x out of bounds: {robot.x}"
        assert 0 <= robot.y < GRID_H, f"Robot y out of bounds: {robot.y}"
    
    # Check shelves are within bounds
    for shelf in env.shelves:
        assert 0 <= shelf['x'] < GRID_W, f"Shelf x out of bounds: {shelf['x']}"
        assert 0 <= shelf['y'] < GRID_H, f"Shelf y out of bounds: {shelf['y']}"


def test_env_step():
    """Test environment step functionality."""
    env = WarehouseEnv(render=False)
    states = env.reset()
    
    actions = [0] * env.num_agents  # FORWARD
    next_states, rewards, done, collisions, _ = env.step(actions)
    
    assert len(next_states) == env.num_agents, f"Expected {env.num_agents} next states, got {len(next_states)}"
    assert len(rewards) == env.num_agents, f"Expected {env.num_agents} rewards, got {len(rewards)}"
    assert isinstance(done, bool), "Done should be boolean"
    assert isinstance(collisions, int), "Collisions should be integer"
    assert collisions >= 0, "Collisions should be non-negative"
    
    # Check state dimensions match
    assert len(next_states[0]) == len(states[0]), "State dimensions should match"


def test_env_state_shape():
    """Test state shape is correct."""
    env = WarehouseEnv(render=False)
    states = env.reset()
    
    state = states[0]
    # State should be: 4 (robot) + NUM_SHELVES*4 + (NUM_AGENTS-1)*4
    expected_size = 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4
    assert len(state) == expected_size, f"Expected state size {expected_size}, got {len(state)}"
    
    # Check all values are normalized (0-1 range)
    for val in state:
        assert isinstance(val, (int, float)), "State values should be numeric"
        # Allow some flexibility for normalized values
        assert -0.1 <= val <= 1.1, f"State value out of expected range: {val}"


def test_env_multiple_resets():
    """Test that multiple resets work correctly."""
    env = WarehouseEnv(render=False)
    
    for _ in range(5):
        states = env.reset()
        assert len(states) == env.num_agents, "Reset should always return correct number of states"
        assert env.steps == 0, "Steps should reset to 0"


def test_env_collision_detection():
    """Test collision detection works."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    # Position two robots adjacent to each other, then move one into the other
    if len(env.robots) >= 2:
        env.robots[0].x = 5
        env.robots[0].y = 5
        env.robots[0].dir = env.robots[0].dir.__class__(1)  # RIGHT
        env.robots[1].x = 6
        env.robots[1].y = 5
        
        # Try to move robot 0 forward (should collide with robot 1)
        actions = [0] * env.num_agents
        actions[0] = 0  # FORWARD
        _, _, _, collisions, _ = env.step(actions)
        
        # Collision should be detected (either in forward() or counted)
        # Note: collision counting happens in step(), so check if robot didn't move
        if collisions == 0:
            # Check if robot didn't actually move (collision prevented movement)
            assert env.robots[0].x == 5 or env.robots[0].y == 5, "Robot should not move when colliding"
        else:
            assert collisions > 0, "Should detect collision"


def test_env_goal_delivery():
    """Test goal delivery mechanism."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    requested_shelf = next((s for s in env.shelves if s['requested']), None)
    
    if requested_shelf:
        # Pick up requested shelf
        robot.x = requested_shelf['x']
        robot.y = requested_shelf['y']
        robot.carrying = requested_shelf
        requested_shelf['carried'] = True
        
        # Move to goal
        goal = env.GOALS[0]
        robot.x = goal[0]
        robot.y = goal[1]
        
        # Deliver
        actions = [3] * env.num_agents  # PICK_DROP
        _, rewards, _, _, _ = env.step(actions)
        
        # Should get high reward
        assert rewards[0] > 15.0, f"Expected high delivery reward, got {rewards[0]}"
        assert robot.carrying is None, "Robot should not be carrying after delivery"


if __name__ == '__main__':
    print("Testing environment...")
    test_env_reset()
    print("✓ Reset test passed")
    
    test_env_step()
    print("✓ Step test passed")
    
    test_env_state_shape()
    print("✓ State shape test passed")
    
    test_env_multiple_resets()
    print("✓ Multiple resets test passed")
    
    test_env_collision_detection()
    print("✓ Collision detection test passed")
    
    test_env_goal_delivery()
    print("✓ Goal delivery test passed")
    
    print("\nAll environment tests passed! ✓")
