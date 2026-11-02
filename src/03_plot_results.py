"""
DERS 3 — Sonuçları görselleştir (Burgers + Navier–Stokes).
Önce 01_ ve 02_ betiklerini çalıştırıp results/ klasörünü doldurun.
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.interpolate import griddata

ROOT = os.path.join(os.path.dirname(__file__), "..")
R, FIG = f"{ROOT}/results", f"{ROOT}/figures"
plt.rcParams.update({"font.size": 10, "figure.dpi": 130})

# ============================================================ BURGERS
if os.path.exists(f"{R}/burgers.npz"):
    b = np.load(f"{R}/burgers.npz"); lg = json.load(open(f"{R}/burgers_log.json"))
    x, t, E, Up, Fp = b["x"].ravel(), b["t"].ravel(), b["Exact"], b["U_pred"], b["F_pred"]

    fig = plt.figure(figsize=(12, 7.5), constrained_layout=True)
    gs = fig.add_gridspec(3, 3)
    ax = fig.add_subplot(gs[0, :])
    im = ax.imshow(Up.T, extent=[t.min(), t.max(), x.min(), x.max()], origin="lower",
                   aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
    ax.scatter(b["X_f_train"][::20, 1], b["X_f_train"][::20, 0], s=1, c="0.4", alpha=0.4,
               label="kollokasyon (fizik) noktaları (1/20'si)")
    ax.scatter(b["X_u_train"][:, 1], b["X_u_train"][:, 0], s=14, c="k", marker="x",
               label=f"veri noktaları (IC+BC, {len(b['X_u_train'])})")
    for tt in (0.25, 0.5, 0.75):
        ax.axvline(tt, c="w", lw=1, ls="--")
    ax.set_xlabel("t"); ax.set_ylabel("x"); fig.colorbar(im, ax=ax)
    ax.set_title(f"PINN tahmini u(t, x)   — göreli L2 hata = {lg['error_u']:.2e}")
    ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    for k, tt in enumerate((0.25, 0.5, 0.75)):
        j = np.argmin(abs(t - tt)); a = fig.add_subplot(gs[1, k])
        a.plot(x, E[j], "b-", lw=2, label="Tam çözüm"); a.plot(x, Up[j], "r--", lw=2, label="PINN")
        a.set_title(f"t = {tt}"); a.set_xlabel("x"); a.set_ylim(-1.1, 1.1); a.grid(alpha=.3)
        if k == 0: a.set_ylabel("u"); a.legend(fontsize=8)
    a = fig.add_subplot(gs[2, 0:2])
    im = a.imshow(np.abs(E - Up).T, extent=[0, 1, -1, 1], origin="lower", aspect="auto", cmap="magma")
    a.set_title("|hata| — hata şokun (x=0) etrafında yoğunlaşır"); a.set_xlabel("t"); a.set_ylabel("x")
    fig.colorbar(im, ax=a)
    a = fig.add_subplot(gs[2, 2]); h = lg["hist"]
    a.semilogy(h["it"], h["mse_u"], label="MSE_u (veri)"); a.semilogy(h["it"], h["mse_f"], label="MSE_f (fizik)")
    sw = next((i for i, p in zip(h["it"], h["phase"]) if p == "lbfgs"), None)
    if sw: a.axvline(sw, c="k", ls=":"); a.text(sw, a.get_ylim()[1] if False else max(h["mse_u"]), " Adam→L-BFGS", fontsize=8, va="top")
    a.set_xlabel("iterasyon"); a.set_title("Kayıp eğrisi"); a.legend(fontsize=8); a.grid(alpha=.3)
    fig.suptitle("Ders 1 — Burgers denklemi (ileri problem)", fontsize=13)
    fig.savefig(f"{FIG}/01_burgers_result.png"); plt.close(fig)
    print("Burgers şekli kaydedildi")

# ============================================================ NAVIER-STOKES
for tag in ("clean", "noisy"):
    if not os.path.exists(f"{R}/ns_{tag}.npz"):
        continue
    d = np.load(f"{R}/ns_{tag}.npz"); lg = json.load(open(f"{R}/ns_{tag}_log.json")); res = lg["res"]
    X = d["X_star"]
    gx, gy = np.meshgrid(np.linspace(1, 8, 250), np.linspace(-2, 2, 140))
    G = lambda f: griddata(X, f.ravel(), (gx, gy), method="cubic")
    p_shift = d["p_p"] - d["p_p"].mean() + d["p_e"].mean()
    rows = [("u", d["u_e"], d["u_p"], "viridis"), ("v", d["v_e"], d["v_p"], "RdBu_r"),
            ("p", d["p_e"], p_shift, "magma")]
    fig, axs = plt.subplots(3, 3, figsize=(13, 8), constrained_layout=True)
    for r, (nm, ex, pr, cm) in enumerate(rows):
        Ge, Gp = G(ex), G(pr); lo, hi = np.nanmin(Ge), np.nanmax(Ge)
        for c, (F, ttl) in enumerate([(Ge, f"Gerçek {nm} (DNS)"), (Gp, f"PINN {nm}"), (np.abs(Ge - Gp), f"|hata| {nm}")]):
            im = axs[r, c].pcolormesh(gx, gy, F, cmap=cm if c < 2 else "Greys", shading="auto",
                                      vmin=lo if c < 2 else 0, vmax=hi if c < 2 else None)
            axs[r, c].set_aspect("equal"); axs[r, c].set_title(ttl); fig.colorbar(im, ax=axs[r, c], shrink=.8)
    axs[2, 1].set_title("PINN p  (VERİ OLMADAN! sabit kaydırılmış)")
    fig.suptitle(f"Ders 2 — Navier–Stokes, t = 10   |  err u={res['err_u']:.2%}  v={res['err_v']:.2%}  "
                 f"p={res['err_p_shifted']:.2%}  |  λ1={res['lambda_1']:.4f}  λ2={res['lambda_2']:.5f}", fontsize=12)
    fig.savefig(f"{FIG}/02_ns_fields_{tag}.png"); plt.close(fig)

    h = lg["hist"]; it = np.array(h["it"])
    fig, axs = plt.subplots(1, 3, figsize=(14, 3.6), constrained_layout=True)
    axs[0].plot(it, h["l1"], c="C0"); axs[0].axhline(1.0, c="k", ls="--", label="gerçek λ1 = 1")
    axs[0].set_title("λ1 (konveksiyon katsayısı) öğrenimi"); axs[0].legend()
    axs[1].plot(it, h["l2"], c="C1"); axs[1].axhline(0.01, c="k", ls="--", label="gerçek λ2 = 1/Re = 0.01")
    axs[1].set_title("λ2 (viskozite) öğrenimi"); axs[1].legend(); axs[1].set_ylim(-0.02, 0.05)
    axs[2].semilogy(it, h["data"], label="veri kaybı"); axs[2].semilogy(it, h["phys"], label="fizik kaybı")
    axs[2].set_title("Kayıp bileşenleri"); axs[2].legend()
    sw = next((i for i, p in zip(h["it"], h["phase"]) if p == "lbfgs"), None)
    for a in axs:
        a.set_xlabel("iterasyon"); a.grid(alpha=.3)
        if sw: a.axvline(sw, c="gray", ls=":")
    fig.savefig(f"{FIG}/02_ns_lambdas_{tag}.png"); plt.close(fig)
    print(f"NS ({tag}) şekilleri kaydedildi:", json.dumps(res))

# ============================================================ ADAM PLATOSU vs L-BFGS
# Aynı ağ, aynı veri: yalnız Adam (lr=1e-3) ile L-BFGS ağırlıklı eğitimin karşılaştırması
import re
def parse(path):
    it, data, l1 = [], [], []
    for ln in open(path):
        m = re.search(r"it\s+(\d+) loss \S+ data (\S+) phys \S+ λ1 (\S+)", ln)
        if m: it.append(int(m[1])); data.append(float(m[2])); l1.append(float(m[3]))
    return np.array(it), np.array(data), np.array(l1)
pa, pb = f"{R}/ns_adam_only_attempt.log", f"{R}/ns_clean_train.log"
if os.path.exists(pa) and os.path.exists(pb):
    A, B = parse(pa), parse(pb)
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.6), constrained_layout=True)
    axs[0].semilogy(A[0], A[1], label="yalnız Adam (lr 1e-3)"); axs[0].semilogy(B[0], B[1], label="1000 Adam → L-BFGS")
    axs[0].set_title("Veri kaybı (Σ, 5000 nokta)"); axs[0].axvline(1000, c="gray", ls=":")
    axs[1].plot(A[0], A[2], label="yalnız Adam"); axs[1].plot(B[0], B[2], label="Adam → L-BFGS")
    axs[1].axhline(1, c="k", ls="--", lw=1); axs[1].set_title("λ1 (gerçek = 1)")
    for a in axs: a.set_xlabel("iterasyon / fonksiyon değerlendirmesi"); a.grid(alpha=.3); a.legend()
    axs[0].set_xlim(0, max(A[0].max(), 6000)); axs[1].set_xlim(0, max(A[0].max(), 6000))
    fig.suptitle("Ortalama akış platosu: Adam ~450'de takılıyor, L-BFGS girdap yapısını ~2500. adımda yakalıyor")
    fig.savefig(f"{FIG}/02_ns_plateau.png"); plt.close(fig)
    print("plato şekli kaydedildi")
