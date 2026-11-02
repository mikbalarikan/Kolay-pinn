"""
pinn_core.py — Tüm örneklerin paylaştığı PINN yapı taşları.

Orijinal repo (maziarraissi/PINNs, TensorFlow 1.x) her dosyada aynı üç parçayı
tekrar eder: xavier_init, initialize_NN, neural_net. Burada PyTorch ile tek yerde
toplandı. Mantık birebir aynıdır.
"""
import torch
import torch.nn as nn


class MLP(nn.Module):
    """Tam bağlantılı ağ: girişi [-1, 1]'e ölçekler, gizli katmanlarda tanh kullanır.

    Orijinaldeki karşılığı:
        H = 2.0*(X - lb)/(ub - lb) - 1.0          # giriş normalizasyonu
        for l: H = tanh(H @ W + b)                # gizli katmanlar
        Y = H @ W_son + b_son                      # lineer çıkış
    """

    def __init__(self, layers, lb, ub):
        super().__init__()
        self.register_buffer("lb", torch.tensor(lb, dtype=torch.float32))
        self.register_buffer("ub", torch.tensor(ub, dtype=torch.float32))
        self.linears = nn.ModuleList(
            nn.Linear(layers[i], layers[i + 1]) for i in range(len(layers) - 1)
        )
        for lin in self.linears:  # Xavier (Glorot) başlatma, bias = 0
            nn.init.xavier_normal_(lin.weight)
            nn.init.zeros_(lin.bias)

    def forward(self, X):
        H = 2.0 * (X - self.lb) / (self.ub - self.lb) - 1.0
        for lin in self.linears[:-1]:
            H = torch.tanh(lin(H))   # tanh: sonsuz kez türevlenebilir -> u_xx vs. hesaplanabilir
        return self.linears[-1](H)


def grad(out, inp):
    """d(out)/d(inp). TensorFlow'daki tf.gradients(out, inp)[0] karşılığı.

    create_graph=True -> türevin de türevini alabilmek için (u_xx, u_yy ...).
    """
    return torch.autograd.grad(
        out, inp, grad_outputs=torch.ones_like(out), create_graph=True
    )[0]


def grads(out, *inps):
    """Tek autograd geçişinde birden çok kısmi türev: (d out/d x, d out/d y, ...).
    Ayrı ayrı grad() çağırmaktan daha hızlıdır (graf bir kez geriye yürünür)."""
    return torch.autograd.grad(
        out, inps, grad_outputs=torch.ones_like(out), create_graph=True
    )


def as_tensor(a, requires_grad=False):
    return torch.tensor(a, dtype=torch.float32, requires_grad=requires_grad)
