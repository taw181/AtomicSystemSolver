#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 14:43:07 2020

@author: tom
"""
import qutip as qu
import numpy as np
import qutipfuncs as quf
from fractions import Fraction
import time
from qobjects import Level, Laser, Decay, Cavity
from H_funcs import funcs, func_generator


def build_system_from_dict(system_dict):
    levels = []
    for v in system_dict["levels"].values():
        levels.append(Level(**v))
    lasers = []
    for v in system_dict["lasers"]:
        lasers.append(Laser(**v))
    decays = []
    for v in system_dict["decays"]:
        decays.append(Decay(**v))
    cavities = [None]
    for v in system_dict["cavities"]:
        cavities = [Cavity(**v)]
    try:
        atom_system = AtomSystem(
            levels, lasers, decays, system_dict["params"], cavities
        )
        return atom_system
    except Exception as e:
        print("Failed to build system")
        print(e)


class AtomSystem:
    def __init__(self, levels, lasers, decays, params, cavities):
        qu.settings.auto_tidyup = True
        qu.settings.auto_tidyup_atol = 1e-10
        t0 = time.time()
        self.params = params
        self.levels = levels
        self.cavity = cavities[0]
        self.lasers = lasers
        self.decays = decays
        self.result = None
        self.Bdir = [0, 0, 1]
        # self.tlist = np.linspace(0,params['tmax'],params['steps'])
        self._atom()
        self._transitions()
        if self.cavity:
            self._cavity()

        self._Bfield()
        # for laser in lasers:
        #     quf.pol(laser,self.params['Bdir'])
        self._interactions()
        self._hamiltonian()
        self._decays()
        t = time.time() - t0
        print("Time to build system: {}".format(round(t, 5)))

    def _atom(self):
        levels = self.levels
        self.astates = []
        self.projectors = {}
        if not self.params["zeeman"]:
            for level in levels:
                level.J = 0
        self.Nat = sum([i.N for i in levels])
        n = 0
        for level in levels:
            states = [qu.basis(self.Nat, i) for i in n + np.arange(level.N)]
            # if self.cavity:
            #     N = self.cavity.N
            #     states = [qu.tensor(astate,qu.qeye(N)) for astate in states]
            level.states = states
            self.projectors[level.name] = [i * i.dag() for i in states]
            n += level.N
        self.Iat = qu.qeye(self.Nat)

    def _cavity(self):
        cavity = self.cavity
        N = cavity.N
        self.Ic = qu.qeye(N)
        for key in self.projectors.keys():
            self.projectors[key] = [
                qu.tensor(proj, qu.qeye(N)) for proj in self.projectors[key]
            ]
        for key in self.Aops.keys():
            self.Aops[key] = [qu.tensor(Aop, qu.qeye(N)) for Aop in self.Aops[key]]
        self.a = qu.tensor(self.Iat, qu.destroy(N))
        self.ad = self.a.dag()

    def _Bfield(self):
        self.HB = 0
        for level in self.levels:
            if level.J != 0:
                scaling_factor = self.params["freq_scaling"]
                w = quf.zeemanFS(level.J, level.S, level.L, 1e-4, scaling_factor)
                for i, m in enumerate(level.M):
                    self.HB += self.projectors[level.name][i] * m * w * self.params["B"]

    def _transitions(self):
        levels = self.levels
        self.Aops = {}
        for p, level_g in enumerate(levels):
            Jg = level_g.J
            states_g = level_g.states
            for q, level_e in enumerate(levels):
                if level_e.name != level_g.name:
                    Je = level_e.J
                    states_e = level_e.states
                    if abs(Jg - Je) <= 1 or not self.params["zeeman"]:
                        name = level_g.name + level_e.name
                        if level_g.J != 0:
                            self.Aops[name] = [
                                sum(
                                    [
                                        states_g[i]
                                        * states_e[j].dag()
                                        * qu.clebsch(
                                            Jg, 1, Je, level_g.M[i], k, level_e.M[j]
                                        )
                                        for i in range(level_g.N)
                                        for j in range(level_e.N)
                                    ]
                                )
                                for k in [-1, 0, 1]
                            ]
                        else:
                            self.Aops[name] = [
                                sum(
                                    [
                                        states_g[i] * states_e[j].dag()
                                        for i in range(level_g.N)
                                        for j in range(level_e.N)
                                    ]
                                )
                            ]

    def _interactions(self):
        cavity = self.cavity
        self.HL_0 = []
        self.HL_t = []
        for laser in self.lasers:
            name = laser.name
            if self.params["zeeman"]:
                pol_at = quf.pol(laser, self.Bdir)
                HL = sum(
                    [
                        pol_at[i] * self.Aops[name][i]
                        for i in range(len(self.Aops[name]))
                    ]
                )
            else:
                HL = sum(self.Aops[name])
            # H = laser.Omega * HL + np.conj(laser.Omega) * HL.dag() ## for allowing a laser phase
            HL_0 = laser.Omega * (HL + HL.dag())
            if laser.func:
                print(laser.name)
                print(laser.func)
                HL_func = func_generator(funcs[laser.func], laser.name)
                self.HL_t.append([HL_0, HL_func])
                # self.HL_t.append([HL_0, lambda t, args: funcs[f](t, args, name=n)])
            else:
                self.HL_0.append(HL_0)
        # self.HL = sum(self.HL)
        if self.cavity:
            name = self.cavity.name
            if self.params["zeeman"]:
                pol_c = quf.pol(cavity, self.Bdir)
                Hc = sum(
                    [pol_c[i] * self.Aops[name][i] for i in range(len(self.Aops[name]))]
                )
            else:
                Hc = sum(self.Aops[name])
            self.Hc = cavity.g * self.ad * Hc + np.conj(cavity.g) * self.a * Hc.dag()

    def _hamiltonian(self):
        H0 = []
        for laser in self.lasers:
            name = laser.L1
            proj = sum(self.projectors[name])
            H0.append(laser.Delta * proj)
        if self.cavity:
            name = self.cavity.name
            dL = 0
            for laser in self.lasers:
                if laser.name == name:
                    dL = laser.Delta
            H0.append((self.cavity.Delta - dL) * self.ad * self.a)
        self.H0 = sum(H0)

        # if self.params['tdep']:
        #     self.H = [self.H0,[self.HL,params['pulseshape']]]
        # else:
        #     self.H = self.H0 + self.HL
        self.H = self.H0 + sum(self.HL_0) + self.HB
        if self.cavity:
            self.H += self.Hc

    def _decays(self):
        self.c_ops = []
        for decay in self.decays:
            name = decay.name
            for Aop in self.Aops[name]:
                c_op = np.sqrt(decay.gamma) * Aop
                self.c_ops.append(c_op)
        if self.cavity:
            name = self.cavity.name
            c_op = np.sqrt(self.cavity.kappa) * self.a
            self.c_ops.append(c_op)

    def solve(self):
        t0 = time.time()
        tlist = np.linspace(0, self.params["t_max"], self.params["n_step"])
        levels = self.levels
        if self.params["mixed"]:
            self.rho0 = sum(
                [
                    level.pop[i] * qu.ket2dm(level.states[i])
                    for level in levels
                    for i in range(len(level.pop))
                ]
            )
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0, qu.ket2dm(self.cavity.psi0))
        else:
            self.rho0 = sum(
                [
                    level.pop[i] * level.states[i]
                    for level in levels
                    for i in range(len(level.pop))
                ]
            )
            if self.cavity:
                self.rho0 = qu.tensor(self.rho0, self.cavity.psi0)

            self.rho0 = self.rho0.unit()

        options = qu.Options(store_states=True)
        self.args = {}
        for laser in self.lasers:
            if laser.func:
                self.args.update(laser.args)
        self.result = qu.mesolve(
            [self.H, *self.HL_t],
            self.rho0,
            tlist,
            c_ops=self.c_ops,
            options=options,
            args=self.args,
        )

        self.e_ops = {}
        for key, lst in self.projectors.items():
            if self.params["zeeman"]:
                for i, op in enumerate(lst):
                    for level in levels:
                        if level.name == key:
                            M_dec = str(level.M[i])
                            M_frac = Fraction(M_dec)
                            M_frac = "{}/{}".format(
                                M_frac.numerator, M_frac.denominator
                            )
                            new_key = key + " $m_J=$" + M_frac
                    self.e_ops[new_key] = op
            else:
                self.e_ops[key] = lst[0]
        if self.cavity:
            self.e_ops["n"] = self.ad * self.a
        t = time.time() - t0
        print("Time to solve system: {}".format(round(t, 5)))
        return self.result, self.e_ops
