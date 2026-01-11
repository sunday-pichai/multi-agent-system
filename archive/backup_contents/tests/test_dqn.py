import torch
from dqn import DQN

def test_dqn_forward_shape():
    model = DQN(10, action_size=5)
    x = torch.randn(2, 10)
    y = model(x)
    assert y.shape == (2, 5)

if __name__ == '__main__':
    test_dqn_forward_shape()
    print('DQN forward shape test passed')