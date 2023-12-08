from copy import deepcopy
import json
import numpy as np

default_params = {
    "freq_scaling": 2 * np.pi * 21e6,
    # "tlist": np.linspace(0, 10, 1000).tolist(),
    "B": 0,
    "zeeman": False,
    "mixed": True,
    "t_start": 0,
    "t_max": 5,
    "n_step": 100,
}

default_level = {"name": "g", "S": 0, "L": 0, "J": 0, "pop": [1], "energy": 0}

default_laser = {
    "L1": "1",
    "L2": "2",
    "Omega": 1.0,
    "Delta": 0.0,
    "k": 0,
    "S": [1, 1, 1],
    "lw": 0,
}

default_cavity = {
    "L1": "1",
    "L2": "2",
    "g": 1.0,
    "Delta": 0.0,
    "k": 0,
    "pol": [1, 0, 1],
    "kappa": 0,
    "N": 2,
    "n": 0,
    "modes": 2,
}

default_decay = {
    "L1": "1",
    "L2": "2",
    "gamma": 1.0,
}

defaults_dict = {
    "levels": default_level,
    "lasers": default_laser,
    "params": default_params,
    "decays": default_decay,
    "cavities": default_cavity,
}
with open("defaults.json", "a") as default:
    json.dump(defaults_dict, default)


class AutoUpdateDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.callbacks = []

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def __setitem__(self, key, value):
        if self.get(key) != value:
            super().__setitem__(key, value)
            for callback in self.callbacks:
                callback(key, value)


def add_level(d0, d1):
    d = deepcopy(default_level)
    d.update(d1)
    d0[d1["name"]] = d


def add_laser(l0, d1):
    d = deepcopy(default_laser)
    d.update(d1)
    l0.append(d)


def add_cavity(l0, d1):
    d = deepcopy(default_cavity)
    d.update(d1)
    l0.append(d)


sysdict = {}

""" TLA """
levels = {}

g = {"name": "g", "S": 0, "L": 1, "J": 0, "pop": [0]}

e = {"name": "e", "S": 0, "L": 1, "J": 0, "pop": [1], "energy": 1}

add_level(levels, g)
add_level(levels, e)

lasers = []
l1 = {"L1": "g", "L2": "e", "Omega": 1.0, "Delta": 0.5}
add_laser(lasers, l1)
params = default_params

sysdict["TLA"] = {
    "levels": levels,
    "lasers": lasers,
    "params": params,
    "decays": [],
    "cavities": [],
}

""" TLA with decay """
TLA_spon = deepcopy(sysdict["TLA"])
decays = []
decay = {
    "L1": "e",
    "L2": "g",
    "gamma": 1.0,
}
decays.append(decay)
TLA_spon["decays"] = decays
sysdict["TLA_spon"] = TLA_spon

""" TLA with cavity """
TLA_c = deepcopy(sysdict["TLA"])
cavities = []
cavity = {
    "L1": "g",
    "L2": "e",
}
add_cavity(cavities, cavity)
TLA_c["cavities"] = cavities
sysdict["TLA_c"] = TLA_c

""" Lambda """
levels = {}
level = {
    "name": "1",
    "S": 0.5,
    "L": 0,
    "J": 0.5,
    "pop": [0],
    "energy": 0
}
add_level(levels, level)
level = {
    "name": "2",
    "S": 0.5,
    "L": 1,
    "J": 0.5,
    "pop": [1],
    "energy": 2
}
add_level(levels, level)
level = {"name": "3", "S": 0.5, "L": 2, "J": 1.5, "pop": [0], "energy": 0.5}
add_level(levels, level)

lasers = []
laser = {"L1": "1", "L2": "2", "Omega": 1.0, "Delta": 0.5}
add_laser(lasers, laser)
laser = {"L1": "3", "L2": "2", "Omega": 0.5, "Delta": 0.0}
add_laser(lasers, laser)

params = default_params

sysdict["Lambda"] = {
    "levels": levels,
    "lasers": lasers,
    "params": params,
    "decays": [],
    "cavities": [],
}

with open("systems.json", "r+") as systems:
    file_store = json.load(systems)

file_store.update(sysdict)

with open("systems.json", "w") as systems:
    json.dump(file_store, systems)
