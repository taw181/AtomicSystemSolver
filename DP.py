import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Decay
from system_builder import AtomSystem
from systems import default_params
from scipy.optimize import curve_fit


def gaussian(x, mu, sigma, A, c):
    return c - A * np.exp(-(((x - mu) / sigma) ** 2))


def lorentzian(x, mu, sigma, A, c):
    return c - A / ((x - mu) ** 2 + sigma**2)


# Levels
level1 = Level(name="1", L=0, J=0.5, S=0.5, pop=[0])
level2 = Level(name="2", L=1, J=0.5, S=0.5, pop=[0])
level3 = Level(name="3", L=2, J=1.5, S=0.5, pop=[0.25, 0.25, 0.25, 0.25])
levels = [level1, level2, level3]


Omega = 0.5
Delta = 0
laser1 = Laser(Omega=0.5, Delta=-1, L1="1", L2="2", k=0, S=[1, 0, 1])
laser2 = Laser(Omega=Omega, Delta=0, L1="2", L2="3", k=90, S=[-0.8, 0.2, 0])
lasers = [laser1, laser2]

decay12 = Decay("2", "1", 1)
decay23 = Decay("2", "3", 1)

decays = [decay12, decay23]

# Params
params = default_params
params["t_max"] = 100
params["n_step"] = 200
params["zeeman"] = True
params["mixed"] = True
params["freq_scaling"] = 2 * np.pi * 15e6

Blist = np.linspace(0, 2.5, 50)
B2list = np.linspace(0, 0.5, 10)
fl = np.zeros_like(Blist)
occ_D1 = np.zeros_like(Blist)
occ_D2 = np.zeros_like(Blist)
occ_D3 = np.zeros_like(Blist)
occ_D4 = np.zeros_like(Blist)
mulist = []
sigmalist = []

for j, B2 in enumerate(B2list):
    for i, B in enumerate(Blist):
        Bdir = [0, B2, B - 1.1]
        norm = quf.norm(Bdir)
        params["B"] = norm
        params["Bdir"] = [b / norm for b in Bdir]
        atom = AtomSystem(levels, lasers, params, decays=decays)
        result, e_ops = atom.solve()
        fl[i] = qu.expect(atom.e_ops["2 $m_J=$1/2"], result.states[-1]) + qu.expect(
            atom.e_ops["2 $m_J=$-1/2"], result.states[-1]
        )
        occ_D1[i] = qu.expect(atom.e_ops["3 $m_J=$-3/2"], result.states[-1])
        occ_D2[i] = qu.expect(atom.e_ops["3 $m_J=$-1/2"], result.states[-1])
        occ_D3[i] = qu.expect(atom.e_ops["3 $m_J=$1/2"], result.states[-1])
        occ_D4[i] = qu.expect(atom.e_ops["3 $m_J=$3/2"], result.states[-1])
    p0 = [1.1, 0.5, max(fl) - min(fl), max(fl)]

    plt.figure()
    plt.plot(Blist, fl)
    try:
        p, cov = curve_fit(lorentzian, Blist, fl, p0)
        mulist.append(p[0])
        sigmalist.append(p[1])
        plt.plot(Blist, lorentzian(Blist, *p))
    except Exception as e:
        mulist.append(None)
        sigmalist.append(None)
        print(e)

plt.figure()
plt.plot(B2list, mulist)

plt.figure()
plt.plot(B2list, sigmalist)

plt.show()
# plt.figure()
# plt.plot(Blist, fl)
# plt.plot(Blist, occ_D1)
# plt.plot(Blist, occ_D2)
# plt.plot(Blist, occ_D3)
# plt.plot(Blist, occ_D4)
# plt.show()
