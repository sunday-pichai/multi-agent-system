"""Bounded safety verification over symmetry-reduced quotient states."""

from typing import Any, Dict, List

from symmetry_reduction import canonicalize_state


NO_PAIR_DISTANCE = 999


def _min_pairwise_manhattan(robots) -> int:
    if len(robots) < 2:
        return NO_PAIR_DISTANCE

    min_distance = NO_PAIR_DISTANCE
    for idx_a in range(len(robots)):
        for idx_b in range(idx_a + 1, len(robots)):
            a = robots[idx_a]
            b = robots[idx_b]
            distance = abs(a.x - b.x) + abs(a.y - b.y)
            if distance < min_distance:
                min_distance = distance
    return min_distance


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
    """Run bounded verification trials and return safety/trace summary."""
    overall_min_margin = NO_PAIR_DISTANCE
    total_steps = 0
    total_collisions = 0

    for trial_idx in range(trials):
        env.reset()
        visited = set()
        trace = [[(robot.x, robot.y) for robot in env.robots]]
        action_history: List[List[int]] = []

        initial_distance = _min_pairwise_manhattan(env.robots)
        if initial_distance < min_separation:
            return {
                "safe": False,
                "counterexample": trace,
                "actions": action_history,
                "conflicts": [
                    {"type": "separation", "time": 0, "min_distance": initial_distance}
                ],
                "delta_q": initial_distance - min_separation,
            }

        for step_idx in range(horizon):
            state_key = canonicalize_state(env, include_shelves=include_shelves)
            if state_key in visited:
                break
            visited.add(state_key)

            actions = planner.compute_actions(env)
            action_history.append(actions)
            _, _, _, collisions, _ = env.step(actions)

            total_steps += 1
            total_collisions += collisions
            trace.append([(robot.x, robot.y) for robot in env.robots])

            min_distance = _min_pairwise_manhattan(env.robots)
            margin = min_distance - min_separation
            if margin < overall_min_margin:
                overall_min_margin = margin

            if collisions > 0 or env.last_conflicts:
                conflict_list = []
                for conflict in env.last_conflicts:
                    entry = dict(conflict)
                    entry["time"] = step_idx
                    conflict_list.append(entry)
                return {
                    "safe": False,
                    "counterexample": trace,
                    "actions": action_history,
                    "conflicts": conflict_list,
                    "delta_q": overall_min_margin,
                    "avg_collision_rate": (total_collisions / total_steps) if total_steps else 0.0,
                }

            if min_distance < min_separation:
                return {
                    "safe": False,
                    "counterexample": trace,
                    "actions": action_history,
                    "conflicts": [
                        {"type": "separation", "time": step_idx, "min_distance": min_distance}
                    ],
                    "delta_q": overall_min_margin,
                    "avg_collision_rate": (total_collisions / total_steps) if total_steps else 0.0,
                }

        if progress_every and (trial_idx + 1) % progress_every == 0:
            msg = f"Verify progress: {trial_idx + 1}/{trials} trials"
            if logger is not None:
                logger.info(msg)
            else:
                print(msg)

    if overall_min_margin == NO_PAIR_DISTANCE:
        overall_min_margin = 0

    return {
        "safe": True,
        "delta_q": overall_min_margin,
        "avg_collision_rate": (total_collisions / total_steps) if total_steps else 0.0,
    }
