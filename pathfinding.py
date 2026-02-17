from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import heapq
from typing import Dict, Iterable, List, Optional, Set, Tuple

from agent import Action, Direction, Robot


GridPos = Tuple[int, int]

FORWARD_DX = (0, 1, 0, -1)
FORWARD_DY = (-1, 0, 1, 0)
ACTION_ORDER = (Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT)

NO_TARGET_SCORES = {
    Action.FORWARD: 0.0,
    Action.TURN_LEFT: 1.0,
    Action.TURN_RIGHT: 1.0,
    Action.WAIT: 2.0,
}
TARGET_PENALTIES = {
    Action.FORWARD: 0.0,
    Action.TURN_LEFT: 0.5,
    Action.TURN_RIGHT: 0.5,
    Action.WAIT: 1.0,
}


@dataclass(frozen=True)
class NodeKey:
    x: int
    y: int
    dir_value: int
    t: int


class _TimedTable:
    def __init__(self) -> None:
        self.positions: Dict[int, Set[GridPos]] = defaultdict(set)
        self.edges: Dict[int, Set[Tuple[GridPos, GridPos]]] = defaultdict(set)

    def has_position(self, pos: GridPos, t: int) -> bool:
        return pos in self.positions.get(t, ())

    def has_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        return (from_pos, to_pos) in self.edges.get(t, ())


class ReservationTable(_TimedTable):
    def is_reserved(self, pos: GridPos, t: int) -> bool:
        return self.has_position(pos, t)

    def is_edge_reserved(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        return self.has_edge(from_pos, to_pos, t)

    def reserve_positions(self, positions: List[GridPos]) -> None:
        for t, pos in enumerate(positions):
            self.positions[t].add(pos)
            if t and positions[t - 1] != pos:
                self.edges[t].add((positions[t - 1], pos))


class ConstraintTable(_TimedTable):
    def forbid_position(self, pos: GridPos, t: int) -> None:
        self.positions[t].add(pos)

    def forbid_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        self.edges[t].add((from_pos, to_pos))

    def is_forbidden(self, pos: GridPos, t: int) -> bool:
        return self.has_position(pos, t)

    def is_edge_forbidden(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        return self.has_edge(from_pos, to_pos, t)


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
    if action == Action.TURN_LEFT:
        return x, y, Direction((direction.value - 1) % 4)
    if action == Action.TURN_RIGHT:
        return x, y, Direction((direction.value + 1) % 4)
    if action in (Action.WAIT, Action.PICK_DROP):
        return x, y, direction
    if action == Action.FORWARD:
        nx = x + FORWARD_DX[direction.value]
        ny = y + FORWARD_DY[direction.value]
        return (nx, ny, direction) if 0 <= nx < grid_w and 0 <= ny < grid_h else None
    raise ValueError(f"Unknown action: {action}")


def simulate_positions(
    start_pos: GridPos,
    start_dir: Direction,
    actions: List[Action],
    grid_w: int,
    grid_h: int,
    horizon: int,
) -> List[GridPos]:
    x, y = start_pos
    direction = start_dir
    positions: List[GridPos] = [start_pos]
    for step in range(horizon):
        action = actions[step] if step < len(actions) else Action.WAIT
        result = apply_action(x, y, direction, action, grid_w, grid_h)
        x, y, direction = result if result is not None else (x, y, direction)
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
        if cur_pos != next_pos and table.is_edge_forbidden(cur_pos, next_pos, t):
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
    blocked_static: Optional[Set[GridPos]] = None,
    visual: Optional[Dict[str, object]] = None,
    constraints: Optional[Iterable[ConstraintTable]] = None,
    max_expansions: int = 6000,
) -> Optional[List[Action]]:
    del visual

    start = NodeKey(start_pos[0], start_pos[1], start_dir.value, 0)
    open_heap: List[Tuple[int, int, int, NodeKey]] = []
    heapq.heappush(open_heap, (manhattan(start_pos, goal), 0, 0, start))

    g_score: Dict[NodeKey, int] = {start: 0}
    parent: Dict[NodeKey, Tuple[NodeKey, Action]] = {}
    sequence = 0
    expansions = 0

    while open_heap:
        _, g, _, current = heapq.heappop(open_heap)
        expansions += 1
        if expansions > max_expansions:
            return None
        if g != g_score.get(current, float("inf")):
            continue

        cur_pos = (current.x, current.y)
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

        cur_dir = Direction(current.dir_value)
        nt = current.t + 1
        for action in ACTION_ORDER:
            result = apply_action(current.x, current.y, cur_dir, action, grid_w, grid_h)
            if result is None:
                continue

            nx, ny, ndir = result
            next_pos = (nx, ny)

            if blocked_static and next_pos in blocked_static:
                continue
            if nt == 1 and next_pos in blocked_t1:
                continue
            if reservations.is_reserved(next_pos, nt):
                continue
            if cur_pos != next_pos and (
                reservations.is_edge_reserved(cur_pos, next_pos, nt)
                or reservations.is_edge_reserved(next_pos, cur_pos, nt)
            ):
                continue
            if _blocked_by_constraints(constraints, cur_pos, next_pos, nt):
                continue

            next_key = NodeKey(nx, ny, ndir.value, nt)
            next_g = g + 1
            if next_g >= g_score.get(next_key, float("inf")):
                continue
            g_score[next_key] = next_g
            sequence += 1
            heapq.heappush(
                open_heap,
                (next_g + manhattan(next_pos, goal), next_g, sequence, next_key),
            )
            parent[next_key] = (current, action)

    return None


class AssignmentManager:
    def __init__(self) -> None:
        self.agent_to_shelf: Dict[int, int] = {}
        self.shelf_to_agent: Dict[int, int] = {}

    def update_assignments(self, env) -> None:
        shelves_by_id = {shelf["id"]: shelf for shelf in env.shelves}

        for agent_id, shelf_id in list(self.agent_to_shelf.items()):
            shelf = shelves_by_id.get(shelf_id)
            if shelf is not None and not shelf["carried"] and shelf["requested"]:
                continue
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
            best_dist = float("inf")
            best_robot_idx = -1
            best_shelf_idx = -1

            for r_idx, robot in enumerate(free_robots):
                for s_idx, shelf in enumerate(free_shelves):
                    dist = manhattan((robot.x, robot.y), (shelf["x"], shelf["y"]))
                    if dist < best_dist:
                        best_dist = dist
                        best_robot_idx = r_idx
                        best_shelf_idx = s_idx

            if best_robot_idx < 0:
                break

            robot = free_robots.pop(best_robot_idx)
            shelf = free_shelves.pop(best_shelf_idx)
            self.agent_to_shelf[robot.id] = shelf["id"]
            self.shelf_to_agent[shelf["id"]] = robot.id

    def get_target_for_robot(self, robot: Robot, env) -> Optional[GridPos]:
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
        if not goals:
            raise ValueError("No goals defined")
        return min(goals, key=lambda goal: manhattan(pos, goal))


class IdleTracker:
    def __init__(self, idle_limit: int = 4) -> None:
        self.idle_limit = idle_limit
        self.last_positions: Dict[int, GridPos] = {}
        self.idle_steps: Dict[int, int] = {}

    def track_idle_agents(self, env, assignment_manager: AssignmentManager) -> None:
        for robot in env.robots:
            pos = (robot.x, robot.y)
            previous = self.last_positions.get(robot.id, pos)
            if previous == pos:
                self.idle_steps[robot.id] = self.idle_steps.get(robot.id, 0) + 1
            else:
                self.idle_steps[robot.id] = 0
            self.last_positions[robot.id] = pos

            if self.idle_steps[robot.id] < self.idle_limit:
                continue
            shelf_id = assignment_manager.agent_to_shelf.pop(robot.id, None)
            if shelf_id is not None:
                assignment_manager.shelf_to_agent.pop(shelf_id, None)
            self.idle_steps[robot.id] = 0


class CooperativePlanner:
    def __init__(self, grid_w: int, grid_h: int, plan_horizon: int = 30) -> None:
        if grid_w <= 0 or grid_h <= 0:
            raise ValueError("Grid dimensions must be positive")

        self.grid_w = grid_w
        self.grid_h = grid_h
        self.plan_horizon = plan_horizon

        self.constraints = ConstraintTable()
        self.assignment_manager = AssignmentManager()
        self.idle_tracker = IdleTracker()
        self.priority_offset = 0

        try:
            from config import ASTAR_MAX_NODES, IDLE_LIMIT

            self.astar_max_nodes = ASTAR_MAX_NODES
            self.idle_tracker.idle_limit = IDLE_LIMIT
        except ImportError:
            self.astar_max_nodes = 3500
            self.idle_tracker.idle_limit = 4

    def add_constraint_position(self, pos: GridPos, t: int) -> None:
        if t < 0:
            raise ValueError("Time cannot be negative")
        self.constraints.forbid_position(pos, t)

    def add_constraint_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        if t < 0:
            raise ValueError("Time cannot be negative")
        self.constraints.forbid_edge(from_pos, to_pos, t)

    def _planning_order(self, robots: List[Robot]) -> List[Robot]:
        if not robots:
            return []
        shift = self.priority_offset % len(robots)
        planning_order = robots[shift:] + robots[:shift]
        self.priority_offset = (self.priority_offset + 1) % len(robots)
        return planning_order

    def _base_debug(self, robot_id: int, priority: int) -> Dict[str, object]:
        return {
            "priority": priority,
            "assigned_shelf_id": self.assignment_manager.agent_to_shelf.get(robot_id),
            "idle_steps": self.idle_tracker.idle_steps.get(robot_id, 0),
            "target": None,
            "mode": "unknown",
            "astar_found": False,
            "path_len": 0,
            "path_preview": [],
        }

    def _reserve_actions(
        self,
        reservations: ReservationTable,
        robot: Robot,
        actions: List[Action],
    ) -> None:
        positions = simulate_positions(
            (robot.x, robot.y),
            robot.dir,
            actions,
            self.grid_w,
            self.grid_h,
            self.plan_horizon,
        )
        reservations.reserve_positions(positions)

    def _commit_plan(
        self,
        actions_by_id: Dict[int, int],
        planner_debug_by_agent: Dict[int, Dict[str, object]],
        reservations: ReservationTable,
        robot: Robot,
        chosen_action: Action,
        planned_path: List[Action],
        debug: Dict[str, object],
    ) -> None:
        debug["chosen_action_pre_sanitize"] = chosen_action.name
        planner_debug_by_agent[robot.id] = debug
        actions_by_id[robot.id] = chosen_action.value
        self._reserve_actions(reservations, robot, planned_path if planned_path else [chosen_action])

    def _plan_navigation(
        self,
        robot: Robot,
        env,
        reservations: ReservationTable,
        occupied_now: Set[GridPos],
        shelf_positions: Set[GridPos],
        allowed_shelf_entries: Dict[int, GridPos],
        debug: Dict[str, object],
    ) -> Tuple[Action, List[Action]]:
        target = self.assignment_manager.get_target_for_robot(robot, env)
        blocked_t1 = occupied_now - {(robot.x, robot.y)}
        blocked_static = self._blocked_shelf_positions(robot, target, env)

        debug["target"] = target
        debug["blocked_t1_count"] = len(blocked_t1)
        debug["blocked_static_count"] = len(blocked_static)

        if robot.carrying is None and target is not None and target in shelf_positions:
            allowed_shelf_entries[robot.id] = target

        if target is None:
            if robot.carrying is None and (robot.x, robot.y) in env.GOALS:
                clear_target = self._nearest_requested_shelf(robot, env)
                debug["mode"] = "goal_clear"
                debug["target"] = clear_target
                action = self._best_immediate_action(
                    robot,
                    clear_target,
                    reservations,
                    blocked_t1 | blocked_static,
                )
                return action, []
            debug["mode"] = "no_target_wait"
            return Action.WAIT, []

        path = astar_time(
            (robot.x, robot.y),
            robot.dir,
            target if target else (robot.x, robot.y),
            self.grid_w,
            self.grid_h,
            reservations,
            self.plan_horizon,
            blocked_t1,
            blocked_static=blocked_static,
            visual=None,
            constraints=[self.constraints],
            max_expansions=self.astar_max_nodes,
        )

        planned_path = path if path is not None else []
        debug["astar_found"] = bool(planned_path)
        debug["path_len"] = len(planned_path)
        debug["path_preview"] = [action.name for action in planned_path[:6]]

        if planned_path:
            debug["mode"] = "astar_path"
            return planned_path[0], planned_path

        if target == (robot.x, robot.y):
            debug["mode"] = "target_reached_wait"
            return Action.WAIT, []

        debug["mode"] = "immediate_fallback"
        action = self._best_immediate_action(
            robot,
            target,
            reservations,
            blocked_t1 | blocked_static,
        )
        return action, []

    def compute_actions(self, env) -> List[int]:
        self.idle_tracker.track_idle_agents(env, self.assignment_manager)
        self.assignment_manager.update_assignments(env)

        reservations = ReservationTable()
        occupied_now = {(robot.x, robot.y) for robot in env.robots}
        actions_by_id: Dict[int, int] = {}
        allowed_shelf_entries: Dict[int, GridPos] = {}
        planner_debug_by_agent: Dict[int, Dict[str, object]] = {}

        planning_order = self._planning_order(sorted(env.robots, key=lambda r: r.id))
        priority_rank = {robot.id: idx for idx, robot in enumerate(planning_order)}
        shelf_positions = {
            (shelf["x"], shelf["y"])
            for shelf in env.shelves
            if not shelf["carried"]
        }

        for robot in planning_order:
            debug = self._base_debug(robot.id, priority_rank.get(robot.id, 0))
            if self._should_pick_drop(robot, env):
                chosen_action, planned_path = Action.PICK_DROP, []
                debug["mode"] = "pick_drop"
            else:
                chosen_action, planned_path = self._plan_navigation(
                    robot,
                    env,
                    reservations,
                    occupied_now,
                    shelf_positions,
                    allowed_shelf_entries,
                    debug,
                )
            self._commit_plan(
                actions_by_id,
                planner_debug_by_agent,
                reservations,
                robot,
                chosen_action,
                planned_path,
                debug,
            )

        env._planner_allowed_shelf_entries = allowed_shelf_entries
        actions = [actions_by_id[robot.id] for robot in env.robots]
        sanitized = self._sanitize_immediate_conflicts(env, actions, priority_rank)
        env._planner_last_actions = list(sanitized)

        for robot, action in zip(env.robots, sanitized):
            debug = planner_debug_by_agent.get(robot.id)
            if debug is None:
                continue
            debug["chosen_action"] = Action(action).name
            debug["sanitized"] = debug.get("chosen_action_pre_sanitize") != debug["chosen_action"]

        env._planner_debug_by_agent = planner_debug_by_agent
        return sanitized

    def _blocked_shelf_positions(
        self,
        robot: Robot,
        target: Optional[GridPos],
        env,
    ) -> Set[GridPos]:
        blocked: Set[GridPos] = set()
        for shelf in env.shelves:
            if shelf["carried"]:
                continue
            shelf_pos = (shelf["x"], shelf["y"])
            if robot.carrying is None and target is not None and shelf_pos == target:
                continue
            blocked.add(shelf_pos)
        return blocked

    @staticmethod
    def _nearest_requested_shelf(robot: Robot, env) -> Optional[GridPos]:
        requested = [
            (shelf["x"], shelf["y"])
            for shelf in env.shelves
            if shelf["requested"] and not shelf["carried"]
        ]
        if not requested:
            return None
        return min(requested, key=lambda pos: manhattan((robot.x, robot.y), pos))

    def _sanitize_immediate_conflicts(
        self,
        env,
        actions: List[int],
        priority_rank: Dict[int, int],
    ) -> List[int]:
        actions_by_id = {robot.id: Action(action) for robot, action in zip(env.robots, actions)}
        intents: Dict[int, Tuple[GridPos, GridPos]] = {}

        for robot in sorted(env.robots, key=lambda r: priority_rank.get(r.id, r.id)):
            action = actions_by_id.get(robot.id, Action.WAIT)
            if action != Action.FORWARD:
                continue

            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                actions_by_id[robot.id] = Action.WAIT
                continue

            nx, ny, _ = result
            if (nx, ny) in self._blocked_shelf_positions(
                robot,
                self.assignment_manager.get_target_for_robot(robot, env),
                env,
            ):
                actions_by_id[robot.id] = Action.WAIT
                continue
            intents[robot.id] = ((robot.x, robot.y), (nx, ny))

        target_owner: Dict[GridPos, int] = {}
        for robot_id in sorted(intents, key=lambda rid: priority_rank.get(rid, rid)):
            _, target = intents[robot_id]
            if target in target_owner:
                actions_by_id[robot_id] = Action.WAIT
            else:
                target_owner[target] = robot_id

        active_ids = [
            robot_id
            for robot_id in sorted(intents, key=lambda rid: priority_rank.get(rid, rid))
            if actions_by_id[robot_id] == Action.FORWARD
        ]
        for i, a_id in enumerate(active_ids):
            a_from, a_to = intents[a_id]
            for b_id in active_ids[i + 1:]:
                b_from, b_to = intents[b_id]
                if a_from == b_to and a_to == b_from:
                    actions_by_id[b_id] = Action.WAIT

        return [actions_by_id[robot.id].value for robot in env.robots]

    def _best_immediate_action(
        self,
        robot: Robot,
        target: Optional[GridPos],
        reservations: ReservationTable,
        blocked_t1: Set[GridPos],
    ) -> Action:
        cur_pos = (robot.x, robot.y)
        best_score = float("inf")
        best_action = Action.WAIT

        for action in ACTION_ORDER:
            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                continue

            nx, ny, _ = result
            next_pos = (nx, ny)
            if next_pos in blocked_t1:
                continue
            if reservations.is_reserved(next_pos, 1):
                continue
            if cur_pos != next_pos and (
                reservations.is_edge_reserved(cur_pos, next_pos, 1)
                or reservations.is_edge_reserved(next_pos, cur_pos, 1)
            ):
                continue
            if _blocked_by_constraints([self.constraints], cur_pos, next_pos, 1):
                continue

            score = self._immediate_action_score(action, cur_pos, next_pos, target)
            if score < best_score:
                best_score = score
                best_action = action

        return best_action

    @staticmethod
    def _immediate_action_score(
        action: Action,
        cur_pos: GridPos,
        next_pos: GridPos,
        target: Optional[GridPos],
    ) -> float:
        if target is None:
            return NO_TARGET_SCORES[action]
        return (
            manhattan(next_pos, target)
            + TARGET_PENALTIES[action]
            + (0.2 if next_pos == cur_pos else 0.0)
        )

    def _should_pick_drop(self, robot: Robot, env) -> bool:
        if robot.carrying is not None:
            if bool(robot.carrying.get("requested")):
                return (robot.x, robot.y) in env.GOALS
            return False

        shelf_here = next(
            (
                shelf
                for shelf in env.shelves
                if shelf["x"] == robot.x
                and shelf["y"] == robot.y
                and not shelf["carried"]
                and bool(shelf.get("requested"))
                and self.assignment_manager.agent_to_shelf.get(robot.id) == shelf["id"]
            ),
            None,
        )
        return shelf_here is not None
