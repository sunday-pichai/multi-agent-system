import math
import random
from typing import Dict, List, Optional, Tuple

import pygame

import config as cfg
from agent import Action, Robot

pygame.init()
GridPos = Tuple[int, int]

_DX = [0, 1, 0, -1]
_DY = [-1, 0, 1, 0]


class WarehouseEnv:
    """Grid environment for multi-agent warehouse simulation."""

    def __init__(self, render: bool = True, num_agents: Optional[int] = None) -> None:
        self.grid_w = cfg.GRID_W
        self.grid_h = cfg.GRID_H
        self.GOALS = list(cfg.GOALS)
        self.num_shelves = cfg.NUM_SHELVES
        self.num_agents = num_agents if num_agents is not None else cfg.NUM_AGENTS
        self.render_enabled = render
        self.render_fps = cfg.RENDER_FPS
        self._renderer = None

        if self.render_enabled:
            cell_size = self._compute_cell_size()
            self.cell_size = cell_size
            self.grid_width_px = self.grid_w * cell_size
            self.grid_height_px = self.grid_h * cell_size
            from renderer import Renderer
            self._renderer = Renderer(self.grid_w, self.grid_h, cell_size)
            # Expose screen/clock so existing handle_event still works
            self.screen = self._renderer.screen
            self.clock = self._renderer.clock

        self.reset()

    def _compute_cell_size(self) -> int:
        optimal = min(2560 // self.grid_w, 1440 // self.grid_h)
        return min(cfg.CELL_SIZE, optimal) if cfg.CELL_SIZE > 0 else optimal

    def get_random_free_position(self, occupied_positions: set) -> Tuple[int, int]:
        while True:
            x = random.randint(0, self.grid_w - 1)
            y = random.randint(0, self.grid_h - 1)
            if (x, y) not in occupied_positions:
                return x, y

    def reset(self) -> List[List[float]]:
        occupied = set(self.GOALS)

        self.robots: List[Robot] = []
        for robot_id in range(self.num_agents):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            self.robots.append(Robot(robot_id, x, y))

        self.shelves: List[Dict] = []
        for shelf_id in range(self.num_shelves):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            shelf = {
                "id": shelf_id,
                "x": x,
                "y": y,
                "carried": False,
                "requested": True,
            }
            self.shelves.append(shelf)

        self.steps = 0
        self.last_collisions = 0
        self.last_delivered = 0
        self.last_conflicts: List[Dict] = []
        self.selected_agent_id = self.robots[0].id if self.robots else -1
        self._planner_allowed_shelf_entries: Dict[int, GridPos] = {}
        self._planner_last_actions: List[int] = [Action.WAIT.value for _ in range(self.num_agents)]
        self._planner_debug_by_agent: Dict[int, Dict] = {}
        self.event_log: List[str] = []
        self.traffic_heat: List[List[int]] = [[0 for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        self.collision_heat: List[List[int]] = [[0 for _ in range(self.grid_w)] for _ in range(self.grid_h)]
        self.total_collisions = 0
        self.total_deliveries = 0
        return [self.get_state(robot) for robot in self.robots]

    def handle_event(self, event) -> None:
        """Handle UI events for agent selection controls."""
        if not self.render_enabled:
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            cell_size = getattr(self, 'cell_size', cfg.CELL_SIZE)
            grid_width_px = getattr(self, 'grid_width_px', self.grid_w * cell_size)
            grid_height_px = getattr(self, 'grid_height_px', self.grid_h * cell_size)
            if 0 <= mouse_x < grid_width_px and 0 <= mouse_y < grid_height_px:
                gx = mouse_x // cell_size
                gy = mouse_y // cell_size
                selected = next((robot for robot in self.robots if robot.x == gx and robot.y == gy), None)
                if selected is not None:
                    self.selected_agent_id = selected.id

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_RIGHT, pygame.K_PERIOD):
                self._cycle_selected_agent(1)
            elif event.key in (pygame.K_LEFT, pygame.K_COMMA):
                self._cycle_selected_agent(-1)

    def _cycle_selected_agent(self, delta: int) -> None:
        if not self.robots:
            self.selected_agent_id = -1
            return

        ids = [robot.id for robot in sorted(self.robots, key=lambda robot: robot.id)]
        if self.selected_agent_id not in ids:
            self.selected_agent_id = ids[0]
            return

        idx = ids.index(self.selected_agent_id)
        self.selected_agent_id = ids[(idx + delta) % len(ids)]

    def get_state(self, robot: Robot) -> List[float]:
        state: List[float] = [
            self._normalize(robot.x, self.grid_w),
            self._normalize(robot.y, self.grid_h),
            robot.dir.value / 3.0,
            1.0 if robot.carrying else 0.0,
        ]

        shelves_sorted = sorted(self.shelves, key=lambda shelf: shelf["id"])
        for shelf_idx in range(self.num_shelves):
            if shelf_idx < len(shelves_sorted):
                shelf = shelves_sorted[shelf_idx]
                state.extend(
                    [
                        self._normalize(shelf["x"], self.grid_w),
                        self._normalize(shelf["y"], self.grid_h),
                        1.0 if shelf["carried"] else 0.0,
                        1.0 if shelf["requested"] else 0.0,
                    ]
                )
            else:
                state.extend([0.0, 0.0, 0.0, 0.0])

        other_robots = [other for other in self.robots if other is not robot]
        for other_idx in range(self.num_agents - 1):
            if other_idx < len(other_robots):
                other = other_robots[other_idx]
                state.extend(
                    [
                        self._normalize(other.x, self.grid_w),
                        self._normalize(other.y, self.grid_h),
                        other.dir.value / 3.0,
                        1.0 if other.carrying else 0.0,
                    ]
                )
            else:
                state.extend([0.0, 0.0, 0.0, 0.0])

        return state

    def get_dist_to_target(self, robot: Robot) -> Optional[float]:
        if robot.carrying:
            carrying_requested = bool(robot.carrying["requested"])
            if not carrying_requested:
                return None

            min_distance = math.inf
            for gx, gy in self.GOALS:
                distance = abs(robot.x - gx) + abs(robot.y - gy)
                min_distance = min(min_distance, distance)
            return min_distance

        requested_shelves = [
            shelf
            for shelf in self.shelves
            if shelf["requested"] and not shelf["carried"]
        ]
        if not requested_shelves:
            return None

        min_distance = math.inf
        for shelf in requested_shelves:
            distance = abs(robot.x - shelf["x"]) + abs(robot.y - shelf["y"])
            min_distance = min(min_distance, distance)
        return min_distance

    def step(self, actions: List[int], record_trajectories: bool = False):
        decoded = [
            self._decode_action(actions[i]) if i < len(actions) else Action.WAIT
            for i in range(self.num_agents)
        ]
        self._planner_last_actions = [a.value for a in decoded]
        self.last_conflicts = []
        self._record_intent_conflicts([a.value for a in decoded])

        trajectories = [[(r.x, r.y)] for r in self.robots] if record_trajectories else None
        old_distances = [self.get_dist_to_target(r) for r in self.robots]
        rewards = [-0.01] * self.num_agents
        step_events: List[str] = []
        delivered_count = 0

        # ── process non-forward actions & collect forward intents ──
        forward_intents: Dict[int, Tuple[GridPos, GridPos]] = {}
        early_blocked: set = set()

        for idx, (robot, action) in enumerate(zip(self.robots, decoded)):
            if action == Action.FORWARD:
                ok = self._collect_forward_intent(idx, robot, forward_intents, early_blocked, step_events)
            elif action == Action.TURN_LEFT:
                robot.turn_left(); rewards[idx] -= 0.002
            elif action == Action.TURN_RIGHT:
                robot.turn_right(); rewards[idx] -= 0.002
            elif action == Action.PICK_DROP:
                r, ev = robot.pick_or_drop(self); rewards[idx] += r
                if ev != "NOOP": step_events.append(f"R{robot.id}: {ev.lower()}")
                if ev == "DELIVERED": delivered_count += 1
            else:
                rewards[idx] -= 0.003  # WAIT

        # ── resolve forward conflicts ─────────────────────
        collisions = len(early_blocked)
        for idx in early_blocked:
            rewards[idx] -= 0.2
            self.collision_heat[self.robots[idx].y][self.robots[idx].x] += 1

        static_positions = {
            (r.x, r.y) for i, r in enumerate(self.robots)
            if i not in forward_intents
        }
        blocked = self._resolve_forward_conflicts(forward_intents, static_positions)
        for idx, (_, target) in forward_intents.items():
            if idx in blocked:
                rewards[idx] -= 0.2; collisions += 1
                self.collision_heat[self.robots[idx].y][self.robots[idx].x] += 1
                step_events.append(f"R{self.robots[idx].id}: blocked by robot conflict")
            else:
                robot = self.robots[idx]
                robot.x, robot.y = target
                if robot.carrying is not None:
                    robot.carrying["x"], robot.carrying["y"] = target
                rewards[idx] += 0.01

        # ── distance-based shaping & bookkeeping ──────────
        for robot in self.robots:
            self.traffic_heat[robot.y][robot.x] += 1

        self._apply_distance_rewards(rewards, old_distances)

        if delivered_count > 0:
            bonus = 2.0 * delivered_count
            rewards = [r + bonus for r in rewards]

        self.steps += 1
        self.last_collisions = collisions
        self.last_delivered = delivered_count
        self.total_collisions += collisions
        self.total_deliveries += delivered_count
        done = self.steps > 1000

        if self.last_conflicts:
            step_events.append(f"conflicts: {len(self.last_conflicts)}")
        for ev in step_events[-6:]:
            self.event_log.append(f"t{self.steps}: {ev}")
        self.event_log = self.event_log[-28:]

        states = [self.get_state(r) for r in self.robots]
        if trajectories is not None:
            for idx, robot in enumerate(self.robots):
                trajectories[idx].append((robot.x, robot.y))
        return states, rewards, done, collisions, trajectories

    # ── forward-intent helpers ────────────────────────────
    def _collect_forward_intent(
        self, idx: int, robot: Robot,
        intents: Dict[int, Tuple[GridPos, GridPos]],
        early_blocked: set, events: List[str],
    ) -> None:
        nx = robot.x + _DX[robot.dir.value]
        ny = robot.y + _DY[robot.dir.value]
        if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
            early_blocked.add(idx); events.append(f"R{robot.id}: blocked by boundary")
        elif robot._occupied_by_shelf(nx, ny, self):
            early_blocked.add(idx); events.append(f"R{robot.id}: blocked by shelf")
        else:
            intents[idx] = ((robot.x, robot.y), (nx, ny))

    @staticmethod
    def _resolve_forward_conflicts(
        intents: Dict[int, Tuple[GridPos, GridPos]],
        static_positions: set,
    ) -> set:
        """Return set of agent indices whose forward move is blocked."""
        blocked: set = set()

        # Blocked by static (non-moving) agents
        for idx, (_, tgt) in intents.items():
            if tgt in static_positions:
                blocked.add(idx)

        # Same-target conflicts
        target_counts: Dict[GridPos, int] = {}
        for idx, (_, tgt) in intents.items():
            if idx not in blocked:
                target_counts[tgt] = target_counts.get(tgt, 0) + 1
        for idx, (_, tgt) in intents.items():
            if target_counts.get(tgt, 0) > 1:
                blocked.add(idx)

        # Head-on swap conflicts
        active = [(i, f, t) for i, (f, t) in intents.items() if i not in blocked]
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                if active[i][1] == active[j][2] and active[i][2] == active[j][1]:
                    blocked.add(active[i][0]); blocked.add(active[j][0])

        return blocked

    def _apply_distance_rewards(self, rewards: List[float], old_dists: List[Optional[float]]) -> None:
        for idx, robot in enumerate(self.robots):
            new_d = self.get_dist_to_target(robot)
            old_d = old_dists[idx]
            if old_d is not None and new_d is not None:
                delta = old_d - new_d
                rewards[idx] += delta * (0.12 if delta > 0 else 0.04)
            if robot.carrying is not None and not robot.carrying["requested"]:
                rewards[idx] -= 0.05

    def render(self) -> None:
        if self._renderer is not None:
            self._renderer.draw(self, self.render_fps)

    def evaluate(
        self,
        planner,
        num_episodes: int = 50,
        max_steps_per_episode: int = 200,
        progress_every: int = 0,
        logger=None,
    ) -> float:
        total_collisions = 0

        for episode_idx in range(num_episodes):
            self.reset()
            done = False
            steps_in_episode = 0

            while not done and steps_in_episode < max_steps_per_episode:
                actions = planner.compute_actions(self)
                _, _, done, collisions, _ = self.step(actions)
                total_collisions += collisions
                steps_in_episode += 1

            if progress_every and (episode_idx + 1) % progress_every == 0:
                msg = f"Eval progress: {episode_idx + 1}/{num_episodes} episodes"
                if logger:
                    logger.info(msg)
                else:
                    print(msg)

        if num_episodes <= 0 or self.num_agents <= 0:
            return 0.0
        return total_collisions / (num_episodes * self.num_agents)

    @staticmethod
    def _normalize(value: int, max_value: int) -> float:
        denominator = max(max_value - 1, 1)
        return value / denominator

    @staticmethod
    def _decode_action(action_idx: int) -> Action:
        try:
            return Action(action_idx)
        except Exception:
            return Action.WAIT

    def _record_intent_conflicts(self, actions: List[int]) -> None:
        intents: Dict[int, Tuple[GridPos, GridPos]] = {}

        for idx, robot in enumerate(self.robots):
            action = self._decode_action(actions[idx] if idx < len(actions) else Action.WAIT.value)
            if action != Action.FORWARD:
                continue
            nx = robot.x + _DX[robot.dir.value]
            ny = robot.y + _DY[robot.dir.value]
            if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
                self.last_conflicts.append(
                    {"type": "boundary", "agent": robot.id,
                     "from": (robot.x, robot.y), "to": (nx, ny)})
                continue
            intents[robot.id] = ((robot.x, robot.y), (nx, ny))

        # Vertex conflicts
        target_to_agents: Dict[GridPos, List[int]] = {}
        for aid, (_, tgt) in intents.items():
            target_to_agents.setdefault(tgt, []).append(aid)
        for tgt, agents in target_to_agents.items():
            if len(agents) > 1:
                self.last_conflicts.append({"type": "vertex", "agents": agents, "pos": tgt})

        # Edge (swap) conflicts
        items = list(intents.items())
        for i in range(len(items)):
            a_id, (a_from, a_to) = items[i]
            for j in range(i + 1, len(items)):
                b_id, (b_from, b_to) = items[j]
                if a_from == b_to and a_to == b_from:
                    self.last_conflicts.append(
                        {"type": "edge", "agents": [a_id, b_id],
                         "from": a_from, "to": a_to})
