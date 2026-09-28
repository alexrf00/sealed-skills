"""Figures and LaTeX tables for the evaluation, from results/*.json.

usage: python experiments/make_figures.py
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True, "grid.color": "#e3e6e4", "grid.linewidth": 0.6})
C_NOGUARD, C_GUARD = "#b8863b", "#2b5d4f"
MODELS = {"llama3.1:8b": "Llama 3.1 8B", "qwen2.5:7b": "Qwen 2.5 7B"}
CATS = ["direct", "authority", "transform", "indirect", "tool", "multiturn"]


def pct(x):
    return "--" if x is None else f"{100 * x:.1f}"


def fig_categories(s):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.5), sharey=True)
    for ax, m in zip(axes, MODELS):
        x = np.arange(len(CATS))
        for off, g, col, lab in ((-0.2, False, C_NOGUARD, "no guard"), (0.2, True, C_GUARD, "guard")):
            cat = s["by_category"][f"{m}|guard={g}"]
            ax.bar(x + off, [100 * cat[c]["substantial"] for c in CATS], width=0.38, color=col, label=lab)
        ax.set_xticks(x, CATS, rotation=25)
        ax.set_title(MODELS[m], fontsize=9)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("substantial extraction (%)")
    axes[0].legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "categories.pdf")
    plt.close(fig)


def fig_filters(s):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.7), sharey=True)
    names = [n for n in s["filters"]]
    for ax, m in zip(axes, MODELS):
        for g, col in ((False, C_NOGUARD), (True, C_GUARD)):
            key = f"{m}|guard={g}"
            base = s["by_config"][key]
            ax.scatter([0], [100 * base["substantial"]], color=col, marker="x", s=30)
            for n in names:
                r = s["filters"][n][key]
                ax.scatter([100 * r["benign_blocked"]], [100 * r["residual_substantial"]], color=col,
                           marker="o" if n.startswith("lex") and "sem" not in n else ("s" if n.startswith("sem") else "^"), s=18)
        ax.set_title(MODELS[m], fontsize=9)
        ax.set_xlabel("benign replies blocked (%)")
        ax.set_xlim(-3, 100)
        ax.set_ylim(-3, 100)
    axes[0].set_ylabel("residual substantial extraction (%)")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], color="gray", marker="x", ls="", label="no filter"),
         Line2D([], [], color="gray", marker="o", ls="", label="lexical"),
         Line2D([], [], color="gray", marker="s", ls="", label="semantic"),
         Line2D([], [], color="gray", marker="^", ls="", label="lexical+semantic"),
         Line2D([], [], color=C_NOGUARD, marker="o", ls="", label="no guard"),
         Line2D([], [], color=C_GUARD, marker="o", ls="", label="guard")]
    axes[1].legend(handles=h, frameon=False, fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "filters.pdf")
    plt.close(fig)


def fig_crypto(b):
    fig, ax = plt.subplots(figsize=(3.5, 2.4))
    xs = [r["bytes"] for r in b["by_size"]]
    ax.loglog(xs, [r["seal_ms"] for r in b["by_size"]], "o-", color=C_NOGUARD, label="seal (1 recipient)", ms=3)
    ax.loglog(xs, [r["open_ms"] for r in b["by_size"]], "s-", color=C_GUARD, label="open", ms=3)
    ax.set_xlabel("skill size (bytes)")
    ax.set_ylabel("median time (ms)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIG / "crypto.pdf")
    plt.close(fig)


def table_main(s):
    rows = []
    for m in MODELS:
        for g in (False, True):
            c = s["by_config"][f"{m}|guard={g}"]
            rows.append(f"{MODELS[m]} & {'yes' if g else 'no'} & {pct(c['full'])} & {pct(c['substantial'])} & "
                        f"{pct(c['mean_rule_frac'])} & {pct(c['canary'])} & {pct(c['benign_success'])} & {pct(c['benign_rule_frac'])} \\\\")
    head = [r"\begin{tabular}{llrrrrrr}", r"\toprule",
            r"& & \multicolumn{4}{c}{Attacks} & \multicolumn{2}{c}{Benign tasks} \\",
            r"\cmidrule(lr){3-6}\cmidrule(lr){7-8}",
            r"Model & Guard & Full & Subst. & Rules & Canary & Success & Rules \\", r"\midrule"]
    (TAB / "main.tex").write_text("\n".join(head + rows + [r"\bottomrule", r"\end{tabular}"]) + "\n", encoding="utf-8")


def table_filters(s):
    pick = [n for n in s["filters"] if n in ("lex12", "lex24", "sem@benignFPR0.05", "lex12+sem@benignFPR0.05", "lex12+sem@benignFPR0.1")]
    label = {"lex12": "Lexical, $L{=}12$", "lex24": "Lexical, $L{=}24$", "sem@benignFPR0.05": "Semantic ($\\tau_{5\\%}$)",
             "lex12+sem@benignFPR0.05": "Lex.\\ + sem.\\ ($\\tau_{5\\%}$)", "lex12+sem@benignFPR0.1": "Lex.\\ + sem.\\ ($\\tau_{10\\%}$)"}
    rows = []
    for g in (False, True):
        base = [s["by_config"][f"{m}|guard={g}"]["substantial"] for m in MODELS]
        rows.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{'with' if g else 'without'} guard instruction}}}} \\\\")
        rows.append("No filter & " + " & ".join(f"{pct(b)} & 0.0" for b in base) + " \\\\")
        for n in pick:
            cells = []
            for m in MODELS:
                r = s["filters"][n][f"{m}|guard={g}"]
                cells.append(f"{pct(r['residual_substantial'])} & {pct(r['benign_blocked'])}")
            rows.append(f"{label[n]} & " + " & ".join(cells) + " \\\\")
    head = [r"\begin{tabular}{lrrrr}", r"\toprule",
            r"& \multicolumn{2}{c}{Llama 3.1 8B} & \multicolumn{2}{c}{Qwen 2.5 7B} \\",
            r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}", r"Filter & Res. & Blk. & Res. & Blk. \\", r"\midrule"]
    (TAB / "filters.tex").write_text("\n".join(head + rows + [r"\bottomrule", r"\end{tabular}"]) + "\n", encoding="utf-8")


def main():
    s = json.loads((RES / "summary.json").read_text())
    fig_categories(s)
    fig_filters(s)
    table_main(s)
    table_filters(s)
    if (RES / "bench_crypto.json").exists():
        fig_crypto(json.loads((RES / "bench_crypto.json").read_text()))
    print("figures and tables written")


if __name__ == "__main__":
    main()
