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

    def __init__(self,levels,lasers,params,cavity=None):
        self.params = params
        self.levels = levels
        self.cavity = cavity
        self.result = None
        # self.tlist = np.linspace(0,params['tmax'],params['steps'])
        self._atom(levels)
        self._transitions(levels)
        if cavity:
            self._cavity(cavity)

        self._Bfield(levels,params)
        # for laser in lasers:
        #     quf.pol(laser,self.params['Bdir'])
        self._interactions(levels,lasers,cavity)
        self._hamiltonian(levels,lasers)
        #self._solve(levels)

    def _atom(self,levels):
        self.astates=[]
        self.projectors={}
        self.Nat = sum([i.N for i in levels])
        n=0
        for level in levels:
            states = [qu.basis(self.Nat,i) for i in n+np.arange(level.N)]
            # if self.cavity:
            #     N = self.cavity.N
            #     states = [qu.tensor(astate,qu.qeye(N)) for astate in states]
            level.states = states
            self.projectors[level.name] = [i*i.dag() for i in states]
            n+=level.N
        self.Iat = qu.qeye(self.Nat)

    def _cavity(self,cavity):
        N = cavity.N
        self.Ic = qu.qeye(N)
        # astates = [qu.tensor(astate,qu.qeye(N)) for astate in self.astates]
        # self.astates = astates
        for key in self.projectors.keys():
            self.projectors[key] = [qu.tensor(proj,qu.qeye(N)) for proj in self.projectors[key]]
        for key in self.Aops.keys():
            self.Aops[key] = [qu.tensor(Aop,qu.qeye(N)) for Aop in self.Aops[key]]
        # cstates = [qu.tensor(qu.qeye(self.Nat),cstate) for cstate in cavity.states]
        # self.cstates=cstates
        self.a = qu.tensor(self.Iat,qu.destroy(N))
        self.ad = self.a.dag()

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

    def _interactions(self,levels,lasers,cavity):
        self.HL = []
        for laser in lasers:
            name = laser.name
            if self.params['zeeman']:
                pol_at = quf.pol(laser,self.params['Bdir'])
                HL = sum([pol_at[i]*self.Aops[name][i] for i in range(len(self.Aops[name]))])
            else:
                HL = sum(self.Aops[name])
            self.HL.append(laser.Omega * HL + np.conj(laser.Omega)*HL.dag())
        self.HL = sum(self.HL)
        if self.cavity:
            name = cavity.name
            if self.params['zeeman']:
                pol_c = quf.pol(cavity,self.params['Bdir'])
                Hc = sum([pol_c[i]*self.Aops[name][i] for i in range(len(self.Aops[name]))])
            else:
                Hc = sum(self.Aops[name])
            self.Hc = cavity.g*self.ad*Hc + np.conj(cavity.g)*self.a*Hc.dag()


    def _hamiltonian(self,levels,lasers):
        self.H0 = qu.Qobj(np.zeros([self.Nat,self.Nat]))
        if self.cavity:
            self.H0 = qu.tensor(self.H0,self.Ic)

        # if self.params['tdep']:
        #     self.H = [self.H0,[self.HL,params['pulseshape']]]
        # else:
        #     self.H = self.H0 + self.HL
        self.H = self.H0 + self.HL + self.HB
        if self.cavity:
            self.H += self.Hc


# H =   Omega * (sm + sm.dag())
    def solve(self):
        levels = self.levels
        if self.params['mixed']:
            self.rho0 = sum([level.pop[i]*qu.ket2dm(level.states[i]) for level in levels for i in range(len(level.pop))])
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0,self.cavity.psi0)
        else:
            self.rho0 = qu.ket2dm(sum([level.pop[i]*level.states[i] for level in levels for i in range(len(level.pop))]).unit())
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0,qu.ket2dm(self.cavity.psi0))
        self.e_ops = []
        for i in self.projectors.values():
            self.e_ops += i
        if self.cavity:    
            self.e_ops.append(self.ad*self.a)
        # C_spon = np.sqrt(params['gamma'])*self.sm
        # C_lw_g = np.sqrt(LW)*proj_g
        # C_lw_e = np.sqrt(LW)*proj_e
        # self.c_ops = [C_spon]
        tlist = self.params['tlist']
        self.result = qu.mesolve(self.H,self.rho0,tlist,e_ops = self.e_ops)
        return self.result
