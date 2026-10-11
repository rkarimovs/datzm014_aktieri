"""Reference values for all instances, saved to results/reference.json.

Up to 24 merged scenes the exact optimum is computed with dynamic programming.
For larger instances the best known value is the best of 10 long SA runs
(10x the default number of moves). run_tests.py replaces a best known value
if any test run finds a better solution.
"""
import glob
import json
import os

from talent.evaluation import total_cost
from talent.exact import merge_identical_scenes, solve_exact
from talent.instance import load_dzn
from talent.sa import simulated_annealing

PUBLISHED_IDLE_OPTIMA = {"rehearsal": 17, "film2": 87, "film1": 146}   # CSPLib prob039
EXACT_LIMIT = 24
OUT = "results/reference.json"


def main():
    paths = sorted(glob.glob("instances/published/*.dzn")) + sorted(glob.glob("instances/generated/*.dzn"))
    ref = {}
    if os.path.exists(OUT):
        with open(OUT) as f:
            ref = json.load(f)
    for path in paths:
        inst = load_dzn(path)
        if inst.name in ref:
            continue
        if len(merge_identical_scenes(inst)[0]) <= EXACT_LIMIT:
            value, order, secs = solve_exact(inst, max_merged=EXACT_LIMIT)
            assert total_cost(inst, order) == value
            published = PUBLISHED_IDLE_OPTIMA.get(inst.name)
            if published is not None:
                assert value - inst.fixed_cost == published
            entry = {"value": value, "type": "optimal", "method": "exact DP", "seconds": round(secs, 2),
                     "order": [s + 1 for s in order]}
        else:
            runs = [simulated_annealing(inst, max_iters=40000 * inst.n_scenes, seed=1000 + k) for k in range(10)]
            best = min(runs, key=lambda r: r.cost)
            entry = {"value": best.cost, "type": "best_known", "method": "best of 10 long SA runs",
                     "seconds": round(sum(r.seconds for r in runs), 2), "order": [s + 1 for s in best.perm]}
        entry.update({"scenes": inst.n_scenes, "actors": inst.n_actors, "fixed_cost": inst.fixed_cost,
                      "idle": entry["value"] - inst.fixed_cost})
        ref[inst.name] = entry
        print(f"{inst.name:12s} {entry['type']:10s} {entry['value']:6d}  {entry['seconds']} s", flush=True)
        with open(OUT, "w") as f:
            json.dump(ref, f, indent=1)


if __name__ == "__main__":
    main()
