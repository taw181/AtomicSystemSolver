import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *
from hamiltonian_builder import *
from pulseshapes import gauss
from systems import defaultParams

#Levels
level1 = Level(name='S', J=1/2, pop=[1,0])
level2 = Level(name='P', J=1/2, L=1, kind='e')
level3 = Level(name='D', J=3/2, L=2,pop=[0,0,0,0])
levels = [level1,level2,level3]

#Lasers
laser1 = Laser(Omega=1, L1='S', L2='P', k=0, S=[0,0,-1], f=gauss)
laser2 = Laser(Omega=0, L1='D', L2='P',k=90.0, S=[1,1,1])
lasers = [laser1,laser2]

cavity = Cavity(g=1, kappa=1, L1='P', L2='D',k=0, n=0)

#Params
params = defaultParams
params['Bdir'] = [0,0,1]
params['B'] = 0.0
tlist = np.linspace(0,10,1000)
params['tlist'] = tlist
params['mixed'] = False
params['zeeman'] = True

Gamma_phys = 2*np.pi*21.57*1e6
params['Gamma_phys'] = Gamma_phys
params['Gammas'] = {}
params['Gammas']['SP'] = 0

tpulse = 5; wpulse = 1; pmax = 10
args={'tc': tpulse, 'w': wpulse,'pmax' : pmax}
params['args'] = args
# params['Gammas']['PS'] = pa
# params['Gammas']['PD'] = 2*np.pi*1.48*1e6

Ca40 = AtomSystem(levels,lasers,params,cavity=cavity)

result = Ca40.solve_eops_dict()

P_g = result['S']
P_e = result['P']
P_r = result['D']
P_c = result['cavity']

plt.figure()
for P in P_g:
    plt.plot(tlist,P)
plt.figure()
for P in P_e:
    plt.plot(tlist,P)
plt.figure()
for P in P_r:
    plt.plot(tlist,P)
plt.figure()
plt.plot(tlist,P_c)
plt.show()


# P_g = result.expect[0:level1.N]
# P_e = result.expect[level1.N:level1.N+level2.N]
# P_r = result.expect[level1.N+level2.N:level1.N+level2.N+level3.N]
# P_c = result.expect[-1]
#
# plt.figure()
# for P in P_g:
#     plt.plot(tlist,P,label='g')
# plt.figure()
# for P in P_e:
#     plt.plot(tlist,P,label='g')
# plt.figure()
# for P in P_r:
#     plt.plot(tlist,P,label='g')
# plt.figure()
# plt.plot(tlist,P_c,label='g')
# plt.show()
