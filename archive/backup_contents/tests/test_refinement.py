from env import WarehouseEnv
from refinement import extract_failure_cases, fine_tune_on_cases
from dqn import DQN


def test_extract_and_finetune_changes_weights():
    env = WarehouseEnv(render=False)
    # create a simple head-on collision
    env.robots = []
    from agent import Robot, Direction
    r0 = Robot(0, 5, 5)
    r1 = Robot(1, 6, 5)
    r0.dir = Direction.RIGHT
    r1.dir = Direction.LEFT
    env.robots.append(r0)
    env.robots.append(r1)

    # both forward will collide
    actions_sequence = [[0, 0]]

    # verify that collision would occur
    from verification import verify_collision_by_actions
    res = verify_collision_by_actions(env, actions_sequence)
    assert res['safe'] is False

    cases = extract_failure_cases(env, actions_sequence)
    assert len(cases) >= 2
    assert all('agent' in c and 'action' in c for c in cases)

    # build two small DQNs
    state_size = len(env.get_state(env.robots[0]))
    d0 = DQN(state_size)
    d1 = DQN(state_size)

    before0 = {k: v.clone() for k, v in d0.state_dict().items()}
    before1 = {k: v.clone() for k, v in d1.state_dict().items()}

    summary = fine_tune_on_cases([d0, d1], cases, steps=10, batch_size=4)
    assert 'loss' in summary

    after0 = d0.state_dict()
    after1 = d1.state_dict()

    changed0 = any(not torch.allclose(before0[k], after0[k]) for k in before0)
    changed1 = any(not torch.allclose(before1[k], after1[k]) for k in before1)
    assert changed0 or changed1


if __name__ == '__main__':
    test_extract_and_finetune_changes_weights()
    print('refinement test passed')