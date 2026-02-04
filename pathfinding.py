from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Iterable
import heapq

from agent import Action, Direction, Robot


GridPos = Tuple[int, int]


@dataclass(frozen=True)
class NodeKey:
    x: int
    y: int
    dir_value: int
    t: int


class ReservationTable:
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
    if action == Action.TURN_LEFT:
        return x, y, Direction((direction.value - 1) % 4)
    if action == Action.TURN_RIGHT:
        return x, y, Direction((direction.value + 1) % 4)
    if action == Action.WAIT:
        return x, y, direction
    if action == Action.FORWARD:
        dx, dy = [0, 1, 0, -1], [-1, 0, 1, 0]  # U R D L
        nx = x + dx[direction.value]
        ny = y + dy[direction.value]
        if not (0 <= nx < grid_w and 0 <= ny < grid_h):
            return None
        return nx, ny, direction
    return None


def simulate_positions(
    start_pos: GridPos,
    start_dir: Direction,
    actions: List[Action],
    grid_w: int,
    grid_h: int,
    horizon: int,
) -> List[GridPos]:
    positions: List[GridPos] = [start_pos]
    x, y = start_pos
    direction = start_dir
    for step in range(horizon):
        action = actions[step] if step < len(actions) else Action.WAIT
        result = apply_action(x, y, direction, action, grid_w, grid_h)
        if result is None:
            result = (x, y, direction)
        x, y, direction = result
        positions.append((x, y))
    return positions


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
    start_key = NodeKey(start_pos[0], start_pos[1], start_dir.value, 0)
    open_heap: List[Tuple[int, int, int, NodeKey]] = []
    seq = 0
    heapq.heappush(open_heap, (manhattan(start_pos, goal), 0, seq, start_key))

    g_score: Dict[NodeKey, int] = {start_key: 0}
    came_from: Dict[NodeKey, Tuple[NodeKey, Action]] = {}

    actions = [Action.FORWARD, Action.TURN_LEFT, Action.TURN_RIGHT, Action.WAIT]

    expansions = 0
    while open_heap:
        _, g, _, current = heapq.heappop(open_heap)
        expansions += 1
        if expansions > max_expansions:
            return None
        cur_pos = (current.x, current.y)
        cur_dir = Direction(current.dir_value)

        if cur_pos == goal:
            # reconstruct action path
            path: List[Action] = []
            node = current
            while node in came_from:
                prev, action = came_from[node]
                path.append(action)
                node = prev
            path.reverse()
            return path

        if current.t >= max_time:
            continue

        for action in actions:
            result = apply_action(
                current.x, current.y, cur_dir, action, grid_w, grid_h
            )
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
            if constraints:
                blocked = False
                for table in constraints:
                    if table.is_forbidden(next_pos, nt) or table.is_edge_forbidden(cur_pos, next_pos, nt):
                        blocked = True
                        break
                if blocked:
                    continue

            next_key = NodeKey(nx, ny, ndir.value, nt)
            tentative_g = g + 1
            if tentative_g < g_score.get(next_key, 1_000_000):
                g_score[next_key] = tentative_g
                f = tentative_g + manhattan(next_pos, goal)
                seq += 1
                heapq.heappush(open_heap, (f, tentative_g, seq, next_key))
                came_from[next_key] = (current, action)

    return None


class CooperativePlanner:
    def __init__(self, grid_w: int, grid_h: int, plan_horizon: int = 80) -> None:
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.plan_horizon = plan_horizon
        self.agent_to_shelf: Dict[int, int] = {}
        self.shelf_to_agent: Dict[int, int] = {}
        self.constraints = ConstraintTable()
        try:
            from config import USE_CBS, CBS_MAX_NODES, ASTAR_MAX_NODES, IDLE_LIMIT
            self.use_cbs = USE_CBS
            self.cbs_max_nodes = CBS_MAX_NODES
            self.astar_max_nodes = ASTAR_MAX_NODES
            self.idle_limit = IDLE_LIMIT
        except Exception:
            self.use_cbs = True
            self.cbs_max_nodes = 200
            self.astar_max_nodes = 6000
            self.idle_limit = 6
        self.last_positions: Dict[int, GridPos] = {}
        self.idle_steps: Dict[int, int] = {}

    def add_constraint_position(self, pos: GridPos, t: int) -> None:
        self.constraints.forbid_position(pos, t)

    def add_constraint_edge(self, from_pos: GridPos, to_pos: GridPos, t: int) -> None:
        self.constraints.forbid_edge(from_pos, to_pos, t)

    def compute_actions(self, env) -> List[int]:
        # Track idle agents to force reassignment and movement
        for robot in env.robots:
            pos = (robot.x, robot.y)
            last = self.last_positions.get(robot.id)
            if last == pos:
                self.idle_steps[robot.id] = self.idle_steps.get(robot.id, 0) + 1
            else:
                self.idle_steps[robot.id] = 0
            self.last_positions[robot.id] = pos
            if self.idle_steps[robot.id] >= self.idle_limit:
                shelf_id = self.agent_to_shelf.pop(robot.id, None)
                if shelf_id is not None:
                    self.shelf_to_agent.pop(shelf_id, None)
                self.idle_steps[robot.id] = 0

        self._update_assignments(env)
        reservations = ReservationTable()
        occupied = {(r.x, r.y) for r in env.robots}
        actions_by_id: Dict[int, int] = {}

        if self.use_cbs:
            cbs_actions = self._plan_with_cbs(env)
            if cbs_actions is not None:
                return cbs_actions

        for robot in sorted(env.robots, key=lambda r: r.id):
            blocked_t1 = occupied - {(robot.x, robot.y)}
            target = self._target_for_robot(robot, env)
            if self._should_pick_drop(robot, env):
                action = Action.PICK_DROP
                reservations.reserve_positions(
                    simulate_positions(
                        (robot.x, robot.y),
                        robot.dir,
                        [],
                        self.grid_w,
                        self.grid_h,
                        self.plan_horizon,
                    )
                )
                actions_by_id[robot.id] = action.value
                continue

            if target is None:
                action = Action.WAIT
                reservations.reserve_positions(
                    simulate_positions(
                        (robot.x, robot.y),
                        robot.dir,
                        [],
                        self.grid_w,
                        self.grid_h,
                        self.plan_horizon,
                    )
                )
                actions_by_id[robot.id] = action.value
                continue

            plan = astar_time(
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
            if not plan:
                action = self._fallback_action(robot, env)
                plan = []
            else:
                action = plan[0]

            reservations.reserve_positions(
                simulate_positions(
                    (robot.x, robot.y),
                    robot.dir,
                    plan,
                    self.grid_w,
                    self.grid_h,
                    self.plan_horizon,
                )
            )
            actions_by_id[robot.id] = action.value

        return [actions_by_id[r.id] for r in env.robots]

    def _fallback_action(self, robot: Robot, env) -> Action:
        # Try to move forward if possible; otherwise rotate to break symmetry
        result = apply_action(robot.x, robot.y, robot.dir, Action.FORWARD, self.grid_w, self.grid_h)
        if result is not None:
            nx, ny, _ = result
            if all((r.x, r.y) != (nx, ny) for r in env.robots):
                return Action.FORWARD
        return Action.TURN_RIGHT

    def _plan_with_cbs(self, env) -> Optional[List[int]]:
        robots = sorted(env.robots, key=lambda r: r.id)
        targets: Dict[int, Optional[GridPos]] = {}
        for robot in robots:
            if self._should_pick_drop(robot, env):
                targets[robot.id] = None
            else:
                targets[robot.id] = self._target_for_robot(robot, env)

        @dataclass(order=True)
        class CBSNode:
            cost: int
            constraints: Dict[int, ConstraintTable] = field(compare=False)
            paths: Dict[int, List[Action]] = field(compare=False)

        def compute_path(robot: Robot, target: GridPos, local_constraints: ConstraintTable) -> Optional[List[Action]]:
            return astar_time(
                (robot.x, robot.y),
                robot.dir,
                target,
                self.grid_w,
                self.grid_h,
                ReservationTable(),
                self.plan_horizon,
                set(),
                constraints=[self.constraints, local_constraints],
                max_expansions=self.astar_max_nodes,
            )

        def build_positions(robot: Robot, actions: List[Action]) -> List[GridPos]:
            return simulate_positions(
                (robot.x, robot.y),
                robot.dir,
                actions,
                self.grid_w,
                self.grid_h,
                self.plan_horizon,
            )

        def find_conflict(paths: Dict[int, List[Action]]) -> Optional[Dict]:
            positions = {}
            for robot in robots:
                actions = paths.get(robot.id, [])
                positions[robot.id] = build_positions(robot, actions)

            for t in range(1, self.plan_horizon + 1):
                seen: Dict[GridPos, int] = {}
                for rid, pos_list in positions.items():
                    pos = pos_list[t] if t < len(pos_list) else pos_list[-1]
                    if pos in seen:
                        return {'type': 'vertex', 'time': t, 'pos': pos, 'agents': [seen[pos], rid]}
                    seen[pos] = rid
                for a_id, a_pos in positions.items():
                    for b_id, b_pos in positions.items():
                        if a_id >= b_id:
                            continue
                        a_prev = a_pos[t - 1] if t - 1 < len(a_pos) else a_pos[-1]
                        a_now = a_pos[t] if t < len(a_pos) else a_pos[-1]
                        b_prev = b_pos[t - 1] if t - 1 < len(b_pos) else b_pos[-1]
                        b_now = b_pos[t] if t < len(b_pos) else b_pos[-1]
                        if a_prev == b_now and a_now == b_prev:
                            return {'type': 'edge', 'time': t, 'agents': [a_id, b_id], 'from': a_prev, 'to': a_now}
            return None

        base_constraints = {r.id: ConstraintTable() for r in robots}
        base_paths: Dict[int, List[Action]] = {}
        total_cost = 0
        for robot in robots:
            if targets[robot.id] is None:
                base_paths[robot.id] = []
                continue
            path = compute_path(robot, targets[robot.id], base_constraints[robot.id])
            if path is None:
                return None
            base_paths[robot.id] = path
            total_cost += len(path)

        open_list: List[CBSNode] = []
        heapq.heappush(open_list, CBSNode(total_cost, base_constraints, base_paths))

        expansions = 0
        while open_list and expansions < self.cbs_max_nodes:
            node = heapq.heappop(open_list)
            conflict = find_conflict(node.paths)
            if conflict is None:
                actions_by_id = {}
                for robot in robots:
                    if self._should_pick_drop(robot, env):
                        actions_by_id[robot.id] = Action.PICK_DROP.value
                        continue
                    actions = node.paths.get(robot.id, [])
                    actions_by_id[robot.id] = actions[0].value if actions else Action.WAIT.value
                return [actions_by_id[r.id] for r in env.robots]

            expansions += 1
            for agent_id in conflict['agents']:
                new_constraints = {aid: tbl for aid, tbl in node.constraints.items()}
                local = ConstraintTable()
                prior = node.constraints[agent_id]
                for t, positions in prior.positions.items():
                    for pos in positions:
                        local.forbid_position(pos, t)
                for t, edges in prior.edges.items():
                    for edge in edges:
                        local.forbid_edge(edge[0], edge[1], t)

                if conflict['type'] == 'vertex':
                    local.forbid_position(conflict['pos'], conflict['time'])
                elif conflict['type'] == 'edge':
                    local.forbid_edge(conflict['from'], conflict['to'], conflict['time'])

                new_constraints[agent_id] = local

                new_paths = dict(node.paths)
                robot = next(r for r in robots if r.id == agent_id)
                target = targets[agent_id]
                if target is None:
                    continue
                new_path = compute_path(robot, target, local)
                if new_path is None:
                    continue
                new_paths[agent_id] = new_path
                new_cost = sum(len(p) for p in new_paths.values())
                heapq.heappush(open_list, CBSNode(new_cost, new_constraints, new_paths))

        return None

    def _update_assignments(self, env) -> None:
        shelves_by_id = {s['id']: s for s in env.shelves}
        for agent_id, shelf_id in list(self.agent_to_shelf.items()):
            shelf = shelves_by_id.get(shelf_id)
            if shelf is None or shelf['carried'] or not shelf['requested']:
                self.agent_to_shelf.pop(agent_id, None)
                self.shelf_to_agent.pop(shelf_id, None)

        unassigned = [
            s for s in env.shelves
            if s['requested'] and not s['carried'] and s['id'] not in self.shelf_to_agent
        ]
        for robot in env.robots:
            if robot.carrying:
                continue
            if robot.id in self.agent_to_shelf:
                continue
            if not unassigned:
                break
            best = min(unassigned, key=lambda s: manhattan((robot.x, robot.y), (s['x'], s['y'])))
            self.agent_to_shelf[robot.id] = best['id']
            self.shelf_to_agent[best['id']] = robot.id
            unassigned.remove(best)

    def _target_for_robot(self, robot: Robot, env) -> Optional[GridPos]:
        if robot.carrying:
            if robot.carrying.get('requested'):
                return self._nearest_goal((robot.x, robot.y), env.GOALS)
            return None

        shelf_id = self.agent_to_shelf.get(robot.id)
        if shelf_id is None:
            return None
        shelf = next((s for s in env.shelves if s['id'] == shelf_id), None)
        if shelf is None:
            return None
        return shelf['x'], shelf['y']

    def _nearest_goal(self, pos: GridPos, goals: List[GridPos]) -> GridPos:
        return min(goals, key=lambda g: manhattan(pos, g))

    def _should_pick_drop(self, robot: Robot, env) -> bool:
        if robot.carrying and robot.carrying.get('requested'):
            return (robot.x, robot.y) in env.GOALS
        if robot.carrying:
            return False

        shelf = next(
            (s for s in env.shelves if s['x'] == robot.x and s['y'] == robot.y and not s['carried']),
            None,
        )
        if shelf is None or not shelf.get('requested'):
            return False
        return self.agent_to_shelf.get(robot.id) == shelf['id']
