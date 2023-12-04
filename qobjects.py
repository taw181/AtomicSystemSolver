#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:38:54 2020

@author: tom
"""
import numpy as np
import qutip as qu
import qutipfuncs as qf


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
    def __init__(self, name="LJ", J=0, S=1 / 2, L=0, pop=0, energy=0):
        self.name = name
        self._J = J
        self.S = S
        self.L = L
        self.update_states()
        self.pop = pop
        if pop == 0:
            self.pop = [0] * self.N

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


class Laser:
    def __init__(self, L1="1", L2="2", Omega=0, Delta=0, lw=0, k=0, S=None):
        self.L1 = L1
        self.L2 = L2
        self.name = L1 + L2
        self.Omega = Omega
        self.Delta = Delta
        self.lw = lw
        if type(k) is int or type(k) is float:
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


class Decay:
    def __init__(self, L1="1", L2="2", gamma=0):
        self.L1 = L1
        self.L2 = L2
        self.name = L1 + L2
        self.gamma = gamma


class Cavity:
    def __init__(
        self, L1="1", L2="2", g=0, kappa=0, Delta=0, N=2, n=0, modes="2", k=0, pol=None
    ):
        self.L1 = L1
        self.L2 = L2
        self.name = L1 + L2
        self.g = g
        self.kappa = kappa
        self.Delta = Delta
        if type(k) is int or type(k) is float:
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
        self.psi0 = qu.basis(self.N, n)
