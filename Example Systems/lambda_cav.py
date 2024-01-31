import qutip as qu
import matplotlib.pyplot as plt
from qobjects import Level, Laser, Cavity
from system_builder import AtomSystem
from systems import default_params
from H_funcs import gaussian


# Levels
level1 = Level(name="1", pop=[1])
level2 = Level(name="2", pop=[0])
level3 = Level(name="3", pop=[0])
levels = [level1, level2, level3]

# Lasers
gauss_args = {"sigma": 4, "mu": 10, "t_on": 0, "t_off": 20}

Omega = 1
Delta = 0
Delta_c = 5
laser1 = Laser(
    Omega=Omega, Delta=Delta, L1="1", L2="2", func="gaussian", args=gauss_args
)
lasers = [laser1]

cavity = Cavity(g=1, Delta=Delta_c, kappa=0.5, L1="3", L2="2", N=3, n=0)

# Params
params = default_params
params["t_max"] = 20
params["n_step"] = 200

atom = AtomSystem(levels, lasers, params, decays=[], cavities=[cavity])
result, e_ops = atom.solve()
eff = (
    2
    * cavity.kappa
    * sum(qu.expect(result.states, e_ops["n"]))
    * 100
    * (params["t_max"] / params["n_step"])
)
print(eff)
tlist = atom.tlist
laser_fn = gaussian(tlist, gauss_args)
plt.figure()
for label, op in e_ops.items():
    exp = qu.expect(result.states, op)
    plt.plot(tlist, exp, label=label)
plt.plot(tlist, laser_fn, label="laser")
plt.legend()
plt.show()
