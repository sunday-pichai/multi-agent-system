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
GRID_W: int = 20
GRID_H: int = 20
CELL_SIZE: int = 30  # default cell size (px)
NUM_AGENTS: int = 8
NUM_SHELVES: int = 20
GOALS: List[Tuple[int, int]] = [(9, 18), (10, 18)]

# DQN Hyperparameters and training defaults
STATE_SIZE: int = 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4
ACTION_SIZE: int = 5
HIDDEN: int = 512
LR: float = 0.0005
GAMMA: float = 0.99
EPS_START: float = 1.0
EPS_END: float = 0.01
EPS_DECAY: float = 0.99995
BATCH_SIZE: int = 128
TARGET_UPDATE: int = 500
MEMORY_SIZE: int = 100000
WARMUP_STEPS: int = 5000
SAVE_INTERVAL: int = 20000

# Model paths (per-agent)
MODEL_PATHS = [f"dqn_agent_{i}.pth" for i in range(NUM_AGENTS)]


def load_from_yaml(path: Optional[str] = None) -> None:
    """Load configuration overrides from YAML file and mutate module-level constants.

    If PyYAML is not installed, this is a no-op (logs a warning).
    """
    global GRID_W, GRID_H, CELL_SIZE, NUM_AGENTS, NUM_SHELVES, GOALS
    global LR, GAMMA, BATCH_SIZE, TARGET_UPDATE, MEMORY_SIZE, WARMUP_STEPS, SAVE_INTERVAL

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

    training = cfg.get('training', {})
    if 'lr' in training:
        LR = float(training['lr'])
    if 'gamma' in training:
        GAMMA = float(training['gamma'])
    if 'batch_size' in training:
        BATCH_SIZE = int(training['batch_size'])
    if 'target_update' in training:
        TARGET_UPDATE = int(training['target_update'])
    if 'memory_size' in training:
        MEMORY_SIZE = int(training['memory_size'])
    if 'warmup_steps' in training:
        WARMUP_STEPS = int(training['warmup_steps'])
    if 'save_interval' in training:
        SAVE_INTERVAL = int(training['save_interval'])

    # Update dependent derived values
    globals()['STATE_SIZE'] = 4 + NUM_SHELVES * 4 + (NUM_AGENTS - 1) * 4
    globals()['MODEL_PATHS'] = [f"dqn_agent_{i}.pth" for i in range(NUM_AGENTS)]

    logger.info("Loaded config overrides from %s", cfg_path)

