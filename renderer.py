"""Rendering module – draws the warehouse grid using Pygame."""

from typing import List, Set, Tuple

import pygame
import pygame.gfxdraw

import config as cfg

GridPos = Tuple[int, int]

_ORBIT_COLORS = [
    (100, 150, 220), (220, 150, 100), (150, 220, 150),
    (220, 100, 180), (200, 200, 120), (100, 200, 200),
]


class Renderer:
    """Draws the warehouse grid.  Holds only Pygame surface / font refs."""

    def __init__(self, grid_w: int, grid_h: int, cell_size: int) -> None:
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.cs = cell_size

        w_px = grid_w * cell_size
        h_px = grid_h * cell_size
        self.screen = pygame.display.set_mode((w_px, h_px))
        pygame.display.set_caption("Warehouse Simulation")
        self.clock = pygame.time.Clock()

        try:
            self.font_small = pygame.font.SysFont("arial", max(10, cell_size // 7), bold=True)
            self.font_tiny = pygame.font.SysFont("arial", max(8, cell_size // 10))
        except Exception:
            self.font_small = pygame.font.Font(None, max(10, cell_size // 7))
            self.font_tiny = pygame.font.Font(None, max(8, cell_size // 10))

    # ── public ────────────────────────────────────────────
    def draw(self, env, fps: int) -> None:
        self.screen.fill(cfg.BG_PURE)
        self._draw_grid()
        robot_positions = {(r.x, r.y) for r in env.robots}
        self._draw_goals(env.GOALS)
        self._draw_shelves(env.shelves, robot_positions)
        self._draw_robots(env.robots)
        self._draw_conflicts(env.last_conflicts)
        pygame.display.flip()
        self.clock.tick(fps if fps > 0 else 0)

    # ── grid ──────────────────────────────────────────────
    def _draw_grid(self) -> None:
        cs, w, h = self.cs, self.grid_w, self.grid_h
        for x in range(w + 1):
            pygame.draw.aaline(self.screen, cfg.GRID_SUBTLE, (x * cs, 0), (x * cs, h * cs))
        for y in range(h + 1):
            pygame.draw.aaline(self.screen, cfg.GRID_SUBTLE, (0, y * cs), (w * cs, y * cs))

    # ── goals ─────────────────────────────────────────────
    def _draw_goals(self, goals: List[GridPos]) -> None:
        cs, m = self.cs, 2
        sz = cs - m * 2
        for gx, gy in goals:
            px, py = gx * cs + m, gy * cs + m
            pygame.draw.rect(self.screen, cfg.GOAL_SHADOW, (px + 1, py + 1, sz, sz))
            rect = pygame.Rect(px, py, sz, sz)
            pygame.draw.rect(self.screen, cfg.GOAL_PRIMARY, rect)
            pygame.draw.rect(self.screen, cfg.GOAL_SHADOW, rect, 2)
            txt = self.font_small.render("GOAL", True, cfg.TEXT_ON_DARK)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ── shelves ───────────────────────────────────────────
    def _draw_shelves(self, shelves, robot_positions: Set[GridPos]) -> None:
        cs, m = self.cs, 3
        sz = cs - m * 2
        for s in shelves:
            if s["carried"] or (s["x"], s["y"]) in robot_positions:
                continue
            px, py = s["x"] * cs + m, s["y"] * cs + m
            if s["requested"]:
                color, shadow, tc = cfg.SHELF_ACTIVE, cfg.SHELF_SHADOW, cfg.TEXT_ON_DARK
                border = cfg.SHELF_SHADOW
            else:
                color, shadow, tc = cfg.SHELF_IDLE, (150, 150, 160), cfg.TEXT_PRIMARY
                border = (160, 160, 170)
            pygame.draw.rect(self.screen, shadow, (px + 1, py + 1, sz, sz))
            rect = pygame.Rect(px, py, sz, sz)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, border, rect, 2)
            txt = self.font_tiny.render(str(s["id"] % 100), True, tc)
            self.screen.blit(txt, txt.get_rect(center=rect.center))

    # ── robots ────────────────────────────────────────────
    def _draw_robots(self, robots) -> None:
        orbit_map = _orbit_map(robots)
        cs = self.cs
        for idx, robot in enumerate(robots):
            cx = robot.x * cs + cs // 2
            cy = robot.y * cs + cs // 2
            r = cs // 3 - 2

            if robot.carrying:
                body, shadow = cfg.ROBOT_CARRYING, (200, 100, 40)
            else:
                body, shadow = cfg.ROBOT_PRIMARY, cfg.ROBOT_SHADOW

            pygame.gfxdraw.filled_circle(self.screen, cx + 1, cy + 1, r, shadow)
            pygame.gfxdraw.filled_circle(self.screen, cx, cy, r, body)
            pygame.gfxdraw.aacircle(self.screen, cx, cy, r, shadow)

            if robot.carrying and robot.carrying.get("requested"):
                iy = cy - r - 6
                pygame.gfxdraw.filled_circle(self.screen, cx + 1, iy + 1, 5, (200, 150, 30))
                pygame.gfxdraw.filled_circle(self.screen, cx, iy, 5, cfg.ACCENT_GOLD)
                pygame.gfxdraw.aacircle(self.screen, cx, iy, 5, (220, 170, 40))

            self._draw_arrow(cx, cy, r, robot.dir.value)

            oc = _ORBIT_COLORS[orbit_map.get(idx, 0) % len(_ORBIT_COLORS)]
            pygame.draw.rect(self.screen, oc, (cx + r - 5, cy - r + 1, 4, 4))

    def _draw_arrow(self, cx: int, cy: int, radius: int, d: int) -> None:
        """Direction arrow with shaft + filled arrowhead."""
        length = radius - 1
        head = 5
        sw = 2
        color = cfg.TEXT_ON_DARK

        if d == 0:  # UP
            pygame.draw.rect(self.screen, color,
                             (cx - sw // 2, cy - length, sw, length - head))
            pts = [(cx, cy - length),
                   (cx - head, cy - length + head),
                   (cx + head, cy - length + head)]
        elif d == 1:  # RIGHT
            pygame.draw.rect(self.screen, color,
                             (cx, cy - sw // 2, length - head, sw))
            pts = [(cx + length, cy),
                   (cx + length - head, cy - head),
                   (cx + length - head, cy + head)]
        elif d == 2:  # DOWN
            pygame.draw.rect(self.screen, color,
                             (cx - sw // 2, cy, sw, length - head))
            pts = [(cx, cy + length),
                   (cx - head, cy + length - head),
                   (cx + head, cy + length - head)]
        else:  # LEFT
            pygame.draw.rect(self.screen, color,
                             (cx - length + head, cy - sw // 2, length - head, sw))
            pts = [(cx - length, cy),
                   (cx - length + head, cy - head),
                   (cx - length + head, cy + head)]

        coords = tuple(c for p in pts for c in p)
        pygame.gfxdraw.filled_trigon(self.screen, *coords, color)
        pygame.gfxdraw.aatrigon(self.screen, *coords, color)

    # ── conflicts overlay ─────────────────────────────────
    def _draw_conflicts(self, conflicts) -> None:
        cs = self.cs
        for c in conflicts:
            if c.get("type") == "vertex" and "pos" in c:
                px, py = c["pos"]
                overlay = pygame.Surface((cs, cs), pygame.SRCALPHA)
                overlay.fill((255, 60, 60, 70))
                self.screen.blit(overlay, (px * cs, py * cs))
            elif c.get("type") == "edge":
                f, t = c.get("from"), c.get("to")
                if f and t:
                    pygame.draw.line(
                        self.screen, (255, 80, 80),
                        (f[0] * cs + cs // 2, f[1] * cs + cs // 2),
                        (t[0] * cs + cs // 2, t[1] * cs + cs // 2), 3,
                    )


def _orbit_map(robots) -> dict:
    """Map robot index -> orbit index for coloring."""
    try:
        from symmetry_reduction import detect_role_orbits
        orbits = detect_role_orbits(robots)
    except Exception:
        orbits = [[i] for i in range(len(robots))]
    return {ai: oi for oi, orbit in enumerate(orbits) for ai in orbit}
