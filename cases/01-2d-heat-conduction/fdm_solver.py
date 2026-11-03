"""
Step 3 - Reference FDM solver for 2D steady conduction in a square plate.

Nondimensional problem (see README.md):
    theta_xx + theta_yy = 0            on [0,1]^2
    theta = 1                          on x=0, x=1, y=1   (walls at 70 C)
    d(theta)/dy = Bi * theta           on y=0             (convective cooling)

theta = (T - T_inf) / (T_w - T_inf),  x,y scaled by L.

Discretization: 2nd-order central differences on a uniform N x N node grid.
The Robin BC uses a ghost node below y=0:
    theta[i,-1] = theta[i,1] - 2*dy*Bi*theta[i,0]
Bottom corners belong to the Dirichlet side walls (theta = 1).
The linear system is solved with a sparse direct solver.

Usage:
    python fdm_solver.py                 # default Bi from README, N=101
    python fdm_solver.py --Bi 4.08 --N 201
"""

import argparse
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# ---------------- physical inputs (Step 1) ----------------
L = 0.1          # plate size [m]
K_SOLID = 49.0   # steel conductivity [W/m K]
T_WALL = 70.0    # top/left/right wall temperature [C]
T_INF = 20.0     # water free-stream temperature [C]
U_INF = 1.0      # water velocity [m/s]

# water @ 20 C (Incropera, Table A.6)
NU_W, K_W, PR_W = 1.004e-6, 0.598, 7.01


def h_flat_plate(U=U_INF, L=L, nu=NU_W, k=K_W, Pr=PR_W):
    """Average h for laminar flow over an isothermal flat plate."""
    Re = U * L / nu
    assert Re < 5e5, "turbulent - use a different correlation"
    Nu = 0.664 * Re**0.5 * Pr ** (1 / 3)
    return Nu * k / L, Re, Nu


H_CONV, RE, NU = h_flat_plate()
BI_DEFAULT = H_CONV * L / K_SOLID


# ---------------- FDM solver ----------------
def solve_fdm(N=101, Bi=BI_DEFAULT):
    """Return x (N,), y (N,), theta (N,N) indexed theta[j, i] = theta(y_j, x_i)."""
    x = np.linspace(0.0, 1.0, N)
    y = np.linspace(0.0, 1.0, N)
    d = 1.0 / (N - 1)                       # dx = dy
    idx = lambda i, j: j * N + i            # flatten (i: x, j: y)

    A = sp.lil_matrix((N * N, N * N))
    b = np.zeros(N * N)

    for j in range(N):
        for i in range(N):
            p = idx(i, j)
            if i == 0 or i == N - 1 or j == N - 1:
                A[p, p] = 1.0               # Dirichlet theta = 1
                b[p] = 1.0
            elif j == 0:
                # Robin with ghost node, multiplied by d^2
                A[p, idx(i - 1, j)] = 1.0
                A[p, idx(i + 1, j)] = 1.0
                A[p, idx(i, j + 1)] = 2.0
                A[p, p] = -4.0 - 2.0 * d * Bi
            else:
                A[p, idx(i - 1, j)] = 1.0
                A[p, idx(i + 1, j)] = 1.0
                A[p, idx(i, j - 1)] = 1.0
                A[p, idx(i, j + 1)] = 1.0
                A[p, p] = -4.0

    theta = spla.spsolve(A.tocsr(), b).reshape(N, N)
    return x, y, theta


# ---------------- analytical series (verification) ----------------
def analytical(x, y, Bi=BI_DEFAULT, n_terms=4000):
    """
    theta = 1 - sum_{n odd} A_n sin(n pi x) sinh(n pi (1-y)),
    A_n = 4 Bi / (n pi) / (n pi cosh(n pi) + Bi sinh(n pi)).
    Evaluated in overflow-safe form.
    """
    X, Y = np.meshgrid(x, y)
    phi = np.zeros_like(X)
    for n in range(1, 2 * n_terms, 2):
        a = n * np.pi
        # sinh(a(1-y)) / cosh(a)  and  sinh(a)/cosh(a) = tanh(a)
        ratio = np.exp(-a * Y) * (1 - np.exp(-2 * a * (1 - Y))) / (1 + np.exp(-2 * a))
        phi += (4 * Bi / a) / (a + Bi * np.tanh(a)) * np.sin(a * X) * ratio
    return 1.0 - phi


def bottom_heat_rate(x, theta_bottom, Bi=BI_DEFAULT):
    """
    Heat rate leaving through the bottom per unit depth [W/m]:
        Q' = h L (T_w - T_inf) * integral_0^1 theta(x,0) dx
    """
    q_star = np.trapezoid(theta_bottom, x)          # = Q' / (h L dT)
    h = Bi * K_SOLID / L
    return h * L * (T_WALL - T_INF) * q_star, q_star


def to_celsius(theta):
    return T_INF + theta * (T_WALL - T_INF)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=101)
    ap.add_argument("--Bi", type=float, default=BI_DEFAULT)
    ap.add_argument("--out", default=str(Path(__file__).parent / "data"))
    args = ap.parse_args()

    print(f"Re = {RE:.0f}, Nu = {NU:.1f}, h = {H_CONV:.0f} W/m2K, Bi(default) = {BI_DEFAULT:.3f}")
    print(f"Solving N = {args.N}, Bi = {args.Bi:.3f}")

    x, y, th = solve_fdm(args.N, args.Bi)
    th_ex = analytical(x, y, args.Bi)
    err = th - th_ex
    rel_l2 = np.linalg.norm(err) / np.linalg.norm(th_ex)
    Q, q_star = bottom_heat_rate(x, th[0], args.Bi)

    print(f"rel. L2 error vs analytical = {rel_l2:.2e}, max |err| = {np.abs(err).max():.2e}")
    print(f"theta(0.5,0) = {th[0, args.N // 2]:.4f}  ->  T = {to_celsius(th[0, args.N // 2]):.2f} C")
    print(f"min T = {to_celsius(th.min()):.2f} C")
    print(f"bottom heat rate Q' = {Q:.0f} W/m  (int theta_b dx = {q_star:.4f})")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    np.savez(out / f"fdm_N{args.N}.npz", x=x, y=y, theta=th, theta_exact=th_ex,
             Bi=args.Bi, L=L, k=K_SOLID, T_wall=T_WALL, T_inf=T_INF)
    X, Y = np.meshgrid(x, y)
    np.savetxt(out / f"fdm_N{args.N}.csv",
               np.column_stack([X.ravel(), Y.ravel(), th.ravel(), to_celsius(th).ravel()]),
               delimiter=",", header="x,y,theta,T_C", comments="", fmt="%.6e")
    print(f"saved -> {out}")
