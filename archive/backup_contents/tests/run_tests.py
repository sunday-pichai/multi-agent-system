import sys
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print('Running basic tests...')
from tests import test_dqn, test_env, test_symmetry, test_verification, test_verification_quotient, test_refinement, test_replay, test_verify_refine_integration  # noqa: E402

if __name__ == '__main__':
    test_dqn.test_dqn_forward_shape()
    print('DQN test OK')
    test_env.test_env_reset_step()
    print('Env test OK')
    test_symmetry.test_simple_symmetry_two_agents()
    test_symmetry.test_asymmetric_three_agents()
    print('Symmetry tests OK')
    test_verification.test_colliding_two_agents()
    print('Verification tests OK')
    test_verification_quotient.test_quotient_detection_and_falsifier()
    print('Verification (quotient) tests OK')
