"""Skeleton for verification-guided refinement.

High-level API:
- given counterexample traces, create replay cases or shaped rewards that encourage avoidance
- provide functions to fine-tune existing DQN models on the failure cases
"""
from typing import Any, List, Dict
import random
import copy

import torch
import torch.nn.functional as F


def _clone_env(env):
    """Create a shallow clone of the environment to replay actions without mutating the original."""
    from env import WarehouseEnv
    from agent import Robot

    new = WarehouseEnv(render=False, num_agents=env.num_agents)
    # overwrite random initialization with copies
    new.robots = []
    for r in env.robots:
        nr = Robot(r.id, r.x, r.y)
        nr.dir = r.dir
        nr.carrying = copy.deepcopy(r.carrying)
        new.robots.append(nr)
    new.shelves = [dict(s) for s in env.shelves]
    new.steps = env.steps
    return new


def extract_failure_cases(env, actions_sequence: List[List[int]]) -> List[Dict]:
    """Convert an actions sequence that led to a collision into (agent, state, action, reward, next_state, done) cases.

    The function clones the env and replays `actions_sequence` to produce training cases suitable for targeted fine-tuning.
    """
    clone = _clone_env(env)
    cases: List[Dict] = []

    for actions in actions_sequence:
        states = [clone.get_state(r) for r in clone.robots]
        next_states, rewards, done, cols, _ = clone.step(actions)
        for i, a in enumerate(actions):
            cases.append({
                'agent': i,
                'state': states[i],
                'action': a,
                'reward': rewards[i],
                'next_state': next_states[i],
                'done': done
            })
        if cols > 0:
            break

    return cases


def fine_tune_on_cases(dqns: List[Any], cases: List[Dict], steps: int = 200, batch_size: int = 16, lr: float = 1e-3, gamma: float = 0.99, device: str = 'cpu', replay=None):
    """Fine-tune DQN models using the provided cases.

    - `dqns`: list of PyTorch models (shared or one-per-agent)
    - `cases`: list of dicts produced by `extract_failure_cases` (optional if `replay` provided)
    - `replay`: optional ReplayBuffer/PrioritizedReplayBuffer to sample from
    - returns a dict summary with final loss
    """
    if not cases and replay is None:
        return {'loss': 0.0, 'steps': 0}

    # if replay buffer provided, draw a portion to form working cases
    working_cases = list(cases) if cases else []
    if replay is not None:
        working_cases.extend(replay.sample(min(batch_size * 4, len(replay))))

    if not working_cases:
        return {'loss': 0.0, 'steps': 0}

    params = []
    for m in dqns:
        params += list(m.parameters())
    optimizer = torch.optim.Adam(params, lr=lr)

    losses = []
    for step in range(steps):
        # sample from replay if provided (prefer prioritized indices)
        if replay is not None and hasattr(replay, 'sample'):
            if hasattr(replay, 'sample'):
                # prioritized buffer returns (indices, items)
                try:
                    sample_indices, batch = replay.sample(batch_size, return_indices=True)
                except TypeError:
                    batch = replay.sample(batch_size)
                    sample_indices = None
        else:
            batch = random.sample(working_cases, min(batch_size, len(working_cases)))
            sample_indices = None

        total_loss = 0.0
        td_errors = []
        for bi, c in enumerate(batch):
            # if the stored item is a raw transition tuple, normalize to dict
            if isinstance(c, tuple) or isinstance(c, list):
                # expected: (agent, state, action, reward, next_state, done)
                agent_idx, s_raw, a, r, ns_raw, done = c
                cdict = {'agent': agent_idx, 'state': s_raw, 'action': a, 'reward': r, 'next_state': ns_raw, 'done': done}
            else:
                cdict = c

            agent_idx = cdict['agent']
            model = dqns[agent_idx % len(dqns)]
            s = torch.from_numpy(__import__('numpy').array(cdict['state'], dtype=__import__('numpy').float32)).to(device)
            ns = torch.from_numpy(__import__('numpy').array(cdict['next_state'], dtype=__import__('numpy').float32)).to(device)
            a = int(cdict['action'])
            r = float(cdict['reward'])
            done = bool(cdict['done'])

            q_vals = model(s.unsqueeze(0))  # shape [1, A]
            with torch.no_grad():
                next_q = model(ns.unsqueeze(0))
                max_next = next_q.max().item()

            target = torch.tensor(r + (0.0 if done else gamma * max_next), dtype=q_vals.dtype, device=q_vals.device)
            pred = q_vals[0, a]
            loss = F.huber_loss(pred, target)
            total_loss = total_loss + loss

            # TD error for priority
            td_err = abs((pred - target).item())
            td_errors.append(td_err)

        optimizer.zero_grad()
        total_loss.backward()
        optimizer.step()
        losses.append(total_loss.item())

        # update replay priorities if indices available
        if replay is not None and sample_indices:
            # map indices -> td_errors
            priorities = [e + 1e-6 for e in td_errors]
            replay.update_priorities(sample_indices, priorities)

    return {'loss': float(losses[-1]) if losses else 0.0, 'steps': steps}
