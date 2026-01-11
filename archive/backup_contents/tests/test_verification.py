from env import WarehouseEnv
from verification import verify_collision_by_actions


def test_colliding_two_agents():
    env = WarehouseEnv(render=False)
    # place two robots facing each other so FORWARD,FORWARD causes a collision
    env.robots = []
    from agent import Robot, Direction
    # agent0 at (5,5) facing RIGHT, agent1 at (6,5) facing LEFT
    r0 = Robot(0, 5, 5)
    r1 = Robot(1, 6, 5)
    r0.dir = Direction.RIGHT
    r1.dir = Direction.LEFT
    env.robots.append(r0)
    env.robots.append(r1)

    actions = [[0, 0]]  # both FORWARD
    res = verify_collision_by_actions(env, actions)
    assert res['safe'] is False, "Expected a collision but verification reported safe"

if __name__ == '__main__':
    test_colliding_two_agents()
    print('verification collision test passed')