"""Simulated annealing for the talent scheduling problem."""
import math
import random
import time
from dataclasses import dataclass, field

from .evaluation import total_cost

MOVES = ("swap", "insert", "reverse")


@dataclass
class SAResult:
    perm: list
    cost: int
    idle: int
    iterations: int
    accepted: int
    improvements: int
    seconds: float
    t0: float
    t_end: float
    alpha: float
    trace: list = field(default_factory=list)   # (iteration, T, current cost, best cost)


def apply_move(perm, move, i, j):
    p = perm[:]
    if move == "swap":
        p[i], p[j] = p[j], p[i]
    elif move == "insert":
        p.insert(j, p.pop(i))
    else:
        if i > j:
            i, j = j, i
        p[i:j + 1] = p[i:j + 1][::-1]
    return p


def random_move(n, rng, thresholds):
    r = rng.random()
    if r < thresholds[0]:
        move = "swap"
    elif r < thresholds[1]:
        move = "insert"
    else:
        move = "reverse"
    i = rng.randrange(n)
    j = rng.randrange(n - 1)
    if j >= i:
        j += 1
    return move, i, j


def initial_temperature(inst, perm, cost, rng, thresholds, p0, samples=400):
    # T0 such that an average worsening move is accepted with probability p0
    worse = []
    for _ in range(samples):
        move, i, j = random_move(len(perm), rng, thresholds)
        delta = total_cost(inst, apply_move(perm, move, i, j)) - cost
        if delta > 0:
            worse.append(delta)
    if not worse:
        return 1.0
    return sum(worse) / len(worse) / -math.log(p0)


def descent(inst, perm, cost):
    """Best-improvement local search with insert moves."""
    n = len(perm)
    while True:
        best_delta, best_p = 0, None
        for i in range(n):
            for j in range(n):
                if i != j:
                    p = apply_move(perm, "insert", i, j)
                    delta = total_cost(inst, p) - cost
                    if delta < best_delta:
                        best_delta, best_p = delta, p
        if best_p is None:
            return perm, cost
        perm, cost = best_p, cost + best_delta


def simulated_annealing(inst, max_iters=None, seed=None, init=None, p0=0.5, p_end=0.001,
                        iters_per_temp=None, cycles=3, reheat=0.3, move_weights=(1, 1, 1),
                        polish=True, time_limit=None, trace_every=None):
    """
    max_iters       total number of moves, default 4000 * n
    p0              acceptance probability of an average worsening at the start
    p_end           acceptance probability of the smallest possible worsening
                    (min wage * min duration) at the end
    iters_per_temp  moves per temperature level, default n(n-1)/4
    cycles, reheat  each cycle after the first restarts from the best order
                    with T = reheat * T0
    """
    start = time.perf_counter()
    rng = random.Random(seed)
    n = inst.n_scenes
    if max_iters is None:
        max_iters = 4000 * n
    if iters_per_temp is None:
        iters_per_temp = max(10, n * (n - 1) // 4)
    w = float(sum(move_weights))
    thresholds = (move_weights[0] / w, (move_weights[0] + move_weights[1]) / w)

    if init is None:
        cur = list(range(n))
        rng.shuffle(cur)
    else:
        cur = list(init)
    cur_cost = total_cost(inst, cur)
    best, best_cost = cur[:], cur_cost

    t0 = initial_temperature(inst, cur, cur_cost, rng, thresholds, p0)
    min_worsening = min(x for x in inst.wage if x > 0) * min(inst.duration)
    t_end = min(min_worsening / -math.log(p_end), t0)
    levels = max(1, max_iters // cycles // iters_per_temp)

    def cooling_factor(t_start):
        return (t_end / t_start) ** (1.0 / levels) if t_start > t_end else 1.0

    alpha = cooling_factor(t0)
    if trace_every is None:
        trace_every = iters_per_temp

    it = accepted = improvements = 0
    trace = [(0, t0, cur_cost, best_cost)]
    exp = math.exp
    rand = rng.random
    T = t0
    timed_out = False
    for cycle in range(cycles):
        if timed_out:
            break
        if cycle > 0:
            T = max(reheat * t0, t_end)
            cur, cur_cost = best[:], best_cost
        factor = cooling_factor(T)
        for _ in range(levels):
            for _ in range(iters_per_temp):
                move, i, j = random_move(n, rng, thresholds)
                cand = apply_move(cur, move, i, j)
                cand_cost = total_cost(inst, cand)
                delta = cand_cost - cur_cost
                if delta <= 0 or rand() < exp(-delta / T):
                    cur, cur_cost = cand, cand_cost
                    accepted += 1
                    if cur_cost < best_cost:
                        best, best_cost = cur[:], cur_cost
                        improvements += 1
                it += 1
                if it % trace_every == 0:
                    trace.append((it, T, cur_cost, best_cost))
            T *= factor
            if time_limit is not None and time.perf_counter() - start > time_limit:
                timed_out = True
                break

    if polish:
        best, best_cost = descent(inst, best, best_cost)
        trace.append((it, T, best_cost, best_cost))

    return SAResult(best, best_cost, best_cost - inst.fixed_cost, it, accepted, improvements,
                    time.perf_counter() - start, t0, t_end, alpha, trace)
