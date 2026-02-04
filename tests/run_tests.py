"""Test runner for all tests."""
import sys
import importlib
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_module_tests(module):
    tests = [getattr(module, name) for name in dir(module) if name.startswith("test_")]
    for test_fn in tests:
        test_fn()


def run_all_tests() -> int:
    print("=" * 60)
    print("Running Warehouse MAS Test Suite")
    print("=" * 60)

    test_modules = [
        ("Reward Structure", "test_rewards"),
        ("Environment", "test_env"),
        ("Agent", "test_agent"),
        ("Planning Components", "test_training"),
        ("Integration", "test_integration"),
    ]

    tests_passed = 0
    tests_failed = 0

    for test_name, module_name in test_modules:
        print(f"\n{'=' * 60}")
        print(f"Running {test_name} Tests")
        print('=' * 60)
        try:
            module = importlib.import_module(f"tests.{module_name}")
            run_module_tests(module)
            tests_passed += 1
            print(f"\n[OK] {test_name} tests completed successfully")
        except Exception:
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
    print(f"\n[FAIL] {tests_failed} test suite(s) failed")
    return 1


if __name__ == '__main__':
    sys.exit(run_all_tests())
