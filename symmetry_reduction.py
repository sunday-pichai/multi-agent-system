"""Utilities for role-based symmetry reduction."""

from typing import Dict, Iterable, List, Tuple


AgentKey = Tuple[int, int, int, int]
OrbitKey = Tuple[AgentKey, ...]
StateKey = Tuple[OrbitKey, ...]


def _agent_role(robot) -> Tuple[int, int]:
    """Return compact role: (carrying_anything, carrying_requested)."""
    if robot.carrying is None:
        return 0, 0
    if robot.carrying.get("requested"):
        return 1, 1
    return 1, 0


def detect_role_orbits(robots: Iterable) -> List[List[int]]:
    """Group robot indices by role."""
    role_to_indices: Dict[Tuple[int, int], List[int]] = {}

    for index, robot in enumerate(robots):
        role = _agent_role(robot)
        if role not in role_to_indices:
            role_to_indices[role] = []
        role_to_indices[role].append(index)

    return list(role_to_indices.values())


def canonicalize_agents(robots: Iterable, orbits: List[List[int]]) -> StateKey:
    """Canonical key for agent states under within-orbit permutation."""
    robot_list = list(robots)
    orbit_keys: List[OrbitKey] = []

    for orbit in orbits:
        members: List[AgentKey] = []
        for robot_index in orbit:
            robot = robot_list[robot_index]
            _, carrying_requested = _agent_role(robot)
            members.append((robot.x, robot.y, robot.dir.value, carrying_requested))
        orbit_keys.append(tuple(sorted(members)))

    return tuple(orbit_keys)


def canonicalize_state(
    env, include_shelves: bool = False
) -> Tuple[StateKey, Tuple[Tuple[int, int, int], ...]]:
    """Project full environment state into a canonical quotient key."""
    orbits = detect_role_orbits(env.robots)
    agent_key = canonicalize_agents(env.robots, orbits)

    if not include_shelves:
        return agent_key, ()

    shelf_key_items: List[Tuple[int, int, int]] = []
    for shelf in env.shelves:
        if shelf.get("carried"):
            continue
        requested_flag = 1 if shelf.get("requested") else 0
        shelf_key_items.append((shelf["x"], shelf["y"], requested_flag))
    shelf_key = tuple(sorted(shelf_key_items))
    return agent_key, shelf_key


def build_quotient_model(env) -> Dict[str, object]:
    """Build minimal quotient metadata (orbit map + representatives)."""
    orbits = detect_role_orbits(env.robots)

    representatives: List[int] = []
    mapping: Dict[int, int] = {}

    for orbit_index, orbit in enumerate(orbits):
        representatives.append(orbit[0])
        for agent_index in orbit:
            mapping[agent_index] = orbit_index

    return {
        "representatives": representatives,
        "mapping": mapping,
        "orbits": orbits,
    }
