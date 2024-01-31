import qutip as qu
import numpy as np
import matplotlib.pyplot as plt
from qobjects import Level, Laser
from system_builder import AtomSystem
from systems import default_params

import time

# Levels
level1 = Level(name="1", pop=[1])
level2 = Level(name="2", pop=[0])
levels = [level1, level2]

# Lasers
Omega = 1
Delta = 0
Delta_c = 5
laser1 = Laser(Omega=Omega, Delta=Delta, L1="1", L2="2")
lasers = [laser1]

# Params
params = default_params
params["t_max"] = 5
params["n_step"] = 200

Olist = np.linspace(0, 10, 10)
t0 = time.time()
for Omega in Olist:
    laser1 = Laser(Omega=Omega, Delta=0, L1="1", L2="2")
    lasers = [laser1]
    atom = AtomSystem(levels, lasers, params)
    result, e_ops = atom.solve()
t1 = time.time() - t0
print(round(t1, 5))

t0 = time.time()
laser1 = Laser(Omega=Omega, Delta=Delta, L1="1", L2="2")
lasers = [laser1]
atom = AtomSystem(levels, lasers, params)
for Omega in Olist:
    laser1.Omega = Omega
    result, e_ops = atom.solve()
t1 = time.time() - t0
print(round(t1, 5))

tlist = atom.tlist
plt.figure()
for label, op in e_ops.items():
    exp = qu.expect(result.states, op)
    plt.plot(tlist, exp, label=label)
plt.legend()
plt.show()
