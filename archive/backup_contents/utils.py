from pathlib import Path
import torch
from typing import Iterable, Optional

from config import MODEL_PATHS


def save_models(dqns: Iterable, save_dir: Optional[str] = None) -> None:
    """Save a list of DQN models. If save_dir is provided, models are saved inside it."""
    if save_dir:
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        for i, dqn in enumerate(dqns):
            torch.save(dqn.state_dict(), str(Path(save_dir) / MODEL_PATHS[i]))
    else:
        for i, dqn in enumerate(dqns):
            torch.save(dqn.state_dict(), MODEL_PATHS[i])
    print("Models saved!")
