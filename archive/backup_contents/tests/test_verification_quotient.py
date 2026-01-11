from env import WarehouseEnv
from verification import verify_on_quotient


class DummyForwardModel:
    """Simple model that always returns action FORWARD (index 0) as highest Q."""
    def __call__(self, x):
        import torch
        # return a batch tensor with high value for action 0
        return torch.tensor([[10.0, 0.0, 0.0, 0.0, 0.0]])


def test_quotient_detection_and_falsifier():
    env = WarehouseEnv(render=False)
    # create two symmetric agents facing each other so identical policy (FORWARD) causes collision
    env.robots = []
    from agent import Robot, Direction
    r0 = Robot(0, 5, 5)
    r1 = Robot(1, 6, 5)
    r0.dir = Direction.RIGHT
    r1.dir = Direction.LEFT
    env.robots.append(r0)
    env.robots.append(r1)

    # make environment deterministic for the test: remove shelves so orbits depend only on robots
    env.shelves = []

    # force detect_permutation_symmetries to return a single orbit grouping the two agents
    import symmetry_reduction
    _orig = symmetry_reduction.detect_permutation_symmetries
    symmetry_reduction.detect_permutation_symmetries = lambda agents_pos, shelves_pos, grid_size=None: [{'orbit': [0, 1], 'signature': None}]

    try:
        model = DummyForwardModel()
        res = verify_on_quotient(env, policy_models=[model], horizon=2, trials=5)
        assert res['safe'] is False, f"Expected a collision under quotient policy, got {res}"
    finally:
        # restore
        symmetry_reduction.detect_permutation_symmetries = _orig


if __name__ == '__main__':
    test_quotient_detection_and_falsifier()
    print('verification quotient test passed')