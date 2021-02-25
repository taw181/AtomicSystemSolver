# -*- coding: utf-8 -*-
"""
Created on Thu Jan 11 21:44:50 2018

@author: twalk
"""
import numpy as np

def murelj(Jg,Je):
    import numpy as np
    import qutip as qu
    intg = int(2*Jg+1)
    inte = int(2*Je+1)
    Mg = list(np.arange(-Jg,Jg+1))
    Me = list(np.arange(-Je,Je+1))
    Am = np.zeros([intg,inte])
    A0 = np.zeros([intg,inte])
    Ap = np.zeros([intg,inte])
    if abs(Jg-Je)>1:
        print('true')
        return Am,A0,Ap
    else:
        for k in np.arange(0,intg):
            m = Mg[k]
            if abs(m-1) <= Je:
                Am[k,Me.index(m-1)]=qu.clebsch(Jg,1,Je,m,-1,m-1)
            if abs(m) <= Je:
                A0[k,Me.index(m)]  =qu.clebsch(Jg,1,Je,m,0,m)
            if abs(m+1) <= Je:
                Ap[k,Me.index(m+1)]=qu.clebsch(Jg,1,Je,m,1,m+1)
        return Am,A0,Ap

def zeemanFS(J,S,L,B,Gamma_phys):
    #
    #  w = zeeman(J,S,L,F,I,B) calculates the angular frequency shift
    #  in terms of the linewidth Gamma_phys for unit change of m
    #  for an atom in magnetic field B (in Tesla)
    #
    #  e.g. Ca+:   Gamma_phys = 2*pi*22.282E6 = 140E6
    #
    #  application:
    #  Zeeman-shift for a field of 1 Gauss = 10^-4 Tesla
    #  fzeeman = zeemanFS(J,S,L,1E-4,2*pi*1E6)  in MHz
    #
    #  zeemanFS(1/2,1/2,0,1E-4,2*pi*1E6) = 2.7993
    #  zeemanFS(1/2,1/2,1,1E-4,2*pi*1E6) = 0.9331
    #  zeemanFS(3/2,1/2,1,1E-4,2*pi*1E6) = 1.8662
    #  zeemanFS(3/2,1/2,2,1E-4,2*pi*1E6) = 1.1197
    #  zeemanFS(5/2,1/2,2,1E-4,2*pi*1E6) = 1.6796

    #  w1 = zeemanFS(1/2,1/2,0,B,140E6)
    #  w2 = zeemanFS(1/2,1/2,1,B,140E6)
    #  w3 = zeemanFS(3/2,1/2,2,B,140E6)
    #  w4 = zeemanFS(3/2,1/2,1,B,140E6)
    #  Hzeeman = tensor(ida,qo(np.diag([ w1*M1 w2*M2 w3*M3 w4*M4 ])))

    muB = 9.274078E-24
    hbar = 1.054572669125E-34
    #
    E = (1+(J*(J+1)+S*(S+1)-L*(L+1))/(2*J*(J+1)))* muB*B
    w = E/(hbar*Gamma_phys)
    return w

def norm(lst):
    import numpy as np
    return np.sqrt(sum([i**2 for i in lst]))

def adj(M):
    return (M.T).conj()


def convMatPol(k, B):
    import numpy as np
    # U = convMatPol(k, B) calculates a converion matrix of the spherical basis
    # vectors (= p, 0, m) between the laser's frame and atom's frame.
    # The laser frame is defined by the z-direction given by vector k
    # and the atom's frame is with the the z-direction given by vector B.
    # All vectors are a column.

    if norm(k) == 0:
        print('vector k is zero.')
    else:
        ez_l = k/norm(k)


    if norm(B) == 0:
        print('vector B is zero.')
        ez_a = ez_l  # when B = 0, the atomic frame is set identical to the laser's
    else:
        ez_a = B/norm(B)
#    end

    # Generate x, y unit vectors in the laser frame.
    # x, y directions are arbitrary in the plane perpendicular to k.
    # We choose the y-direction to be in the xy -plane in the global
    # frame.

    ez = [0,  0,  1]
    ey_l = np.cross(ez, ez_l)
    if norm(ey_l)==0:
        # if k//ez
        ey_l = [0,  1,  0]
    else:
        ey_l = ey_l/norm(ey_l)
    ex_l =  np.cross(ey_l, ez_l)
    ex_l = ex_l/norm(ex_l)

    # Likewise generate x, y unit vectors in the atomic frame.
    ey_a =  np.cross(ez, ez_a)
    if norm(ey_a)==0:
        # if k//ez
        ey_a = [0,  1,  0]
    else:
        ey_a = ey_a/norm(ey_a)

    ex_a =  np.cross(ey_a, ez_a)
    ex_a = ex_a/norm(ex_a)

    # Calculate ratotion matrix between {ex,y,z_l} and {ex,y,z_a}
    R = np.array([[np.dot(ex_l, ex_a), np.dot(ex_l, ey_a), np.dot(ex_l, ez_a)], \
        [np.dot(ey_l, ex_a), np.dot(ey_l, ey_a), np.dot(ey_l, ez_a)] ,\
        [np.dot(ez_l, ex_a), np.dot(ez_l, ey_a), np.dot(ez_l, ez_a)]])

    # Coversion from Cartesian basis to spherical basis
    S = np.array([[-1/np.sqrt(2), -1j/np.sqrt(2), 0], [0, 0, 1], [1/np.sqrt(2), -1j/np.sqrt(2), 0]])
    U = np.transpose(R).dot((S.T).conj())
    U = S.dot(U)
    U = U.T

    return U

def pol(field,Bdir):
    #convert polarisation of field to atom frame given quantisation axis Bdir
    U = convMatPol(field.k, Bdir)
    pol_at = adj(U).dot(field.pol)
    return pol_at

def ExEyDelta2Stokes(Ex, Ey, Delta):
    # S = StokesParams(Ex, Ey, Delta)
    # returns Stokes parameters S1, S2 and S3, assuming S0 = Ex^2+Ey^2=1, from
    # Ex, Ey and phase difference between them Delta.

    S1 = Ex^2-Ey^2
    S2 = 2*Ex*Ey*np.cos(Delta)
    S3 = 2*Ex*Ey*np.sin(Delta)
    return S1, S2, S3

def Stokes2EpEm(S1, S2, S3):
    Ex, Ey, delta = getExEyDelta(S1, S2, S3)
    Ep, Em = convertExEyDelta2EpEm(Ex, Ey, delta)
    return Ep,Em


def getExEyDelta(S1, S2, S3):
    Ex = np.sqrt((1+S1)/2)
    Ey = np.sqrt((1-S1)/2)
    delta = np.angle(S2+1j*S3)
    return Ex, Ey, delta

def convertExEyDelta2EpEm(Ex, Ey, delta):
    Ep = -(Ex+1j*Ey*np.exp(-1j*delta))/np.sqrt(2)
    Em = (Ex-1j*Ey*np.exp(-1j*delta))/np.sqrt(2)
    return Ep,Em
