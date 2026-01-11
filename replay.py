"""Experience replay utilities: simple FIFO ReplayBuffer and a lightweight PrioritizedReplayBuffer.

This implementation is intentionally small and dependency-free for unit testing and refinement.
"""
from typing import List, Tuple, Any
import random
import math


class ReplayBuffer:
    def __init__(self, capacity: int = 10000):
        self.capacity = capacity
        self.buffer: List[Any] = []
        self.pos = 0

    def push(self, transition: Any):
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
        else:
            self.buffer[self.pos] = transition
            self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int):
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)


class PrioritizedReplayBuffer:
    def __init__(self, capacity: int = 10000, alpha: float = 0.6, eps: float = 1e-6):
        self.capacity = capacity
        self.buffer: List[Any] = []
        self.priorities: List[float] = []
        self.alpha = alpha
        self.eps = eps
        self.pos = 0

    def _get_probabilities(self):
        scaled = [p ** self.alpha for p in self.priorities]
        s = sum(scaled)
        if s <= 0:
            return [1 / len(self.priorities)] * len(self.priorities)
        return [x / s for x in scaled]

    def push(self, transition: Any, priority: float = None):
        if priority is None:
            priority = max(self.priorities) if self.priorities else 1.0
        if len(self.buffer) < self.capacity:
            self.buffer.append(transition)
            self.priorities.append(priority + self.eps)
        else:
            self.buffer[self.pos] = transition
            self.priorities[self.pos] = priority + self.eps
            self.pos = (self.pos + 1) % self.capacity

    def sample(self, batch_size: int, return_indices: bool = False):
        """Sample items, optionally returning their indices for priority updates.

        Returns a list of items or (indices_list, items_list) if return_indices=True.
        """
        if not self.buffer:
            return ([] if not return_indices else ([], []))
        probs = self._get_probabilities()
        # draw indices without replacement
        batch_indices = set()
        while len(batch_indices) < min(batch_size, len(self.buffer)):
            r = random.random()
            acc = 0.0
            for i, p in enumerate(probs):
                acc += p
                if r <= acc:
                    batch_indices.add(i)
                    break
        indices = list(batch_indices)
        items = [self.buffer[i] for i in indices]
        return (indices, items) if return_indices else items

    def update_priorities(self, indices: List[int], priorities: List[float]):
        for i, p in zip(indices, priorities):
            self.priorities[i] = p + self.eps

    def __len__(self):
        return len(self.buffer)