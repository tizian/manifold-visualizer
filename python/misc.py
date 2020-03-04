import copy
import numpy as np
np.set_printoptions(suppress=True)
from enum import Enum, IntEnum

Epsilon = 1e-4

class ConstraintType(IntEnum):
    HalfVector = 0,
    AngleDifference = 1

class StrategyType(IntEnum):
    MNEE = 0,
    SMS = 1

class ModeType(IntEnum):
    Raytracing = 0,
    ManifoldExploration = 1,
    SpecularManifoldSampling = 2

def lerp(t, a, b):
    return a + (b - a)*t

def normalize(v):
    n = np.sqrt(v[0]**2 + v[1]**2)
    return v/n

def norm(v):
    return np.sqrt(v[0]**2 + v[1]**2)

def cross(u, v):
    return u[0]*v[1] - u[1]*v[0]

def dot(u, v):
    return u @ v

def reflect(w, n):
    return True, 2*(w @ n)*n - w

def d_reflect(w, dw_du, n, dn_du):
    dot_w_n    = dot(w, n)
    dot_dwdu_n = dot(dw_du, n)
    dot_w_dndu = dot(w, dn_du)
    return 2*((dot_dwdu_n + dot_w_dndu)*n + dot_w_n*dn_du) - dw_du

def refract(w, n_, eta_):
    n = copy.copy(n_)
    eta = copy.copy(eta_)

    if dot(w, n) < 0:
        eta = 1.0 / eta
        n = -n
    f = 1.0 / eta

    dot_w_n = dot(w, n)
    root_term = 1.0 - f*f * (1 - dot_w_n*dot_w_n)
    if root_term < 0:
        return False, np.array([0,0])  # TIR

    wt = -f*(w - dot_w_n*n) - n*np.sqrt(root_term)
    return True, wt

def d_refract(w, dw_du, n_, dn_du_, eta_):
    n     = copy.copy(n_)
    dn_du = copy.copy(dn_du_)
    eta   = copy.copy(eta_)

    if dot(w, n) < 0:
        eta = 1.0 / eta
        n = -n
        dn_du = -dn_du
    f = 1.0 / eta

    dot_w_n    = dot(w, n)
    dot_dwdu_n = dot(dw_du, n)
    dot_w_dndu = dot(w, dn_du)
    root = np.sqrt(1 - f*f*(1 - dot_w_n*dot_w_n))

    a_u  = -f*(dw_du - ((dot_dwdu_n + dot_w_dndu)*n + dot_w_n*dn_du))
    b1_u = dn_du * root
    b2_u = n * 1/(2*root) * (-f*f*(-2*dot_w_n*(dot_dwdu_n + dot_w_dndu)))
    b_u  = -(b1_u + b2_u)
    return a_u + b_u

def angle(w):
    phi = np.arctan2(w[1], w[0])
    if phi < 0:
        phi += 2*np.pi
    return phi

def d_angle(w, dw_du):
    yx = w[1] / w[0]
    d_atan = 1/(1 + yx*yx)
    d_phi = d_atan * (w[0]*dw_du[1] - w[1]*dw_du[0]) / (w[0]*w[0])
    return d_phi