from pathlib import Path
import logging
from typing import List, Optional, Tuple


try:
    import yaml  # type: ignore
except Exception:
    yaml = None


logger = logging.getLogger("warehouse.config")


# ── UI Colors ──────────────────────────────────────────────
BG_PURE = (255, 255, 255)
GRID_SUBTLE = (245, 245, 248)
ROBOT_PRIMARY = (60, 140, 255)
ROBOT_CARRYING = (255, 140, 60)
ROBOT_SHADOW = (40, 100, 200)
SHELF_IDLE = (180, 180, 190)
SHELF_ACTIVE = (70, 200, 120)
SHELF_SHADOW = (50, 150, 90)
GOAL_PRIMARY = (50, 130, 200)
GOAL_SHADOW = (30, 100, 160)
TEXT_PRIMARY = (30, 30, 35)
TEXT_ON_DARK = (255, 255, 255)
ACCENT_GOLD = (255, 200, 50)

# ── Environment ───────────────────────────────────────────
GRID_W: int = 16
GRID_H: int = 16
CELL_SIZE: int = 80
NUM_AGENTS: int = 6
NUM_SHELVES: int = 8
GOALS: List[Tuple[int, int]] = [(7, 14), (8, 14)]

# ── Planning ──────────────────────────────────────────────
ACTION_SIZE: int = 5
PLAN_HORIZON: int = 30
ASTAR_MAX_NODES: int = 3500
IDLE_LIMIT: int = 4
RESERVATION_WINDOW: int = 8
UNPLANNED_HOLD_STEPS: int = 2
ESCAPE_IDLE_STEPS: int = 6
RENDER_FPS: int = 2

# ── Verification / refinement ────────────────────────────
MIN_SEPARATION: int = 1
VERIFY_HORIZON: int = 30
VERIFY_TRIALS: int = 20
REFINE_ITERATIONS: int = 2
REFINE_MAX_CONSTRAINTS: int = 100


def state_size() -> int:
    """Return input state size for one robot policy/state vector."""
    return 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4


STATE_SIZE: int = state_size()

# ── YAML mapping: (section, yaml_key) → module global name ─
_YAML_INT_FIELDS = {
    ("grid", "width"): "GRID_W",
    ("grid", "height"): "GRID_H",
    ("grid", "cell_size"): "CELL_SIZE",
    ("agents", "num_agents"): "NUM_AGENTS",
    ("agents", "num_shelves"): "NUM_SHELVES",
    ("planning", "horizon"): "PLAN_HORIZON",
    ("planning", "astar_max_nodes"): "ASTAR_MAX_NODES",
    ("planning", "idle_limit"): "IDLE_LIMIT",
    ("planning", "reservation_window"): "RESERVATION_WINDOW",
    ("planning", "unplanned_hold_steps"): "UNPLANNED_HOLD_STEPS",
    ("planning", "escape_idle_steps"): "ESCAPE_IDLE_STEPS",
    ("render", "fps"): "RENDER_FPS",
    ("verification", "min_separation"): "MIN_SEPARATION",
    ("verification", "horizon"): "VERIFY_HORIZON",
    ("verification", "trials"): "VERIFY_TRIALS",
    ("refinement", "iterations"): "REFINE_ITERATIONS",
    ("refinement", "max_constraints"): "REFINE_MAX_CONSTRAINTS",
}


def load_from_yaml(path: Optional[str] = None) -> None:
    """Load optional overrides from YAML file into module-level settings."""
    import sys

    cfg_path = Path(path) if path else Path("config.yaml")
    if not cfg_path.exists():
        logger.debug("No config file found at %s", cfg_path)
        return
    if yaml is None:
        logger.warning("PyYAML is not installed, ignoring %s", cfg_path)
        return

    with cfg_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        logger.warning("Invalid config structure in %s (expected mapping)", cfg_path)
        return

    module = sys.modules[__name__]
    for (section, key), global_name in _YAML_INT_FIELDS.items():
        value = data.get(section, {}).get(key)
        if value is not None:
            setattr(module, global_name, int(value))

    goals = data.get("agents", {}).get("goals")
    if isinstance(goals, list):
        module.GOALS = [tuple(g) for g in goals]

    module.STATE_SIZE = state_size()
    logger.info("Loaded config overrides from %s", cfg_path)
