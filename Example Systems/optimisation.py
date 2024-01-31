import qutip as qu
import numpy as np
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Cavity, Decay
from system_builder import AtomSystem
from systems import default_params
from scipy.optimize import minimize
from H_funcs import gaussian

from bayes_opt import BayesianOptimization, SequentialDomainReductionTransformer

t_max = 10 / (2 * np.pi)
# Params
params = default_params
params["t_max"] = t_max
params["n_step"] = int(100 * t_max)

kappa = 0.5


# Levels
level1 = Level(name="1", pop=[1])
level2 = Level(name="2", pop=[0])
level3 = Level(name="3", pop=[0])
levels = [level1, level2, level3]

# Lasers
gauss_args = {"sigma": t_max / 5, "mu": t_max / 2, "t_on": 0, "t_off": t_max}


def phogun(Omega, Delta, Delta_c):
    laser1 = Laser(
        Omega=Omega, Delta=Delta, L1="1", L2="2", func="gaussian", args=gauss_args
    )
    lasers = [laser1]
    decay1 = Decay(gamma=20, L1="2", L2="1")
    decay2 = Decay(gamma=2, L1="2", L2="3")
    decays = [decay1, decay2]
    cavity = Cavity(g=1, Delta=Delta_c, kappa=kappa, L1="3", L2="2", N=3, n=0)

    atom = AtomSystem(levels, lasers, params, decays=decays, cavities=[cavity])
    result, e_ops = atom.solve()

    return result, e_ops, atom


def phogun_eff(Omega, Delta, Delta_c):
    result, e_ops, atom = phogun(Omega, Delta, Delta_c)
    eff = (
        2
        * kappa
        * sum(qu.expect(result.states, e_ops["n"]))
        * 100
        * (params["t_max"] / params["n_step"])
    )
    return eff


def phogun_eff_array(x):
    Omega, Delta, Delta_c = x
    result, e_ops, atom = phogun(Omega, Delta, Delta_c)
    eff = (
        2
        * kappa
        * sum(qu.expect(result.states, e_ops["n"]))
        * 100
        * (params["t_max"] / params["n_step"])
    )
    return -eff


def phogun_eff_delt(Delta):
    return phogun_eff(1, Delta, -10)


# Bounded region of parameter space
pbounds = {"Omega": (0, 10), "Delta": (-50, 0), "Delta_c": (-50, 0)}

bounds_transformer = SequentialDomainReductionTransformer(minimum_window=0.5)

optimizer = BayesianOptimization(
    f=phogun_eff,
    pbounds=pbounds,
    random_state=1,
    # bounds_transformer=bounds_transformer
)
optimizer.maximize(
    init_points=2,
    n_iter=20,
)

print(optimizer.max)

Omega_opt = optimizer.max["params"]["Omega"]
Delta_opt = optimizer.max["params"]["Delta"]
Delta_c_opt = optimizer.max["params"]["Delta_c"]

result, e_ops, atom = phogun(Omega_opt, Delta_opt, Delta_c_opt)
tlist = atom.tlist
laser_fn = gaussian(tlist, gauss_args)
plt.figure()
for label, op in e_ops.items():
    exp = qu.expect(result.states, op)
    plt.plot(tlist, exp, label=label)
plt.plot(tlist, laser_fn, label="laser")
plt.legend()

Omegas = []
Deltas = []
Delta_cs = []
for i, res in enumerate(optimizer.res):
    Omega = res["params"]["Omega"]
    Delta = res["params"]["Delta"]
    Delta_c = res["params"]["Delta_c"]
    Omegas.append(Omega)
    Deltas.append(Delta)
    Delta_cs.append(Delta_c)

fig, axs = plt.subplots(nrows=3)
axs[0].plot(Omegas)
axs[1].plot(Deltas)
axs[2].plot(Delta_cs)
plt.show()

# pbounds = {'Delta': (-50, 0)}

# optimizer = BayesianOptimization(
#     f=phogun_eff_delt,
#     pbounds=pbounds,
#     random_state=1,
#     # bounds_transformer=bounds_transformer
# )
# optimizer.maximize(
#     init_points=2,
#     n_iter=50,
# )

# Deltas = []
# for i, res in enumerate(optimizer.res):
#     Delta = res['params']['Delta']
#     Deltas.append(Delta)
# plt.figure()
# plt.plot(Deltas)
# plt.show()

p = minimize(phogun_eff_array, [1, 25, 50])

print(p["x"])
