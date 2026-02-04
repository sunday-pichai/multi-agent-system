"""Integration tests for the planning-based system."""
from env import WarehouseEnv
from pathfinding import CooperativePlanner
from config import GRID_W, GRID_H, NUM_AGENTS, PLAN_HORIZON


def test_config_loading():
    assert GRID_W > 0, "GRID_W should be positive"
    assert GRID_H > 0, "GRID_H should be positive"
    assert NUM_AGENTS > 0, "NUM_AGENTS should be positive"
    assert PLAN_HORIZON > 0, "PLAN_HORIZON should be positive"


def test_simulation_episode():
    env = WarehouseEnv(render=False)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=20)

    env.reset()
    total_collisions = 0
    for _ in range(50):
        actions = planner.compute_actions(env)
        _, _, done, cols, _ = env.step(actions)
        total_collisions += cols
        if done:
            break

    assert total_collisions >= 0, "Collision count should be non-negative"


def test_evaluation_functionality():
    env = WarehouseEnv(render=False)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=20)

    collision_rate = env.evaluate(planner, num_episodes=3, max_steps_per_episode=50)

    assert isinstance(collision_rate, (int, float)), "Collision rate should be numeric"
    assert collision_rate >= 0, "Collision rate should be non-negative"


if __name__ == '__main__':
    print("Running integration tests...")
    test_config_loading()
    print("[OK] Config loading test passed")

    test_simulation_episode()
    print("[OK] Simulation episode test passed")

    test_evaluation_functionality()
    print("[OK] Evaluation functionality test passed")

    print("\nAll integration tests passed!")
