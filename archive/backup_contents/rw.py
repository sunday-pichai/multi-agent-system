import pygame
import sys
import random
import math
from enum import Enum
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import deque
import numpy as np
import matplotlib.pyplot as plt
import os
import argparse
import logging
import time
from pathlib import Path

pygame.init()

# ─── COLORS ────────────────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
BLACK      = (0, 0, 0)
GRAY       = (140, 140, 140)
DARK_BLUE  = (40, 60, 120)
TEAL       = (0, 140, 140)
ORANGE     = (255, 160, 60)
RED        = (220, 40, 40)
GOAL_COLOR = (80, 80, 80)
GOLD       = (255, 215, 80)
GREEN      = (60, 220, 100)

# ─── CONFIG ────────────────────────────────────────────────────────────────
GRID_W, GRID_H = 20, 20  # Scaled up
CELL_SIZE = 30  # Slightly smaller cells to reduce window size
NUM_AGENTS = 8  # Scaled up
NUM_SHELVES = 20  # Scaled up
GOALS = [(9, 18), (10, 18)]  # Adjusted for larger grid

# DQN Hyperparameters (adjusted for scale)
STATE_SIZE = 4 + NUM_SHELVES*4 + (NUM_AGENTS-1)*4
ACTION_SIZE = 5
HIDDEN = 512  # Larger network for complexity
LR = 0.0005  # Slower learning for stability
GAMMA = 0.99
EPS_START = 1.0
EPS_END = 0.01
EPS_DECAY = 0.99995  # Slower decay for more exploration
BATCH_SIZE = 128
TARGET_UPDATE = 500  # Less frequent for larger MAS
MEMORY_SIZE = 100000  # Larger memory
WARMUP_STEPS = 5000
SAVE_INTERVAL = 20000
MODEL_PATHS = [f"dqn_agent_{i}.pth" for i in range(NUM_AGENTS)]

class Direction(Enum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

class Action(Enum):
    FORWARD = 0
    TURN_LEFT = 1
    TURN_RIGHT = 2
    PICK_DROP = 3
    WAIT = 4

# ─── NEURAL NETWORK ────────────────────────────────────────────────────────
class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_size, HIDDEN),
            nn.ReLU(),
            nn.Linear(HIDDEN, HIDDEN),
            nn.ReLU(),
            nn.Linear(HIDDEN, HIDDEN // 2),
            nn.ReLU(),
            nn.Linear(HIDDEN // 2, action_size)
        )
    
    def forward(self, x):
        return self.net(x)

# ─── AGENT ─────────────────────────────────────────────────────────────────
class Robot:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.dir = random.choice(list(Direction))
        self.carrying = None
    
    def turn_left(self):
        self.dir = Direction((self.dir.value - 1) % 4)
    
    def turn_right(self):
        self.dir = Direction((self.dir.value + 1) % 4)
    
    def forward(self, env):
        dx, dy = [0,1,0,-1], [-1,0,1,0]  # U R D L
        nx = self.x + dx[self.dir.value]
        ny = self.y + dy[self.dir.value]
        
        if not (0 <= nx < env.grid_w and 0 <= ny < env.grid_h):
            return False, True  # boundary bump
        
        # collision with other robots
        for other in env.robots:
            if other is not self and other.x == nx and other.y == ny:
                return False, True  # agent collision
        
        self.x, self.y = nx, ny
        
        if self.carrying:
            self.carrying['x'], self.carrying['y'] = nx, ny
            
        return True, False

    def pick_or_drop(self, env):
        if self.carrying:
            if (self.x, self.y) in GOALS and self.carrying['requested']:
                print(f"Agent {self.id + 1} DELIVERED shelf {self.carrying['id']}")
                env.shelves.remove(self.carrying)
                occupied = set((r.x, r.y) for r in env.robots) | set((s['x'], s['y']) for s in env.shelves) | set(GOALS)
                x, y = env.get_random_free_position(occupied)
                new_id = max([s['id'] for s in env.shelves] + [-1]) + 1
                new_shelf = {'id': new_id, 'x': x, 'y': y, 'carried': False, 'requested': True}
                env.shelves.append(new_shelf)
                self.carrying = None
                return 15.0, "DELIVERED"
            else:
                self.carrying['carried'] = False
                self.carrying = None
                return -0.5, "DROPPED"
        else:
            for s in env.shelves:
                if s['x'] == self.x and s['y'] == self.y and not s['carried']:
                    s['carried'] = True
                    self.carrying = s
                    return 3.0 if s['requested'] else -2.0, "PICKED"
        return -0.4, "NOOP"

# ─── ENVIRONMENT ───────────────────────────────────────────────────────────
class WarehouseEnv:
    def __init__(self, render=True, num_agents=NUM_AGENTS):
        self.grid_w = GRID_W
        self.grid_h = GRID_H
        self.render_enabled = render
        self.num_agents = num_agents
        
        if render:
            self.screen = pygame.display.set_mode((GRID_W*CELL_SIZE, GRID_H*CELL_SIZE))
            pygame.display.set_caption("Scalable Warehouse MAS - Symmetry & Verification Demo")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.SysFont("consolas", 18)  # Smaller font for larger grid
        
        self.reset()
    
    def get_random_free_position(self, occupied_positions):
        while True:
            x = random.randint(0, self.grid_w - 1)
            y = random.randint(0, self.grid_h - 1)
            if (x, y) not in occupied_positions:
                return x, y
    
    def reset(self):
        occupied = set(GOALS)
        
        self.robots = []
        for i in range(self.num_agents):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            self.robots.append(Robot(i, x, y))
        
        self.shelves = []
        for i in range(NUM_SHELVES):
            x, y = self.get_random_free_position(occupied)
            occupied.add((x, y))
            requested = random.random() < 0.4
            self.shelves.append({
                'id': i,
                'x': x, 'y': y,
                'carried': False,
                'requested': requested
            })
        
        self.steps = 0
        return [self.get_state(r) for r in self.robots]
    
    def get_state(self, robot):
        norm = lambda v, maxv: v / max(maxv-1, 1)
        
        state = [
            norm(robot.x, GRID_W),
            norm(robot.y, GRID_H),
            robot.dir.value / 3.0,
            1.0 if robot.carrying else 0.0
        ]
        
        shelves_sorted = sorted(self.shelves, key=lambda s: s['id'])
        for i in range(NUM_SHELVES):
            if i < len(shelves_sorted):
                s = shelves_sorted[i]
                state.extend([
                    norm(s['x'], GRID_W),
                    norm(s['y'], GRID_H),
                    1.0 if s['carried'] else 0.0,
                    1.0 if s['requested'] else 0.0
                ])
            else:
                state.extend([0.0] * 4)
        
        others = [o for o in self.robots if o is not robot]
        for i in range(NUM_AGENTS - 1):
            if i < len(others):
                o = others[i]
                state.extend([
                    norm(o.x, GRID_W),
                    norm(o.y, GRID_H),
                    o.dir.value / 3.0,
                    1.0 if o.carrying else 0.0
                ])
            else:
                state.extend([0.0] * 4)
        
        return np.array(state, dtype=np.float32)
    
    def get_dist_to_target(self, robot):
        if robot.carrying:
            if robot.carrying['requested']:
                min_d = math.inf
                for gx, gy in GOALS:
                    d = abs(robot.x - gx) + abs(robot.y - gy)
                    min_d = min(min_d, d)
                return min_d
            else:
                return 0
        else:
            requested = [s for s in self.shelves if s['requested'] and not s['carried']]
            if not requested:
                return 0
            min_d = math.inf
            for s in requested:
                d = abs(robot.x - s['x']) + abs(robot.y - s['y'])
                min_d = min(min_d, d)
            return min_d
    
    def step(self, actions, record_trajectories=False):
        rewards = []
        collisions = 0
        if record_trajectories:
            trajectories = [[(r.x, r.y)] for r in self.robots]
        else:
            trajectories = None
        
        for robot, a_idx in zip(self.robots, actions):
            r = -0.02
            
            old_dist = self.get_dist_to_target(robot)
            
            action = Action(a_idx)
            add_r, msg = 0, ""
            bump = False
            if action == Action.FORWARD:
                moved, bump = robot.forward(self)
                if bump:
                    r -= 0.7
                    collisions += 1
            elif action == Action.TURN_LEFT:
                robot.turn_left()
            elif action == Action.TURN_RIGHT:
                robot.turn_right()
            elif action == Action.PICK_DROP:
                add_r, msg = robot.pick_or_drop(self)
                r += add_r
            # WAIT
            
            new_dist = self.get_dist_to_target(robot)
            r += (old_dist - new_dist) * 0.05
            
            if robot.carrying and robot.carrying is not None and not robot.carrying['requested']:
                r -= 0.1
            
            rewards.append(r)
        
        self.steps += 1
        done = self.steps > 1000  # Longer episodes for larger grid
        
        states = [self.get_state(r) for r in self.robots]
        
        if record_trajectories:
            for i, r in enumerate(self.robots):
                trajectories[i].append((r.x, r.y))
        
        return states, rewards, done, collisions, trajectories
    
    def render(self):
        if not self.render_enabled:
            return
            
        self.screen.fill(WHITE)
        
        # Grid
        for x in range(self.grid_w + 1):
            pygame.draw.line(self.screen, GRAY, (x*CELL_SIZE, 0), (x*CELL_SIZE, self.grid_h*CELL_SIZE), 1)
        for y in range(self.grid_h + 1):
            pygame.draw.line(self.screen, GRAY, (0, y*CELL_SIZE), (self.grid_w*CELL_SIZE, y*CELL_SIZE), 1)
        
        # Goals
        for gx, gy in GOALS:
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
                txt = self.font.render(str(s['id'] % 100), True, BLACK)  # Short ID for many shelves
                self.screen.blit(txt, txt.get_rect(center=r.center))
        
        # Robots
        for i, r in enumerate(self.robots):
            center_x = r.x * CELL_SIZE + CELL_SIZE // 2
            center_y = r.y * CELL_SIZE + CELL_SIZE // 2
            
            if r.carrying and r.carrying['requested']:
                pygame.draw.circle(self.screen, GOLD, (center_x, center_y), CELL_SIZE//2 - 4, 3)
            
            color = RED if r.carrying else ORANGE
            pygame.draw.circle(self.screen, color, (center_x, center_y), CELL_SIZE//3)
            
            dx, dy = [0, 0.4, 0, -0.4], [-0.4, 0, 0.4, 0]
            ex = center_x + dx[r.dir.value] * CELL_SIZE * 0.45
            ey = center_y + dy[r.dir.value] * CELL_SIZE * 0.45
            pygame.draw.line(self.screen, BLACK, (center_x, center_y), (ex, ey), 4)
            
            txt = self.font.render(str(i+1), True, WHITE)
            self.screen.blit(txt, txt.get_rect(center=(center_x, center_y)))
        
        pygame.display.flip()
        self.clock.tick(20)  # Faster tick for larger scale

    def evaluate(self, dqns, device, num_episodes=50, plot=False):
        total_collisions = 0
        total_steps = 0
        all_trajectories = []
        
        for ep in range(num_episodes):
            states = self.reset()
            done = False
            episode_collisions = 0
            trajectories = [[(r.x, r.y)] for r in self.robots]
            
            while not done:
                actions = []
                for i, state in enumerate(states):
                    with torch.no_grad():
                        q = dqns[i % len(dqns)] if len(dqns) < self.num_agents else dqns[i]  # Share if fewer models
                        a = q(torch.from_numpy(state).unsqueeze(0).to(device)).argmax().item()
                    actions.append(a)
                
                states, _, done, cols, _ = self.step(actions)
                episode_collisions += cols
                total_steps += 1
                for i, r in enumerate(self.robots):
                    trajectories[i].append((r.x, r.y))
            
            total_collisions += episode_collisions
            all_trajectories.append(trajectories)
        
        collision_rate = (total_collisions / total_steps) * 100 if total_steps > 0 else 0
        
        if plot:
            self.plot_trajectories(all_trajectories[0], "Baseline Trajectories") 
        
        return collision_rate

    def plot_trajectories(self, trajectories, title="Trajectories"):
        colors = plt.cm.rainbow(np.linspace(0, 1, len(trajectories)))
        fig, ax = plt.subplots(figsize=(8, 8))
        for i, traj in enumerate(trajectories):
            x, y = zip(*traj)
            ax.plot(x, y, marker='o', markersize=3, linewidth=1, color=colors[i], label=f'Agent {i+1}')
        ax.set_xlim(0, self.grid_w)
        ax.set_ylim(0, self.grid_h)
        ax.set_title(title)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()

def save_models(dqns, save_dir=None):
    """Save DQN state dicts. If save_dir is provided, models will be saved into that directory."""
    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        for i, dqn in enumerate(dqns):
            torch.save(dqn.state_dict(), str(Path(save_dir) / MODEL_PATHS[i]))
    else:
        for i, dqn in enumerate(dqns):
            torch.save(dqn.state_dict(), MODEL_PATHS[i])
    print("Models saved!")

"""Compatibility wrapper: keep `rw.py` entrypoint but delegate to `main.py`.

This preserves previous CLI usage like `python rw.py --mode train`.
"""
from main import main

if __name__ == '__main__':
    main()
