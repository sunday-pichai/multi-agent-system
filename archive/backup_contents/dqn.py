import torch.nn as nn
from config import HIDDEN, ACTION_SIZE
from typing import Any

class DQN(nn.Module):
    """Simple fully-connected DQN network.

    Args:
        state_size: size of the input state vector (inferred by caller)
        action_size: number of discrete actions
    """
    def __init__(self, state_size: int, action_size: int = ACTION_SIZE) -> None:
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

    def forward(self, x: Any) -> Any:
        return self.net(x)
