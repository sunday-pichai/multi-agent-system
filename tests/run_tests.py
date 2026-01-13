"""Test runner for all tests."""
import sys
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def run_all_tests():
    """Run all test modules."""
    print("=" * 60)
    print("Running Warehouse MAS Test Suite")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    test_modules = [
        ("Reward Structure", "test_rewards"),
        ("Environment", "test_env"),
        ("Agent", "test_agent"),
        ("Training Components", "test_training"),
        ("Integration", "test_integration"),
    ]
    
    for test_name, module_name in test_modules:
        print(f"\n{'=' * 60}")
        print(f"Running {test_name} Tests")
        print('=' * 60)
        try:
            module = __import__(f"tests.{module_name}", fromlist=[module_name])
            if hasattr(module, '__main__'):
                # Run main if it exists
                if hasattr(module, 'test_all'):
                    module.test_all()
                else:
                    # Import and run individual test functions
                    import importlib
                    importlib.reload(module)
            tests_passed += 1
            print(f"\n[OK] {test_name} tests completed successfully")
        except Exception as e:
            tests_failed += 1
            print(f"\n[FAIL] {test_name} tests FAILED")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Passed: {tests_passed}")
    print(f"Failed: {tests_failed}")
    print("=" * 60)
    
    if tests_failed == 0:
        print("\nAll tests passed!")
        return 0
    else:
        print(f"\n[FAIL] {tests_failed} test suite(s) failed")
        return 1


if __name__ == '__main__':
    # Run individual test modules
    from tests import test_rewards
    from tests import test_env
    from tests import test_agent
    from tests import test_training
    from tests import test_integration
    
    print("=" * 60)
    print("Running Warehouse MAS Test Suite")
    print("=" * 60)
    print()
    
    try:
        print("\n" + "=" * 60)
        print("Reward Structure Tests")
        print("=" * 60)
        test_rewards.test_step_penalty()
        print("[OK] Step penalty test passed")
        test_rewards.test_collision_penalty()
        print("[OK] Collision penalty test passed")
        test_rewards.test_delivery_reward()
        print("[OK] Delivery reward test passed")
        test_rewards.test_pick_rewards()
        print("[OK] Pick rewards test passed")
        test_rewards.test_distance_reward()
        print("[OK] Distance reward test passed")
        test_rewards.test_successful_forward_reward()
        print("[OK] Successful forward reward test passed")
    except Exception as e:
        print(f"[FAIL] Reward tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("Environment Tests")
        print("=" * 60)
        test_env.test_env_reset()
        print("[OK] Reset test passed")
        test_env.test_env_step()
        print("[OK] Step test passed")
        test_env.test_env_state_shape()
        print("[OK] State shape test passed")
        test_env.test_env_multiple_resets()
        print("[OK] Multiple resets test passed")
        test_env.test_env_collision_detection()
        print("[OK] Collision detection test passed")
        test_env.test_env_goal_delivery()
        print("[OK] Goal delivery test passed")
    except Exception as e:
        print(f"[FAIL] Environment tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("Agent Tests")
        print("=" * 60)
        test_agent.test_robot_initialization()
        print("[OK] Initialization test passed")
        test_agent.test_robot_turn_left()
        print("[OK] Turn left test passed")
        test_agent.test_robot_turn_right()
        print("[OK] Turn right test passed")
        test_agent.test_robot_forward_movement()
        print("[OK] Forward movement test passed")
        test_agent.test_robot_boundary_collision()
        print("[OK] Boundary collision test passed")
        test_agent.test_robot_agent_collision()
        print("[OK] Agent collision test passed")
        test_agent.test_robot_pick_shelf()
        print("[OK] Pick shelf test passed")
        test_agent.test_robot_deliver_shelf()
        print("[OK] Deliver shelf test passed")
        test_agent.test_robot_drop_shelf()
        print("[OK] Drop shelf test passed")
    except Exception as e:
        print(f"[FAIL] Agent tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("Training Component Tests")
        print("=" * 60)
        test_training.test_dqn_forward()
        print("[OK] DQN forward test passed")
        test_training.test_dqn_gradient_flow()
        print("[OK] DQN gradient flow test passed")
        test_training.test_dqn_gradient_clipping()
        print("[OK] DQN gradient clipping test passed")
        test_training.test_replay_buffer()
        print("[OK] Replay buffer test passed")
        test_training.test_prioritized_replay_buffer()
        print("[OK] Prioritized replay buffer test passed")
        test_training.test_dqn_training_step()
        print("[OK] DQN training step test passed")
        test_training.test_optimizer_uses_config_lr()
        print("[OK] Optimizer LR test passed")
    except Exception as e:
        print(f"[FAIL] Training component tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    try:
        print("\n" + "=" * 60)
        print("Integration Tests")
        print("=" * 60)
        test_integration.test_config_loading()
        print("[OK] Config loading test passed")
        test_integration.test_full_training_episode()
        print("[OK] Full training episode test passed")
        test_integration.test_evaluation_functionality()
        print("[OK] Evaluation functionality test passed")
        test_integration.test_reward_improvement_over_episodes()
        print("[OK] Reward improvement test passed")
    except Exception as e:
        print(f"[FAIL] Integration tests failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
