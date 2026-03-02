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
ACTION_COSTS = {
    Action.FORWARD: 1.0,
    Action.TURN_LEFT: 1.0,
    Action.TURN_RIGHT: 1.0,
    Action.WAIT: 1.25,
}

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

    def reserve_position(self, pos: GridPos, t: int) -> None:
        self.positions[t].add(pos)

    def reserve_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        self.edges[t].add((from_pos, to_pos))

    def reserve_positions(self, positions: List[GridPos]) -> None:
        for t in range(len(positions)):
            pos = positions[t]
            self.reserve_position(pos, t)
            if t > 0:
                previous_pos = positions[t - 1]
                if previous_pos != pos:
                    self.reserve_edge(previous_pos, pos, t)


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


def minimum_cost_matching(costs: List[List[float]]) -> List[int]:
    """Return column assignment per row using Hungarian algorithm.

    - costs[i][j] is the cost of assigning row i to column j.
    - Returns a list of length rows. Each element is the chosen column index, or -1.
    """
    if not costs:
        return []

    row_count = len(costs)

    col_count = 0
    if costs[0]:
        col_count = len(costs[0])
    if col_count == 0:
        return [-1] * row_count

    # The matrix must be square, so use the larger dimension
    size = row_count
    if col_count > size:
        size = col_count

    # Find the largest cost value for padding
    max_cost = 0.0
    for row in costs:
        for value in row:
            if value > max_cost:
                max_cost = value
    pad_cost = max_cost + 1e6

    # Build a square matrix filled with the pad cost
    matrix = []
    for r in range(size):
        new_row = []
        for c in range(size):
            new_row.append(pad_cost)
        matrix.append(new_row)

    # Copy the real costs into the matrix
    for r in range(row_count):
        for c in range(col_count):
            matrix[r][c] = float(costs[r][c])

    # Hungarian algorithm potentials and assignments
    u = [0.0] * (size + 1)
    v = [0.0] * (size + 1)
    p = [0] * (size + 1)
    way = [0] * (size + 1)

    for i in range(1, size + 1):
        p[0] = i
        minv = [float("inf")] * (size + 1)
        used = [False] * (size + 1)
        j0 = 0
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0
            for j in range(1, size + 1):
                if used[j]:
                    continue
                cur = matrix[i0 - 1][j - 1] - u[i0] - v[j]
                if cur < minv[j]:
                    minv[j] = cur
                    way[j] = j0
                if minv[j] < delta:
                    delta = minv[j]
                    j1 = j
            for j in range(size + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    # Read out the assignment
    assignment = [-1] * row_count
    for j in range(1, size + 1):
        i = p[j]
        if i == 0:
            continue
        row = i - 1
        col = j - 1
        if row < row_count and col < col_count:
            assignment[row] = col
    return assignment


def apply_action(
    x: int,
    y: int,
    direction: Direction,
    action: Action,
    grid_w: int,
    grid_h: int,
) -> Optional[Tuple[int, int, Direction]]:
    if action == Action.TURN_LEFT:
        new_direction = Direction((direction.value - 1) % 4)
        return x, y, new_direction

    if action == Action.TURN_RIGHT:
        new_direction = Direction((direction.value + 1) % 4)
        return x, y, new_direction

    if action == Action.WAIT:
        return x, y, direction

    if action == Action.PICK_DROP:
        return x, y, direction

    if action == Action.FORWARD:
        next_x = x + FORWARD_DX[direction.value]
        next_y = y + FORWARD_DY[direction.value]
        inside_grid = 0 <= next_x < grid_w and 0 <= next_y < grid_h
        if inside_grid:
            return next_x, next_y, direction
        else:
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
    x = start_pos[0]
    y = start_pos[1]
    direction = start_dir
    positions: List[GridPos] = [start_pos]

    for step in range(horizon):
        # Pick the action for this step, or wait if we ran out of actions
        if step < len(actions):
            action = actions[step]
        else:
            action = Action.WAIT

        result = apply_action(x, y, direction, action, grid_w, grid_h)

        # If the action succeeded, update position and direction
        if result is not None:
            x = result[0]
            y = result[1]
            direction = result[2]
        # Otherwise the robot stays where it is

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
        if cur_pos != next_pos:
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
    blocked_by_time: Optional[Dict[int, Set[GridPos]]] = None,
    blocked_static: Optional[Set[GridPos]] = None,
    visual: Optional[Dict[str, object]] = None,
    constraints: Optional[Iterable[ConstraintTable]] = None,
    max_expansions: int = 6000,
) -> Optional[List[Action]]:

    start_node = NodeKey(start_pos[0], start_pos[1], start_dir.value, 0)
    start_heuristic = float(manhattan(start_pos, goal))

    open_heap: List[Tuple[float, float, int, NodeKey]] = []
    heapq.heappush(open_heap, (start_heuristic, 0.0, 0, start_node))

    g_score: Dict[NodeKey, float] = {start_node: 0.0}
    parent: Dict[NodeKey, Tuple[NodeKey, Action]] = {}
    sequence_counter = 0
    expansion_count = 0

    while open_heap:
        _, current_g, _, current_node = heapq.heappop(open_heap)
        expansion_count = expansion_count + 1

        if expansion_count > max_expansions:
            return None

        # Skip if we already found a cheaper way to reach this node
        best_known_g = g_score.get(current_node, float("inf"))
        if current_g > best_known_g + 1e-9:
            continue

        current_pos = (current_node.x, current_node.y)

        # --- Goal check ---
        if current_pos == goal:
            # Walk backwards through parent links to reconstruct the path
            path: List[Action] = []
            trace_node = current_node
            while trace_node in parent:
                parent_node, parent_action = parent[trace_node]
                path.append(parent_action)
                trace_node = parent_node
            path.reverse()
            return path

        # Don't expand beyond the time horizon
        if current_node.t >= max_time:
            continue

        current_direction = Direction(current_node.dir_value)
        next_time_step = current_node.t + 1

        # --- Try each possible action ---
        for action in ACTION_ORDER:
            result = apply_action(
                current_node.x, current_node.y,
                current_direction, action,
                grid_w, grid_h,
            )
            if result is None:
                continue

            next_x = result[0]
            next_y = result[1]
            next_direction = result[2]
            next_pos = (next_x, next_y)

            # Check: is this cell permanently blocked (e.g. a shelf)?
            if blocked_static is not None:
                if next_pos in blocked_static:
                    continue

            # Check: is this cell blocked at the first time step?
            if next_time_step == 1:
                if next_pos in blocked_t1:
                    continue

            # Check: is this cell blocked at this particular time step?
            if blocked_by_time is not None:
                blocked_cells_now = blocked_by_time.get(next_time_step, ())
                if next_pos in blocked_cells_now:
                    continue

            # Check: is another robot already reserving this cell?
            if reservations.is_reserved(next_pos, next_time_step):
                continue

            # Check: would two robots swap positions (edge conflict)?
            if current_pos != next_pos:
                forward_reserved = reservations.is_edge_reserved(
                    current_pos, next_pos, next_time_step,
                )
                reverse_reserved = reservations.is_edge_reserved(
                    next_pos, current_pos, next_time_step,
                )
                if forward_reserved or reverse_reserved:
                    continue

            # Check: does a constraint forbid this move?
            if _blocked_by_constraints(constraints, current_pos, next_pos, next_time_step):
                continue

            # --- This move is allowed. Compute its cost. ---
            next_node = NodeKey(next_x, next_y, next_direction.value, next_time_step)
            action_cost = ACTION_COSTS.get(action, 1.0)
            next_g = current_g + action_cost

            # Only keep this path if it is strictly better
            best_g_for_next = g_score.get(next_node, float("inf"))
            if next_g >= best_g_for_next - 1e-9:
                continue

            # Record this path
            g_score[next_node] = next_g
            sequence_counter = sequence_counter + 1
            heuristic = float(manhattan(next_pos, goal))
            f_score = next_g + heuristic

            heapq.heappush(
                open_heap,
                (f_score, next_g, sequence_counter, next_node),
            )
            parent[next_node] = (current_node, action)

    # No path found
    return None


class AssignmentManager:
    def __init__(self) -> None:
        self.agent_to_shelf: Dict[int, int] = {}
        self.shelf_to_agent: Dict[int, int] = {}

    def update_assignments(self, env) -> None:
        # Build a lookup: shelf_id -> shelf dict
        shelves_by_id: Dict[int, dict] = {}
        for shelf in env.shelves:
            shelves_by_id[shelf["id"]] = shelf

        # Remove assignments that are no longer valid
        agents_to_remove: List[int] = []
        for agent_id in self.agent_to_shelf:
            shelf_id = self.agent_to_shelf[agent_id]
            shelf = shelves_by_id.get(shelf_id)
            # Keep the assignment only if the shelf exists, is not carried, and is requested
            if shelf is not None and not shelf["carried"] and shelf["requested"]:
                continue
            agents_to_remove.append(agent_id)

        for agent_id in agents_to_remove:
            shelf_id = self.agent_to_shelf.pop(agent_id, None)
            if shelf_id is not None:
                self.shelf_to_agent.pop(shelf_id, None)

        # Find robots that are free: not carrying anything and not already assigned
        free_robots: List[Robot] = []
        for robot in env.robots:
            if robot.carrying is not None:
                continue
            if robot.id in self.agent_to_shelf:
                continue
            free_robots.append(robot)

        # Find shelves that need picking up: requested, not carried, not assigned
        free_shelves: List[dict] = []
        for shelf in env.shelves:
            if not shelf["requested"]:
                continue
            if shelf["carried"]:
                continue
            if shelf["id"] in self.shelf_to_agent:
                continue
            free_shelves.append(shelf)

        if not free_robots:
            return
        if not free_shelves:
            return

        # Build cost matrix: distance from each free robot to each free shelf
        costs: List[List[float]] = []
        for robot in free_robots:
            row: List[float] = []
            for shelf in free_shelves:
                robot_pos = (robot.x, robot.y)
                shelf_pos = (shelf["x"], shelf["y"])
                dist = manhattan(robot_pos, shelf_pos)
                row.append(float(dist))
            costs.append(row)

        # Use Hungarian algorithm to find the best assignment
        assignment = minimum_cost_matching(costs)

        # Apply the new assignments
        for r_idx in range(len(assignment)):
            s_idx = assignment[r_idx]
            if s_idx < 0:
                continue
            if s_idx >= len(free_shelves):
                continue
            robot = free_robots[r_idx]
            shelf = free_shelves[s_idx]
            self.agent_to_shelf[robot.id] = shelf["id"]
            self.shelf_to_agent[shelf["id"]] = robot.id

    def get_target_for_robot(
        self,
        robot: Robot,
        env,
        delivery_targets: Optional[Dict[int, GridPos]] = None,
    ) -> Optional[GridPos]:
        # --- Robot is carrying a shelf ---
        if robot.carrying is not None:
            is_requested = bool(robot.carrying.get("requested"))
            if is_requested:
                # Check if there is a pre-assigned delivery target
                if delivery_targets is not None:
                    target = delivery_targets.get(robot.id)
                    if target is not None:
                        return target
                # Otherwise go to the nearest goal
                return self._nearest_goal((robot.x, robot.y), env.GOALS)
            # Carrying a non-requested shelf: no target
            return None

        # --- Robot is not carrying anything ---
        shelf_id = self.agent_to_shelf.get(robot.id)
        if shelf_id is None:
            return None

        # Find the assigned shelf in the environment
        assigned_shelf = None
        for shelf in env.shelves:
            if shelf["id"] != shelf_id:
                continue
            if not shelf["requested"]:
                continue
            if shelf["carried"]:
                continue
            assigned_shelf = shelf
            break

        if assigned_shelf is None:
            # Assignment is stale, clean it up
            self.agent_to_shelf.pop(robot.id, None)
            self.shelf_to_agent.pop(shelf_id, None)
            return None

        return assigned_shelf["x"], assigned_shelf["y"]

    @staticmethod
    def _nearest_goal(pos: GridPos, goals: List[GridPos]) -> GridPos:
        if not goals:
            raise ValueError("No goals defined")

        best_goal = goals[0]
        best_distance = manhattan(pos, goals[0])

        for i in range(1, len(goals)):
            dist = manhattan(pos, goals[i])
            if dist < best_distance:
                best_distance = dist
                best_goal = goals[i]

        return best_goal


class IdleTracker:
    def __init__(self, idle_limit: int = 4) -> None:
        self.idle_limit = idle_limit
        self.last_positions: Dict[int, GridPos] = {}
        self.idle_steps: Dict[int, int] = {}

    def track_idle_agents(self, env, assignment_manager: AssignmentManager) -> None:
        for robot in env.robots:
            current_pos = (robot.x, robot.y)
            previous_pos = self.last_positions.get(robot.id, current_pos)

            if previous_pos == current_pos:
                old_idle = self.idle_steps.get(robot.id, 0)
                self.idle_steps[robot.id] = old_idle + 1
            else:
                self.idle_steps[robot.id] = 0

            self.last_positions[robot.id] = current_pos

            # If the robot has been idle too long, drop its shelf assignment
            if self.idle_steps[robot.id] < self.idle_limit:
                continue

            shelf_id = assignment_manager.agent_to_shelf.pop(robot.id, None)
            if shelf_id is not None:
                assignment_manager.shelf_to_agent.pop(shelf_id, None)
            self.idle_steps[robot.id] = 0


def _read_config_int(name: str, default: int) -> int:
    """Read an integer from the config module, falling back to default."""
    try:
        import config as cfg
        value = getattr(cfg, name, default)
        return int(value)
    except ImportError:
        return default


class CooperativePlanner:
    def __init__(self, grid_w: int, grid_h: int, plan_horizon: int = 30) -> None:
        if grid_w <= 0 or grid_h <= 0:
            raise ValueError("Grid dimensions must be positive")

        self.grid_w = grid_w
        self.grid_h = grid_h
        self.plan_horizon = plan_horizon

        self.constraints = ConstraintTable()
        self.assignment_manager = AssignmentManager()

        idle_limit = _read_config_int("IDLE_LIMIT", 4)
        self.idle_tracker = IdleTracker(idle_limit=idle_limit)
        self.priority_offset = 0

        self.astar_max_nodes = _read_config_int("ASTAR_MAX_NODES", 3500)

        # Reservation window: clamp between 2 and plan_horizon
        reservation_window = _read_config_int("RESERVATION_WINDOW", 8)
        if reservation_window > plan_horizon:
            reservation_window = plan_horizon
        if reservation_window < 2:
            reservation_window = 2
        self.reservation_window = reservation_window

        # Steps to hold unplanned robots in place (at least 1)
        unplanned_hold = _read_config_int("UNPLANNED_HOLD_STEPS", 2)
        if unplanned_hold < 1:
            unplanned_hold = 1
        self.unplanned_hold_steps = unplanned_hold

        # Steps before trying an escape move (at least 2)
        escape_idle = _read_config_int("ESCAPE_IDLE_STEPS", 6)
        if escape_idle < 2:
            escape_idle = 2
        self.escape_idle_steps = escape_idle

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

        # Rotate the list so different robots get priority each round
        shift = self.priority_offset % len(robots)
        rotated = robots[shift:] + robots[:shift]
        self.priority_offset = (self.priority_offset + 1) % len(robots)

        # Build a position-in-rotation lookup
        rotated_index: Dict[int, int] = {}
        for idx in range(len(rotated)):
            rotated_index[rotated[idx].id] = idx

        # Build (sort_key, robot) pairs so we can sort explicitly
        sortable: List[Tuple[Tuple[int, int, int], Robot]] = []
        for robot in rotated:
            # Robots carrying a requested shelf get priority (0 beats 1)
            is_carrying_requested = (
                robot.carrying is not None and bool(robot.carrying.get("requested"))
            )
            if is_carrying_requested:
                carry_priority = 0
            else:
                carry_priority = 1

            # More-idle robots get higher priority (negative so ascending sort works)
            idle = self.idle_tracker.idle_steps.get(robot.id, 0)
            negative_idle = -idle

            # Break remaining ties by rotation position
            rotation_pos = rotated_index.get(robot.id, 0)

            sort_key = (carry_priority, negative_idle, rotation_pos)
            sortable.append((sort_key, robot))

        sortable.sort()

        result: List[Robot] = []
        for sort_key, robot in sortable:
            result.append(robot)
        return result

    def _base_debug(self, robot_id: int, priority: int) -> Dict[str, object]:
        debug: Dict[str, object] = {}
        debug["priority"] = priority
        debug["assigned_shelf_id"] = self.assignment_manager.agent_to_shelf.get(robot_id)
        debug["idle_steps"] = self.idle_tracker.idle_steps.get(robot_id, 0)
        debug["target"] = None
        debug["mode"] = "unknown"
        debug["astar_found"] = False
        debug["path_len"] = 0
        debug["path_preview"] = []
        return debug

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
            self.reservation_window,
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

        if planned_path:
            actions_to_reserve = planned_path
        else:
            actions_to_reserve = [chosen_action]
        self._reserve_actions(reservations, robot, actions_to_reserve)

    def _plan_navigation(
        self,
        robot: Robot,
        env,
        reservations: ReservationTable,
        blocked_by_time: Dict[int, Set[GridPos]],
        shelf_positions: Set[GridPos],
        allowed_shelf_entries: Dict[int, GridPos],
        delivery_targets: Dict[int, GridPos],
        debug: Dict[str, object],
    ) -> Tuple[Action, List[Action]]:
        # Find the target for this robot
        target = self.assignment_manager.get_target_for_robot(
            robot,
            env,
            delivery_targets=delivery_targets,
        )

        # Figure out which cells are blocked at time step 1
        blocked_at_t1 = blocked_by_time.get(1, set())
        blocked_t1 = set(blocked_at_t1)

        # Figure out which shelf positions this robot cannot enter
        blocked_static = self._blocked_shelf_positions(robot, target, env)

        idle_steps = self.idle_tracker.idle_steps.get(robot.id, 0)

        # Record debug info
        debug["target"] = target
        debug["blocked_t1_count"] = len(blocked_t1)

        future_blocked_count = 0
        for t in blocked_by_time:
            if t > 1:
                future_blocked_count = future_blocked_count + len(blocked_by_time[t])
        debug["blocked_future_count"] = future_blocked_count
        debug["blocked_static_count"] = len(blocked_static)

        # If picking up a shelf, record that this robot is allowed to enter the shelf cell
        if robot.carrying is None and target is not None:
            if target in shelf_positions:
                allowed_shelf_entries[robot.id] = target

        # --- No target assigned ---
        if target is None:
            # If sitting on a goal with nothing to carry, try to move away
            if robot.carrying is None:
                robot_on_goal = (robot.x, robot.y) in env.GOALS
                if robot_on_goal:
                    clear_target = self._nearest_requested_shelf(robot, env)
                    debug["mode"] = "goal_clear"
                    debug["target"] = clear_target
                    all_blocked = blocked_t1 | blocked_static
                    action = self._best_immediate_action(
                        robot, clear_target, reservations, all_blocked,
                    )
                    return action, []

            debug["mode"] = "no_target_wait"
            return Action.WAIT, []

        # --- Has a target: run A* to find a path ---
        astar_goal = target
        if target is None:
            astar_goal = (robot.x, robot.y)

        path = astar_time(
            (robot.x, robot.y),
            robot.dir,
            astar_goal,
            self.grid_w,
            self.grid_h,
            reservations,
            self.plan_horizon,
            blocked_t1,
            blocked_by_time=blocked_by_time,
            blocked_static=blocked_static,
            visual=None,
            constraints=[self.constraints],
            max_expansions=self.astar_max_nodes,
        )

        if path is not None:
            planned_path = path
        else:
            planned_path = []

        # Record what A* found
        debug["astar_found"] = len(planned_path) > 0
        debug["path_len"] = len(planned_path)

        preview: List[str] = []
        for i in range(len(planned_path)):
            if i >= 6:
                break
            preview.append(planned_path[i].name)
        debug["path_preview"] = preview
        debug["idle_steps"] = idle_steps

        # --- A* found a path ---
        if planned_path:
            first_action = planned_path[0]

            # If path starts with WAIT but we have been idle too long, try to escape
            if first_action == Action.WAIT:
                not_at_target = target != (robot.x, robot.y)
                idle_too_long = idle_steps >= self.escape_idle_steps
                if not_at_target and idle_too_long:
                    all_blocked = blocked_t1 | blocked_static
                    escape_action = self._best_immediate_action(
                        robot, target, reservations, all_blocked,
                    )
                    if escape_action != Action.WAIT:
                        debug["mode"] = "stuck_path_escape"
                        return escape_action, [escape_action]

            debug["mode"] = "astar_path"
            return planned_path[0], planned_path

        # --- A* found no path ---

        # If we are already at the target, just wait
        if target == (robot.x, robot.y):
            debug["mode"] = "target_reached_wait"
            return Action.WAIT, []

        # If we have been idle too long, try any move that gets us closer
        if idle_steps >= self.escape_idle_steps:
            all_blocked = blocked_t1 | blocked_static
            escape_action = self._best_immediate_action(
                robot, target, reservations, all_blocked,
            )
            if escape_action != Action.WAIT:
                debug["mode"] = "no_path_escape"
                return escape_action, [escape_action]

        # Nothing worked, just wait
        debug["mode"] = "no_spacetime_path_wait"
        return Action.WAIT, []

    def compute_actions(self, env) -> List[int]:
        # Track which robots have been sitting still
        self.idle_tracker.track_idle_agents(env, self.assignment_manager)

        # Update shelf-to-robot assignments
        self.assignment_manager.update_assignments(env)

        reservations = ReservationTable()

        # Record where every robot is right now
        occupied_now: Set[GridPos] = set()
        for robot in env.robots:
            occupied_now.add((robot.x, robot.y))

        actions_by_id: Dict[int, int] = {}
        allowed_shelf_entries: Dict[int, GridPos] = {}
        planner_debug_by_agent: Dict[int, Dict[str, object]] = {}
        delivery_targets = self._assign_delivery_goals(env)

        # Sort robots by ID first, then determine planning order
        id_robot_pairs: List[Tuple[int, Robot]] = []
        for robot in env.robots:
            id_robot_pairs.append((robot.id, robot))
        id_robot_pairs.sort()

        robots_sorted_by_id: List[Robot] = []
        for robot_id, robot in id_robot_pairs:
            robots_sorted_by_id.append(robot)

        planning_order = self._planning_order(robots_sorted_by_id)

        # Record priority rank for each robot
        priority_rank: Dict[int, int] = {}
        for idx in range(len(planning_order)):
            priority_rank[planning_order[idx].id] = idx

        # Find all shelf positions that are not being carried
        shelf_positions: Set[GridPos] = set()
        for shelf in env.shelves:
            if not shelf["carried"]:
                shelf_positions.add((shelf["x"], shelf["y"]))

        # --- Plan for each robot, in priority order ---
        for idx in range(len(planning_order)):
            robot = planning_order[idx]

            # Cells occupied by other robots are blocked at time 1
            blocked_t1 = occupied_now - {(robot.x, robot.y)}

            # Cells of not-yet-planned robots are blocked for a few extra steps
            unplanned_positions: Set[GridPos] = set()
            for later_idx in range(idx + 1, len(planning_order)):
                other = planning_order[later_idx]
                unplanned_positions.add((other.x, other.y))

            blocked_by_time: Dict[int, Set[GridPos]] = {1: set(blocked_t1)}
            if unplanned_positions:
                for t in range(2, self.unplanned_hold_steps + 1):
                    blocked_by_time[t] = set(unplanned_positions)

            debug = self._base_debug(robot.id, priority_rank.get(robot.id, 0))

            # Decide what this robot should do
            should_pick_or_drop = self._should_pick_drop(robot, env)

            if should_pick_or_drop:
                chosen_action = Action.PICK_DROP
                planned_path: List[Action] = []
                debug["mode"] = "pick_drop"
            else:
                chosen_action, planned_path = self._plan_navigation(
                    robot,
                    env,
                    reservations,
                    blocked_by_time,
                    shelf_positions,
                    allowed_shelf_entries,
                    delivery_targets,
                    debug,
                )

            # Save the plan and reserve space-time cells
            self._commit_plan(
                actions_by_id,
                planner_debug_by_agent,
                reservations,
                robot,
                chosen_action,
                planned_path,
                debug,
            )

        # Store allowed shelf entries so the environment can use them
        env._planner_allowed_shelf_entries = allowed_shelf_entries

        # Build the action list in robot order
        actions: List[int] = []
        for robot in env.robots:
            actions.append(actions_by_id[robot.id])

        # Fix any immediate conflicts between robots
        sanitized = self._sanitize_immediate_conflicts(env, actions, priority_rank)
        env._planner_last_actions = list(sanitized)

        # Update debug info with final (post-sanitize) actions
        for i in range(len(env.robots)):
            robot = env.robots[i]
            action_value = sanitized[i]
            debug = planner_debug_by_agent.get(robot.id)
            if debug is None:
                continue
            debug["chosen_action"] = Action(action_value).name
            pre_sanitize_name = debug.get("chosen_action_pre_sanitize")
            debug["sanitized"] = pre_sanitize_name != debug["chosen_action"]

        env._planner_debug_by_agent = planner_debug_by_agent
        return sanitized

    def _blocked_shelf_positions(
        self,
        robot: Robot,
        target: Optional[GridPos],
        env,
    ) -> Set[GridPos]:
        """Return the set of shelf cells this robot must NOT enter."""
        robot_is_picking = robot.carrying is None and target is not None

        blocked: Set[GridPos] = set()
        for shelf in env.shelves:
            if shelf["carried"]:
                continue
            shelf_pos = (shelf["x"], shelf["y"])
            # Allow entering the target shelf cell if the robot is going to pick it up
            if robot_is_picking and shelf_pos == target:
                continue
            blocked.add(shelf_pos)
        return blocked

    @staticmethod
    def _nearest_requested_shelf(robot: Robot, env) -> Optional[GridPos]:
        """Find the closest shelf that is requested and not yet picked up."""
        best_pos = None
        best_distance = float("inf")

        for shelf in env.shelves:
            if not shelf["requested"]:
                continue
            if shelf["carried"]:
                continue
            shelf_pos = (shelf["x"], shelf["y"])
            dist = manhattan((robot.x, robot.y), shelf_pos)
            if dist < best_distance:
                best_distance = dist
                best_pos = shelf_pos

        return best_pos

    def _assign_delivery_goals(self, env) -> Dict[int, GridPos]:
        """Assign each carrier robot a specific goal to deliver to."""
        # Find robots that are carrying a requested shelf
        carriers: List[Robot] = []
        for robot in env.robots:
            if robot.carrying is None:
                continue
            is_requested = bool(robot.carrying.get("requested"))
            if not is_requested:
                continue
            carriers.append(robot)

        goals = list(env.GOALS)

        if not carriers:
            return {}
        if not goals:
            return {}

        # Build delivery slots: each goal appears once per tier
        # (tiers add a penalty so multiple carriers spread across goals)
        slots: List[Tuple[GridPos, int]] = []
        for tier in range(len(carriers)):
            for goal in goals:
                slots.append((goal, tier))

        # Build cost matrix
        costs: List[List[float]] = []
        for robot in carriers:
            row: List[float] = []
            for slot_idx in range(len(slots)):
                goal = slots[slot_idx][0]
                tier = slots[slot_idx][1]
                dist = float(manhattan((robot.x, robot.y), goal))
                cost = dist + 2.0 * tier
                row.append(cost)
            costs.append(row)

        # Run Hungarian matching
        assignment = minimum_cost_matching(costs)

        # Build the result
        targets: Dict[int, GridPos] = {}
        for i in range(len(assignment)):
            j = assignment[i]
            if j < 0:
                continue
            if j >= len(slots):
                continue
            robot_id = carriers[i].id
            goal_pos = slots[j][0]
            targets[robot_id] = goal_pos

        return targets

    def _sanitize_immediate_conflicts(
        self,
        env,
        actions: List[int],
        priority_rank: Dict[int, int],
    ) -> List[int]:
        """Fix forward-move conflicts between robots, respecting priority."""

        # Map robot id -> chosen action
        actions_by_id: Dict[int, Action] = {}
        for i in range(len(env.robots)):
            robot = env.robots[i]
            actions_by_id[robot.id] = Action(actions[i])

        # Sort robots by priority
        rank_robot_pairs: List[Tuple[int, Robot]] = []
        for robot in env.robots:
            rank = priority_rank.get(robot.id, robot.id)
            rank_robot_pairs.append((rank, robot))
        rank_robot_pairs.sort()

        robots_by_priority: List[Robot] = []
        for rank, robot in rank_robot_pairs:
            robots_by_priority.append(robot)

        # Check each forward-moving robot: can it actually move?
        intents: Dict[int, Tuple[GridPos, GridPos]] = {}

        for robot in robots_by_priority:
            action = actions_by_id.get(robot.id, Action.WAIT)
            if action != Action.FORWARD:
                continue

            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                actions_by_id[robot.id] = Action.WAIT
                continue

            next_x = result[0]
            next_y = result[1]
            next_pos = (next_x, next_y)

            # Don't move into a blocked shelf cell
            robot_target = self.assignment_manager.get_target_for_robot(robot, env)
            blocked_shelves = self._blocked_shelf_positions(robot, robot_target, env)
            if next_pos in blocked_shelves:
                actions_by_id[robot.id] = Action.WAIT
                continue

            intents[robot.id] = ((robot.x, robot.y), next_pos)

        # --- Resolve same-target conflicts: first robot by priority wins ---
        intent_ids_by_priority: List[int] = []
        for robot_id in intents:
            intent_ids_by_priority.append(robot_id)

        # Sort intent IDs by priority rank
        rank_id_pairs: List[Tuple[int, int]] = []
        for rid in intent_ids_by_priority:
            rank = priority_rank.get(rid, rid)
            rank_id_pairs.append((rank, rid))
        rank_id_pairs.sort()

        intent_ids_by_priority = []
        for rank, rid in rank_id_pairs:
            intent_ids_by_priority.append(rid)

        target_owner: Dict[GridPos, int] = {}
        for robot_id in intent_ids_by_priority:
            from_pos, to_pos = intents[robot_id]
            if to_pos in target_owner:
                actions_by_id[robot_id] = Action.WAIT
            else:
                target_owner[to_pos] = robot_id

        # --- Resolve head-on swap conflicts ---
        active_ids: List[int] = []
        for robot_id in intent_ids_by_priority:
            if actions_by_id[robot_id] == Action.FORWARD:
                active_ids.append(robot_id)

        for i in range(len(active_ids)):
            a_id = active_ids[i]
            a_from = intents[a_id][0]
            a_to = intents[a_id][1]
            for j in range(i + 1, len(active_ids)):
                b_id = active_ids[j]
                b_from = intents[b_id][0]
                b_to = intents[b_id][1]
                # If robot A wants to go where B is, and B wants to go where A is
                if a_from == b_to and a_to == b_from:
                    # Lower priority robot (B) must stop
                    actions_by_id[b_id] = Action.WAIT

        # Build the final result in env.robots order
        result: List[int] = []
        for robot in env.robots:
            result.append(actions_by_id[robot.id].value)
        return result

    def _best_immediate_action(
        self,
        robot: Robot,
        target: Optional[GridPos],
        reservations: ReservationTable,
        blocked_t1: Set[GridPos],
    ) -> Action:
        """Pick the best single-step action that is not blocked."""
        current_pos = (robot.x, robot.y)
        best_score = float("inf")
        best_action = Action.WAIT

        for action in ACTION_ORDER:
            result = apply_action(robot.x, robot.y, robot.dir, action, self.grid_w, self.grid_h)
            if result is None:
                continue

            next_x = result[0]
            next_y = result[1]
            next_pos = (next_x, next_y)

            # Is this cell blocked?
            if next_pos in blocked_t1:
                continue

            # Is it reserved by another robot?
            if reservations.is_reserved(next_pos, 1):
                continue

            # Would we swap with another robot?
            if current_pos != next_pos:
                forward_reserved = reservations.is_edge_reserved(current_pos, next_pos, 1)
                reverse_reserved = reservations.is_edge_reserved(next_pos, current_pos, 1)
                if forward_reserved or reverse_reserved:
                    continue

            # Is it forbidden by a constraint?
            if _blocked_by_constraints([self.constraints], current_pos, next_pos, 1):
                continue

            # Score this action — lower is better
            score = self._immediate_action_score(action, current_pos, next_pos, target)
            if score < best_score:
                best_score = score
                best_action = action

        return best_action

    @staticmethod
    def _immediate_action_score(
        action: Action,
        current_pos: GridPos,
        next_pos: GridPos,
        target: Optional[GridPos],
    ) -> float:
        """Score an immediate action. Lower is better."""
        if target is None:
            return NO_TARGET_SCORES[action]

        distance_to_target = manhattan(next_pos, target)
        action_penalty = TARGET_PENALTIES[action]

        staying_in_place_penalty = 0.0
        if next_pos == current_pos:
            staying_in_place_penalty = 0.2

        return distance_to_target + action_penalty + staying_in_place_penalty

    def _should_pick_drop(self, robot: Robot, env) -> bool:
        """Should this robot pick up or drop off a shelf right now?"""
        # --- Robot is carrying a shelf ---
        if robot.carrying is not None:
            is_requested = bool(robot.carrying.get("requested"))
            if not is_requested:
                return False
            on_goal = (robot.x, robot.y) in env.GOALS
            return on_goal

        # --- Robot is not carrying anything ---
        # Check if there is an assigned, requested shelf right here
        for shelf in env.shelves:
            if shelf["x"] != robot.x:
                continue
            if shelf["y"] != robot.y:
                continue
            if shelf["carried"]:
                continue
            if not bool(shelf.get("requested")):
                continue
            assigned_shelf_id = self.assignment_manager.agent_to_shelf.get(robot.id)
            if assigned_shelf_id != shelf["id"]:
                continue
            # Found a matching shelf right here
            return True

        return False
