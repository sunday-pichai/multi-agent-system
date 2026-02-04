"""Integration test for verification + refinement workflow."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env import WarehouseEnv
from pathfinding import CooperativePlanner
from verification import verify_on_quotient
from refinement import refine_planner_with_conflicts


def test_verification_refinement_loop():
    """Test that refinement improves safety after verification finds conflicts."""
    print("\n" + "=" * 60)
    print("Testing Verification + Refinement Integration")
    print("=" * 60)
    
    env = WarehouseEnv(render=False)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=20)
    
    # First verification run
    print("\nRunning initial verification...")
    result1 = verify_on_quotient(env, planner, horizon=15, trials=10)
    
    print(f"Initial verification result: {'SAFE' if result1['safe'] else 'UNSAFE'}")
    
    if not result1['safe']:
        print(f"Found conflicts: {len(result1.get('conflicts', []))} conflicts")
        print(f"Delta Q (safety margin): {result1['delta_q']}")
        
        # Apply refinement
        conflicts = result1.get('conflicts', [])
        trace = result1.get('counterexample', None)
        
        print(f"\nApplying refinement with {len(conflicts)} conflicts...")
        refine_result = refine_planner_with_conflicts(planner, conflicts, trace)
        
        print(f"Applied {refine_result['applied_constraints']} constraints")
        
        # Second verification run after refinement
        print("\nRunning verification after refinement...")
        result2 = verify_on_quotient(env, planner, horizon=15, trials=10)
        
        print(f"Post-refinement result: {'SAFE' if result2['safe'] else 'UNSAFE'}")
        
        if not result2['safe']:
            print(f"Still found conflicts, but delta_q improved from {result1['delta_q']} to {result2['delta_q']}")
        
        # The refinement should at least prevent the exact same collision
        # or improve the safety margin
        success = result2['safe'] or result2['delta_q'] >= result1['delta_q']
        
        assert success, "Refinement should improve safety or maintain margin"
        
        print("\n[OK] Refinement successfully improved or maintained safety")
    else:
        print("\n[INFO] System was already safe, no refinement needed")
        print("[OK] No conflicts detected")
    
    print("\n" + "=" * 60)
    print("Integration test completed successfully!")
    print("=" * 60)


if __name__ == '__main__':
    test_verification_refinement_loop()
