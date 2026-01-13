"""Test agent (Robot) functionality."""
from agent import Robot, Direction, Action
from env import WarehouseEnv


def test_robot_initialization():
    """Test robot initialization."""
    robot = Robot(0, 5, 5)
    
    assert robot.id == 0, "Robot ID should be 0"
    assert robot.x == 5, "Robot x should be 5"
    assert robot.y == 5, "Robot y should be 5"
    assert robot.dir in Direction, "Robot direction should be valid"
    assert robot.carrying is None, "Robot should not be carrying initially"


def test_robot_turn_left():
    """Test robot turning left."""
    robot = Robot(0, 5, 5)
    initial_dir = robot.dir
    
    robot.turn_left()
    
    # Direction should change
    assert robot.dir != initial_dir, "Direction should change after turn_left"
    # Should cycle: UP -> LEFT -> DOWN -> RIGHT -> UP
    expected_value = (initial_dir.value - 1) % 4
    assert robot.dir.value == expected_value, f"Expected direction value {expected_value}, got {robot.dir.value}"


def test_robot_turn_right():
    """Test robot turning right."""
    robot = Robot(0, 5, 5)
    initial_dir = robot.dir
    
    robot.turn_right()
    
    # Direction should change
    assert robot.dir != initial_dir, "Direction should change after turn_right"
    # Should cycle: UP -> RIGHT -> DOWN -> LEFT -> UP
    expected_value = (initial_dir.value + 1) % 4
    assert robot.dir.value == expected_value, f"Expected direction value {expected_value}, got {robot.dir.value}"


def test_robot_forward_movement():
    """Test robot forward movement."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    old_x, old_y = robot.x, robot.y
    robot.dir = Direction.UP  # Move up
    
    moved, bump = robot.forward(env)
    
    if not bump:
        assert moved, "Should move if no bump"
        assert robot.y == old_y - 1, "Should move up (y decreases)"
        assert robot.x == old_x, "X should not change when moving up"


def test_robot_boundary_collision():
    """Test robot collision with boundary."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    robot.x = 0
    robot.y = 0
    robot.dir = Direction.LEFT  # Try to move left (out of bounds)
    
    moved, bump = robot.forward(env)
    
    assert not moved, "Should not move when hitting boundary"
    assert bump, "Should detect boundary bump"
    assert robot.x == 0, "X should not change"
    assert robot.y == 0, "Y should not change"


def test_robot_agent_collision():
    """Test robot collision with another agent."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    if len(env.robots) >= 2:
        robot1 = env.robots[0]
        robot2 = env.robots[1]
        
        robot1.x = 5
        robot1.y = 5
        robot1.dir = Direction.RIGHT
        
        robot2.x = 6
        robot2.y = 5
        
        moved, bump = robot1.forward(env)
        
        assert not moved, "Should not move when colliding with another agent"
        assert bump, "Should detect agent collision"


def test_robot_pick_shelf():
    """Test robot picking up a shelf."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    shelf = env.shelves[0]
    
    robot.x = shelf['x']
    robot.y = shelf['y']
    robot.carrying = None
    shelf['carried'] = False
    
    reward, msg = robot.pick_or_drop(env)
    
    assert robot.carrying == shelf, "Robot should be carrying the shelf"
    assert shelf['carried'] == True, "Shelf should be marked as carried"
    assert msg == "PICKED", f"Expected 'PICKED', got '{msg}'"
    assert reward > 0, f"Should get positive reward for picking, got {reward}"


def test_robot_deliver_shelf():
    """Test robot delivering a requested shelf to goal."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    requested_shelf = next((s for s in env.shelves if s['requested']), None)
    
    if requested_shelf:
        robot.carrying = requested_shelf
        robot.x = env.GOALS[0][0]
        robot.y = env.GOALS[0][1]
        
        initial_shelf_count = len(env.shelves)
        
        reward, msg = robot.pick_or_drop(env)
        
        assert msg == "DELIVERED", f"Expected 'DELIVERED', got '{msg}'"
        assert reward > 15.0, f"Should get high reward for delivery, got {reward}"
        assert robot.carrying is None, "Robot should not be carrying after delivery"
        # New shelf should be created
        assert len(env.shelves) == initial_shelf_count, "New shelf should be created after delivery"


def test_robot_drop_shelf():
    """Test robot dropping a shelf (not at goal)."""
    env = WarehouseEnv(render=False)
    env.reset()
    
    robot = env.robots[0]
    shelf = env.shelves[0]
    
    robot.carrying = shelf
    robot.x = 5  # Not at goal
    robot.y = 5
    
    reward, msg = robot.pick_or_drop(env)
    
    assert msg == "DROPPED", f"Expected 'DROPPED', got '{msg}'"
    assert robot.carrying is None, "Robot should not be carrying after drop"
    assert shelf['carried'] == False, "Shelf should not be marked as carried"


if __name__ == '__main__':
    print("Testing agent functionality...")
    test_robot_initialization()
    print("✓ Initialization test passed")
    
    test_robot_turn_left()
    print("✓ Turn left test passed")
    
    test_robot_turn_right()
    print("✓ Turn right test passed")
    
    test_robot_forward_movement()
    print("✓ Forward movement test passed")
    
    test_robot_boundary_collision()
    print("✓ Boundary collision test passed")
    
    test_robot_agent_collision()
    print("✓ Agent collision test passed")
    
    test_robot_pick_shelf()
    print("✓ Pick shelf test passed")
    
    test_robot_deliver_shelf()
    print("✓ Deliver shelf test passed")
    
    test_robot_drop_shelf()
    print("✓ Drop shelf test passed")
    
    print("\nAll agent tests passed! ✓")
