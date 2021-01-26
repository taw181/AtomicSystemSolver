#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 17 12:38:54 2020

@author: tom
"""
import numpy as np
import qutip as qu
import qutipfuncs as qf

def _pol_from_stokes(self):
    ep, em = qf.Stokes2EpEm(*self.S)
    self.pol = [ep, 0, em]

class Level():
    def __init__(self, name='LJ', kind='g', J=0, S=1/2, L=0, pop=0):
        self.name = name
        self.J = J
        self.S = S
        self.L = L
        self.N = int(2*J+1)
        self.M = np.arange(-J,J+1)
        self.kind = kind
        self.states = [qu.basis(self.N,i) for i in range(self.N)]
        self.pop = pop
        if pop == 0:
            self.pop = [0]*self.N


class Atom():
    def __init__(self):
        self.levels = []
        self.levels.append(Level(kind=g, J=1/2, L=0))


class Laser():
    def __init__(self,  L1=None, L2=None, Omega=0, Delta=0, lw=0, k=[0, 0, 1], S=[0, 0, 1]):
        self.L1 = L1
        self.L2 = L2
        self.name = L1+L2
        self.Omega = Omega
        self.Delta = Delta
        self.lw = lw
        self.k = k
        self.S = S
        _pol_from_stokes(self)


class Cavity():

    def __init__(self, L1='1', L2='2', g=0, kappa=0, Delta=0, N=2, modes='2', k=[0, 0, 1], pol=[1, 0, 1],n=0):
        self.L1 = L1
        self.L2 = L2
        self.name = L1+L2
        self.g = g
        self.kappa = kappa
        self.Delta = Delta
        self.k = k
        self.pol = pol
        self.N = N
        self.modes = modes
        self.states = [qu.basis(self.N,i) for i in range(self.N)]
        self.psi0 = qu.basis(self.N,n)
