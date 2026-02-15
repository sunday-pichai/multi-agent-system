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
    """Unique key for a state in the time-expanded graph."""
    x: int
    y: int
    dir_value: int
    t: int


class ReservationTable:
    """
    Time-indexed reservations for vertex and edge occupancy to prevent collisions.
    - Positions: reserved vertices at specific times.
    - Edges: reserved directed edges at specific times for moves.
    Reservations ensure no vertex conflicts and no edge conflicts (same or opposite direction).
    """

    def __init__(self) -> None:
        self.positions: Dict[int, Set[GridPos]] = defaultdict(set)
        self.edges: Dict[int, Set[Tuple[GridPos, GridPos]]] = defaultdict(set)

    def is_reserved(self, pos: GridPos, t: int) -> bool:
        """Check if a position is reserved at time t (vertex conflict)."""
        return pos in self.positions.get(t, set())

    def is_edge_reserved(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        """Check if a directed edge is reserved at time t."""
        return (from_pos, to_pos) in self.edges.get(t, set())

    def reserve_positions(self, positions: List[GridPos]) -> None:
        """
        Reserve a trajectory of positions over time.
        - Reserves positions at each t.
        - Reserves edges only for actual moves (when positions change).
        """
        for t, pos in enumerate(positions):
            self.positions[t].add(pos)
            if t > 0 and positions[t - 1] != pos:
                self.edges[t].add((positions[t - 1], pos))


class ConstraintTable:
    """
    Hard constraints for forbidden vertices and edges at specific times.
    Used for refinement in case of higher-level conflict resolution.
    """

    def __init__(self) -> None:
        self.positions: Dict[int, Set[GridPos]] = defaultdict(set)
        self.edges: Dict[int, Set[Tuple[GridPos, GridPos]]] = defaultdict(set)

    def forbid_position(self, pos: GridPos, t: int) -> None:
        """Forbid a position at time t."""
        self.positions[t].add(pos)

    def forbid_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        """Forbid a directed edge at time t."""
        self.edges[t].add((from_pos, to_pos))

    def is_forbidden(self, pos: GridPos, t: int) -> bool:
        """Check if a position is forbidden at time t."""
        return pos in self.positions.get(t, set())

    def is_edge_forbidden(self, from_pos: GridPos, to_pos: GridPos, t: int) -> bool:
        """Check if a directed edge is forbidden at time t."""
        return (from_pos, to_pos) in self.edges.get(t, set())


def manhattan(a: GridPos, b: GridPos) -> int:
    """Manhattan distance between two grid positions."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def apply_action(
    x: int,
    y: int,
    direction: Direction,
    action: Action,
    grid_w: int,
    grid_h: int,
) -> Optional[Tuple[int, int, Direction]]:
    """
    Apply an action to the current state.
    Returns None if the action is invalid (e.g., forward out of bounds).
    """
    if action == Action.TURN_LEFT:
        return x, y, Direction((direction.value - 1) % 4)

    if action == Action.TURN_RIGHT:
        return x, y, Direction((direction.value + 1) % 4)

    if action == Action.WAIT or action == Action.PICK_DROP:
        return x, y, direction

    if action == Action.FORWARD:
        nx = x + FORWARD_DX[direction.value]
        ny = y + FORWARD_DY[direction.value]
        if 0 <= nx < grid_w and 0 <= ny < grid_h:
            return nx, ny, direction
        return None

    raise ValueError(f"Unknown action: {action}")


def simulate_positions(
    start_pos: GridPos,
    start_dir: Direction,
    actions: List[Action],
    grid_w: int,
    grid_h: int,
    horizon: int,
) -> List[GridPos]:
    """
    Simulate a sequence of actions to generate positions over time.
    Pads with WAIT if actions are shorter than horizon.
    Treats invalid forwards as WAIT for safety.
    Returns positions[0..horizon], where positions[0] is start.
    """
    x, y = start_pos
    direction = start_dir
    positions: List[GridPos] = [(x, y)]

    for step in range(horizon):
        action = actions[step] if step < len(actions) else Action.WAIT
        result = apply_action(x, y, direction, action, grid_w, grid_h)
        if result is None:
            result = (x, y, direction)  # Safety: treat invalid as stay
        x, y, direction = result
        positions.append((x, y))

    return positions


def _blocked_by_constraints(
    constraints: Optional[Iterable[ConstraintTable]],
    cur_pos: GridPos,
    next_pos: GridPos,
    t: int,
) -> bool:
    """Check if a move or stay is forbidden by any constraint table."""
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
    """
    A* search in time-expanded state space (x, y, dir, t).
    - Uniform cost (1 per action), admissible heuristic (Manhattan ignoring direction).
    - Avoids reservations and constraints.
    - Checks for vertex conflicts, same-direction edge conflicts, and opposite-direction (swap) conflicts.
    - Returns shortest sequence of actions to goal, or None if no path found within limits.
    """
    start = NodeKey(start_pos[0], start_pos[1], start_dir.value, 0)
    open_heap: List[Tuple[int, int, int, NodeKey]] = []  # (f, g, sequence, key) for min-heap
    sequence = 0
    h_start = manhattan(start_pos, goal)
    heapq.heappush(open_heap, (h_start, 0, sequence, start))

    g_score: Dict[NodeKey, int] = {start: 0}
    parent: Dict[NodeKey, Tuple[NodeKey, Action]] = {}
    expanded_positions: Set[GridPos] = set()

    def _current_frontier_positions() -> List[GridPos]:
        """Return non-stale frontier positions currently in the open set."""
        frontier: Set[GridPos] = set()
        for _, g_val, _, key in open_heap:
            if g_val == g_score.get(key, float('inf')):
                frontier.add((key.x, key.y))
        return list(frontier)

    action_order = [Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT]  # Prefer forward

    expansions = 0
    while open_heap:
        f, g, _, current = heapq.heappop(open_heap)
        expansions += 1
        if expansions > max_expansions:
            return None

        if g != g_score.get(current, float('inf')):
            continue  # Stale entry

        cur_pos = (current.x, current.y)
        cur_dir = Direction(current.dir_value)
        expanded_positions.add(cur_pos)

        if cur_pos == goal:
            # Reconstruct path
            path: List[Action] = []
            node_positions: List[GridPos] = [cur_pos]
            node = current
            while node in parent:
                prev, action = parent[node]
                path.append(action)
                node = prev
                node_positions.append((node.x, node.y))
            path.reverse()
            node_positions.reverse()
            movement_positions: List[GridPos] = []
            for pos in node_positions:
                if not movement_positions or movement_positions[-1] != pos:
                    movement_positions.append(pos)
            if visual is not None:
                visual["found"] = True
                visual["expanded"] = list(expanded_positions)
                visual["frontier"] = _current_frontier_positions()
                visual["path_positions"] = node_positions
                visual["movement_path_positions"] = movement_positions
                visual["expansions"] = expansions
                visual["goal"] = goal
                visual["start"] = start_pos
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

            if blocked_static and next_pos in blocked_static:
                continue

            # Immediate occupancy block for t=1
            if nt == 1 and next_pos in blocked_t1:
                continue

            # Vertex reservation check
            if reservations.is_reserved(next_pos, nt):
                continue

            # Edge reservation checks (only for moves)
            if cur_pos != next_pos:
                # Same direction conflict
                if reservations.is_edge_reserved(cur_pos, next_pos, nt):
                    continue
                # Opposite direction (swap/head-on) conflict
                if reservations.is_edge_reserved(next_pos, cur_pos, nt):
                    continue

            # Constraint checks
            if _blocked_by_constraints(constraints, cur_pos, next_pos, nt):
                continue

            next_key = NodeKey(nx, ny, ndir.value, nt)
            next_g = g + 1

            if next_g >= g_score.get(next_key, float('inf')):
                continue

            g_score[next_key] = next_g
            h = manhattan(next_pos, goal)
            f = next_g + h
            sequence += 1
            heapq.heappush(open_heap, (f, next_g, sequence, next_key))
            parent[next_key] = (current, action)

    if visual is not None:
        visual["found"] = False
        visual["expanded"] = list(expanded_positions)
        visual["frontier"] = _current_frontier_positions()
        visual["path_positions"] = []
        visual["movement_path_positions"] = []
        visual["expansions"] = expansions
        visual["goal"] = goal
        visual["start"] = start_pos
    return None


class AssignmentManager:
    """
    Manages assignments of robots to requested shelves.
    Uses greedy successive shortest path approximation for min-cost assignment.
    Resets assignments for completed or invalid tasks.
    """

    def __init__(self) -> None:
        self.agent_to_shelf: Dict[int, int] = {}
        self.shelf_to_agent: Dict[int, int] = {}

    def update_assignments(self, env) -> None:
        """Update assignments based on current environment state."""
        shelves_by_id = {shelf["id"]: shelf for shelf in env.shelves}

        # Clean up invalid assignments
        for agent_id, shelf_id in list(self.agent_to_shelf.items()):
            shelf = shelves_by_id.get(shelf_id)
            if shelf is None or shelf["carried"] or not shelf["requested"]:
                self.agent_to_shelf.pop(agent_id, None)
                self.shelf_to_agent.pop(shelf_id, None)

        # Collect free robots and free requested shelves
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

        # Greedy assignment: repeatedly assign closest pair
        while free_robots and free_shelves:
            best_dist = float('inf')
            best_robot_idx = -1
            best_shelf_idx = -1

            for r_idx, robot in enumerate(free_robots):
                for s_idx, shelf in enumerate(free_shelves):
                    dist = manhattan((robot.x, robot.y), (shelf["x"], shelf["y"]))
                    if dist < best_dist:
                        best_dist = dist
                        best_robot_idx = r_idx
                        best_shelf_idx = s_idx

            if best_robot_idx == -1:
                break

            robot = free_robots.pop(best_robot_idx)
            shelf = free_shelves.pop(best_shelf_idx)
            self.agent_to_shelf[robot.id] = shelf["id"]
            self.shelf_to_agent[shelf["id"]] = robot.id

    def get_target_for_robot(self, robot: Robot, env) -> Optional[GridPos]:
        """Get the target position for a robot based on assignment."""
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

        return (assigned_shelf["x"], assigned_shelf["y"])

    @staticmethod
    def _nearest_goal(pos: GridPos, goals: List[GridPos]) -> GridPos:
        """Find the nearest goal position."""
        if not goals:
            raise ValueError("No goals defined")
        return min(goals, key=lambda goal: manhattan(pos, goal))


class IdleTracker:
    """Tracks idle robots and detects stuck situations."""

    def __init__(self, idle_limit: int = 4) -> None:
        self.idle_limit = idle_limit
        self.last_positions: Dict[int, GridPos] = {}
        self.idle_steps: Dict[int, int] = {}

    def track_idle_agents(self, env, assignment_manager: AssignmentManager) -> None:
        """Update idle counts and reset assignments for stuck robots."""
        for robot in env.robots:
            pos = (robot.x, robot.y)
            previous_pos = self.last_positions.get(robot.id, pos)

            if previous_pos == pos:
                self.idle_steps[robot.id] = self.idle_steps.get(robot.id, 0) + 1
            else:
                self.idle_steps[robot.id] = 0

            self.last_positions[robot.id] = pos

            if self.idle_steps[robot.id] >= self.idle_limit:
                shelf_id = assignment_manager.agent_to_shelf.pop(robot.id, None)
                if shelf_id is not None:
                    assignment_manager.shelf_to_agent.pop(shelf_id, None)
                self.idle_steps[robot.id] = 0


class CooperativePlanner:
    """
    Advanced multi-agent planner using prioritized planning with reservations and constraints.
    - Prioritizes robots by ID for planning order.
    - Uses time-expanded A* for low-level pathfinding.
    - Greedy assignment for robot-to-shelf matching.
    - Idle detection for stuck resolution.
    - Fallback to local avoidance if global path fails.
    - Designed for robustness: fixed collision checks, admissible search, modular components.
    """

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
        """Add a position constraint."""
        if t < 0:
            raise ValueError("Time cannot be negative")
        self.constraints.forbid_position(pos, t)

    def add_constraint_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        """Add an edge constraint."""
        if t < 0:
            raise ValueError("Time cannot be negative")
        self.constraints.forbid_edge(from_pos, to_pos, t)

    def compute_actions(self, env) -> List[int]:
        """Compute actions for all robots in the environment."""
        self.idle_tracker.track_idle_agents(env, self.assignment_manager)
        self.assignment_manager.update_assignments(env)

        reservations = ReservationTable()
        occupied_now = {(robot.x, robot.y) for robot in env.robots}
        actions_by_id: Dict[int, int] = {}
        allowed_shelf_entries: Dict[int, GridPos] = {}
        planner_debug_by_agent: Dict[int, Dict[str, object]] = {}
        selected_agent_id = getattr(env, "selected_agent_id", -1)
        selected_astar_visual: Dict[str, object] = {
            "agent_id": selected_agent_id,
            "found": False,
            "expanded": [],
            "frontier": [],
            "path_positions": [],
            "mode": "none",
        }
        robots_by_id = sorted(env.robots, key=lambda r: r.id)
        if robots_by_id:
            shift = self.priority_offset % len(robots_by_id)
            planning_order = robots_by_id[shift:] + robots_by_id[:shift]
            self.priority_offset = (self.priority_offset + 1) % len(robots_by_id)
        else:
            planning_order = []
        priority_rank = {robot.id: idx for idx, robot in enumerate(planning_order)}
        shelf_positions = {
            (shelf["x"], shelf["y"])
            for shelf in env.shelves
            if not shelf["carried"]
        }


        # Plan in rotating priority order to reduce deadlocks/starvation
        for robot in planning_order:
            planned_path = []  # Ensure planned_path is always defined
            debug: Dict[str, object] = {
                "priority": priority_rank.get(robot.id, 0),
                "assigned_shelf_id": self.assignment_manager.agent_to_shelf.get(robot.id),
                "idle_steps": self.idle_tracker.idle_steps.get(robot.id, 0),
                "target": None,
                "mode": "unknown",
                "astar_found": False,
                "path_len": 0,
                "path_preview": [],
            }
            if self._should_pick_drop(robot, env):
                chosen_action = Action.PICK_DROP
                debug["mode"] = "pick_drop"
            else:
                target = self.assignment_manager.get_target_for_robot(robot, env)
                blocked_t1 = occupied_now - {(robot.x, robot.y)}
                blocked_static = self._blocked_shelf_positions(robot, target, env)
                visual_capture = robot.id == selected_agent_id
                debug["target"] = target
                debug["blocked_t1_count"] = len(blocked_t1)
                debug["blocked_static_count"] = len(blocked_static)
                if robot.carrying is None and target is not None and target in shelf_positions:
                    allowed_shelf_entries[robot.id] = target
                if target is None:
                    if robot.carrying is None and (robot.x, robot.y) in env.GOALS:
                        clear_target = self._nearest_requested_shelf(robot, env)
                        chosen_action = self._best_immediate_action(
                            robot,
                            clear_target,
                            reservations,
                            blocked_t1 | blocked_static,
                        )
                        debug["mode"] = "goal_clear"
                        debug["target"] = clear_target
                        if visual_capture:
                            selected_astar_visual["mode"] = "goal_clear_no_astar"
                    else:
                        chosen_action = Action.WAIT
                        debug["mode"] = "no_target_wait"
                        if visual_capture:
                            selected_astar_visual["mode"] = "no_target_wait"
                    debug["chosen_action_pre_sanitize"] = chosen_action.name
                    planner_debug_by_agent[robot.id] = debug
                    actions_by_id[robot.id] = chosen_action.value
                    positions = simulate_positions(
                        (robot.x, robot.y),
                        robot.dir,
                        [chosen_action],
                        self.grid_w,
                        self.grid_h,
                        self.plan_horizon,
                    )
                    reservations.reserve_positions(positions)
                    continue

                path = astar_time(
                    (robot.x, robot.y),
                    robot.dir,
                    target if target else (robot.x, robot.y),  # Fallback to stay
                    self.grid_w,
                    self.grid_h,
                    reservations,
                    self.plan_horizon,
                    blocked_t1,
                    blocked_static=blocked_static,
                    visual=selected_astar_visual if visual_capture else None,
                    constraints=[self.constraints],
                    max_expansions=self.astar_max_nodes,
                )
                planned_path = path if path is not None else []
                debug["astar_found"] = bool(planned_path)
                debug["path_len"] = len(planned_path)
                debug["path_preview"] = [action.name for action in planned_path[:6]]

                if planned_path:
                    chosen_action = planned_path[0]
                    debug["mode"] = "astar_path"
                elif target == (robot.x, robot.y):
                    chosen_action = Action.WAIT
                    debug["mode"] = "target_reached_wait"
                    if visual_capture:
                        selected_astar_visual["mode"] = "target_reached_wait"
                else:
                    chosen_action = self._best_immediate_action(
                        robot,
                        target,
                        reservations,
                        blocked_t1 | blocked_static,
                    )
                    debug["mode"] = "immediate_fallback"
                    if visual_capture and not selected_astar_visual.get("found", False):
                        selected_astar_visual["mode"] = "immediate_fallback"

            debug["chosen_action_pre_sanitize"] = chosen_action.name
            planner_debug_by_agent[robot.id] = debug
            actions_by_id[robot.id] = chosen_action.value

            # Reserve the planned trajectory (pad with WAIT)
            reservation_actions = planned_path if planned_path else [chosen_action]
            positions = simulate_positions(
                (robot.x, robot.y),
                robot.dir,
                reservation_actions,
                self.grid_w,
                self.grid_h,
                self.plan_horizon,
            )
            reservations.reserve_positions(positions)

        env._planner_allowed_shelf_entries = allowed_shelf_entries
        actions = [actions_by_id[robot.id] for robot in env.robots]
        sanitized = self._sanitize_immediate_conflicts(env, actions, priority_rank)
        env._planner_last_actions = list(sanitized)
        selected_astar_visual["selected_action"] = (
            Action(sanitized[selected_agent_id]).name
            if 0 <= selected_agent_id < len(sanitized)
            else "WAIT"
        )
        env._selected_astar_visual = selected_astar_visual
        for robot, action in zip(env.robots, sanitized):
            debug = planner_debug_by_agent.get(robot.id)
            if debug is None:
                continue
            debug["chosen_action"] = Action(action).name
            pre = debug.get("chosen_action_pre_sanitize")
            debug["sanitized"] = pre != debug["chosen_action"]
        env._planner_debug_by_agent = planner_debug_by_agent
        return sanitized

    def _blocked_shelf_positions(self, robot: Robot, target: Optional[GridPos], env) -> Set[GridPos]:
        """Return shelf cells that should be treated as blocked for this robot."""
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
        """Find nearest requested shelf position for goal-clearing motion guidance."""
        requested = [
            (shelf["x"], shelf["y"])
            for shelf in env.shelves
            if shelf["requested"] and not shelf["carried"]
        ]
        if not requested:
            return None
        return min(requested, key=lambda pos: manhattan((robot.x, robot.y), pos))

    def _sanitize_immediate_conflicts(self, env, actions: List[int], priority_rank: Dict[int, int]) -> List[int]:
        """
        Final safety pass to avoid immediate t=1 vertex and swap conflicts.
        Keeps higher-priority robots for this step and yields lower-priority robots.
        """
        actions_by_id = {robot.id: Action(action) for robot, action in zip(env.robots, actions)}
        intents: Dict[int, Tuple[GridPos, GridPos]] = {}
        blocked_by_shelf: Set[int] = set()

        for robot in sorted(env.robots, key=lambda r: priority_rank.get(r.id, r.id)):
            action = actions_by_id.get(robot.id, Action.WAIT)
            if action != Action.FORWARD:
                continue

            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                actions_by_id[robot.id] = Action.WAIT
                continue

            nx, ny, _ = result
            if self._blocked_shelf_positions(robot, self.assignment_manager.get_target_for_robot(robot, env), env).__contains__((nx, ny)):
                blocked_by_shelf.add(robot.id)
                actions_by_id[robot.id] = Action.WAIT
                continue
            intents[robot.id] = ((robot.x, robot.y), (nx, ny))

        target_owner: Dict[GridPos, int] = {}
        for robot_id in sorted(intents.keys(), key=lambda rid: priority_rank.get(rid, rid)):
            _, target = intents[robot_id]
            if target in target_owner:
                actions_by_id[robot_id] = Action.WAIT
            else:
                target_owner[target] = robot_id

        active_ids = [
            robot_id
            for robot_id in sorted(intents.keys(), key=lambda rid: priority_rank.get(rid, rid))
            if actions_by_id[robot_id] == Action.FORWARD
        ]
        for i in range(len(active_ids)):
            a_id = active_ids[i]
            a_from, a_to = intents[a_id]
            for j in range(i + 1, len(active_ids)):
                b_id = active_ids[j]
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
        """
        Select the best safe immediate action when global planning fails.
        Prefers actions that reduce distance to target.
        """
        cur_pos = (robot.x, robot.y)
        candidates = [Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT]
        best_score = float('inf')
        best_action = Action.WAIT

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
            if cur_pos != next_pos:
                if reservations.is_edge_reserved(cur_pos, next_pos, t):
                    continue
                if reservations.is_edge_reserved(next_pos, cur_pos, t):
                    continue
            if _blocked_by_constraints([self.constraints], cur_pos, next_pos, t):
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
        """Score an immediate action: lower is better."""
        if target is None:
            return {
                Action.FORWARD: 0.0,
                Action.TURN_LEFT: 1.0,
                Action.TURN_RIGHT: 1.0,
                Action.WAIT: 2.0,
            }[action]

        dist = manhattan(next_pos, target)
        penalty = {
            Action.FORWARD: 0.0,
            Action.TURN_LEFT: 0.5,
            Action.TURN_RIGHT: 0.5,
            Action.WAIT: 1.0,
        }[action]
        stay_penalty = 0.2 if next_pos == cur_pos else 0.0
        return dist + penalty + stay_penalty

    def _should_pick_drop(self, robot: Robot, env) -> bool:
        """Determine if the robot should perform PICK_DROP action."""
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