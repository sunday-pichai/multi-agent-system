import math
import random
from typing import Dict, List, Optional, Tuple

import pygame
import pygame.gfxdraw

import config as cfg
from agent import Action, Robot


pygame.init()
GridPos = Tuple[int, int]


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

        if self.render_enabled:
            # 1440p resolution: 2560x1440
            # Calculate cell size to fit grid nicely
            target_width = 2560
            target_height = 1440
            cell_size_w = target_width // self.grid_w
            cell_size_h = target_height // self.grid_h
            # Use the smaller to ensure it fits
            optimal_cell_size = min(cell_size_w, cell_size_h)
            # Use config cell size if it's reasonable, otherwise use calculated
            if cfg.CELL_SIZE > 0:
                cell_size = min(cfg.CELL_SIZE, optimal_cell_size)
            else:
                cell_size = optimal_cell_size
            
            width_px = self.grid_w * cell_size
            height_px = self.grid_h * cell_size
            self.grid_width_px = width_px
            self.grid_height_px = height_px
            self.screen = pygame.display.set_mode((width_px, height_px))
            pygame.display.set_caption("Warehouse Simulation")
            self.clock = pygame.time.Clock()
            # High-quality fonts for crisp rendering - scale with cell size
            font_size = max(14, cell_size // 5)
            font_small_size = max(10, cell_size // 7)
            font_tiny_size = max(8, cell_size // 10)
            try:
                self.font = pygame.font.SysFont("arial", font_size, bold=True)
                self.font_small = pygame.font.SysFont("arial", font_small_size, bold=True)
                self.font_tiny = pygame.font.SysFont("arial", font_tiny_size)
            except:
                self.font = pygame.font.Font(None, font_size)
                self.font_small = pygame.font.Font(None, font_small_size)
                self.font_tiny = pygame.font.Font(None, font_tiny_size)
            self.cell_size = cell_size

        self.reset()

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
        rewards: List[float] = []
        collisions = 0
        delivered_count = 0

        decoded_actions = [
            self._decode_action(actions[idx]) if idx < len(actions) else Action.WAIT
            for idx in range(self.num_agents)
        ]
        self._planner_last_actions = [action.value for action in decoded_actions]
        step_events: List[str] = []

        self.last_conflicts = []
        self._record_intent_conflicts([action.value for action in decoded_actions])

        trajectories = None
        if record_trajectories:
            trajectories = [[(robot.x, robot.y)] for robot in self.robots]

        old_distances = [self.get_dist_to_target(robot) for robot in self.robots]
        rewards = [-0.01 for _ in self.robots]

        forward_intents: Dict[int, Tuple[GridPos, GridPos]] = {}
        blocked_forward: set = set()
        blocked_forward_early: set = set()

        for idx, (robot, action) in enumerate(zip(self.robots, decoded_actions)):
            if action == Action.FORWARD:
                nx = robot.x + [0, 1, 0, -1][robot.dir.value]
                ny = robot.y + [-1, 0, 1, 0][robot.dir.value]

                if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
                    blocked_forward_early.add(idx)
                    step_events.append(f"R{robot.id}: blocked by boundary")
                    continue

                if robot._occupied_by_shelf(nx, ny, self):
                    blocked_forward_early.add(idx)
                    step_events.append(f"R{robot.id}: blocked by shelf")
                    continue

                forward_intents[idx] = ((robot.x, robot.y), (nx, ny))
                continue

            if action == Action.TURN_LEFT:
                robot.turn_left()
                rewards[idx] -= 0.002
            elif action == Action.TURN_RIGHT:
                robot.turn_right()
                rewards[idx] -= 0.002
            elif action == Action.PICK_DROP:
                extra_reward, event = robot.pick_or_drop(self)
                rewards[idx] += extra_reward
                if event != "NOOP":
                    step_events.append(f"R{robot.id}: {event.lower()}")
                if event == "DELIVERED":
                    delivered_count += 1
            elif action == Action.WAIT:
                rewards[idx] -= 0.003

        for idx in blocked_forward_early:
            rewards[idx] -= 0.2
            collisions += 1
            robot = self.robots[idx]
            self.collision_heat[robot.y][robot.x] += 1

        static_positions = {
            (robot.x, robot.y)
            for idx, robot in enumerate(self.robots)
            if idx not in forward_intents
        }

        for idx, (_, target) in forward_intents.items():
            if target in static_positions:
                blocked_forward.add(idx)

        target_counts: Dict[GridPos, int] = {}
        for idx, (_, target) in forward_intents.items():
            if idx in blocked_forward:
                continue
            target_counts[target] = target_counts.get(target, 0) + 1

        for idx, (_, target) in forward_intents.items():
            if target_counts.get(target, 0) > 1:
                blocked_forward.add(idx)

        forward_items = [(idx, move[0], move[1]) for idx, move in forward_intents.items() if idx not in blocked_forward]
        for i in range(len(forward_items)):
            idx_a, from_a, to_a = forward_items[i]
            for j in range(i + 1, len(forward_items)):
                idx_b, from_b, to_b = forward_items[j]
                if from_a == to_b and to_a == from_b:
                    blocked_forward.add(idx_a)
                    blocked_forward.add(idx_b)

        for idx, (_, target) in forward_intents.items():
            if idx in blocked_forward:
                rewards[idx] -= 0.2
                collisions += 1
                robot = self.robots[idx]
                self.collision_heat[robot.y][robot.x] += 1
                step_events.append(f"R{robot.id}: blocked by robot conflict")
                continue

            robot = self.robots[idx]
            robot.x, robot.y = target
            if robot.carrying is not None:
                robot.carrying["x"] = robot.x
                robot.carrying["y"] = robot.y
            rewards[idx] += 0.01

        for robot in self.robots:
            self.traffic_heat[robot.y][robot.x] += 1

        for idx, robot in enumerate(self.robots):
            new_distance = self.get_dist_to_target(robot)
            old_distance = old_distances[idx]
            if old_distance is not None and new_distance is not None:
                distance_improvement = old_distance - new_distance
                if distance_improvement > 0:
                    rewards[idx] += distance_improvement * 0.12
                elif distance_improvement < 0:
                    rewards[idx] += distance_improvement * 0.04

            if robot.carrying is not None and not robot.carrying["requested"]:
                rewards[idx] -= 0.05

        if delivered_count > 0:
            team_bonus = 2.0 * delivered_count
            rewards = [reward + team_bonus for reward in rewards]

        self.steps += 1
        self.last_collisions = collisions
        self.last_delivered = delivered_count
        self.total_collisions += collisions
        self.total_deliveries += delivered_count
        done = self.steps > 1000

        if self.last_conflicts:
            step_events.append(f"conflicts: {len(self.last_conflicts)}")

        for event in step_events[-6:]:
            self.event_log.append(f"t{self.steps}: {event}")
        if len(self.event_log) > 28:
            self.event_log = self.event_log[-28:]

        states = [self.get_state(robot) for robot in self.robots]

        if trajectories is not None:
            for idx, robot in enumerate(self.robots):
                trajectories[idx].append((robot.x, robot.y))

        return states, rewards, done, collisions, trajectories

    def render(self) -> None:
        if not self.render_enabled:
            return

        cell_size = getattr(self, 'cell_size', cfg.CELL_SIZE)
        grid_width_px = getattr(self, 'grid_width_px', self.grid_w * cell_size)
        # Pure white background for crisp minimal look
        self.screen.fill(cfg.BG_PURE)

        # Draw ultra-subtle grid with anti-aliased lines
        for x in range(self.grid_w + 1):
            pygame.draw.aaline(
                self.screen,
                cfg.GRID_SUBTLE,
                (x * cell_size, 0),
                (x * cell_size, self.grid_h * cell_size),
            )
        for y in range(self.grid_h + 1):
            pygame.draw.aaline(
                self.screen,
                cfg.GRID_SUBTLE,
                (0, y * cell_size),
                (grid_width_px, y * cell_size),
            )

        # Get robot positions to avoid drawing shelves under them
        robot_positions = {(robot.x, robot.y) for robot in self.robots}

        # Draw goal cells - crisp solid design with subtle shadow
        for gx, gy in self.GOALS:
            goal_x = gx * cell_size
            goal_y = gy * cell_size
            margin = 2
            size = cell_size - margin * 2
            
            # Subtle shadow offset
            shadow_offset = 1
            shadow_rect = pygame.Rect(
                goal_x + margin + shadow_offset,
                goal_y + margin + shadow_offset,
                size,
                size,
            )
            pygame.draw.rect(self.screen, cfg.GOAL_SHADOW, shadow_rect)
            
            # Main goal rectangle
            goal_rect = pygame.Rect(goal_x + margin, goal_y + margin, size, size)
            pygame.draw.rect(self.screen, cfg.GOAL_PRIMARY, goal_rect)
            
            # Crisp border
            pygame.draw.rect(self.screen, cfg.GOAL_SHADOW, goal_rect, 2)
            
            # Clean text
            text = self.font_small.render("GOAL", True, cfg.TEXT_ON_DARK)
            text_rect = text.get_rect(center=goal_rect.center)
            self.screen.blit(text, text_rect)

        # Draw shelves - solid crisp boxes
        for shelf in self.shelves:
            if shelf["carried"]:
                continue
            
            shelf_pos = (shelf["x"], shelf["y"])
            if shelf_pos in robot_positions:
                continue
            
            shelf_x = shelf["x"] * cell_size
            shelf_y = shelf["y"] * cell_size
            margin = 3
            size = cell_size - margin * 2
            
            # Choose colors
            if shelf["requested"]:
                shelf_color = cfg.SHELF_ACTIVE
                shadow_color = cfg.SHELF_SHADOW
                text_color = cfg.TEXT_ON_DARK
            else:
                shelf_color = cfg.SHELF_IDLE
                shadow_color = (150, 150, 160)
                text_color = cfg.TEXT_PRIMARY
            
            # Subtle shadow
            shadow_offset = 1
            shadow_rect = pygame.Rect(
                shelf_x + margin + shadow_offset,
                shelf_y + margin + shadow_offset,
                size,
                size,
            )
            pygame.draw.rect(self.screen, shadow_color, shadow_rect)
            
            # Main shelf rectangle
            shelf_rect = pygame.Rect(shelf_x + margin, shelf_y + margin, size, size)
            pygame.draw.rect(self.screen, shelf_color, shelf_rect)
            
            # Crisp border
            border_color = shadow_color if shelf["requested"] else (160, 160, 170)
            pygame.draw.rect(self.screen, border_color, shelf_rect, 2)
            
            # Shelf ID - crisp text
            shelf_id_text = str(shelf["id"] % 100)
            text = self.font_tiny.render(shelf_id_text, True, text_color)
            text_rect = text.get_rect(center=shelf_rect.center)
            self.screen.blit(text, text_rect)

        # Draw robot symmetry orbits
        try:
            from symmetry_reduction import detect_role_orbits
            orbits = detect_role_orbits(self.robots)
        except Exception:
            orbits = [[idx] for idx in range(len(self.robots))]

        # Refined orbit colors
        orbit_colors = [
            (100, 150, 220),
            (220, 150, 100),
            (150, 220, 150),
            (220, 100, 180),
            (200, 200, 120),
            (100, 200, 200),
        ]
        orbit_by_agent = {}
        for orbit_idx, orbit in enumerate(orbits):
            for agent_idx in orbit:
                orbit_by_agent[agent_idx] = orbit_idx

        # Draw robots - advanced crisp design with anti-aliasing
        for idx, robot in enumerate(self.robots):
            center_x = robot.x * cell_size + cell_size // 2
            center_y = robot.y * cell_size + cell_size // 2
            radius = cell_size // 3 - 2

            # Robot body color
            if robot.carrying:
                body_color = cfg.ROBOT_CARRYING
                shadow_color = (200, 100, 40)
            else:
                body_color = cfg.ROBOT_PRIMARY
                shadow_color = cfg.ROBOT_SHADOW

            # Draw shadow circle (subtle depth)
            shadow_offset = 1
            pygame.gfxdraw.filled_circle(
                self.screen,
                center_x + shadow_offset,
                center_y + shadow_offset,
                radius,
                shadow_color,
            )

            # Main robot body - anti-aliased circle
            pygame.gfxdraw.filled_circle(
                self.screen,
                center_x,
                center_y,
                radius,
                body_color,
            )

            # Crisp border
            pygame.gfxdraw.aacircle(
                self.screen,
                center_x,
                center_y,
                radius,
                shadow_color,
            )

            # Carrying indicator - gold accent
            if robot.carrying and robot.carrying.get("requested"):
                indicator_y = center_y - radius - 6
                # Shadow
                pygame.gfxdraw.filled_circle(
                    self.screen,
                    center_x + 1,
                    indicator_y + 1,
                    5,
                    (200, 150, 30),
                )
                # Main circle
                pygame.gfxdraw.filled_circle(
                    self.screen,
                    center_x,
                    indicator_y,
                    5,
                    cfg.ACCENT_GOLD,
                )
                pygame.gfxdraw.aacircle(
                    self.screen,
                    center_x,
                    indicator_y,
                    5,
                    (220, 170, 40),
                )

            # Direction arrow - crisp anti-aliased design
            arrow_length = radius - 1
            arrow_head_size = 5
            arrow_shaft_width = 2
            
            if robot.dir.value == 0:  # UP
                # Arrow shaft
                shaft_rect = pygame.Rect(
                    center_x - arrow_shaft_width // 2,
                    center_y - arrow_length,
                    arrow_shaft_width,
                    arrow_length - arrow_head_size,
                )
                pygame.draw.rect(self.screen, cfg.TEXT_ON_DARK, shaft_rect)
                # Arrowhead
                arrow_points = [
                    (center_x, center_y - arrow_length),
                    (center_x - arrow_head_size, center_y - arrow_length + arrow_head_size),
                    (center_x + arrow_head_size, center_y - arrow_length + arrow_head_size),
                ]
            elif robot.dir.value == 1:  # RIGHT
                shaft_rect = pygame.Rect(
                    center_x,
                    center_y - arrow_shaft_width // 2,
                    arrow_length - arrow_head_size,
                    arrow_shaft_width,
                )
                pygame.draw.rect(self.screen, cfg.TEXT_ON_DARK, shaft_rect)
                arrow_points = [
                    (center_x + arrow_length, center_y),
                    (center_x + arrow_length - arrow_head_size, center_y - arrow_head_size),
                    (center_x + arrow_length - arrow_head_size, center_y + arrow_head_size),
                ]
            elif robot.dir.value == 2:  # DOWN
                shaft_rect = pygame.Rect(
                    center_x - arrow_shaft_width // 2,
                    center_y,
                    arrow_shaft_width,
                    arrow_length - arrow_head_size,
                )
                pygame.draw.rect(self.screen, cfg.TEXT_ON_DARK, shaft_rect)
                arrow_points = [
                    (center_x, center_y + arrow_length),
                    (center_x - arrow_head_size, center_y + arrow_length - arrow_head_size),
                    (center_x + arrow_head_size, center_y + arrow_length - arrow_head_size),
                ]
            else:  # LEFT
                shaft_rect = pygame.Rect(
                    center_x - arrow_length + arrow_head_size,
                    center_y - arrow_shaft_width // 2,
                    arrow_length - arrow_head_size,
                    arrow_shaft_width,
                )
                pygame.draw.rect(self.screen, cfg.TEXT_ON_DARK, shaft_rect)
                arrow_points = [
                    (center_x - arrow_length, center_y),
                    (center_x - arrow_length + arrow_head_size, center_y - arrow_head_size),
                    (center_x - arrow_length + arrow_head_size, center_y + arrow_head_size),
                ]
            
            # Draw arrowhead with anti-aliasing
            pygame.gfxdraw.filled_trigon(
                self.screen,
                int(arrow_points[0][0]),
                int(arrow_points[0][1]),
                int(arrow_points[1][0]),
                int(arrow_points[1][1]),
                int(arrow_points[2][0]),
                int(arrow_points[2][1]),
                cfg.TEXT_ON_DARK,
            )
            pygame.gfxdraw.aatrigon(
                self.screen,
                int(arrow_points[0][0]),
                int(arrow_points[0][1]),
                int(arrow_points[1][0]),
                int(arrow_points[1][1]),
                int(arrow_points[2][0]),
                int(arrow_points[2][1]),
                cfg.TEXT_ON_DARK,
            )

            # Orbit indicator - subtle corner marker
            orbit_idx = orbit_by_agent.get(idx, 0)
            orbit_color = orbit_colors[orbit_idx % len(orbit_colors)]
            corner_size = 4
            corner_x = center_x + radius - corner_size - 1
            corner_y = center_y - radius + 1
            corner_rect = pygame.Rect(corner_x, corner_y, corner_size, corner_size)
            pygame.draw.rect(self.screen, orbit_color, corner_rect)

            # Robot ID removed - clean minimal design without numbers

        # Conflict highlight overlay
        for conflict in self.last_conflicts:
            if conflict.get("type") == "vertex" and "pos" in conflict:
                cx, cy = conflict["pos"]
                overlay = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                overlay.fill((255, 60, 60, 70))
                self.screen.blit(overlay, (cx * cell_size, cy * cell_size))
            elif conflict.get("type") == "edge":
                from_pos = conflict.get("from")
                to_pos = conflict.get("to")
                if from_pos and to_pos:
                    x1 = from_pos[0] * cell_size + cell_size // 2
                    y1 = from_pos[1] * cell_size + cell_size // 2
                    x2 = to_pos[0] * cell_size + cell_size // 2
                    y2 = to_pos[1] * cell_size + cell_size // 2
                    pygame.draw.line(self.screen, (255, 80, 80), (x1, y1), (x2, y2), 3)

        pygame.display.flip()
        if self.render_fps > 0:
            self.clock.tick(self.render_fps)
        else:
            self.clock.tick(0)

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
        dx = [0, 1, 0, -1]
        dy = [-1, 0, 1, 0]

        for idx, robot in enumerate(self.robots):
            action_idx = actions[idx] if idx < len(actions) else Action.WAIT.value
            action = self._decode_action(action_idx)
            if action != Action.FORWARD:
                continue

            nx = robot.x + dx[robot.dir.value]
            ny = robot.y + dy[robot.dir.value]
            if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
                self.last_conflicts.append(
                    {
                        "type": "boundary",
                        "agent": robot.id,
                        "from": (robot.x, robot.y),
                        "to": (nx, ny),
                    }
                )
                continue

            intents[robot.id] = ((robot.x, robot.y), (nx, ny))

        target_to_agents: Dict[GridPos, List[int]] = {}
        for agent_id, (_, target) in intents.items():
            target_to_agents.setdefault(target, []).append(agent_id)

        for target, agents in target_to_agents.items():
            if len(agents) > 1:
                self.last_conflicts.append({"type": "vertex", "agents": agents, "pos": target})

        intent_items = list(intents.items())
        for idx_a in range(len(intent_items)):
            a_id, (a_from, a_to) = intent_items[idx_a]
            for idx_b in range(idx_a + 1, len(intent_items)):
                b_id, (b_from, b_to) = intent_items[idx_b]
                if a_from == b_to and a_to == b_from:
                    self.last_conflicts.append(
                        {
                            "type": "edge",
                            "agents": [a_id, b_id],
                            "from": a_from,
                            "to": a_to,
                        }
                    )
