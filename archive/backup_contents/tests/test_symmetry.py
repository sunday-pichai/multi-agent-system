from symmetry_reduction import detect_permutation_symmetries


def test_simple_symmetry_two_agents():
    # Two agents in symmetric positions (mirror across center)
    agents = [(5, 5), (14, 5)]
    orbits = detect_permutation_symmetries(agents)
    # Expect them to be grouped together due to identical empty neighborhood signatures
    assert any(len(o['orbit']) == 2 for o in orbits), f"Unexpected orbits: {orbits}"


def test_asymmetric_three_agents():
    agents = [(1, 1), (2, 1), (10, 10)]
    orbits = detect_permutation_symmetries(agents)
    # expect the far-away one to be its own orbit
    assert any(len(o['orbit']) == 1 for o in orbits)

if __name__ == '__main__':
    test_simple_symmetry_two_agents()
    print('symmetry simple test passed')
    test_asymmetric_three_agents()
    print('symmetry asymmetric test passed')