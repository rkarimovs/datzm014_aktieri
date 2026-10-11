"""Objective function: total salary cost of a shooting order."""


def total_cost(inst, perm):
    # An actor is paid on day k if they appear somewhere in perm[0..k] and
    # somewhere in perm[k..n-1], i.e. present = prefix_or & suffix_or.
    sa = inst.scene_actors
    n = len(perm)
    suffix = [0] * n
    acc = 0
    for k in range(n - 1, -1, -1):
        acc |= sa[perm[k]]
        suffix[k] = acc
    W = inst.wage_table
    d = inst.duration
    prefix = 0
    cost = 0
    for k in range(n):
        s = perm[k]
        prefix |= sa[s]
        cost += d[s] * W[prefix & suffix[k]]
    return cost


def idle_cost(inst, perm):
    return total_cost(inst, perm) - inst.fixed_cost


def total_cost_simple(inst, perm):
    """Direct O(n*m) version of total_cost, used in tests."""
    start, t = {}, 0
    for s in perm:
        start[s] = t
        t += inst.duration[s]
    cost = 0
    for a, scenes in enumerate(inst.actor_scenes):
        if scenes:
            first = min(start[s] for s in scenes)
            last = max(start[s] + inst.duration[s] for s in scenes)
            cost += inst.wage[a] * (last - first)
    return cost


def schedule_table(inst, perm):
    """X = acting, - = waiting (paid), . = not hired."""
    pos = {s: k for k, s in enumerate(perm)}
    lines = [
        "scene    " + " ".join(f"{s + 1:>3}" for s in perm),
        "days     " + " ".join(f"{inst.duration[s]:>3}" for s in perm),
    ]
    for a, scenes in enumerate(inst.actor_scenes):
        first = min(pos[s] for s in scenes) if scenes else 0
        last = max(pos[s] for s in scenes) if scenes else -1
        row = []
        for k, s in enumerate(perm):
            if inst.plays[a][s]:
                row.append("  X")
            elif first < k < last:
                row.append("  -")
            else:
                row.append("  .")
        lines.append(f"actor{a + 1:<3} " + " ".join(row) + f"   wage {inst.wage[a]}")
    return "\n".join(lines)
