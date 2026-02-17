"""Test planning components: Cooperative A*, reservations, and action output."""
import random

from env import WarehouseEnv
from pathfinding import CooperativePlanner, ReservationTable, astar_time, simulate_positions
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


def test_astar_respects_timed_cell_reservations():
    reservations = ReservationTable()
    reservations.reserve_position((3, 0), 3)

    path = astar_time(
        (0, 0),
        Direction.RIGHT,
        (4, 0),
        grid_w=5,
        grid_h=1,
        reservations=reservations,
        max_time=10,
        blocked_t1=set(),
    )

    assert path is not None, "Expected a valid path with waiting around timed reservation"
    positions = simulate_positions((0, 0), Direction.RIGHT, path, 5, 1, horizon=len(path))
    assert len(positions) > 3
    assert positions[3] != (3, 0), "Planner must avoid reserved cell-time conflict"
    assert positions[-1] == (4, 0), "Planner should still reach the goal"


def test_planner_waits_when_spacetime_search_fails():
    env = WarehouseEnv(render=False, num_agents=1)
    env.reset()

    robot = env.robots[0]
    robot.x = 0
    robot.y = 0
    robot.dir = Direction.RIGHT

    for shelf in env.shelves:
        shelf["requested"] = False
        shelf["carried"] = False

    env.shelves[0]["x"] = 2
    env.shelves[0]["y"] = 0
    env.shelves[0]["requested"] = True
    env.shelves[0]["carried"] = False

    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=10)
    planner.astar_max_nodes = 0

    actions = planner.compute_actions(env)
    assert actions[0] == Action.WAIT.value, "No-path fallback should WAIT instead of turning in place"


def test_astar_blocks_optimistic_wait_on_unplanned_agent():
    reservations = ReservationTable()
    reservations.reserve_position((7, 14), 2)
    reservations.reserve_edge((6, 14), (7, 14), 2)

    path = astar_time(
        (7, 14),
        Direction.UP,
        (1, 5),
        grid_w=16,
        grid_h=16,
        reservations=reservations,
        max_time=40,
        blocked_t1={(6, 14), (7, 13)},
        blocked_by_time={2: {(7, 13)}},
    )

    assert path is not None, "Expected a path that clears the goal cell"
    assert path[0] == Action.TURN_RIGHT, "Planner should turn to clear out instead of waiting"


def test_planner_clears_blocked_goal_cell():
    env = WarehouseEnv(render=False, num_agents=3)
    env.reset()

    r0, r1, r2 = env.robots
    r0.x, r0.y, r0.dir = 6, 14, Direction.RIGHT
    r1.x, r1.y, r1.dir = 7, 14, Direction.UP
    r2.x, r2.y, r2.dir = 7, 13, Direction.RIGHT

    carried_a = {"id": 0, "x": 6, "y": 14, "carried": True, "requested": True}
    carried_b = {"id": 1, "x": 7, "y": 13, "carried": True, "requested": True}
    requested = {"id": 2, "x": 1, "y": 5, "carried": False, "requested": True}
    env.shelves = [carried_a, carried_b, requested]

    r0.carrying = carried_a
    r1.carrying = None
    r2.carrying = carried_b

    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=20)
    planner.escape_idle_steps = 1
    planner.unplanned_hold_steps = 2

    for _ in range(3):
        actions = planner.compute_actions(env)
        env.step(actions)

    assert (r1.x, r1.y) != (7, 14), "Robot on goal cell should clear out to unblock deliveries"


def test_planner_avoids_long_global_stall_seed_20():
    random.seed(20)
    env = WarehouseEnv(render=False)
    env.reset()
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=30)

    prev_positions = [(robot.x, robot.y) for robot in env.robots]
    no_move_run = 0
    max_no_move_run = 0

    for _ in range(140):
        actions = planner.compute_actions(env)
        _, _, done, _, _ = env.step(actions)

        moved = any((robot.x, robot.y) != prev_positions[i] for i, robot in enumerate(env.robots))
        prev_positions = [(robot.x, robot.y) for robot in env.robots]
        no_move_run = 0 if moved else no_move_run + 1
        max_no_move_run = max(max_no_move_run, no_move_run)

        if done:
            break

    assert max_no_move_run <= 12, f"Planner stalled too long: {max_no_move_run} steps"


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

    test_astar_respects_timed_cell_reservations()
    print("? Timed reservation test passed")

    test_planner_waits_when_spacetime_search_fails()
    print("? Space-time failure fallback test passed")

    test_astar_blocks_optimistic_wait_on_unplanned_agent()
    print("? Conservative unknown-agent blocking test passed")

    test_planner_clears_blocked_goal_cell()
    print("? Goal-cell clearing test passed")

    test_planner_avoids_long_global_stall_seed_20()
    print("? Long-stall regression test passed")

    print("\nAll planning component tests passed! ?")
