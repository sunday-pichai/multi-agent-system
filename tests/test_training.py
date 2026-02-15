"""Test planning components: Cooperative A*, reservations, and action output."""
from env import WarehouseEnv
from pathfinding import CooperativePlanner, ReservationTable, astar_time
from agent import Direction, Action


def test_planner_action_output():
    env = WarehouseEnv(render=False)
    env.reset()
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=30)

    actions = planner.compute_actions(env)

    assert len(actions) == env.num_agents, f"Expected {env.num_agents} actions, got {len(actions)}"
    assert all(isinstance(a, int) for a in actions), "Actions should be integer-encoded"
    assert all(0 <= a <= 4 for a in actions), "Actions should be within Action enum range"


def test_astar_simple_path():
    reservations = ReservationTable()
    path = astar_time(
        (0, 0),
        Direction.RIGHT,
        (2, 0),
        grid_w=5,
        grid_h=5,
        reservations=reservations,
        max_time=10,
        blocked_t1=set(),
    )
    assert path is not None, "Expected a valid path"
    assert path.count(Action.FORWARD) >= 2, "Expected to move forward toward the goal"


def test_planner_avoids_head_on_collision():
    env = WarehouseEnv(render=False)
    env.reset()
    if env.num_agents < 2:
        return

    env.robots[0].x = 5
    env.robots[0].y = 5
    env.robots[0].dir = Direction.RIGHT

    env.robots[1].x = 6
    env.robots[1].y = 5
    env.robots[1].dir = Direction.LEFT

    for shelf in env.shelves:
        shelf['requested'] = False
        shelf['carried'] = False

    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=10)
    actions = planner.compute_actions(env)
    _, _, _, collisions, _ = env.step(actions)

    assert collisions == 0, "Planner should avoid immediate head-on collisions"


def test_planner_waits_when_no_requested_shelves():
    env = WarehouseEnv(render=False)
    env.reset()

    for shelf in env.shelves:
        shelf['requested'] = False
        shelf['carried'] = False

    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=10)
    actions = planner.compute_actions(env)

    assert len(actions) == env.num_agents
    assert all(action == Action.WAIT.value for action in actions), "Idle robots should WAIT when no task exists"


if __name__ == '__main__':
    print("Testing planning components...")
    test_planner_action_output()
    print("? Planner action output test passed")

    test_astar_simple_path()
    print("? A* simple path test passed")

    test_planner_avoids_head_on_collision()
    print("? Collision avoidance test passed")

    test_planner_waits_when_no_requested_shelves()
    print("? No-task waiting test passed")

    print("\nAll planning component tests passed! ?")
