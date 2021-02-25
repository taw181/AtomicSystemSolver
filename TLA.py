import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from hamiltonian_builder import *
from systems import defaultParams

#Levels
level1 = Level(name='g', pop=[0])
level2 = Level(name='e', L=1, kind='e',pop=[1])
levels = [level1,level2]

#Lasers
laser1 = Laser(Omega=0, Delta = 0, L1='g', L2='e')
lasers = [laser1]

#Params
params = defaultParams
tlist = params['tlist']
params['Gammas']['ge'] = 1
TLA = AtomSystem(levels,lasers,params)
#
result = TLA.solve_eops()
P = result.expect

plt.figure()
for i in P:
    plt.plot(tlist,i)
plt.show()

