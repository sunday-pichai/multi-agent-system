"""Verification-guided refinement for deterministic planners.

This module converts counterexample conflicts into planner constraints.
If conflicts are missing, it derives a coarse constraint from the
counterexample trace to force a change in behavior.
"""
from typing import Dict, List, Tuple, Optional

from pathfinding import CooperativePlanner


def refine_planner_with_conflicts(
    planner: CooperativePlanner,
    conflicts: List[Dict],
    trace: Optional[List[List[Tuple[int, int]]]] = None,
    max_constraints: int = 100,
) -> Dict[str, int]:
    applied = 0
    if conflicts:
        for conflict in conflicts:
            if applied >= max_constraints:
                break
            ctype = conflict.get('type')
            t = int(conflict.get('time', 0))

            if ctype == 'vertex':
                pos = conflict.get('pos')
                if pos:
                    planner.add_constraint_position(pos, t + 1)
                    applied += 1
            elif ctype == 'edge':
                from_pos = conflict.get('from')
                to_pos = conflict.get('to')
                if from_pos and to_pos:
                    planner.add_constraint_edge(from_pos, to_pos, t + 1)
                    planner.add_constraint_edge(to_pos, from_pos, t + 1)
                    applied += 2
            elif ctype == 'boundary':
                to_pos = conflict.get('to')
                if to_pos:
                    planner.add_constraint_position(to_pos, t + 1)
                    applied += 1
            elif ctype == 'separation':
                continue
    elif trace:
        # Fallback: derive a coarse constraint from the trace
        for t in range(1, len(trace)):
            positions = trace[t]
            seen = {}
            collision_pos = None
            for idx, pos in enumerate(positions):
                if pos in seen:
                    collision_pos = pos
                    break
                seen[pos] = idx
            if collision_pos:
                planner.add_constraint_position(collision_pos, t)
                applied += 1
                break
        if applied == 0 and len(trace) > 1:
            # No exact collision; block the closest pair's midpoint cell at that time
            t = 1
            positions = trace[t]
            best = None
            for i in range(len(positions)):
                for j in range(i + 1, len(positions)):
                    ax, ay = positions[i]
                    bx, by = positions[j]
                    d = abs(ax - bx) + abs(ay - by)
                    if best is None or d < best[0]:
                        best = (d, (ax, ay))
            if best:
                planner.add_constraint_position(best[1], t)
                applied += 1

    return {'applied_constraints': applied}
