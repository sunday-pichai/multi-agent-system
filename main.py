"""Entry point for the Warehouse MAS project (deterministic planning)."""
import argparse
import logging
import random
import sys

import config as cfg
from env import WarehouseEnv
from pathfinding import CooperativePlanner
from verification import verify_on_quotient
from refinement import refine_planner_with_conflicts


def set_seed(seed: int) -> None:
    random.seed(seed)


def run_interactive(args):
    env = WarehouseEnv(render=True)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=args.plan_horizon)

    try:
        while True:
            for event in __import__('pygame').event.get():
                if event.type == __import__('pygame').QUIT or (
                    event.type == __import__('pygame').KEYDOWN and event.key == __import__('pygame').K_q
                ):
                    raise KeyboardInterrupt

            actions = planner.compute_actions(env)
            _, _, done, _, _ = env.step(actions)
            if done:
                env.reset()
            env.render()
    except KeyboardInterrupt:
        __import__('pygame').quit()
        sys.exit(0)


def run_simulation(args):
    logger = logging.getLogger('warehouse')
    env = WarehouseEnv(render=args.render)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=args.plan_horizon)

    total_collisions = 0

    for ep in range(args.episodes):
        env.reset()
        episode_collisions = 0
        steps = 0
        done = False

        while not done and steps < args.steps_per_episode:
            actions = planner.compute_actions(env)
            _, _, done, cols, _ = env.step(actions)
            episode_collisions += cols
            total_collisions += cols
            steps += 1

            if args.render:
                env.render()

        if (ep + 1) % args.log_interval == 0:
            avg = total_collisions / ((ep + 1) * env.num_agents) if env.num_agents else 0
            logger.info(
                "Ep %d/%d avg_collisions_per_agent_per_episode=%.3f",
                ep + 1,
                args.episodes,
                avg,
            )


def run_eval(args):
    logger = logging.getLogger('warehouse')
    env = WarehouseEnv(render=False)
    planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=args.plan_horizon)

    rate = env.evaluate(
        planner,
        num_episodes=args.eval_episodes,
        max_steps_per_episode=args.steps_per_episode,
        progress_every=1,
        logger=logger,
    )
    logger.info("Eval avg collisions per agent per episode: %.3f", rate)


def run_verify_refine(args, planner: CooperativePlanner = None):
    logger = logging.getLogger('warehouse')
    env = WarehouseEnv(render=False)
    if planner is None:
        planner = CooperativePlanner(env.grid_w, env.grid_h, plan_horizon=args.plan_horizon)

    for it in range(args.refine_iterations):
        result = verify_on_quotient(
            env,
            planner,
            horizon=args.verify_horizon,
            trials=args.verify_trials,
            include_shelves=args.verify_include_shelves,
            min_separation=args.min_separation,
            progress_every=args.verify_progress,
            logger=logger,
        )

        if result.get('safe', False):
            logger.info(
                "Verification passed at iteration %d (delta_q=%.2f).",
                it + 1,
                float(result.get('delta_q', 0.0)),
            )
            _log_refine_summary(logger, planner, result)
            return planner

        logger.warning(
            "Verification failed at iteration %d. Applying refinement...",
            it + 1,
        )
        conflicts = result.get('conflicts', [])
        trace = result.get('counterexample')
        summary = refine_planner_with_conflicts(
            planner,
            conflicts,
            trace=trace,
            max_constraints=args.refine_max_constraints,
        )
        logger.info("Refinement applied: %s", summary)

    logger.warning("Verify-refine loop exhausted without full safety.")
    if 'result' in locals():
        _log_refine_summary(logger, planner, result)
    return planner


def _log_refine_summary(logger, planner: CooperativePlanner, result):
    avg_rate = float(result.get('avg_collision_rate', 0.0))
    logger.info("Average collision rate (per step): %.4f", avg_rate)

    positions = []
    for t in sorted(planner.constraints.positions.keys()):
        for pos in planner.constraints.positions[t]:
            positions.append((t, pos))

    edges = []
    for t in sorted(planner.constraints.edges.keys()):
        for edge in planner.constraints.edges[t]:
            edges.append((t, edge))

    logger.info("Final constraints: %d positions, %d edges", len(positions), len(edges))
    if positions:
        sample = ", ".join([f"t={t}:{pos}" for t, pos in positions[:10]])
        logger.info("Position constraints sample: %s", sample)
    if edges:
        sample = ", ".join([f"t={t}:{edge[0]}->{edge[1]}" for t, edge in edges[:10]])
        logger.info("Edge constraints sample: %s", sample)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warehouse MAS - deterministic planning")
    parser.add_argument("--mode", choices=["interactive", "simulate", "eval"], default="interactive", help="Run mode")
    parser.add_argument("--render", action="store_true", help="Enable rendering (interactive/simulate)")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to YAML config file")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--cell-size", type=int, default=None, help="Override cell size (px)")
    parser.add_argument("--episodes", type=int, default=8, help="Number of episodes for simulation")
    parser.add_argument("--steps-per-episode", type=int, default=200, help="Max steps per episode")
    parser.add_argument("--log-interval", type=int, default=1, help="Logging interval (episodes)")
    parser.add_argument("--eval-episodes", type=int, default=3, help="Number of episodes for evaluation")
    parser.add_argument("--plan-horizon", type=int, default=None, help="Planning horizon (timesteps)")
    parser.add_argument("--detect-symmetry", action="store_true", help="Run symmetry detection on a freshly-reset environment and print orbits")
    parser.add_argument("--verify-refine", action="store_true", help="Run verification-guided refinement loop")
    parser.add_argument("--verify-horizon", type=int, default=None, help="Verification horizon (timesteps)")
    parser.add_argument("--verify-trials", type=int, default=None, help="Verification trials (random resets)")
    parser.add_argument("--verify-include-shelves", action="store_true", help="Include shelves in quotient key")
    parser.add_argument("--verify-progress", type=int, default=1, help="Progress update frequency for verification (trials)")
    parser.add_argument("--min-separation", type=int, default=None, help="Minimum Manhattan separation for safety")
    parser.add_argument("--refine-iterations", type=int, default=None, help="Max verify/refine iterations")
    parser.add_argument("--refine-max-constraints", type=int, default=None, help="Max constraints added per iteration")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # Load YAML overrides if available
    try:
        cfg.load_from_yaml(args.config)
    except Exception as e:
        logging.getLogger('warehouse').warning('Failed to load config from %s: %s', args.config, e)

    if args.plan_horizon is None:
        args.plan_horizon = cfg.PLAN_HORIZON
    if args.verify_horizon is None:
        args.verify_horizon = cfg.VERIFY_HORIZON
    if args.verify_trials is None:
        args.verify_trials = cfg.VERIFY_TRIALS
    if args.min_separation is None:
        args.min_separation = cfg.MIN_SEPARATION
    if args.refine_iterations is None:
        args.refine_iterations = cfg.REFINE_ITERATIONS
    if args.refine_max_constraints is None:
        args.refine_max_constraints = cfg.REFINE_MAX_CONSTRAINTS

    # Set global seed for reproducibility if provided
    if args.seed is not None:
        set_seed(args.seed)
        logging.getLogger('warehouse').info('Random seed set to %d', args.seed)

    if args.cell_size:
        import config as _config
        _config.CELL_SIZE = args.cell_size

    if args.detect_symmetry:
        env = WarehouseEnv(render=False)
        env.reset()
        from symmetry_reduction import build_quotient_model
        q = build_quotient_model(env)
        print('Detected orbits:')
        for orbit in q['orbits']:
            print(orbit)
        print('Quotient summary:', q)
    elif args.verify_refine:
        run_verify_refine(args)
    elif args.mode == 'interactive':
        run_interactive(args)
    elif args.mode == 'simulate':
        run_simulation(args)
    elif args.mode == 'eval':
        run_eval(args)


if __name__ == '__main__':
    main()
