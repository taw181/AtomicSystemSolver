import qutip as qu
import numpy as np
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Decay
from system_builder import AtomSystem
from systems import default_params

# Levels
level1 = Level(name="1", L=0, J=0.5, S=0.5, pop=[1])
level2 = Level(name="2", L=1, J=0.5, S=0.5, pop=[0])
level3 = Level(name="3", L=2, J=1.5, S=0.5, pop=[0])
levels = [level1, level2, level3]


Omega = 1
Delta = 0
laser1 = Laser(Omega=1, Delta=Delta, L1="1", L2="2", k=0)
laser2 = Laser(Omega=0, Delta=10, L1="2", L2="3", k=0, S=[0, 0, -1])
lasers = [laser1, laser2]

decay12 = Decay("1", "2", 1)
decay23 = Decay("3", "2", 1)
decay21 = Decay("2", "1", 0)
decay32 = Decay("2", "3", 0)

decays = [decay12, decay23, decay21, decay32]

# Params
params = default_params
params["t_max"] = 200
params["n_step"] = 200
params["zeeman"] = True

Blist = np.linspace(-5e-6, 5e-6, 500)
fl = np.zeros_like(Blist)
for i, B in enumerate(Blist):
    params["B"] = B
    atom = AtomSystem(levels, lasers, params, decays=decays)
    H = atom.H
    c_ops = atom.c_ops
    result, e_ops = atom.solve()
    fl[i] = qu.expect(atom.e_ops["2 $m_J=$1/2"], result.states[-1]) + qu.expect(
        atom.e_ops["2 $m_J=$-1/2"], result.states[-1]
    )

plt.figure()
plt.plot(Blist, fl)
plt.show()
