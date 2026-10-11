"""Random instances in the course formulation (one scene per day).

Each actor appears in a scene with their own probability p in [0.15, 0.6],
so there are main and minor roles. About 20% of the actors are expensive.
"""
import random

from .instance import Instance


def generate(n_scenes, n_actors, seed, unit_durations=True):
    rng = random.Random(seed)
    plays = []
    for _ in range(n_actors):
        p = rng.uniform(0.15, 0.6)
        row = [1 if rng.random() < p else 0 for _ in range(n_scenes)]
        while sum(row) < 2:
            row[rng.randrange(n_scenes)] = 1
        plays.append(row)
    for s in range(n_scenes):
        if not any(plays[a][s] for a in range(n_actors)):
            plays[rng.randrange(n_actors)][s] = 1
    wage = [rng.randint(20, 50) if rng.random() < 0.2 else rng.randint(1, 20)
            for _ in range(n_actors)]
    if unit_durations:
        duration = [1] * n_scenes
    else:
        duration = [rng.choice((1, 1, 1, 2, 2, 3)) for _ in range(n_scenes)]
    return Instance(f"gen_s{n_scenes}_a{n_actors}", plays, wage, duration)
