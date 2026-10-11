"""Basic correctness checks: python tests.py"""
import glob
import random

from talent.evaluation import total_cost, total_cost_simple
from talent.exact import solve_exact
from talent.instance import load_dzn
from talent.sa import apply_move, simulated_annealing


def test_evaluation():
    for path in glob.glob("instances/*/*.dzn"):
        inst = load_dzn(path)
        rng = random.Random(0)
        for _ in range(100):
            p = list(range(inst.n_scenes))
            rng.shuffle(p)
            assert total_cost(inst, p) == total_cost_simple(inst, p), inst.name


def test_moves_keep_permutation():
    rng = random.Random(0)
    for _ in range(1000):
        p = list(range(10))
        i, j = rng.sample(range(10), 2)
        for move in ("swap", "insert", "reverse"):
            assert sorted(apply_move(p, move, i, j)) == p


def test_exact_matches_published_optima():
    # waiting-cost optima from CSPLib prob039
    for name, idle in (("rehearsal", 17), ("film2", 87), ("film1", 146)):
        inst = load_dzn(f"instances/published/{name}.dzn")
        value, order, _ = solve_exact(inst)
        assert value - inst.fixed_cost == idle
        assert total_cost(inst, order) == value


def test_sa_small():
    inst = load_dzn("instances/published/rehearsal.dzn")
    res = simulated_annealing(inst, seed=1)
    assert sorted(res.perm) == list(range(inst.n_scenes))
    assert res.cost == total_cost(inst, res.perm) == 109


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name}: ok")
