import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from system_builder import *


#Levels
level1 = Level(name='S12', pop=[1,0])
level2 = Level(name='P12', L=1, kind='e')
level3 = Level(name='D32', J=3/2, L=2,pop=[0,0,0,0])
levels = [level1,level2,level3]

#Lasers
laser1 = Laser(Omega=1, L1='S12', L2='P12',k=[1,0,0], S=[1,0,0])
laser2 = Laser(Omega=1, L1='D32', L2='P12',k=[1,0,0], S=[1,0,0])
lasers = [laser1,laser2]

#Params
params = {}
params['Bdir'] = [0,0,1]
params['B'] = 0
tlist = np.linspace(0,10,1000)
params['tlist'] = tlist
params['mixed'] = False
params['zeeman'] = True

Ca40 = AtomSystem(levels,lasers,params)

result = Ca40.solve()
P_g = result.expect[0:level1.N]
P_e = result.expect[level1.N:level1.N+level2.N]
P_r = result.expect[level1.N+level2.N:level1.N+level2.N+level3.N]

plt.figure()
for P in P_g:
    plt.plot(tlist,P,label='g')
plt.figure()
for P in P_e:
    plt.plot(tlist,P,label='g')
plt.figure()
for P in P_r:
    plt.plot(tlist,P,label='g')
plt.show()
