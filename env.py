import math
import random
from typing import Dict, List, Optional, Tuple

import pygame

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
            width_px = self.grid_w * cfg.CELL_SIZE
            height_px = self.grid_h * cfg.CELL_SIZE
            self.screen = pygame.display.set_mode((width_px, height_px))
            pygame.display.set_caption("Warehouse Simulation")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("consolas", 18)

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
        return [self.get_state(robot) for robot in self.robots]

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

        self.last_conflicts = []
        self._record_intent_conflicts(actions)

        trajectories = None
        if record_trajectories:
            trajectories = [[(robot.x, robot.y)] for robot in self.robots]

        for robot, action_idx in zip(self.robots, actions):
            action = self._decode_action(action_idx)
            reward = -0.01
            old_distance = self.get_dist_to_target(robot)

            if action == Action.FORWARD:
                moved, bump = robot.forward(self)
                if bump:
                    reward -= 0.2
                    collisions += 1
                elif moved:
                    reward += 0.01
            elif action == Action.TURN_LEFT:
                robot.turn_left()
                reward -= 0.002
            elif action == Action.TURN_RIGHT:
                robot.turn_right()
                reward -= 0.002
            elif action == Action.PICK_DROP:
                extra_reward, event = robot.pick_or_drop(self)
                reward += extra_reward
                if event == "DELIVERED":
                    delivered_count += 1
            elif action == Action.WAIT:
                reward -= 0.003

            new_distance = self.get_dist_to_target(robot)
            if old_distance is not None and new_distance is not None:
                distance_improvement = old_distance - new_distance
                if distance_improvement > 0:
                    reward += distance_improvement * 0.12
                elif distance_improvement < 0:
                    reward += distance_improvement * 0.04

            if robot.carrying is not None and not robot.carrying["requested"]:
                reward -= 0.05

            rewards.append(reward)

        if delivered_count > 0:
            team_bonus = 2.0 * delivered_count
            rewards = [reward + team_bonus for reward in rewards]

        self.steps += 1
        self.last_collisions = collisions
        self.last_delivered = delivered_count
        done = self.steps > 1000

        states = [self.get_state(robot) for robot in self.robots]

        if trajectories is not None:
            for idx, robot in enumerate(self.robots):
                trajectories[idx].append((robot.x, robot.y))

        return states, rewards, done, collisions, trajectories

    def render(self) -> None:
        if not self.render_enabled:
            return

        cell_size = cfg.CELL_SIZE
        self.screen.fill(cfg.WHITE)

        # Draw grid
        for x in range(self.grid_w + 1):
            pygame.draw.line(
                self.screen,
                cfg.GRAY,
                (x * cell_size, 0),
                (x * cell_size, self.grid_h * cell_size),
                1,
            )
        for y in range(self.grid_h + 1):
            pygame.draw.line(
                self.screen,
                cfg.GRAY,
                (0, y * cell_size),
                (self.grid_w * cell_size, y * cell_size),
                1,
            )

        # Draw goal cells
        for gx, gy in self.GOALS:
            rect = pygame.Rect(gx * cell_size + 4, gy * cell_size + 4, cell_size - 8, cell_size - 8)
            pygame.draw.rect(self.screen, cfg.GOAL_COLOR, rect)
            text = self.font.render("G", True, cfg.WHITE)
            self.screen.blit(text, text.get_rect(center=rect.center))

        # Draw shelves
        for shelf in self.shelves:
            if shelf["carried"]:
                continue
            color = cfg.GREEN if shelf["requested"] else cfg.TEAL
            rect = pygame.Rect(
                shelf["x"] * cell_size + 8,
                shelf["y"] * cell_size + 8,
                cell_size - 16,
                cell_size - 16,
            )
            pygame.draw.rect(self.screen, color, rect)
            text = self.font.render(str(shelf["id"] % 100), True, cfg.BLACK)
            self.screen.blit(text, text.get_rect(center=rect.center))

        # Draw robot symmetry orbits
        try:
            from symmetry_reduction import detect_role_orbits

            orbits = detect_role_orbits(self.robots)
        except Exception:
            orbits = [[idx] for idx in range(len(self.robots))]

        orbit_colors = [
            (80, 120, 200),
            (200, 120, 80),
            (120, 200, 120),
            (200, 80, 160),
            (160, 160, 80),
            (80, 180, 180),
        ]
        orbit_by_agent = {}
        for orbit_idx, orbit in enumerate(orbits):
            for agent_idx in orbit:
                orbit_by_agent[agent_idx] = orbit_idx

        # Draw robots
        for idx, robot in enumerate(self.robots):
            center_x = robot.x * cell_size + cell_size // 2
            center_y = robot.y * cell_size + cell_size // 2

            if robot.carrying and robot.carrying["requested"]:
                pygame.draw.circle(self.screen, cfg.GOLD, (center_x, center_y), cell_size // 2 - 4, 3)

            body_color = cfg.RED if robot.carrying else cfg.ORANGE
            pygame.draw.circle(self.screen, body_color, (center_x, center_y), cell_size // 3)

            orbit_idx = orbit_by_agent.get(idx, 0)
            orbit_color = orbit_colors[orbit_idx % len(orbit_colors)]
            pygame.draw.circle(self.screen, orbit_color, (center_x, center_y), cell_size // 3 + 2, 2)

            look_dx = [0, 0.4, 0, -0.4]
            look_dy = [-0.4, 0, 0.4, 0]
            end_x = center_x + look_dx[robot.dir.value] * cell_size * 0.45
            end_y = center_y + look_dy[robot.dir.value] * cell_size * 0.45
            pygame.draw.line(self.screen, cfg.BLACK, (center_x, center_y), (end_x, end_y), 4)

            label = self.font.render(str(idx + 1), True, cfg.WHITE)
            self.screen.blit(label, label.get_rect(center=(center_x, center_y)))

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

        for robot, action_idx in zip(self.robots, actions):
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
