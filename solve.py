"""Solve one instance with simulated annealing.

    python solve.py instances/published/film1.dzn
    python solve.py instances/generated/gen_s40_a15.dzn --seed 7 --iters 200000
"""
import argparse
import json
import os

from talent.evaluation import schedule_table
from talent.instance import load_dzn
from talent.sa import simulated_annealing


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--iters", type=int, default=None, help="number of moves, default 4000 * scenes")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--no-polish", action="store_true")
    args = ap.parse_args()

    inst = load_dzn(args.instance)
    res = simulated_annealing(inst, max_iters=args.iters, seed=args.seed,
                              cycles=args.cycles, polish=not args.no_polish)

    print(f"Instance:   {inst.name} ({inst.n_scenes} scenes, {inst.n_actors} actors)")
    print(f"Total cost: {res.cost} (acting {inst.fixed_cost} + waiting {res.idle})")
    ref_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "reference.json")
    if os.path.exists(ref_path):
        with open(ref_path) as f:
            ref = json.load(f).get(inst.name)
        if ref:
            gap = 100.0 * (res.cost - ref["value"]) / ref["value"]
            print(f"Reference:  {ref['value']} ({ref['type']}), gap {gap:.2f} %")
    print(f"Time:       {res.seconds:.2f} s, {res.iterations} moves, "
          f"T0 = {res.t0:.2f}, T_end = {res.t_end:.3f}, alpha = {res.alpha:.5f}")
    print(f"Order:      {' '.join(str(s + 1) for s in res.perm)}")
    print()
    print(schedule_table(inst, res.perm))


if __name__ == "__main__":
    main()
