"""Talent scheduling instance and reading/writing of MiniZinc .dzn files."""
import os
import re


class Instance:
    def __init__(self, name, plays, wage, duration):
        self.name = name
        self.plays = [list(row) for row in plays]   # plays[a][s] = 1 if actor a is in scene s
        self.wage = list(wage)
        self.duration = list(duration)
        self.n_actors = len(self.plays)
        self.n_scenes = len(self.duration)
        self._check()

        # actors of each scene as a bitmask (bit a = actor a)
        self.scene_actors = [
            sum(1 << a for a in range(self.n_actors) if self.plays[a][s])
            for s in range(self.n_scenes)
        ]
        self.actor_scenes = [
            [s for s in range(self.n_scenes) if self.plays[a][s]]
            for a in range(self.n_actors)
        ]
        # cost of the acting days, the same for every order
        self.fixed_cost = sum(
            self.wage[a] * sum(self.duration[s] for s in self.actor_scenes[a])
            for a in range(self.n_actors)
        )
        self.wage_table = make_wage_table(self.wage)

    def _check(self):
        if any(len(row) != self.n_scenes for row in self.plays):
            raise ValueError(f"{self.name}: wrong row length in ia")
        if len(self.wage) != self.n_actors:
            raise ValueError(f"{self.name}: wrong number of wages")
        if any(d <= 0 for d in self.duration):
            raise ValueError(f"{self.name}: durations must be positive")

    def __repr__(self):
        return f"Instance({self.name}, scenes={self.n_scenes}, actors={self.n_actors})"


def make_wage_table(wage):
    """Maps an actor bitmask to the sum of their wages."""
    m = len(wage)
    if m > 20:
        return LazyWageTable(wage)
    table = [0] * (1 << m)
    for mask in range(1, 1 << m):
        low = mask & -mask
        table[mask] = table[mask ^ low] + wage[low.bit_length() - 1]
    return table


class LazyWageTable(dict):
    """Same as the list table, but computed on demand (used for > 20 actors)."""

    def __init__(self, wage):
        super().__init__()
        self.wage = list(wage)

    def __missing__(self, mask):
        value, m = 0, mask
        while m:
            low = m & -m
            value += self.wage[low.bit_length() - 1]
            m ^= low
        self[mask] = value
        return value


def load_dzn(path):
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"%[^\n]*", "", f.read())

    def scalar(key):
        m = re.search(rf"\b{key}\s*=\s*(\d+)\s*;", text)
        if not m:
            raise ValueError(f"{path}: missing {key}")
        return int(m.group(1))

    def array(key):
        m = re.search(rf"\b{key}\s*=\s*(\[.*?\])\s*;", text, re.S)
        if not m:
            raise ValueError(f"{path}: missing {key}")
        return [int(x) for x in re.findall(r"-?\d+", m.group(1))]

    n, m = scalar("numScenes"), scalar("numActors")
    flat = array("ia")
    if len(flat) != n * m:
        raise ValueError(f"{path}: ia has {len(flat)} values, expected {n * m}")
    plays = [flat[a * n:(a + 1) * n] for a in range(m)]
    name = os.path.splitext(os.path.basename(path))[0]
    return Instance(name, plays, array("c"), array("d"))


def save_dzn(inst, path, comment=None):
    lines = [f"% {line}" for line in comment.splitlines()] if comment else []
    lines.append(f"numScenes = {inst.n_scenes};")
    lines.append(f"numActors = {inst.n_actors};")
    lines.append("ia = [|")
    lines += [",".join(map(str, row)) + "|" for row in inst.plays]
    lines[-1] += "];"
    lines.append(f"c = [{','.join(map(str, inst.wage))}];")
    lines.append(f"d = [{','.join(map(str, inst.duration))}];")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
