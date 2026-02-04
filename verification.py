"""Verification utilities for symmetry-reduced deterministic MAS.

This module performs bounded safety verification on a quotient model by
canonicalizing symmetric agent configurations and checking for collisions
and minimum separation violations over a fixed horizon.
"""
from typing import Any, Dict, List, Tuple

from symmetry_reduction import canonicalize_state


def _min_pairwise_manhattan(robots) -> int:
    if len(robots) < 2:
        return 999
    min_d = 999
    for i in range(len(robots)):
        for j in range(i + 1, len(robots)):
            a = robots[i]
            b = robots[j]
            d = abs(a.x - b.x) + abs(a.y - b.y)
            if d < min_d:
                min_d = d
    return min_d


def verify_on_quotient(
    env,
    planner,
    horizon: int = 20,
    trials: int = 50,
    include_shelves: bool = False,
    min_separation: int = 1,
    progress_every: int = 0,
    logger=None,
) -> Dict[str, Any]:
    """Bounded verification on the symmetry-reduced quotient.

    Returns a dict with:
    - safe: bool
    - counterexample: list of agent positions per step (if unsafe)
    - actions: per-step action list (if unsafe)
    - delta_q: minimum safety margin on quotient
    """
    overall_min_margin = 999
    total_steps = 0
    total_collisions = 0

    for trial in range(trials):
        env.reset()
        visited = set()
        trace = [[(r.x, r.y) for r in env.robots]]
        actions_history: List[List[int]] = []

        min_d0 = _min_pairwise_manhattan(env.robots)
        if min_d0 < min_separation:
            return {
                'safe': False,
                'counterexample': trace,
                'actions': actions_history,
                'conflicts': [{'type': 'separation', 'time': 0, 'min_distance': min_d0}],
                'delta_q': min_d0 - min_separation,
            }

        for t in range(horizon):
            key = canonicalize_state(env, include_shelves=include_shelves)
            if key in visited:
                break
            visited.add(key)

            actions = planner.compute_actions(env)
            actions_history.append(actions)
            _, _, _, cols, _ = env.step(actions)
            total_steps += 1
            total_collisions += cols

            trace.append([(r.x, r.y) for r in env.robots])

            min_d = _min_pairwise_manhattan(env.robots)
            margin = min_d - min_separation
            if margin < overall_min_margin:
                overall_min_margin = margin

            if cols > 0 or env.last_conflicts:
                conflicts = []
                for c in env.last_conflicts:
                    entry = dict(c)
                    entry['time'] = t
                    conflicts.append(entry)
                return {
                    'safe': False,
                    'counterexample': trace,
                    'actions': actions_history,
                    'conflicts': conflicts,
                    'delta_q': overall_min_margin,
                    'avg_collision_rate': (total_collisions / total_steps) if total_steps else 0.0,
                }
            if min_d < min_separation:
                return {
                    'safe': False,
                    'counterexample': trace,
                    'actions': actions_history,
                    'conflicts': [{'type': 'separation', 'time': t, 'min_distance': min_d}],
                    'delta_q': overall_min_margin,
                    'avg_collision_rate': (total_collisions / total_steps) if total_steps else 0.0,
                }
        if progress_every and (trial + 1) % progress_every == 0:
            msg = f"Verify progress: {trial + 1}/{trials} trials"
            if logger:
                logger.info(msg)
            else:
                print(msg)

    return {
        'safe': True,
        'delta_q': overall_min_margin if overall_min_margin != 999 else 0,
        'avg_collision_rate': (total_collisions / total_steps) if total_steps else 0.0,
    }
