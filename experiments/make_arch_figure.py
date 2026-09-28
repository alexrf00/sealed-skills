"""Draws paper/figures/architecture.pdf."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "paper" / "figures" / "architecture.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)

INK, ACC, BRASS, USER = "#15201c", "#2b5d4f", "#8f6c1d", "#f4ecd8"

fig, ax = plt.subplots(figsize=(10, 4.3))
ax.set_xlim(0, 100)
ax.set_ylim(0, 44)
ax.axis("off")
plt.rcParams["font.family"] = "DejaVu Sans"


def zone(x, y, w, h, title, fc, ec):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec=ec, lw=1.2))
    ax.text(x + 1, y + h - 1.6, title, fontsize=8.5, fontweight="bold", color=ec, va="top")


def box(x, y, w, h, title, sub=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=0.8", fc="white", ec="#9aa7a1", lw=0.9))
    ax.text(x + w / 2, y + h / 2 + (1.2 if sub else 0), title, ha="center", va="center", fontsize=8.5, fontweight="bold", color=INK)
    if sub:
        ax.text(x + w / 2, y + h / 2 - 1.8, sub, ha="center", va="center", fontsize=7, color="#4a5752")


def arrow(p, q, label=None, lx=0, ly=1.2, style="-|>", color=INK, ls="-"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=10, lw=1.0, color=color, linestyle=ls))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, ha="center", fontsize=7, color=color)


zone(1, 1, 22, 41, "SKILL OWNER (offline)", "#eef2f0", "#4a5752")
box(3, 28, 18, 9, "Seal", "HPKE wrap CEK,\nSTREAM encrypt, sign")
box(3, 8, 18, 9, "Licensing", "owner-signed tokens")

zone(28, 24, 20, 18, "UNTRUSTED CHANNELS", "#f7f8f7", "#6b7671")
box(30, 25, 16, 8.5, "Marketplace / CDN", "stores (manifest, C)")

zone(28, 1, 20, 18, "USER'S DEVICE", USER, BRASS)
box(30, 4, 16, 9, "Client app", "chat · desktop · CLI")

zone(53, 1, 46, 41, "PROVIDER SERVERS (trust boundary)", "#e3eeea", ACC)
box(55, 31, 18, 8, "/.well-known/", "sealed-skill-keys")
box(55, 17, 18, 9, "Unseal", "verify, check licence,\nunwrap, decrypt in RAM")
box(78, 17, 18, 9, "Model", "skill in context\n(guard instruction)")
box(66, 4, 18, 9, "Output filter", "lexical + semantic\n+ canaries")
box(78, 31, 18, 8, "Script runner", "isolated from\nmodel sandbox")

arrow((55, 35.5), (21.3, 35.5), "① fetch pk (HTTPS)", ly=0.9, color=ACC)
arrow((21.3, 30.5), (30, 29.5), "② publish", ly=1.0)
arrow((21.3, 11), (30, 9.5), "③ licence", ly=0.8)
arrow((46.3, 10), (55, 19), "④ skill ID + licence", lx=-6.5, ly=1.0)
arrow((46.3, 28), (55, 23.5), "fetch package", lx=2.5, ly=2.2, color="#6b7671", ls="--")
arrow((73.3, 21.5), (78, 21.5))
arrow((85, 16.7), (80, 13.3))
arrow((87, 26.3), (87, 30.7), style="<|-|>")
arrow((66, 7), (46.3, 7), "⑤ answers only", ly=1.0, color=ACC)

fig.tight_layout()
fig.savefig(OUT, bbox_inches="tight")
fig.savefig(OUT.with_suffix(".png"), dpi=160, bbox_inches="tight")
print("wrote", OUT)
