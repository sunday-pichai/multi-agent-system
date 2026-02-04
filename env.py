import pygame
import random
import math
from typing import List, Tuple, Optional
from agent import Robot
from config import GRID_W, GRID_H, CELL_SIZE, NUM_AGENTS, NUM_SHELVES, GOALS, RENDER_FPS

pygame.init()

class WarehouseEnv:
    """Warehouse environment for multi-agent simulation.

    Attributes:
        grid_w, grid_h: dimensions in cells
        render_enabled: whether to initialize a pygame surface
    """
    GOALS = GOALS

    def __init__(self, render: bool = True, num_agents: int = NUM_AGENTS) -> None:
        self.grid_w = GRID_W
        self.grid_h = GRID_H
        self.render_enabled = render
        self.num_agents = num_agents

        if render:
            self.screen = pygame.display.set_mode((self.grid_w*CELL_SIZE, self.grid_h*CELL_SIZE))
            pygame.display.set_caption("Warehouse MAS - Symmetry-Reduced Verification")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("consolas", 18)
        self.render_fps = RENDER_FPS

        self.reset()

    def get_random_free_position(self, occupied_positions: set) -> Tuple[int, int]:
        while True:
            x = random.randint(0, self.grid_w - 1)
            y = random.randint(0, self.grid_h - 1)
            if (x, y) not in occupied_positions:
                return x, y

    def reset(self) -> List:
        occupied = set(self.GOALS)

        self.robots: List[Robot] = []
        for i in range(self.num_agents):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            self.robots.append(Robot(i, x, y))

        self.shelves = []
        for i in range(NUM_SHELVES):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            requested = True
            self.shelves.append({
                'id': i,
                'x': x, 'y': y,
                'carried': False,
                'requested': requested
            })

        self.steps = 0
        self.last_collisions = 0
        self.last_delivered = 0
        self.last_conflicts = []
        return [self.get_state(r) for r in self.robots]

    def get_state(self, robot: Robot):
        norm = lambda v, maxv: v / max(maxv-1, 1)

        state = [
            norm(robot.x, self.grid_w),
            norm(robot.y, self.grid_h),
            robot.dir.value / 3.0,
            1.0 if robot.carrying else 0.0
        ]

        shelves_sorted = sorted(self.shelves, key=lambda s: s['id'])
        for i in range(NUM_SHELVES):
            if i < len(shelves_sorted):
                s = shelves_sorted[i]
                state.extend([
                    norm(s['x'], self.grid_w),
                    norm(s['y'], self.grid_h),
                    1.0 if s['carried'] else 0.0,
                    1.0 if s['requested'] else 0.0
                ])
            else:
                state.extend([0.0] * 4)

        others = [o for o in self.robots if o is not robot]
        for i in range(self.num_agents - 1):
            if i < len(others):
                o = others[i]
                state.extend([
                    norm(o.x, self.grid_w),
                    norm(o.y, self.grid_h),
                    o.dir.value / 3.0,
                    1.0 if o.carrying else 0.0
                ])
            else:
                state.extend([0.0] * 4)

        return state

    def get_dist_to_target(self, robot: Robot) -> Optional[float]:
        if robot.carrying:
            if robot.carrying['requested']:
                min_d = math.inf
                for gx, gy in self.GOALS:
                    d = abs(robot.x - gx) + abs(robot.y - gy)
                    min_d = min(min_d, d)
                return min_d
            else:
                return None
        else:
            requested = [s for s in self.shelves if s['requested'] and not s['carried']]
            if not requested:
                return None
            min_d = math.inf
            for s in requested:
                d = abs(robot.x - s['x']) + abs(robot.y - s['y'])
                min_d = min(min_d, d)
            return min_d

    def step(self, actions: List[int], record_trajectories: bool = False):
        rewards = []
        collisions = 0
        delivered = 0
        self.last_conflicts = []
        if record_trajectories:
            trajectories = [[(r.x, r.y)] for r in self.robots]
        else:
            trajectories = None

        # Precompute intended forward moves for conflict reporting (no behavior changes)
        intents = {}
        for robot, a_idx in zip(self.robots, actions):
            if a_idx == 0:  # FORWARD
                dx, dy = [0, 1, 0, -1], [-1, 0, 1, 0]
                nx = robot.x + dx[robot.dir.value]
                ny = robot.y + dy[robot.dir.value]
                if not (0 <= nx < self.grid_w and 0 <= ny < self.grid_h):
                    self.last_conflicts.append({
                        'type': 'boundary',
                        'agent': robot.id,
                        'from': (robot.x, robot.y),
                        'to': (nx, ny),
                    })
                else:
                    intents[robot.id] = ((robot.x, robot.y), (nx, ny))

        if intents:
            target_to_agents = {}
            for agent_id, (_, target) in intents.items():
                target_to_agents.setdefault(target, []).append(agent_id)
            for pos, agents in target_to_agents.items():
                if len(agents) > 1:
                    self.last_conflicts.append({
                        'type': 'vertex',
                        'agents': agents,
                        'pos': pos,
                    })
            for a_id, (a_from, a_to) in intents.items():
                for b_id, (b_from, b_to) in intents.items():
                    if a_id >= b_id:
                        continue
                    if a_from == b_to and a_to == b_from:
                        self.last_conflicts.append({
                            'type': 'edge',
                            'agents': [a_id, b_id],
                            'from': a_from,
                            'to': a_to,
                        })

        for robot, a_idx in zip(self.robots, actions):
            r = -0.01  # Slight time penalty to reduce dithering

            old_dist = self.get_dist_to_target(robot)

            action = a_idx
            add_r, msg = 0, ""
            bump = False
            if action == 0:  # FORWARD
                moved, bump = robot.forward(self)
                if bump:
                    r -= 0.2  # Reduced collision penalty (was -0.7)
                    collisions += 1
                elif moved:
                    # Reward successful movement towards target
                    r += 0.01
            elif action == 1:  # TURN_LEFT
                robot.turn_left()
                r -= 0.002
            elif action == 2:  # TURN_RIGHT
                robot.turn_right()
                r -= 0.002
            elif action == 3:  # PICK_DROP
                add_r, msg = robot.pick_or_drop(self)
                r += add_r
                if msg == "DELIVERED":
                    delivered += 1
            elif action == 4:  # WAIT
                r -= 0.003
            # WAIT

            new_dist = self.get_dist_to_target(robot)
            # Increased distance reward multiplier (was 0.05)
            if old_dist is not None and new_dist is not None:
                dist_improvement = old_dist - new_dist
                if dist_improvement > 0:
                    r += dist_improvement * 0.12  # Reward progress
                elif dist_improvement < 0:
                    r += dist_improvement * 0.04  # Smaller penalty for moving away

            # Reduced penalty for carrying non-requested item (was -0.1)
            if robot.carrying and robot.carrying is not None and not robot.carrying['requested']:
                r -= 0.05

            rewards.append(r)

        if delivered > 0:
            team_bonus = 2.0
            rewards = [r + team_bonus * delivered for r in rewards]

        self.steps += 1
        self.last_collisions = collisions
        self.last_delivered = delivered
        done = self.steps > 1000

        states = [self.get_state(r) for r in self.robots]

        if record_trajectories:
            for i, r in enumerate(self.robots):
                trajectories[i].append((r.x, r.y))

        return states, rewards, done, collisions, trajectories

    def render(self):
        if not self.render_enabled:
            return

        from config import GRAY, WHITE, GOAL_COLOR, GOLD, GREEN, TEAL, ORANGE, RED, BLACK, CELL_SIZE

        self.screen.fill(WHITE)

        # Grid
        for x in range(self.grid_w + 1):
            pygame.draw.line(self.screen, GRAY, (x*CELL_SIZE, 0), (x*CELL_SIZE, self.grid_h*CELL_SIZE), 1)
        for y in range(self.grid_h + 1):
            pygame.draw.line(self.screen, GRAY, (0, y*CELL_SIZE), (self.grid_w*CELL_SIZE, y*CELL_SIZE), 1)

        # Goals
        for gx, gy in self.GOALS:
            r = pygame.Rect(gx*CELL_SIZE + 4, gy*CELL_SIZE + 4, CELL_SIZE - 8, CELL_SIZE - 8)
            pygame.draw.rect(self.screen, GOAL_COLOR, r)
            txt = self.font.render("G", True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=r.center))

        # Shelves
        for s in self.shelves:
            if not s['carried']:
                color = GREEN if s['requested'] else TEAL
                r = pygame.Rect(s['x']*CELL_SIZE + 8, s['y']*CELL_SIZE + 8, CELL_SIZE - 16, CELL_SIZE - 16)
                pygame.draw.rect(self.screen, color, r)
                txt = self.font.render(str(s['id'] % 100), True, BLACK)
                self.screen.blit(txt, txt.get_rect(center=r.center))

        # Symmetry orbits (role-based)
        try:
            from symmetry_reduction import detect_role_orbits
            orbits = detect_role_orbits(self.robots)
        except Exception:
            orbits = [[i] for i in range(len(self.robots))]

        orbit_colors = [
            (80, 120, 200),
            (200, 120, 80),
            (120, 200, 120),
            (200, 80, 160),
            (160, 160, 80),
            (80, 180, 180),
        ]
        orbit_by_agent = {}
        for oi, orbit in enumerate(orbits):
            for idx in orbit:
                orbit_by_agent[idx] = oi

        # Robots
        for i, r in enumerate(self.robots):
            center_x = r.x * CELL_SIZE + CELL_SIZE // 2
            center_y = r.y * CELL_SIZE + CELL_SIZE // 2

            if r.carrying and r.carrying['requested']:
                pygame.draw.circle(self.screen, GOLD, (center_x, center_y), CELL_SIZE//2 - 4, 3)

            color = RED if r.carrying else ORANGE
            pygame.draw.circle(self.screen, color, (center_x, center_y), CELL_SIZE//3)

            # Orbit stroke for symmetric agents
            orbit_idx = orbit_by_agent.get(i, 0)
            stroke = orbit_colors[orbit_idx % len(orbit_colors)]
            pygame.draw.circle(self.screen, stroke, (center_x, center_y), CELL_SIZE//3 + 2, 2)

            dx, dy = [0, 0.4, 0, -0.4], [-0.4, 0, 0.4, 0]
            ex = center_x + dx[r.dir.value] * CELL_SIZE * 0.45
            ey = center_y + dy[r.dir.value] * CELL_SIZE * 0.45
            pygame.draw.line(self.screen, BLACK, (center_x, center_y), (ex, ey), 4)

            txt = self.font.render(str(i+1), True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=(center_x, center_y)))

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
    ):
        total_collisions = 0

        for ep in range(num_episodes):
            self.reset()
            done = False
            steps_in_episode = 0

            while not done and steps_in_episode < max_steps_per_episode:
                actions = planner.compute_actions(self)
                _, _, done, cols, _ = self.step(actions)
                total_collisions += cols
                steps_in_episode += 1
            if progress_every and (ep + 1) % progress_every == 0:
                msg = f"Eval progress: {ep + 1}/{num_episodes} episodes"
                if logger:
                    logger.info(msg)
                else:
                    print(msg)

        avg_collisions_per_agent_per_episode = (
            total_collisions / (num_episodes * self.num_agents)
            if num_episodes > 0 else 0
        )
        return avg_collisions_per_agent_per_episode
