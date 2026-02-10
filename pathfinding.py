from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import heapq
from typing import Dict, Iterable, List, Optional, Set, Tuple

from agent import Action, Direction, Robot


GridPos = Tuple[int, int]
FORWARD_DX = [0, 1, 0, -1]   # UP, RIGHT, DOWN, LEFT
FORWARD_DY = [-1, 0, 1, 0]   # UP, RIGHT, DOWN, LEFT


@dataclass(frozen=True)
class NodeKey:
    x: int
    y: int
    dir_value: int
    t: int


class ReservationTable:
    """Time-indexed reservations for vertex and edge occupancy."""

    def __init__(self) -> None:
        self.positions: Dict[int, Set[GridPos]] = defaultdict(set)
        self.edges: Dict[int, Set[Tuple[GridPos, GridPos]]] = defaultdict(set)

    def is_reserved(self, pos: GridPos, t: int) -> bool:
        return pos in self.positions.get(t, set())

    def is_edge_reserved(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        return (from_pos, to_pos) in self.edges.get(t, set())

    def reserve_positions(self, positions: List[GridPos]) -> None:
        for t, pos in enumerate(positions):
            self.positions[t].add(pos)
            if t > 0:
                self.edges[t].add((positions[t - 1], pos))


class ConstraintTable:
    """Hard constraints injected by refinement."""

    def __init__(self) -> None:
        self.positions: Dict[int, Set[GridPos]] = defaultdict(set)
        self.edges: Dict[int, Set[Tuple[GridPos, GridPos]]] = defaultdict(set)

    def forbid_position(self, pos: GridPos, t: int) -> None:
        self.positions[t].add(pos)

    def forbid_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        self.edges[t].add((from_pos, to_pos))

    def is_forbidden(self, pos: GridPos, t: int) -> bool:
        return pos in self.positions.get(t, set())

    def is_edge_forbidden(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        return (from_pos, to_pos) in self.edges.get(t, set())


def manhattan(a: GridPos, b: GridPos) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def apply_action(
    x: int,
    y: int,
    direction: Direction,
    action: Action,
    grid_w: int,
    grid_h: int,
) -> Optional[Tuple[int, int, Direction]]:
    """Apply one action in a bounded grid; return None only for invalid forward."""
    if action == Action.TURN_LEFT:
        return x, y, Direction((direction.value - 1) % 4)

    if action == Action.TURN_RIGHT:
        return x, y, Direction((direction.value + 1) % 4)

    if action == Action.WAIT:
        return x, y, direction

    if action == Action.FORWARD:
        nx = x + FORWARD_DX[direction.value]
        ny = y + FORWARD_DY[direction.value]
        if 0 <= nx < grid_w and 0 <= ny < grid_h:
            return nx, ny, direction
        return None

    return None


def simulate_positions(
    start_pos: GridPos,
    start_dir: Direction,
    actions: List[Action],
    grid_w: int,
    grid_h: int,
    horizon: int,
) -> List[GridPos]:
    """Replay actions and pad with WAIT to build a fixed-horizon trajectory."""
    x, y = start_pos
    direction = start_dir
    positions: List[GridPos] = [(x, y)]

    for step in range(horizon):
        action = actions[step] if step < len(actions) else Action.WAIT
        result = apply_action(x, y, direction, action, grid_w, grid_h)
        if result is None:
            result = (x, y, direction)
        x, y, direction = result
        positions.append((x, y))

    return positions


def _blocked_by_constraints(
    constraints: Optional[Iterable[ConstraintTable]],
    cur_pos: GridPos,
    next_pos: GridPos,
    t: int,
) -> bool:
    if constraints is None:
        return False

    for table in constraints:
        if table.is_forbidden(next_pos, t):
            return True
        if table.is_edge_forbidden(cur_pos, next_pos, t):
            return True
    return False


def astar_time(
    start_pos: GridPos,
    start_dir: Direction,
    goal: GridPos,
    grid_w: int,
    grid_h: int,
    reservations: ReservationTable,
    max_time: int,
    blocked_t1: Set[GridPos],
    constraints: Optional[Iterable[ConstraintTable]] = None,
    max_expansions: int = 6000,
) -> Optional[List[Action]]:
    """A* in a time-expanded state space: (x, y, dir, t)."""
    start = NodeKey(start_pos[0], start_pos[1], start_dir.value, 0)
    open_heap: List[Tuple[float, int, int, NodeKey]] = []
    sequence = 0
    heapq.heappush(open_heap, (float(manhattan(start_pos, goal)), 0, sequence, start))

    g_score: Dict[NodeKey, int] = {start: 0}
    parent: Dict[NodeKey, Tuple[NodeKey, Action]] = {}

    action_order = [Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT]
    action_bias = {
        Action.FORWARD: 0.0,
        Action.TURN_LEFT: 0.25,
        Action.TURN_RIGHT: 0.25,
        Action.WAIT: 0.60,
    }

    expansions = 0
    while open_heap:
        _, g, _, current = heapq.heappop(open_heap)
        expansions += 1
        if expansions > max_expansions:
            return None

        cur_pos = (current.x, current.y)
        cur_dir = Direction(current.dir_value)

        if cur_pos == goal:
            path: List[Action] = []
            node = current
            while node in parent:
                prev, action = parent[node]
                path.append(action)
                node = prev
            path.reverse()
            return path

        if current.t >= max_time:
            continue

        for action in action_order:
            result = apply_action(current.x, current.y, cur_dir, action, grid_w, grid_h)
            if result is None:
                continue

            nx, ny, ndir = result
            nt = current.t + 1
            next_pos = (nx, ny)

            if nt == 1 and next_pos in blocked_t1:
                continue
            if reservations.is_reserved(next_pos, nt):
                continue
            if reservations.is_edge_reserved(next_pos, cur_pos, nt):
                continue
            if _blocked_by_constraints(constraints, cur_pos, next_pos, nt):
                continue

            next_key = NodeKey(nx, ny, ndir.value, nt)
            next_g = g + 1
            if next_g >= g_score.get(next_key, 1_000_000):
                continue

            g_score[next_key] = next_g
            sequence += 1
            h = manhattan(next_pos, goal)
            f = next_g + h + action_bias[action]
            heapq.heappush(open_heap, (f, next_g, sequence, next_key))
            parent[next_key] = (current, action)

    return None


class CooperativePlanner:
    """Deterministic multi-agent planner with reservations and constraints."""

    def __init__(self, grid_w: int, grid_h: int, plan_horizon: int = 30) -> None:
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.plan_horizon = plan_horizon

        self.constraints = ConstraintTable()

        # Assignment state
        self.agent_to_shelf: Dict[int, int] = {}
        self.shelf_to_agent: Dict[int, int] = {}

        # Stuck detection
        self.last_positions: Dict[int, GridPos] = {}
        self.idle_steps: Dict[int, int] = {}

        try:
            from config import ASTAR_MAX_NODES, IDLE_LIMIT

            self.astar_max_nodes = ASTAR_MAX_NODES
            self.idle_limit = IDLE_LIMIT
        except Exception:
            self.astar_max_nodes = 3500
            self.idle_limit = 4

    def add_constraint_position(self, pos: GridPos, t: int) -> None:
        self.constraints.forbid_position(pos, t)

    def add_constraint_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        self.constraints.forbid_edge(from_pos, to_pos, t)

    def compute_actions(self, env) -> List[int]:
        self._track_idle_agents(env)
        self._update_assignments(env)

        reservations = ReservationTable()
        occupied_now = {(robot.x, robot.y) for robot in env.robots}
        actions_by_id: Dict[int, int] = {}

        for robot in sorted(env.robots, key=lambda item: item.id):
            planned_path: List[Action] = []

            if self._should_pick_drop(robot, env):
                chosen_action = Action.PICK_DROP
            else:
                target = self._target_for_robot(robot, env)
                blocked_t1 = occupied_now - {(robot.x, robot.y)}

                if target is not None:
                    path = astar_time(
                        (robot.x, robot.y),
                        robot.dir,
                        target,
                        self.grid_w,
                        self.grid_h,
                        reservations,
                        self.plan_horizon,
                        blocked_t1,
                        constraints=[self.constraints],
                        max_expansions=self.astar_max_nodes,
                    )
                    if path is not None:
                        planned_path = path

                if planned_path:
                    chosen_action = planned_path[0]
                else:
                    chosen_action = self._best_immediate_action(
                        robot,
                        target,
                        reservations,
                        blocked_t1,
                    )

            actions_by_id[robot.id] = chosen_action.value

            reservation_actions = planned_path if planned_path else [chosen_action]
            reservations.reserve_positions(
                simulate_positions(
                    (robot.x, robot.y),
                    robot.dir,
                    reservation_actions,
                    self.grid_w,
                    self.grid_h,
                    self.plan_horizon,
                )
            )

        return [actions_by_id[robot.id] for robot in env.robots]

    def _best_immediate_action(
        self,
        robot: Robot,
        target: Optional[GridPos],
        reservations: ReservationTable,
        blocked_t1: Set[GridPos],
    ) -> Action:
        cur_pos = (robot.x, robot.y)
        candidates = [Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT]
        best_choice: Optional[Tuple[float, Action]] = None

        for action in candidates:
            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                continue

            nx, ny, _ = result
            next_pos = (nx, ny)
            t = 1

            if next_pos in blocked_t1:
                continue
            if reservations.is_reserved(next_pos, t):
                continue
            if reservations.is_edge_reserved(next_pos, cur_pos, t):
                continue
            if self.constraints.is_forbidden(next_pos, t):
                continue
            if self.constraints.is_edge_forbidden(cur_pos, next_pos, t):
                continue

            score = self._immediate_action_score(action, cur_pos, next_pos, target)
            if best_choice is None or score < best_choice[0]:
                best_choice = (score, action)

        if best_choice is None:
            return Action.WAIT
        return best_choice[1]

    @staticmethod
    def _immediate_action_score(
        action: Action,
        cur_pos: GridPos,
        next_pos: GridPos,
        target: Optional[GridPos],
    ) -> float:
        if target is None:
            base_score = {
                Action.FORWARD: 0.0,
                Action.TURN_LEFT: 1.0,
                Action.TURN_RIGHT: 1.1,
                Action.WAIT: 3.0,
            }
            return base_score[action]

        distance_to_target = float(manhattan(next_pos, target))
        action_penalty = {
            Action.FORWARD: 0.0,
            Action.TURN_LEFT: 0.8,
            Action.TURN_RIGHT: 0.9,
            Action.WAIT: 2.0,
        }[action]
        stayed_in_place_penalty = 0.4 if next_pos == cur_pos else 0.0
        return distance_to_target + action_penalty + stayed_in_place_penalty

    def _track_idle_agents(self, env) -> None:
        for robot in env.robots:
            pos = (robot.x, robot.y)
            previous_pos = self.last_positions.get(robot.id)

            if previous_pos == pos:
                self.idle_steps[robot.id] = self.idle_steps.get(robot.id, 0) + 1
            else:
                self.idle_steps[robot.id] = 0

            self.last_positions[robot.id] = pos

            if self.idle_steps[robot.id] >= self.idle_limit:
                shelf_id = self.agent_to_shelf.pop(robot.id, None)
                if shelf_id is not None:
                    self.shelf_to_agent.pop(shelf_id, None)
                self.idle_steps[robot.id] = 0

    def _update_assignments(self, env) -> None:
        shelves_by_id = {shelf["id"]: shelf for shelf in env.shelves}

        for agent_id, shelf_id in list(self.agent_to_shelf.items()):
            shelf = shelves_by_id.get(shelf_id)
            if shelf is None:
                self.agent_to_shelf.pop(agent_id, None)
                self.shelf_to_agent.pop(shelf_id, None)
                continue
            if shelf["carried"] or not shelf["requested"]:
                self.agent_to_shelf.pop(agent_id, None)
                self.shelf_to_agent.pop(shelf_id, None)

        free_robots = [
            robot
            for robot in env.robots
            if robot.carrying is None and robot.id not in self.agent_to_shelf
        ]
        free_shelves = [
            shelf
            for shelf in env.shelves
            if shelf["requested"] and not shelf["carried"] and shelf["id"] not in self.shelf_to_agent
        ]

        while free_robots and free_shelves:
            best_pair: Optional[Tuple[int, int, int]] = None

            for robot_idx, robot in enumerate(free_robots):
                for shelf_idx, shelf in enumerate(free_shelves):
                    dist = manhattan((robot.x, robot.y), (shelf["x"], shelf["y"]))
                    if best_pair is None or dist < best_pair[0]:
                        best_pair = (dist, robot_idx, shelf_idx)

            if best_pair is None:
                break

            _, robot_idx, shelf_idx = best_pair
            robot = free_robots.pop(robot_idx)
            shelf = free_shelves.pop(shelf_idx)
            self.agent_to_shelf[robot.id] = shelf["id"]
            self.shelf_to_agent[shelf["id"]] = robot.id

    def _target_for_robot(self, robot: Robot, env) -> Optional[GridPos]:
        if robot.carrying is not None:
            if bool(robot.carrying.get("requested")):
                return self._nearest_goal((robot.x, robot.y), env.GOALS)
            return None

        shelf_id = self.agent_to_shelf.get(robot.id)
        if shelf_id is None:
            return None

        assigned_shelf = next(
            (
                shelf
                for shelf in env.shelves
                if shelf["id"] == shelf_id and shelf["requested"] and not shelf["carried"]
            ),
            None,
        )
        if assigned_shelf is None:
            self.agent_to_shelf.pop(robot.id, None)
            self.shelf_to_agent.pop(shelf_id, None)
            return None

        return assigned_shelf["x"], assigned_shelf["y"]

    @staticmethod
    def _nearest_goal(pos: GridPos, goals: List[GridPos]) -> GridPos:
        return min(goals, key=lambda goal: manhattan(pos, goal))

    def _should_pick_drop(self, robot: Robot, env) -> bool:
        if robot.carrying is not None:
            if bool(robot.carrying.get("requested")):
                return (robot.x, robot.y) in env.GOALS
            return False

        shelf_here = next(
            (
                shelf
                for shelf in env.shelves
                if shelf["x"] == robot.x and shelf["y"] == robot.y and not shelf["carried"]
            ),
            None,
        )
        if shelf_here is None:
            return False
        if not shelf_here.get("requested"):
            return False
        return self.agent_to_shelf.get(robot.id) == shelf_here["id"]
