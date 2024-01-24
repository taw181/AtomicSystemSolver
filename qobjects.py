#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:38:54 2020

@author: tom
"""
import numpy as np
import qutip as qu
import qutipfuncs as qf
from H_funcs import default_args


def _pol_from_stokes(S):
    ep, em = qf.Stokes2EpEm(*S)
    return [ep, 0, em]


def _k_from_angle(angle):
    angle = np.radians(angle)
    kx = np.sin(angle)
    ky = 0
    kz = np.cos(angle)
    return [kx, ky, kz]


class Level:
    def __init__(self, name="LJ", J=0, S=0.5, L=0, pop=0, energy=0, system=None):
        self.name = name
        self._J = J
        self.S = S
        self.L = L
        self.update_states()
        self.system = system
        self._pop = pop
        if isinstance(pop, (int, float)):
            self._pop = [pop] * self.N

    @property
    def J(self):
        return self._J

    @J.setter
    def J(self, new_J):
        self._J = new_J
        self.update_states()

    def update_states(self):
        self.N = int(2 * self.J + 1)
        self.M = np.arange(-self.J, self.J + 1)
        self.states = [qu.basis(self.N, i) for i in range(self.N)]

    @property
    def pop(self):
        return self._pop

    @pop.setter
    def pop(self, val):
        if isinstance(val, (int, float)):
            self._pop = [val] * self.N
        else:
            self._pop = val
        if self.system:
            self.system._rho()

    def create_dict(self):
        d = {"name": self.name, "J": self._J, "S": self.S, "L": self.L, "pop": self.pop}
        return d


class Coupling:
    def __init__(
        self,
        L1="1",
        L2="2",
        func=None,
        args=None,
        system=None,
    ):
        self.L1 = L1
        self.L2 = L2
        self.name = L1 + L2
        self.system = system
        self.func = func
        self.args = {}

        if func and not args:
            defaults = default_args[func]
            for key, v in defaults.items():
                self.args[self.name + key] = v
        elif args:
            for key, v in args.items():
                self.args[self.name + key] = v

    def create_dict(self):
        pass


class Laser(Coupling):
    def __init__(
        self,
        L1="1",
        L2="2",
        Omega=0,
        Delta=0,
        lw=0,
        k=0,
        S=None,
        func="",
        args=None,
        system=None,
    ):
        super().__init__(L1, L2, func, args, system)
        print(self.L1)
        print(self.L2)
        print(self.name)
        self._Omega = Omega
        self.Delta = Delta
        self.lw = lw
        if isinstance(k, (int, float)):
            self.k = _k_from_angle(k)
        else:
            self.k = k
        if S is None:
            self.S = [0, 0, 1]
        else:
            self.S = S
            for i in range(2):
                if self.S[i] > 1:
                    self.S[i] = 1
            self.S = np.array(self.S) / qf.norm(self.S)
        self.pol = _pol_from_stokes(self.S)

    @property
    def Omega(self):
        return self._Omega

    @Omega.setter
    def Omega(self, new_Omega):
        self._Omega = new_Omega
        if self.system:
            self.system._interactions()
            self.system._hamiltonian()

    @property
    def Delta(self):
        return self._Delta

    @Delta.setter
    def Delta(self, new_Delta):
        self._Delta = new_Delta
        if self.system:
            self.system._hamiltonian()

    def create_dict(self):
        d = {
            "L1": self.L1,
            "L2": self.L2,
            "Omega": self.Omega,
            "Delta": self.Detla,
            "lw": self.lw,
            "k": self.k,
            "S": self.S,
            "func": self.func,
            "args": self.args,
        }
        return d


class Decay(Coupling):
    def __init__(self, L1="1", L2="2", gamma=0, func=None, args=None, system=None):
        super().__init__(L1, L2, func, args, system)
        self._gamma = gamma

    @property
    def gamma(self):
        return self._gamma

    @gamma.setter
    def gamma(self, val):
        self._gamma = val
        if self.system:
            self.system._decays()

    def create_dict(self):
        d = {
            "L1": self.L1,
            "L2": self.L2,
            "gamma": self.gamma,
            "func": self.func,
            "args": self.args,
        }
        return d


class Cavity(Coupling):
    def __init__(
        self,
        L1="1",
        L2="2",
        g=0,
        kappa=0,
        Delta=0,
        N=2,
        n=0,
        n2=0,
        modes=2,
        k=0,
        pol=None,
        func=None,
        args=None,
        system=None,
    ):
        super().__init__(L1, L2, func, args, system)
        self._g = g
        self.kappa = kappa
        self.Delta = Delta
        if isinstance(k, (int, float)):
            self.k = _k_from_angle(k)
        else:
            self.k = k
        if pol is None:
            self.pol = [1, 0, 1]
        else:
            self.pol = pol
        self.N = N
        self.modes = modes
        self.states = [qu.basis(self.N, i) for i in range(self.N)]
        if modes == 1:
            self.psi0 = qu.basis(self.N, n)
        elif modes == 2:
            self.psi0 = qu.tensor(qu.basis(self.N, n), qu.basis(self.N, n2))

    @property
    def g(self):
        return self._g

    @g.setter
    def g(self, val):
        self._g = val
        if self.system:
            self.system._interactions()
            self.system._hamiltonian()

    @property
    def Delta(self):
        return self._Delta

    @Delta.setter
    def Delta(self, new_Delta):
        self._Delta = new_Delta
        if self.system:
            self.system._hamiltonian()

    def create_dict(self):
        d = {
            "L1": self.L1,
            "L2": self.L2,
            "g": self.Omega,
            "Delta": self.Detla,
            "kappa": self.kappa,
            "k": self.k,
            "pol": self.pol,
            "func": self.func,
            "args": self.args,
            "N": self.N,
            "n": self.n,
        }
        return d
