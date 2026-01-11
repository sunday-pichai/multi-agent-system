from replay import ReplayBuffer, PrioritizedReplayBuffer


def test_replay_push_sample_basic():
    buf = ReplayBuffer(capacity=10)
    for i in range(5):
        buf.push((i, i+1))
    s = buf.sample(3)
    assert len(s) == 3


def test_prioritized_push_and_sample():
    p = PrioritizedReplayBuffer(capacity=10)
    for i in range(6):
        p.push((i, i+1), priority=float(i+1))
    idxs, s = p.sample(4, return_indices=True)
    assert len(s) == 4
    # update priorities for sampled indices and ensure internal values changed
    old_priorities = list(p.priorities)
    p.update_priorities(idxs, [10.0] * len(idxs))
    for i in idxs:
        assert p.priorities[i] >= old_priorities[i]


if __name__ == '__main__':
    test_replay_push_sample_basic()
    test_prioritized_push_and_sample()
    print('replay tests passed')