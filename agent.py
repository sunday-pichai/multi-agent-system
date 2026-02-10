import random
from enum import Enum
from typing import Any, Dict, Optional, Tuple


MOVE_X = [0, 1, 0, -1]   # UP, RIGHT, DOWN, LEFT
MOVE_Y = [-1, 0, 1, 0]   # UP, RIGHT, DOWN, LEFT


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
    """Single robot in the warehouse grid."""

    def __init__(self, robot_id: int, x: int, y: int) -> None:
        self.id = robot_id
        self.x = x
        self.y = y
        self.dir = random.choice(list(Direction))
        self.carrying: Optional[Dict[str, Any]] = None

    def turn_left(self) -> None:
        self.dir = Direction((self.dir.value - 1) % 4)

    def turn_right(self) -> None:
        self.dir = Direction((self.dir.value + 1) % 4)

    def forward(self, env: Any) -> Tuple[bool, bool]:
        """Try to move one cell forward.

        Returns:
        - moved: True when position changed
        - bump: True when blocked by wall or another robot
        """
        nx, ny = self._next_forward_cell()

        if not self._inside_bounds(nx, ny, env):
            return False, True

        if self._occupied_by_robot(nx, ny, env):
            return False, True

        self.x = nx
        self.y = ny
        if self.carrying is not None:
            self.carrying["x"] = nx
            self.carrying["y"] = ny
        return True, False

    def pick_or_drop(self, env: Any) -> Tuple[float, str]:
        """Pick shelf at current cell or drop/deliver carried shelf."""
        if self.carrying is None:
            return self._pick_shelf_here(env)

        carrying_requested = bool(self.carrying.get("requested"))
        at_goal = (self.x, self.y) in env.GOALS

        if carrying_requested and at_goal:
            return self._deliver_shelf(env)
        return self._drop_shelf()

    def _next_forward_cell(self) -> Tuple[int, int]:
        dx = MOVE_X[self.dir.value]
        dy = MOVE_Y[self.dir.value]
        return self.x + dx, self.y + dy

    @staticmethod
    def _inside_bounds(x: int, y: int, env: Any) -> bool:
        return 0 <= x < env.grid_w and 0 <= y < env.grid_h

    def _occupied_by_robot(self, x: int, y: int, env: Any) -> bool:
        for other in env.robots:
            if other is self:
                continue
            if other.x == x and other.y == y:
                return True
        return False

    def _pick_shelf_here(self, env: Any) -> Tuple[float, str]:
        for shelf in env.shelves:
            same_cell = shelf["x"] == self.x and shelf["y"] == self.y
            if not same_cell:
                continue
            if shelf["carried"]:
                continue

            shelf["carried"] = True
            self.carrying = shelf
            if shelf["requested"]:
                return 5.0, "PICKED"
            return 0.0, "PICKED"

        return -0.05, "NOOP"

    def _deliver_shelf(self, env: Any) -> Tuple[float, str]:
        if self.carrying is None:
            return -0.05, "NOOP"

        delivered_shelf = self.carrying
        env.shelves.remove(delivered_shelf)

        occupied = {(robot.x, robot.y) for robot in env.robots}
        occupied.update((shelf["x"], shelf["y"]) for shelf in env.shelves)
        occupied.update(env.GOALS)

        spawn_x, spawn_y = env.get_random_free_position(occupied)
        next_id = max([shelf["id"] for shelf in env.shelves] + [-1]) + 1
        new_shelf = {
            "id": next_id,
            "x": spawn_x,
            "y": spawn_y,
            "carried": False,
            "requested": True,
        }
        env.shelves.append(new_shelf)

        self.carrying = None
        return 20.0, "DELIVERED"

    def _drop_shelf(self) -> Tuple[float, str]:
        if self.carrying is None:
            return -0.05, "NOOP"

        self.carrying["carried"] = False
        self.carrying = None
        return -0.1, "DROPPED"
