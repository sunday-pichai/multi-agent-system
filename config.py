from pathlib import Path
import logging
from typing import List, Optional, Tuple


try:
    import yaml  # type: ignore
except Exception:
    yaml = None


logger = logging.getLogger("warehouse.config")


# Colors - Advanced Minimal UI Palette
WHITE = (255, 255, 255)
BLACK = (20, 20, 25)
GRAY = (230, 230, 235)  # Very light grid
DARK_BLUE = (40, 60, 120)
TEAL = (0, 140, 140)
ORANGE = (255, 160, 60)
RED = (220, 40, 40)
GOAL_COLOR = (50, 130, 200)  # Clean blue
GOLD = (255, 200, 50)
GREEN = (70, 200, 120)

# Advanced UI Colors
BG_PURE = (255, 255, 255)  # Pure white background
GRID_SUBTLE = (245, 245, 248)  # Ultra-subtle grid
ROBOT_PRIMARY = (60, 140, 255)  # Vibrant blue
ROBOT_CARRYING = (255, 140, 60)  # Warm orange
ROBOT_SHADOW = (40, 100, 200)  # Darker blue for depth
SHELF_IDLE = (180, 180, 190)  # Neutral gray
SHELF_ACTIVE = (70, 200, 120)  # Fresh green
SHELF_SHADOW = (50, 150, 90)  # Darker green
GOAL_PRIMARY = (50, 130, 200)  # Clean blue
GOAL_SHADOW = (30, 100, 160)  # Darker blue
TEXT_PRIMARY = (30, 30, 35)  # Dark text
TEXT_ON_DARK = (255, 255, 255)  # White text
ACCENT_GOLD = (255, 200, 50)  # Gold accent


# Environment defaults
GRID_W: int = 16
GRID_H: int = 16
CELL_SIZE: int = 80  # Larger cells for 1440p resolution (2560x1440 = 32x18 cells at 80px)
NUM_AGENTS: int = 6
NUM_SHELVES: int = 8
GOALS: List[Tuple[int, int]] = [(7, 14), (8, 14)]


# Planning defaults
ACTION_SIZE: int = 5
PLAN_HORIZON: int = 30
ASTAR_MAX_NODES: int = 3500
IDLE_LIMIT: int = 4
RENDER_FPS: int = 2
ASTAR_VISUALIZATION: bool = True


# Verification and refinement defaults
MIN_SEPARATION: int = 1
VERIFY_HORIZON: int = 30
VERIFY_TRIALS: int = 20
REFINE_ITERATIONS: int = 2
REFINE_MAX_CONSTRAINTS: int = 100


def state_size() -> int:
    """Return input state size for one robot policy/state vector."""
    return 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4


STATE_SIZE: int = state_size()


def load_from_yaml(path: Optional[str] = None) -> None:
    """Load optional overrides from YAML file into module-level settings."""
    global GRID_W, GRID_H, CELL_SIZE, NUM_AGENTS, NUM_SHELVES, GOALS
    global PLAN_HORIZON, ASTAR_MAX_NODES, IDLE_LIMIT, RENDER_FPS, ASTAR_VISUALIZATION
    global MIN_SEPARATION, VERIFY_HORIZON, VERIFY_TRIALS
    global REFINE_ITERATIONS, REFINE_MAX_CONSTRAINTS, STATE_SIZE

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

    grid = data.get("grid", {})
    if "width" in grid:
        GRID_W = int(grid["width"])
    if "height" in grid:
        GRID_H = int(grid["height"])
    if "cell_size" in grid:
        CELL_SIZE = int(grid["cell_size"])

    agents = data.get("agents", {})
    if "num_agents" in agents:
        NUM_AGENTS = int(agents["num_agents"])
    if "num_shelves" in agents:
        NUM_SHELVES = int(agents["num_shelves"])
    if "goals" in agents and isinstance(agents["goals"], list):
        GOALS = [tuple(goal) for goal in agents["goals"]]

    planning = data.get("planning", {})
    if "horizon" in planning:
        PLAN_HORIZON = int(planning["horizon"])
    if "astar_max_nodes" in planning:
        ASTAR_MAX_NODES = int(planning["astar_max_nodes"])
    if "idle_limit" in planning:
        IDLE_LIMIT = int(planning["idle_limit"])

    render = data.get("render", {})
    if "fps" in render:
        RENDER_FPS = int(render["fps"])
    if "astar_visualization" in render:
        ASTAR_VISUALIZATION = bool(render["astar_visualization"])

    verification = data.get("verification", {})
    if "min_separation" in verification:
        MIN_SEPARATION = int(verification["min_separation"])
    if "horizon" in verification:
        VERIFY_HORIZON = int(verification["horizon"])
    if "trials" in verification:
        VERIFY_TRIALS = int(verification["trials"])

    refinement = data.get("refinement", {})
    if "iterations" in refinement:
        REFINE_ITERATIONS = int(refinement["iterations"])
    if "max_constraints" in refinement:
        REFINE_MAX_CONSTRAINTS = int(refinement["max_constraints"])

    STATE_SIZE = state_size()
    logger.info("Loaded config overrides from %s", cfg_path)
