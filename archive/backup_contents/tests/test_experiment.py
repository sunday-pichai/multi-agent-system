from experiments.run_verify_refine_experiment import run_experiment


def test_run_experiment_smoke(tmp_path):
    res = run_experiment(save_dir=str(tmp_path / 'models'), seed=123, iterations=1, refine_steps=10, refine_batch=4, eval_episodes=5)
    assert 'seed' in res and 'pre_rate' in res and 'post_rate' in res


if __name__ == '__main__':
    import pathlib
    test_run_experiment_smoke(pathlib.Path('.'))
    print('experiment smoke test passed')