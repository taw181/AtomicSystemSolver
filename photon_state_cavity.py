import qutip as qu
import numpy as np
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Decay, Cavity
from system_builder import AtomSystem
from systems import default_params

# Levels
level1 = Level(name="g", L=0, J=0.5, S=0.5, pop=[1])
level2 = Level(name="i", L=1, J=0.5, S=0.5, pop=[0])
level3 = Level(name="e", L=2, J=1.5, S=0.5, pop=[0])
levels = [level1, level2, level3]


Omega = 0
Delta = -3
laser1 = Laser(Omega=Omega, Delta=Delta, L1="g", L2="i")
lasers = [laser1]

cavity = Cavity(L1="e", L2="i", g=4, Delta=Delta, kappa=0.5, modes=1, n=1)

decay12 = Decay("g", "i", 0)
decay23 = Decay("e", "i", 0)


decays = [decay12, decay23]

# Params
params = default_params
params["t_max"] = 5
params["n_step"] = 100
params["zeeman"] = False


atom = AtomSystem(levels, lasers, params, decays=decays, cavities=[cavity])

result, e_ops = atom.solve()
# print(result.states[-1])
tlist = atom.tlist

plt.figure()
for label, op in e_ops.items():
    exp = qu.expect(result.states, op)
    plt.plot(tlist, exp, label=label)
plt.legend()
plt.show()


eff = (
    2
    * cavity.kappa
    * sum(qu.expect(result.states, e_ops["n"]))
    * 100
    * (params["t_max"] / params["n_step"])
)
print(eff)

g, i, e = atom.astates
proj_g = atom.projectors["g"][0]
proj_i = atom.projectors["i"][0]
proj_e = atom.projectors["e"][0]
Aops = atom.Aops
s1 = Aops["gi"][0]
s2 = Aops["ie"][0]
a = atom.a

# c1, c2 = atom.c_ops

ca = atom.c_ops[-1]

H = atom.H
K = qu.liouvillian(atom.H) # - qu.to_super(ca)
# Kt = qu.liouvillian(atom.HL_t[0][0])
# K = [K0, [Kt, gaussian]]
K = atom.H
rhototal = [[0 for _ in tlist] for _ in tlist]
result = qu.mesolve(K, atom.rho0, tlist)
rho_pre_emission = result.states
psi_cav_0 = cavity.states[0]
proj_0 = qu.tensor(g, qu.basis(2,0)).proj()
# print(proj_0)
# print(rho_pre_emission[0])
# print(ca*rho_pre_emission[0])

for tL in range(len(tlist)):
    result = qu.mesolve(K, a * rho_pre_emission[tL], tlist[tL:], c_ops=[])
    rho_post_tL = result.states
    for tR in range(tL, len(tlist)):
        n = tR - tL
        result = qu.mesolve(K, rho_post_tL[n] * a.dag(), tlist[tR:], c_ops=[])
        rhofinal = result.states[-1]
        matelement = qu.expect(proj_0, rhofinal)
        rhototal[tR][tL] = np.conjugate(matelement)
        rhototal[tL][tR] = matelement

diagonal = np.diagonal(rhototal)
P1 = np.trapz(diagonal, tlist)
print(P1)
Purity = np.trapz(
    [np.trapz(np.square(rhototal[row]), tlist) for row in range(len(tlist))], tlist
) / (P1**2)
print(Purity)
