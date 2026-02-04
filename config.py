from typing import List, Tuple, Optional
from pathlib import Path
import logging

# Try to load overrides from config.yaml (optional dependency on PyYAML)
try:
    import yaml  # type: ignore
except Exception:
    yaml = None

logger = logging.getLogger('warehouse.config')

# Colors
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

# Default simulation configuration
GRID_W: int = 16
GRID_H: int = 16
CELL_SIZE: int = 30  # default cell size (px)
NUM_AGENTS: int = 6
NUM_SHELVES: int = 8
GOALS: List[Tuple[int, int]] = [(7, 14), (8, 14)]

# Planning defaults
STATE_SIZE: int = 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4
ACTION_SIZE: int = 5
PLAN_HORIZON: int = 40
USE_CBS: bool = True
CBS_MAX_NODES: int = 200
RENDER_FPS: int = 0
ASTAR_MAX_NODES: int = 6000
IDLE_LIMIT: int = 6

# Verification and refinement defaults
MIN_SEPARATION: int = 1
VERIFY_HORIZON: int = 30
VERIFY_TRIALS: int = 20
REFINE_ITERATIONS: int = 2
REFINE_MAX_CONSTRAINTS: int = 100


def load_from_yaml(path: Optional[str] = None) -> None:
    """Load configuration overrides from YAML file and mutate module-level constants.

    If PyYAML is not installed, this is a no-op (logs a warning).
    """
    global GRID_W, GRID_H, CELL_SIZE, NUM_AGENTS, NUM_SHELVES, GOALS
    global PLAN_HORIZON, USE_CBS, CBS_MAX_NODES, RENDER_FPS
    global ASTAR_MAX_NODES, IDLE_LIMIT
    global MIN_SEPARATION, VERIFY_HORIZON, VERIFY_TRIALS
    global REFINE_ITERATIONS, REFINE_MAX_CONSTRAINTS

    cfg_path = Path(path) if path else Path('config.yaml')
    if not cfg_path.exists():
        logger.debug("No config.yaml found at %s", cfg_path)
        return

    if yaml is None:
        logger.warning("PyYAML not installed: ignoring %s. Install pyyaml to enable YAML config.", cfg_path)
        return

    with cfg_path.open('r') as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        logger.warning("Invalid config.yaml structure; expected a mapping at top-level")
        return

    # Apply simple overrides
    grid = cfg.get('grid', {})
    if 'width' in grid:
        GRID_W = int(grid['width'])
    if 'height' in grid:
        GRID_H = int(grid['height'])
    if 'cell_size' in grid:
        CELL_SIZE = int(grid['cell_size'])

    agents = cfg.get('agents', {})
    if 'num_agents' in agents:
        NUM_AGENTS = int(agents['num_agents'])
    if 'num_shelves' in agents:
        NUM_SHELVES = int(agents['num_shelves'])
    if 'goals' in agents and isinstance(agents['goals'], list):
        GOALS = [tuple(g) for g in agents['goals']]

    planning = cfg.get('planning', {})
    if 'horizon' in planning:
        PLAN_HORIZON = int(planning['horizon'])
    if 'use_cbs' in planning:
        USE_CBS = bool(planning['use_cbs'])
    if 'cbs_max_nodes' in planning:
        CBS_MAX_NODES = int(planning['cbs_max_nodes'])
    if 'astar_max_nodes' in planning:
        ASTAR_MAX_NODES = int(planning['astar_max_nodes'])
    if 'idle_limit' in planning:
        IDLE_LIMIT = int(planning['idle_limit'])

    render = cfg.get('render', {})
    if 'fps' in render:
        RENDER_FPS = int(render['fps'])

    verification = cfg.get('verification', {})
    if 'min_separation' in verification:
        MIN_SEPARATION = int(verification['min_separation'])
    if 'horizon' in verification:
        VERIFY_HORIZON = int(verification['horizon'])
    if 'trials' in verification:
        VERIFY_TRIALS = int(verification['trials'])

    refinement = cfg.get('refinement', {})
    if 'iterations' in refinement:
        REFINE_ITERATIONS = int(refinement['iterations'])
    if 'max_constraints' in refinement:
        REFINE_MAX_CONSTRAINTS = int(refinement['max_constraints'])

    # Update dependent derived values
    globals()['STATE_SIZE'] = 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4

    logger.info("Loaded config overrides from %s", cfg_path)
