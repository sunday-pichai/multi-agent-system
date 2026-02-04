"""Symmetry reduction utilities for deterministic MAS verification.

This module provides a lightweight quotient construction by exploiting
agent-role symmetry (e.g., identical robots carrying the same type of load).
It canonically orders agents inside each orbit to reduce permutation
equivalence classes.
"""
from typing import Dict, Iterable, List, Tuple


AgentKey = Tuple[int, int, int, int]
OrbitKey = Tuple[AgentKey, ...]
StateKey = Tuple[OrbitKey, ...]


def _agent_role(robot) -> Tuple[int, int]:
    """Return a compact role signature for an agent."""
    if robot.carrying is None:
        return 0, 0
    return 1, 1 if robot.carrying.get('requested') else 0


def detect_role_orbits(robots: Iterable) -> List[List[int]]:
    """Group agents into orbits based on role symmetry."""
    role_to_indices: Dict[Tuple[int, int], List[int]] = {}
    for idx, robot in enumerate(robots):
        role = _agent_role(robot)
        role_to_indices.setdefault(role, []).append(idx)
    return list(role_to_indices.values())


def canonicalize_agents(robots: Iterable, orbits: List[List[int]]) -> StateKey:
    """Return a canonicalized agent state representation for quotienting."""
    robot_list = list(robots)
    orbit_keys: List[OrbitKey] = []
    for orbit in orbits:
        members: List[AgentKey] = []
        for idx in orbit:
            r = robot_list[idx]
            role = _agent_role(r)
            members.append((r.x, r.y, r.dir.value, role[1]))
        orbit_keys.append(tuple(sorted(members)))
    return tuple(orbit_keys)


def canonicalize_state(env, include_shelves: bool = False) -> Tuple[StateKey, Tuple[Tuple[int, int, int], ...]]:
    """Project full env state into a symmetry-reduced canonical key."""
    orbits = detect_role_orbits(env.robots)
    agent_key = canonicalize_agents(env.robots, orbits)

    if not include_shelves:
        return agent_key, ()

    shelves = []
    for shelf in env.shelves:
        if shelf.get('carried'):
            continue
        shelves.append((shelf['x'], shelf['y'], 1 if shelf.get('requested') else 0))
    shelf_key = tuple(sorted(shelves))
    return agent_key, shelf_key


def build_quotient_model(env) -> Dict[str, object]:
    """Construct a minimal quotient description (representatives and orbit map)."""
    orbits = detect_role_orbits(env.robots)
    reps = [orbit[0] for orbit in orbits]
    mapping = {}
    for idx, orbit in enumerate(orbits):
        for agent_idx in orbit:
            mapping[agent_idx] = idx
    return {'representatives': reps, 'mapping': mapping, 'orbits': orbits}
