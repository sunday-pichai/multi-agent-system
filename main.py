"""Entry point for the Warehouse MAS project.

This module provides CLI-driven modes: interactive, train, eval
"""
from pathlib import Path
import argparse
import logging
import random
import sys
from collections import deque
import torch
import numpy as np

from config import (CELL_SIZE, NUM_AGENTS, BATCH_SIZE, WARMUP_STEPS, TARGET_UPDATE,
                    SAVE_INTERVAL, EPS_START, EPS_END, EPS_DECAY, MEMORY_SIZE, ACTION_SIZE)
import config as cfg
from eval_utils import set_seed, evaluate_repeated
from dqn import DQN
from env import WarehouseEnv
from utils import save_models


def run_interactive(args):
    env = WarehouseEnv(render=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dqns = [DQN(env.get_state(env.robots[0]).__len__(), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    targets = [DQN(env.get_state(env.robots[0]).__len__(), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    optimizers = [torch.optim.Adam(dqn.parameters()) for dqn in dqns]

    for t, dqn in zip(targets, dqns):
        t.load_state_dict(dqn.state_dict())
        t.eval()

    memories = [deque(maxlen=MEMORY_SIZE) for _ in range(NUM_AGENTS)]
    epsilon = EPS_START

    try:
        while True:
            for event in __import__('pygame').event.get():
                if event.type == __import__('pygame').QUIT or (event.type == __import__('pygame').KEYDOWN and event.key == __import__('pygame').K_q):
                    raise KeyboardInterrupt
            if random.random() < epsilon:
                actions = [random.randrange(ACTION_SIZE) for _ in range(NUM_AGENTS)]
            else:
                actions = []
                for i, state in enumerate(env.reset()):
                    q = dqns[i](torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0).to(device))
                    actions.append(q.argmax().item())
            env.step(actions)
            env.render()
    except KeyboardInterrupt:
        save_models(dqns, args.save_dir)
        __import__('pygame').quit()
        sys.exit()


def run_train(args):
    logger = logging.getLogger('warehouse')
    env = WarehouseEnv(render=args.render)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dqns = [DQN(len(env.get_state(env.robots[0])), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    targets = [DQN(len(env.get_state(env.robots[0])), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    optimizers = [torch.optim.Adam(dqn.parameters()) for dqn in dqns]

    # load existing models in save_dir
    for i, dqn in enumerate(dqns):
        p = Path(args.save_dir) / f"dqn_agent_{i}.pth"
        if p.exists():
            dqn.load_state_dict(torch.load(p, map_location=device))
            logger.info("Loaded model for agent %d from %s", i, p)

    for t, dqn in zip(targets, dqns):
        t.load_state_dict(dqn.state_dict())
        t.eval()

    memories = [deque(maxlen=MEMORY_SIZE) for _ in range(NUM_AGENTS)]
    epsilon = EPS_START

    total_steps = 0
    train_updates = 0

    logger.info("Starting training: episodes=%d steps/ep=%d", args.episodes, args.steps_per_episode)

    for ep in range(args.episodes):
        states = env.reset()
        done = False
        episode_steps = 0
        ep_rewards = [0.0] * NUM_AGENTS

        while not done and episode_steps < args.steps_per_episode:
            actions = []
            for i, state in enumerate(states):
                if random.random() < epsilon:
                    a = random.randrange(ACTION_SIZE)
                else:
                    q = dqns[i](torch.from_numpy(np.array(state, dtype=np.float32)).unsqueeze(0).to(device))
                    a = q.argmax().item()
                actions.append(a)
                memories[i].append((state.copy(), a, 0.0, None, False))

            next_states, rewards, done, cols, _ = env.step(actions)
            episode_steps += 1
            total_steps += 1

            for i in range(NUM_AGENTS):
                s, a, _, _, _ = memories[i][-1]
                memories[i][-1] = (s, a, rewards[i], next_states[i].copy(), done)
                ep_rewards[i] += rewards[i]

            states = next_states

            for i in range(NUM_AGENTS):
                if len(memories[i]) < args.batch_size or env.steps < args.warmup_steps:
                    continue
                batch = random.sample(list(memories[i]), args.batch_size)
                ss, aa, rr, ns, dd = zip(*batch)
                ss = torch.from_numpy(np.stack(ss)).to(device)
                aa = torch.LongTensor(aa).to(device)
                rr = torch.FloatTensor(rr).to(device)
                ns = torch.from_numpy(np.stack(ns)).to(device)
                dd = torch.FloatTensor(dd).to(device)
                with torch.no_grad():
                    next_q = targets[i](ns).max(1)[0]
                    target = rr + args.gamma * next_q * (1 - dd)
                current_q = dqns[i](ss).gather(1, aa.unsqueeze(1)).squeeze()
                loss = torch.nn.functional.mse_loss(current_q, target)
                optimizers[i].zero_grad()
                loss.backward()
                optimizers[i].step()
                train_updates += 1

            if total_steps % args.target_update == 0:
                for t, d in zip(targets, dqns):
                    t.load_state_dict(d.state_dict())

            epsilon = max(EPS_END, epsilon * EPS_DECAY)

            if args.save_interval and total_steps % args.save_interval == 0:
                save_models(dqns, args.save_dir)
                logger.info('Saved models at step %d', total_steps)

            if args.render:
                env.render()

        if (ep + 1) % args.log_interval == 0:
            avg_reward = sum(ep_rewards) / NUM_AGENTS if NUM_AGENTS else 0
            logger.info("Ep %d/%d total_steps=%d avg_reward=%.3f epsilon=%.3f", ep + 1, args.episodes, total_steps, avg_reward, epsilon)

    save_models(dqns, args.save_dir)
    logger.info("Training complete. Models saved to %s", args.save_dir)


def run_eval(args):
    logger = logging.getLogger('warehouse')
    env = WarehouseEnv(render=args.render)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dqns = [DQN(len(env.get_state(env.robots[0])), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    for i, dqn in enumerate(dqns):
        p = Path(args.save_dir) / f"dqn_agent_{i}.pth"
        if p.exists():
            dqn.load_state_dict(torch.load(p, map_location=device))
            logger.info("Loaded model %s", p)

    if getattr(args, 'eval_robust', False):
        mean, std = evaluate_repeated(dqns, device, episodes=args.eval_episodes, runs=args.eval_runs)
        logger.info("Eval collision rate (mean/std): %.2f%% ± %.2f", mean, std)
    else:
        rate = env.evaluate(dqns, device, num_episodes=args.eval_episodes, plot=args.render)
        logger.info("Eval collision rate: %.2f%%", rate)


def run_verify_refine(args):
    """Run a simple loop: verify (on quotient) -> extract cases -> store into prioritized replay -> fine-tune models -> checkpoint"""
    import os
    import logging
    from verification import verify_on_quotient
    from refinement import extract_failure_cases, fine_tune_on_cases
    from replay import PrioritizedReplayBuffer
    logger = logging.getLogger('warehouse')

    env = WarehouseEnv(render=False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # load models
    dqns = [DQN(len(env.get_state(env.robots[0])), ACTION_SIZE).to(device) for _ in range(NUM_AGENTS)]
    for i, dqn in enumerate(dqns):
        p = Path(args.save_dir) / f"dqn_agent_{i}.pth"
        if p.exists():
            dqn.load_state_dict(torch.load(p, map_location=device))
            logger.info("Loaded model for agent %d from %s", i, p)

    # prepare replay buffer
    replay = PrioritizedReplayBuffer(capacity=5000)

    try:
        from torch.utils.tensorboard import SummaryWriter
        writer = SummaryWriter(log_dir=Path(args.save_dir) / 'runs')
    except Exception:
        writer = None

    for it in range(getattr(args, 'iterations', 3)):
        logger.info("Verify-refine iteration %d", it + 1)
        res = verify_on_quotient(env, policy_models=dqns, horizon=20, trials=50)
        if res.get('safe', True):
            logger.info('No counterexamples found, stopping.')
            break

        actions = res.get('actions')
        if not actions:
            logger.warning('Counterexample found but no action trace available, skipping')
            break

        cases = extract_failure_cases(env, actions)
        # add cases to prioritized replay with large priority
        for c in cases:
            # convert dict to tuple for compact storage
            tup = (c['agent'], c['state'], c['action'], c['reward'], c['next_state'], c['done'])
            replay.push(tup, priority=10.0)

        # save visualizations for this counterexample
        try:
            from viz import plot_trajectories, plot_collision_heatmap
            plot_dir = Path(args.save_dir) / 'runs' / f'iter_{it+1}'
            plot_dir.mkdir(parents=True, exist_ok=True)
            if res.get('counterexample'):
                plot_trajectories(res['counterexample'], env, save_path=str(plot_dir / 'trajectories.png'), title=f'Iter {it+1} Trajectories')
                plot_collision_heatmap(res['counterexample'], env, save_path=str(plot_dir / 'heatmap.png'), title=f'Iter {it+1} Heatmap')
        except Exception as e:
            logger.warning('Failed to create visualizations: %s', e)

        # fine-tune and log
        summary = fine_tune_on_cases(dqns, cases=None, steps=getattr(args, 'refine_steps', 200), batch_size=getattr(args, 'refine_batch', 16), replay=replay, device=device)
        logger.info('Fine-tune summary: %s', summary)
        if writer is not None:
            writer.add_scalar('refinement/loss', summary.get('loss', 0.0), it)

        # checkpoint with iteration suffix
        iter_save_dir = Path(args.save_dir)
        save_models(dqns, iter_save_dir)
        logger.info('Saved checkpoint after iteration %d', it + 1)

    if writer is not None:
        writer.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Warehouse MAS - interactive, training, and evaluation modes")
    parser.add_argument("--mode", choices=["interactive", "train", "eval"], default="interactive", help="Run mode")
    parser.add_argument("--render", action="store_true", help="Enable rendering (interactive/eval)")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to YAML config file")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--cell-size", type=int, default=None, help="Override cell size (px)")
    parser.add_argument("--episodes", type=int, default=200, help="Number of episodes for training")
    parser.add_argument("--steps-per-episode", type=int, default=1000, help="Max steps per training episode")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="Training batch size")
    parser.add_argument("--warmup-steps", type=int, default=WARMUP_STEPS, help="Warmup steps before training")
    parser.add_argument("--target-update", type=int, default=TARGET_UPDATE, help="Target network update interval")
    parser.add_argument("--save-interval", type=int, default=SAVE_INTERVAL, help="Save interval (steps)")
    parser.add_argument("--save-dir", type=str, default="models", help="Directory to save models")
    parser.add_argument("--log-interval", type=int, default=10, help="Logging interval (episodes)")
    parser.add_argument("--eval-episodes", type=int, default=10, help="Number of episodes for evaluation")
    parser.add_argument("--eval-robust", action="store_true", help="Run repeated eval to get mean/std")
    parser.add_argument("--eval-runs", type=int, default=3, help="Number of eval runs when --eval-robust is used")
    parser.add_argument("--detect-symmetry", action="store_true", help="Run symmetry detection on a freshly-reset environment and print orbits")
    parser.add_argument("--verify-refine", action="store_true", help="Run a verify -> refine loop for a number of iterations")
    parser.add_argument("--iterations", type=int, default=3, help="Number of verify/refine iterations")
    parser.add_argument("--refine-steps", type=int, default=200, help="Fine-tuning steps per iteration")
    parser.add_argument("--refine-batch", type=int, default=16, help="Fine-tuning batch size")
    parser.add_argument("--gamma", type=float, default=0.99, help="Discount factor")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    # Load YAML overrides if available
    try:
        cfg.load_from_yaml(args.config)
    except Exception as e:
        logging.getLogger('warehouse').warning('Failed to load config from %s: %s', args.config, e)

    # Set global seed for reproducibility if provided
    if args.seed is not None:
        set_seed(args.seed)
        logging.getLogger('warehouse').info('Random seed set to %d', args.seed)

    if args.cell_size:
        # override the global CELL_SIZE constant used by env
        from config import CELL_SIZE as _cs
        # Note: changing config.CELL_SIZE at runtime for simplicity
        import config as _config
        _config.CELL_SIZE = args.cell_size

    if args.detect_symmetry:
        env = WarehouseEnv(render=False)
        env.reset()
        agents_pos = [(r.x, r.y) for r in env.robots]
        shelves_pos = [(s['x'], s['y']) for s in env.shelves]
        from symmetry_reduction import detect_permutation_symmetries, build_quotient_model
        orbits = detect_permutation_symmetries(agents_pos, shelves_pos, grid_size=(env.grid_w, env.grid_h))
        print('Detected orbits:')
        for o in orbits:
            print(o)
        q = build_quotient_model(env, orbits)
        print('Quotient summary:', q)
    elif args.mode == 'interactive':
        run_interactive(args)
    elif args.mode == 'train':
        run_train(args)
    elif args.mode == 'eval':
        run_eval(args)

    if getattr(args, 'verify_refine', False):
        run_verify_refine(args)


if __name__ == '__main__':
    main()
