import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1] / 'archive' / 'backup_contents'
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests import test_dqn, test_env, test_symmetry, test_verification, test_verification_quotient

print('DQN')
test_dqn.test_dqn_forward_shape()
print('DQN OK')
print('Env')
test_env.test_env_reset_step()
print('Env OK')
print('Symmetry')
test_symmetry.test_simple_symmetry_two_agents()
test_symmetry.test_asymmetric_three_agents()
print('Symmetry OK')
print('Verification collision')
test_verification.test_colliding_two_agents()
print('Verification collision OK')
print('Verification quotient')
try:
    test_verification_quotient.test_quotient_detection_and_falsifier()
    print('Verification quotient OK')
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Verification quotient FAILED')
