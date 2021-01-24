import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from system_builder import *


#Levels
level1 = Level(name='S12', J=1/2, pop=[1,1])
level2 = Level(name='P12', J=1/2, L=1, kind='e')
level3 = Level(name='D32', J=3/2, L=2,pop=[0,0,0,0])
levels = [level1,level2,level3]

#Lasers
laser1 = Laser(Omega=1, L1='S12', L2='P12',k=[1,0,0], S=[1,0,1])
laser2 = Laser(Omega=0, L1='D32', L2='P12',k=[1,0,0], S=[1,0,0])
lasers = [laser1,laser2]

cavity = Cavity(g=1, L1='D32', L2='P12',k=[0,0,1], n=0)

#Params
params = {}
params['Bdir'] = [0,0,1]
params['B'] = 0
tlist = np.linspace(0,10,1000)
params['tlist'] = tlist
params['mixed'] = False
params['zeeman'] = True

Ca40 = AtomSystem(levels,lasers,params,cavity=cavity)

result = Ca40.solve()
P_g = result.expect[0:level1.N]
P_e = result.expect[level1.N:level1.N+level2.N]
P_r = result.expect[level1.N+level2.N:level1.N+level2.N+level3.N]
P_c = result.expect[-1]

plt.figure()
for P in P_g:
    plt.plot(tlist,P,label='g')
plt.figure()
for P in P_e:
    plt.plot(tlist,P,label='g')
plt.figure()
for P in P_r:
    plt.plot(tlist,P,label='g')
plt.figure()
plt.plot(tlist,P_c,label='g')
plt.show()
