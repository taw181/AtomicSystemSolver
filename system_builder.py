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
from fractions import Fraction


class AtomSystem:

    def __init__(self,levels,lasers,params,cavity=None):
        self.params = params
        self.levels = levels
        self.cavity = cavity
        self.lasers = lasers
        self.result = None
        self.Bdir = [0, 0, 1]
        # self.tlist = np.linspace(0,params['tmax'],params['steps'])
        self._atom()
        self._transitions()
        if cavity:
            self._cavity(cavity)

        self._Bfield()
        # for laser in lasers:
        #     quf.pol(laser,self.params['Bdir'])
        self._interactions()
        self._hamiltonian()
        #self._solve(levels)

    def _atom(self):
        levels = self.levels
        self.astates=[]
        self.projectors={}
        if not self.params['zeeman']:
            for level in levels:
                level.J = 0
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

    def _cavity(self, cavity):
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

    def _Bfield(self):
        self.HB = 0
        for level in self.levels:
            if level.J != 0:
                scaling_factor = 2*np.pi*21.57*1e6
                w = quf.zeemanFS(level.J,level.S,level.L,1E-4,scaling_factor)
                for i,m in enumerate(level.M):
                    self.HB += self.projectors[level.name][i]*m*w*self.params['B']

    def _transitions(self):
        levels = self.levels
        self.Aops = {}
        for p, level_g in enumerate(levels):
            Jg = level_g.J
            states_g = level_g.states
            for q,level_e in enumerate(levels):
                if level_e.name != level_g.name:
                    Je = level_e.J
                    states_e = level_e.states
                    if abs(Jg - Je) <= 1 or not self.params['zeeman']:
                        name = level_g.name + level_e.name
                        if level_g.J != 0:
                            self.Aops[name] = [sum([states_g[i]*states_e[j].dag()*qu.clebsch(Jg,1,Je,level_g.M[i],k,level_e.M[j]) for i in range(level_g.N) for j in range(level_e.N)]) for k in [-1,0,1]]
                        else:
                            self.Aops[name] = [sum([states_g[i]*states_e[j].dag() for i in range(level_g.N) for j in range(level_e.N)])]

    def _interactions(self):
        levels, lasers, cavity = self.levels, self.lasers, self.cavity
        self.HL = []
        for laser in self.lasers:
            name = laser.name
            if self.params['zeeman']:
                pol_at = quf.pol(laser, self.Bdir)
                HL = sum([pol_at[i]*self.Aops[name][i] for i in range(len(self.Aops[name]))])
            else:
                HL = sum(self.Aops[name])
            self.HL.append(laser.Omega * HL + np.conj(laser.Omega ) *HL.dag())
        self.HL = sum(self.HL)
        if self.cavity:
            name = self.cavity.name
            if self.params['zeeman']:
                pol_c = quf.pol(cavity,self.Bdir)
                Hc = sum([pol_c[i]*self.Aops[name][i] for i in range(len(self.Aops[name]))])
            else:
                Hc = sum(self.Aops[name])
            self.Hc = cavity.g * self.ad * Hc + np.conj(cavity.g) * self.a * Hc.dag()


    def _hamiltonian(self):
        H0 = []
        for laser in self.lasers:
            name = laser.L1
            proj = sum(self.projectors[name])
            H0.append(laser.Delta*proj)
        if self.cavity:
            name = self.cavity.name
            dL = 0
            for laser in self.lasers:
                if laser.name == name:
                    dL = laser.Delta
            H0.append((self.cavity.Delta - dL)*self.ad*self.a)
        self.H0 = sum(H0)

        # if self.params['tdep']:
        #     self.H = [self.H0,[self.HL,params['pulseshape']]]
        # else:
        #     self.H = self.H0 + self.HL
        self.H = self.H0 + self.HL + self.HB
        if self.cavity:
            self.H += self.Hc


    def solve(self):
        tlist = np.linspace(0, self.params["t_max"], self.params["n_step"])
        levels = self.levels
        if not self.params['mixed']:
            self.rho0 = sum([level.pop[i]*qu.ket2dm(level.states[i]) for level in levels for i in range(len(level.pop))])
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0,self.cavity.psi0)
        else:
            self.rho0 = sum([level.pop[i]*level.states[i] for level in levels for i in range(len(level.pop))])
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0,qu.ket2dm(self.cavity.psi0))
        # C_spon = np.sqrt(params['gamma'])*self.sm
        # C_lw_g = np.sqrt(LW)*proj_g
        # C_lw_e = np.sqrt(LW)*proj_e
        # self.c_ops = [C_spon]
        tlist = self.params['tlist']
        options = qu.Options(store_states=True)
        self.result = qu.mesolve(self.H, self.rho0, tlist, options=options)
        
        self.e_ops = {}
        for key, lst in self.projectors.items():
            if self.params['zeeman']:
                for i, op in enumerate(lst):
                    for level in levels:
                        if level.name == key:
                            M_dec = str(level.M[i])
                            M_frac = Fraction(M_dec)
                            M_frac = '{}/{}'.format(M_frac.numerator, M_frac.denominator)
                            new_key = key + ' $m_J=$' + M_frac
                    self.e_ops[new_key] = op
            else:
                self.e_ops[key] = lst[0]
        if self.cavity:
            self.e_ops['n'] = (self.ad*self.a)
        return self.result, self.e_ops