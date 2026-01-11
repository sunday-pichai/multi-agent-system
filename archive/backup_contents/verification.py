"""Skeleton verification utilities.

Provide lightweight bounded reachability checks / over-approx verification of safety properties (collision).
Initially includes a brute-force bounded search on the quotient model, later to be replaced with tighter abstractions.
"""
from typing import Any, Dict, List


def verify_collision_free(env, policy_models: List[Any]=None, horizon: int = 20, trials: int = 200) -> Dict[str, Any]:
    """Check safety up to `horizon` steps; return dict with 'safe': bool and optional 'counterexample'.

    If `policy_models` is provided (list of PyTorch models), actions will be chosen from the models; otherwise random actions are used.
    """
    import random
    import torch
    import numpy as np

    def sample_action(i, state):
        if policy_models:
            # use shared model if fewer models than agents
            q = policy_models[i % len(policy_models)]
            with torch.no_grad():
                a = int(q(torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0)).argmax().item())
            return a
        else:
            return random.randrange(5)

    for t in range(trials):  # random trials
        states = env.reset()
        trace = [[(r.x, r.y) for r in env.robots]]
        for h in range(horizon):
            actions = []
            for i, s in enumerate(states):
                a = sample_action(i, s)
                actions.append(a)
            states, _, _, cols, _ = env.step(actions)
            trace.append([(r.x, r.y) for r in env.robots])
            if cols > 0:
                return {'safe': False, 'counterexample': trace}
    return {'safe': True}


def verify_collision_by_actions(env, actions_sequence: List[List[int]]):
    """Given a deterministic sequence of actions (list of per-step action lists), simulate env and return collision trace if any."""
    trace = [ [(r.x, r.y) for r in env.robots] ]
    for actions in actions_sequence:
        states, _, _, cols, _ = env.step(actions)
        trace.append([(r.x, r.y) for r in env.robots])
        if cols > 0:
            return {'safe': False, 'counterexample': trace}
    return {'safe': True}


def verify_on_quotient(env, policy_models: List[Any]=None, horizon: int = 20, trials: int = 200):
    """Run verification on a quotient where agents in the same orbit execute the same actions.

    - Detect permutation symmetries (orbits) using `symmetry_reduction.detect_permutation_symmetries`.
    - For each trial, sample representative actions (either from `policy_models` or random) and apply them to all agents in the corresponding orbit.
    - Return counterexample trace if any collision is found in the full environment.

    This provides a conservative check for symmetry-exploiting counterexamples.
    """
    from symmetry_reduction import detect_permutation_symmetries
    import random
    import torch
    import numpy as np

    agents_pos = [(r.x, r.y) for r in env.robots]
    shelves_pos = [(s['x'], s['y']) for s in env.shelves]
    orbits = detect_permutation_symmetries(agents_pos, shelves_pos, grid_size=(env.grid_w, env.grid_h))

    reps = [o['orbit'][0] for o in orbits]

    def sample_action_for_rep(i, state):
        if policy_models:
            q = policy_models[i % len(policy_models)]
            with torch.no_grad():
                a = int(q(torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0)).argmax().item())
            return a
        else:
            return random.randrange(5)

    for t in range(trials):
        env.reset()
        trace = [ [(r.x, r.y) for r in env.robots] ]
        actions_history = []
        for h in range(horizon):
            rep_actions = {}
            # sample actions for representatives
            for ri, rep_idx in enumerate(reps):
                # use state of the representative
                state = env.get_state(env.robots[rep_idx])
                rep_actions[rep_idx] = sample_action_for_rep(ri, state)

            # build full action list by copying rep actions to their orbit members
            actions = []
            for agent_idx in range(len(env.robots)):
                # find which orbit this agent belongs to
                orbit_id = next((oi for oi, o in enumerate(orbits) if agent_idx in o['orbit']), None)
                if orbit_id is None:
                    actions.append(random.randrange(5))
                else:
                    rep_idx = orbits[orbit_id]['orbit'][0]
                    actions.append(rep_actions[rep_idx])

            actions_history.append(actions)
            states, _, _, cols, _ = env.step(actions)
            trace.append([(r.x, r.y) for r in env.robots])
            if cols > 0:
                return {'safe': False, 'counterexample': trace, 'actions': actions_history, 'orbits': orbits}
    return {'safe': True, 'orbits': orbits}
