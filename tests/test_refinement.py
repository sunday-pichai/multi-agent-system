"""Test suite for refinement module."""
import sys
from pathlib import Path

# Add parent directory to path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pathfinding import CooperativePlanner
from refinement import refine_planner_with_conflicts


def test_vertex_conflict_refinement():
    """Test refinement with vertex conflicts."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'vertex', 'pos': (5, 5), 'time': 3}
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    assert result['applied_constraints'] == 1, "Should apply 1 vertex constraint"
    # Check if the constraint was actually added
    assert planner.constraints.is_forbidden((5, 5), 4), "Position (5,5) should be forbidden at t=4"
    print("[OK] Vertex conflict refinement test passed")


def test_edge_conflict_refinement():
    """Test refinement with edge conflicts."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'edge', 'from': (3, 3), 'to': (3, 4), 'time': 2}
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    assert result['applied_constraints'] == 2, "Should apply 2 edge constraints (bidirectional)"
    # Check both directions are forbidden
    assert planner.constraints.is_edge_forbidden((3, 3), (3, 4), 3), "Edge (3,3)->(3,4) should be forbidden at t=3"
    assert planner.constraints.is_edge_forbidden((3, 4), (3, 3), 3), "Edge (3,4)->(3,3) should be forbidden at t=3"
    print("[OK] Edge conflict refinement test passed")


def test_boundary_conflict_refinement():
    """Test refinement with boundary conflicts."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'boundary', 'to': (0, 0), 'time': 1}
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    assert result['applied_constraints'] == 1, "Should apply 1 boundary constraint"
    assert planner.constraints.is_forbidden((0, 0), 2), "Boundary position should be forbidden at t=2"
    print("[OK] Boundary conflict refinement test passed")


def test_separation_conflict_skip():
    """Test that separation conflicts are skipped."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'separation', 'time': 1, 'min_distance': 0}
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    assert result['applied_constraints'] == 0, "Separation conflicts should not add constraints"
    print("[OK] Separation conflict skip test passed")


def test_multiple_conflicts():
    """Test refinement with multiple conflicts."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'vertex', 'pos': (5, 5), 'time': 3},
        {'type': 'edge', 'from': (3, 3), 'to': (3, 4), 'time': 2},
        {'type': 'boundary', 'to': (0, 0), 'time': 1}
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    # 1 vertex + 2 edge + 1 boundary = 4 constraints
    assert result['applied_constraints'] == 4, f"Should apply 4 constraints, got {result['applied_constraints']}"
    print("[OK] Multiple conflicts test passed")


def test_max_constraints_limit():
    """Test that max_constraints parameter limits the number of applied constraints."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'vertex', 'pos': (i, i), 'time': i} for i in range(10)
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts, max_constraints=5)
    
    assert result['applied_constraints'] == 5, "Should apply exactly 5 constraints due to limit"
    print("[OK] Max constraints limit test passed")


def test_fallback_trace_collision():
    """Test fallback refinement when no conflicts but trace shows collision."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    # Trace where agents 0 and 1 collide at position (5,5) at timestep 1
    trace = [
        [(4, 5), (6, 5)],  # t=0
        [(5, 5), (5, 5)],  # t=1 - collision!
    ]
    
    result = refine_planner_with_conflicts(planner, [], trace=trace)
    
    assert result['applied_constraints'] == 1, "Should apply 1 constraint from trace"
    assert planner.constraints.is_forbidden((5, 5), 1), "Collision position should be forbidden"
    print("[OK] Fallback trace collision test passed")


def test_fallback_trace_no_collision():
    """Test fallback refinement when trace has no exact collision."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    # Trace with close agents but no exact collision
    trace = [
        [(0, 0), (5, 5)],  # t=0
        [(0, 1), (5, 4)],  # t=1
    ]
    
    result = refine_planner_with_conflicts(planner, [], trace=trace)
    
    # Should find closest pair and block one position
    assert result['applied_constraints'] == 1, "Should apply 1 coarse constraint"
    print("[OK] Fallback trace no collision test passed")


def test_no_conflicts_no_trace():
    """Test when there are no conflicts and no trace."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    result = refine_planner_with_conflicts(planner, [], trace=None)
    
    assert result['applied_constraints'] == 0, "Should apply no constraints"
    print("[OK] No conflicts no trace test passed")


def test_missing_conflict_fields():
    """Test handling of conflicts with missing fields."""
    planner = CooperativePlanner(10, 10, plan_horizon=20)
    
    conflicts = [
        {'type': 'vertex', 'time': 3},  # missing 'pos'
        {'type': 'edge', 'from': (3, 3), 'time': 2},  # missing 'to'
        {'type': 'boundary', 'time': 1},  # missing 'to'
    ]
    
    result = refine_planner_with_conflicts(planner, conflicts)
    
    # Should skip conflicts with missing fields
    assert result['applied_constraints'] == 0, "Should skip conflicts with missing required fields"
    print("[OK] Missing conflict fields test passed")


if __name__ == '__main__':
    print("=" * 60)
    print("Running Refinement Logic Tests")
    print("=" * 60)
    
    test_vertex_conflict_refinement()
    test_edge_conflict_refinement()
    test_boundary_conflict_refinement()
    test_separation_conflict_skip()
    test_multiple_conflicts()
    test_max_constraints_limit()
    test_fallback_trace_collision()
    test_fallback_trace_no_collision()
    test_no_conflicts_no_trace()
    test_missing_conflict_fields()
    
    print("\n" + "=" * 60)
    print("All refinement tests passed!")
    print("=" * 60)
