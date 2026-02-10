"""Convert unsafe traces/conflicts into planner constraints."""

from typing import Dict, List, Optional, Tuple

from pathfinding import CooperativePlanner


def refine_planner_with_conflicts(
    planner: CooperativePlanner,
    conflicts: List[Dict],
    trace: Optional[List[List[Tuple[int, int]]]] = None,
    max_constraints: int = 100,
) -> Dict[str, int]:
    """Add constraints to planner and return how many were applied."""
    applied_constraints = 0

    if conflicts:
        for conflict in conflicts:
            if applied_constraints >= max_constraints:
                break

            conflict_type = conflict.get("type")
            time_step = int(conflict.get("time", 0)) + 1

            if conflict_type == "vertex":
                pos = conflict.get("pos")
                if pos is not None:
                    planner.add_constraint_position(pos, time_step)
                    applied_constraints += 1
                continue

            if conflict_type == "edge":
                from_pos = conflict.get("from")
                to_pos = conflict.get("to")
                if from_pos is not None and to_pos is not None:
                    planner.add_constraint_edge(from_pos, to_pos, time_step)
                    planner.add_constraint_edge(to_pos, from_pos, time_step)
                    applied_constraints += 2
                continue

            if conflict_type == "boundary":
                to_pos = conflict.get("to")
                if to_pos is not None:
                    planner.add_constraint_position(to_pos, time_step)
                    applied_constraints += 1
                continue

            # "separation" and unknown types are intentionally ignored.
            continue

    elif trace:
        applied_constraints += _add_fallback_trace_constraint(planner, trace)

    return {"applied_constraints": applied_constraints}


def _add_fallback_trace_constraint(
    planner: CooperativePlanner, trace: List[List[Tuple[int, int]]]
) -> int:
    """Fallback when explicit conflicts are unavailable."""
    # First pass: find exact same-cell collision.
    for time_step in range(1, len(trace)):
        positions = trace[time_step]
        seen = set()
        for pos in positions:
            if pos in seen:
                planner.add_constraint_position(pos, time_step)
                return 1
            seen.add(pos)

    # Second pass: if no exact collision exists, add one coarse constraint
    # for the closest pair at t=1.
    if len(trace) <= 1:
        return 0

    positions = trace[1]
    if len(positions) < 2:
        return 0

    best_distance = None
    best_position = None
    for idx_a in range(len(positions)):
        ax, ay = positions[idx_a]
        for idx_b in range(idx_a + 1, len(positions)):
            bx, by = positions[idx_b]
            distance = abs(ax - bx) + abs(ay - by)
            if best_distance is None or distance < best_distance:
                best_distance = distance
                best_position = (ax, ay)

    if best_position is None:
        return 0

    planner.add_constraint_position(best_position, 1)
    return 1
