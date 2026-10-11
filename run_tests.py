"""Experiments; results are written to results/.

    python run_tests.py              all experiments
    python run_tests.py main         10 runs per instance -> runs.csv, summary.csv, summary.md
    python run_tests.py budget       1000n / 4000n / 16000n moves on the largest instances -> budget.csv
    python run_tests.py budget --only gen_s80_a20:16000
    python run_tests.py trace        convergence of one run on gen_s60_a20
"""
import argparse
import csv
import glob
import json
import os
import statistics

from talent.instance import load_dzn
from talent.sa import simulated_annealing

REF_PATH = "results/reference.json"
RUNS = 10
BUDGET_INSTANCES = ("gen_s60_a20", "gen_s80_a20")
BUDGET_FACTORS = (1000, 4000, 16000)


def gap(value, ref):
    return 100.0 * (value - ref) / ref


def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def update_reference(ref, inst, results, note):
    """Replace a best known value if some run found a better order."""
    best = min(results, key=lambda r: r.cost)
    entry = ref[inst.name]
    if best.cost < entry["value"]:
        print(f"  new best known for {inst.name}: {best.cost} (was {entry['value']})")
        entry.update({"value": best.cost, "idle": best.idle, "method": note,
                      "order": [s + 1 for s in best.perm]})


def instance_paths():
    def by_size(paths):
        return sorted(paths, key=lambda p: load_dzn(p).n_scenes)
    return by_size(glob.glob("instances/published/*.dzn")) + by_size(glob.glob("instances/generated/*.dzn"))


def run_main(ref):
    runs, summary = [], []
    for path in instance_paths():
        inst = load_dzn(path)
        results = [simulated_annealing(inst, seed=seed) for seed in range(1, RUNS + 1)]
        update_reference(ref, inst, results, "best SA run found in run_tests.py main")
        r = ref[inst.name]
        costs = [res.cost for res in results]
        for seed, res in enumerate(results, start=1):
            runs.append([inst.name, seed, res.cost, res.idle, round(res.seconds, 3), res.iterations,
                         round(gap(res.cost, r["value"]), 3)])
        avg = statistics.mean(costs)
        row = {
            "instance": inst.name, "scenes": inst.n_scenes, "actors": inst.n_actors,
            "reference": r["value"], "reference_type": r["type"],
            "reference_idle": r["value"] - inst.fixed_cost,
            "best": min(costs), "avg": round(avg, 1), "worst": max(costs),
            "gap_best_pct": round(gap(min(costs), r["value"]), 2),
            "gap_avg_pct": round(gap(avg, r["value"]), 2),
            "gap_avg_idle_pct": round(gap(avg - inst.fixed_cost, r["value"] - inst.fixed_cost), 2),
            "hits": sum(c == r["value"] for c in costs), "runs": RUNS,
            "avg_seconds": round(statistics.mean(res.seconds for res in results), 2),
            "iterations": results[0].iterations,
        }
        summary.append(row)
        print(f"{inst.name:12s} n={inst.n_scenes:2d} ref={r['value']:5d} best={row['best']:5d} "
              f"avg={row['avg']:8.1f} gap={row['gap_avg_pct']:5.2f}% hits={row['hits']}/{RUNS} "
              f"t={row['avg_seconds']:.2f}s", flush=True)

    write_csv("results/runs.csv", ["instance", "seed", "cost", "idle", "seconds", "iterations", "gap_pct"], runs)
    keys = list(summary[0])
    write_csv("results/summary.csv", keys, [[row[k] for k in keys] for row in summary])
    lines = ["| Instance | Scenes | Actors | Reference | Type | SA best | SA avg | Avg gap % | Hits | Avg time, s |",
             "|---|---:|---:|---:|---|---:|---:|---:|---:|---:|"]
    for row in summary:
        lines.append(f"| {row['instance']} | {row['scenes']} | {row['actors']} | {row['reference']} | "
                     f"{row['reference_type']} | {row['best']} | {row['avg']} | {row['gap_avg_pct']:.2f} | "
                     f"{row['hits']}/{row['runs']} | {row['avg_seconds']:.2f} |")
    with open("results/summary.md", "w") as f:
        f.write("\n".join(lines) + "\n")


def run_budget(ref, pairs):
    path = "results/budget.csv"
    header = ["instance", "iters_per_scene", "iterations", "best", "avg", "gap_avg_pct", "avg_seconds"]
    rows = {}
    if os.path.exists(path):
        with open(path) as f:
            for row in list(csv.reader(f))[1:]:
                rows[(row[0], int(row[1]))] = row
    for name, factor in pairs:
        inst = load_dzn(f"instances/generated/{name}.dzn")
        results = [simulated_annealing(inst, max_iters=factor * inst.n_scenes, seed=s) for s in range(1, RUNS + 1)]
        update_reference(ref, inst, results, f"best SA run found in run_tests.py budget ({factor}n moves)")
        costs = [r.cost for r in results]
        rows[(name, factor)] = [name, factor, factor * inst.n_scenes, min(costs),
                                round(statistics.mean(costs), 1), None,
                                round(statistics.mean(r.seconds for r in results), 2)]
        print("budget", rows[(name, factor)][:5], flush=True)
    for row in rows.values():   # gaps against the current reference values
        row[5] = round(gap(float(row[4]), ref[row[0]]["value"]), 2)
    order = {n: i for i, n in enumerate(BUDGET_INSTANCES)}
    write_csv(path, header, sorted(rows.values(), key=lambda r: (order.get(r[0], 99), int(r[1]))))


def run_trace():
    inst = load_dzn("instances/generated/gen_s60_a20.dzn")
    res = simulated_annealing(inst, seed=1, trace_every=500)
    write_csv("results/convergence_gen_s60_a20.csv", ["iteration", "temperature", "current", "best"],
              [[it, round(t, 4), cur, best] for it, t, cur, best in res.trace])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("experiment", nargs="?", default="all", choices=["all", "main", "budget", "trace"])
    ap.add_argument("--only", nargs="+", metavar="NAME:FACTOR", help="budget pairs, e.g. gen_s60_a20:4000")
    args = ap.parse_args()

    os.makedirs("results", exist_ok=True)
    with open(REF_PATH) as f:
        ref = json.load(f)
    if args.experiment in ("all", "main"):
        run_main(ref)
    if args.experiment in ("all", "trace"):
        run_trace()
    if args.experiment in ("all", "budget"):
        if args.only:
            pairs = [(p.split(":")[0], int(p.split(":")[1])) for p in args.only]
        else:
            pairs = [(n, f) for n in BUDGET_INSTANCES for f in BUDGET_FACTORS]
        run_budget(ref, pairs)
    with open(REF_PATH, "w") as f:
        json.dump(ref, f, indent=1)


if __name__ == "__main__":
    main()
