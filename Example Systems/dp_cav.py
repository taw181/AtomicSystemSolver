import qutip as qu
import numpy as np
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Decay, Cavity
from system_builder import AtomSystem
from systems import default_params


# Levels
level2 = Level(name="2", L=1, J=0.5, S=0.5, pop=[0])
level3 = Level(name="3", L=2, J=1.5, S=0.5, pop=[0, 0, 0, 1])
levels = [level2, level3]


Omega = 0.5
Delta = 0
laser1 = Laser(Omega=0.5, Delta=0, L1="1", L2="2", k=0, S=[1, 0, 1])
laser2 = Laser(Omega=Omega, Delta=0, L1="2", L2="3", k=90, S=[-0.8, 0.2, 0])
lasers = []

decay12 = Decay("2", "1", 1)
decay23 = Decay("2", "3", 1)

decays = []

cavity = Cavity(g=1, Delta=0, kappa=0.0, L1="3", L2="2", N=3, n=1, modes=2)

# Params
params = default_params
params["t_max"] = 10
params["n_step"] = 200
params["zeeman"] = True
params["mixed"] = True
params["freq_scaling"] = 2 * np.pi * 15e6

atom = AtomSystem(levels, lasers, params, cavities=[cavity], decays=decays)
result, e_ops = atom.solve()
occ_D1 = qu.expect(atom.e_ops["3 $m_J=$-3/2"], result.states)
occ_D2 = qu.expect(atom.e_ops["3 $m_J=$-1/2"], result.states)
occ_D3 = qu.expect(atom.e_ops["3 $m_J=$1/2"], result.states)
occ_D4 = qu.expect(atom.e_ops["3 $m_J=$3/2"], result.states)
n = qu.expect(atom.e_ops["n"], result.states)
n2 = qu.expect(atom.e_ops["n2"], result.states)

tlist = atom.tlist
fig, axs = plt.subplots(nrows=2)
axs[0].plot(tlist, n)
axs[0].plot(tlist, n2)

for label in ["3 $m_J=$-3/2", "3 $m_J=$-1/2", "3 $m_J=$1/2", "3 $m_J=$3/2"]:
    o = qu.expect(atom.e_ops[label], result.states)
    axs[1].plot(tlist, o, label=label, alpha=0.5)
plt.legend()
plt.show()
