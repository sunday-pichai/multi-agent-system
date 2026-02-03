import random
from enum import Enum
from typing import Tuple, Any

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

class Robot:
    """Agent representing a robot in the warehouse grid."""
    def __init__(self, id: int, x: int, y: int) -> None:
        self.id = id
        self.x = x
        self.y = y
        self.dir = random.choice(list(Direction))
        self.carrying = None

    def turn_left(self) -> None:
        self.dir = Direction((self.dir.value - 1) % 4)

    def turn_right(self) -> None:
        self.dir = Direction((self.dir.value + 1) % 4)

    def forward(self, env: Any) -> Tuple[bool, bool]:
        """Try to move forward; return (moved, bump).

        bump True indicates boundary/agent collision and movement failed.
        """
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

    def pick_or_drop(self, env: Any) -> Tuple[float, str]:
        if self.carrying:
            if (self.x, self.y) in env.GOALS and self.carrying['requested']:
                env.shelves.remove(self.carrying)
                occupied = set((r.x, r.y) for r in env.robots) | set((s['x'], s['y']) for s in env.shelves) | set(env.GOALS)
                x, y = env.get_random_free_position(occupied)
                new_id = max([s['id'] for s in env.shelves] + [-1]) + 1
                new_shelf = {'id': new_id, 'x': x, 'y': y, 'carried': False, 'requested': True}
                env.shelves.append(new_shelf)
                self.carrying = None
                return 20.0, "DELIVERED"  # Delivery reward
            else:
                self.carrying['carried'] = False
                self.carrying = None
                return -0.1, "DROPPED"  # Small penalty for dropping
        else:
            for s in env.shelves:
                if s['x'] == self.x and s['y'] == self.y and not s['carried']:
                    s['carried'] = True
                    self.carrying = s
                    return 5.0 if s['requested'] else 0.0, "PICKED"  # Avoid rewarding non-requested pickup
        return -0.05, "NOOP"  # Small no-op penalty
