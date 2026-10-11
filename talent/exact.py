"""Exact dynamic programming solver, used only to get reference optima.

Q is the set of scenes not shot yet. If scene s from Q is shot next, the
actors on location are actors(s) | (actors(shot) & actors(Q - s)), which
depends only on Q and s:

    f(Q) = min over s in Q of  d(s) * wage(present) + f(Q - s),   f({}) = 0

Scenes with identical actor sets are merged first, since some optimal order
shoots them one after another (Garcia de la Banda, Stuckey, Chu 2011).
Runs in O(2^N * N) time, so it is usable up to about 24 merged scenes.
"""
import time
from array import array


def merge_identical_scenes(inst):
    groups = {}
    for s in range(inst.n_scenes):
        groups.setdefault(inst.scene_actors[s], []).append(s)
    actors = list(groups)
    members = list(groups.values())
    durations = [sum(inst.duration[s] for s in g) for g in members]
    return actors, members, durations


def solve_exact(inst, max_merged=24):
    start = time.perf_counter()
    act, members, dur = merge_identical_scenes(inst)
    N = len(act)
    if N > max_merged:
        raise ValueError(f"{inst.name}: {N} merged scenes, too many for the DP")
    size = 1 << N
    full = size - 1

    A = array("q", [0]) * size          # A[S] = actors of the scenes in S
    for S in range(1, size):
        low = S & -S
        A[S] = A[S ^ low] | act[low.bit_length() - 1]

    W = inst.wage_table
    f = array("q", [0]) * size
    choice = array("b", [0]) * size
    for Q in range(1, size):
        shot = A[full ^ Q]
        best, best_s = None, -1
        q = Q
        while q:
            low = q & -q
            q ^= low
            s = low.bit_length() - 1
            rest = Q ^ low
            c = dur[s] * W[act[s] | (shot & A[rest])] + f[rest]
            if best is None or c < best:
                best, best_s = c, s
        f[Q] = best
        choice[Q] = best_s

    order, Q = [], full
    while Q:
        s = choice[Q]
        order.extend(members[s])
        Q ^= 1 << s
    return f[full], order, time.perf_counter() - start
