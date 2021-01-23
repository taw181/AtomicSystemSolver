import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from system_builder import *


#Levels
level1 = Level(name='g', pop=[1])
level2 = Level(name='e', L=1, kind='e',pop=[0])
levels = [level1,level2]

#Lasers
laser1 = Laser(Omega=1, L1='g', L2='e')
lasers = [laser1]

#Params
params = {}
params['Bdir'] = [0,0,1]
params['B'] = 0
tlist = np.linspace(0,10,99)
params['tlist'] = tlist
params['mixed'] = False
params['zeeman'] = False

TLA = AtomSystem(levels,lasers,params)

result = TLA.solve()
P = result.expect

plt.figure()
for i in P:
    plt.plot(tlist,i)
plt.show()
