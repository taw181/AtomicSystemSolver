#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 14:43:07 2020

@author: tom
"""
import qutip as qu
import numpy as np
import qutipfuncs as quf
import matplotlib.pyplot as plt
from qobjects import *


class AtomSystem:
      
    def __init__(self,levels,lasers,params):
        self.params = params   
        self.levels = levels
        # self.tlist = np.linspace(0,params['tmax'],params['steps'])
        self._atom(levels)
        self._Bfield(levels,params)
        # if cavity:
        #     self._cavity(cavity)
        self._transitions(levels)
        # for laser in lasers:
        #     quf.pol(laser,self.params['Bdir'])
        self._interactions(levels,lasers)
        self._hamiltonian(levels,lasers)
        #self._solve(levels)
        
    def _atom(self,levels):
        self.astates=[]
        self.projectors={}
        self.Nat = sum([i.N for i in levels])
        n=0
        for level in levels:
            states = [qu.basis(self.Nat,i) for i in n+np.arange(level.N)]
            level.states = states
            self.projectors[level.name] = [i*i.dag() for i in states]
            n+=level.N
            
    def _cavity(self,cavity):
        states = cavity
            
    def _Bfield(self,levels,params):
        self.HB = 0
        for level in levels:
            if level.J != 0:
                lw = 2*np.pi*21.57*1e6
                w = quf.zeemanFS(level.J,level.S,level.L,1E-4,lw) 
                for i,m in enumerate(level.M):
                    self.HB += self.projectors[level.name][i]*m*w*params['B']

    def _transitions(self,levels):
        self.Aops = {}
        for p,level_g in enumerate(levels):
            Jg = level_g.J
            states_g = level_g.states
            if level_g.kind == 'g':
                for q,level_e in enumerate(levels):
                    Je = level_e.J
                    states_e = level_e.states
                    if level_e.kind == 'e' and abs(Jg - Je) <= 1:
                        name = level_g.name + level_e.name
                        if level_g.J != 0:
                            self.Aops[name] = [sum([states_g[i]*states_e[j].dag()*qu.clebsch(Jg,1,Je,level_g.M[i],k,level_e.M[j]) for i in range(level_g.N) for j in range(level_e.N)]) for k in [-1,0,1]]
                        else:
                            self.Aops[name] = [sum([states_g[i]*states_e[j].dag() for i in range(level_g.N) for j in range(level_e.N)])]
    
    def _interactions(self,levels,lasers):
        self.HL = []
        for laser in lasers:
            name = laser.name
            pol_at = quf.pol(laser,params['Bdir'])
            if self.params['zeeman']:
                HL = sum([pol_at[i]*self.Aops[name][i] for i in range(len(self.Aops[name]))])
            else:
                HL = sum(self.Aops[name])
            self.HL.append(laser.Omega * HL + np.conj(laser.Omega)*HL.dag())
        self.HL = sum(self.HL)
    
    def _hamiltonian(self,levels,lasers):
        self.H0 = qu.Qobj(np.zeros([self.Nat,self.Nat]))
        
        # if self.params['tdep']:
        #     self.H = [self.H0,[self.HL,params['pulseshape']]]
        # else:
        #     self.H = self.H0 + self.HL
        self.H = self.H0 + self.HL + self.HB

# H =   Omega * (sm + sm.dag())
    def _solve(self):
        levels = self.levels
        if params['mixed']:
            self.rho0 = sum([level.pop[i]*qu.ket2dm(level.states[i]) for level in levels for i in range(len(level.pop))])
        else:
            self.rho0 = qu.ket2dm(sum([level.pop[i]*level.states[i] for level in levels for i in range(len(level.pop))]).unit())
        # print(self.rho0)
        self.e_ops = []
        for i in self.projectors.values():
            self.e_ops += i
        # C_spon = np.sqrt(params['gamma'])*self.sm
        # C_lw_g = np.sqrt(LW)*proj_g
        # C_lw_e = np.sqrt(LW)*proj_e
        # self.c_ops = [C_spon]
        tlist = self.params['tlist']
        self.result = qu.mesolve(self.H,self.rho0,tlist,e_ops = self.e_ops)
       
level1 = Level(name='S12', pop=[1,0])
level2 = Level(name='P12', L=1, kind='e')
level3 = Level(name='D32', J=3/2, L=2,pop=[0,-1,0,0])
level4 = Level(name='P32', J = 3/2, L=1, kind='e')
levels = [level1,level2,level3]
level1 = Level(name='1', J=0, L=0, S=0, pop=[1])
level2 = Level(name='2', J=0, L=0, S=0, kind='e')
level3 = Level(name='3', J=0, L=0, S=0, pop=[0])
levels = [level1,level2,level3]
laser1 = Laser(Omega=1, L1='1', L2='2',k=[1,0,0], S=[1,0,0])
laser2 = Laser(Omega=0, L1='3', L2='2',k=[1,0,0], S=[1,0,0])
lasers = [laser1,laser2]
params = {}
params['Bdir'] = [0,0,1]
params['B'] = 0
tlist = np.linspace(0,10,1000)
params['tlist'] = tlist
params['mixed'] = False
params['zeeman'] = False

A = AtomSystem(levels,lasers,params)
A._solve()
result = A.result
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