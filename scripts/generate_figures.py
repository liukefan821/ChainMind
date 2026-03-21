#!/usr/bin/env python3
"""
ChainMind — 论文图表生成 (Fig 1-6)
生成 NBC'26 论文所需的全部实验图表，publication-quality matplotlib。

用法:
    cd ~/Projects/ChainMind/scripts
    python generate_figures.py

前置条件:
    - benchmarks.json 已存在 (pipeline.py 输出)
    - gas_data.json 已创建 (Remix 实验后手动填写)

输出: ../figures/ 目录下 6 张 PDF 图
"""

import json
import os
import sys
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ── Config ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
FIG_DIR = os.path.join(SCRIPT_DIR, "..", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Publication style
plt.rcParams.update({
    "font.family": "serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.dpi": 300,
    "savefig.dpi": 300,

})

# Color scheme (academic-friendly, colorblind-safe)
COLORS = {
    "primary": "#2563EB",
    "secondary": "#DC2626",
    "tertiary": "#059669",
    "accent": "#D97706",
    "gray": "#6B7280",
    "light_blue": "#DBEAFE",
    "light_green": "#D1FAE5",
    "light_red": "#FEE2E2",
    "light_yellow": "#FEF3C7",
}


# ═══════════════════════════════════════════════════════════════
#  Data Loading
# ═══════════════════════════════════════════════════════════════

def load_benchmarks():
    """Load benchmark data, fall back to hardcoded values from Day 1 runs."""
    path = os.path.join(DATA_DIR, "benchmarks.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    
    print("⚠️  benchmarks.json not found, using hardcoded Day 1 data")
    return {
        "results": [
            {"n": 10,    "build_ms": 0.93,  "verify_us": 256, "depth": 4,  "proof_bytes": 128},
            {"n": 50,    "build_ms": 2.70,  "verify_us": 280, "depth": 6,  "proof_bytes": 192},
            {"n": 100,   "build_ms": 4.23,  "verify_us": 277, "depth": 7,  "proof_bytes": 224},
            {"n": 500,   "build_ms": 19.6,  "verify_us": 361, "depth": 9,  "proof_bytes": 288},
            {"n": 1000,  "build_ms": 39.8,  "verify_us": 394, "depth": 10, "proof_bytes": 320},
            {"n": 5000,  "build_ms": 198.0, "verify_us": 515, "depth": 13, "proof_bytes": 416},
            {"n": 10000, "build_ms": 392.0, "verify_us": 546, "depth": 14, "proof_bytes": 448},
        ]
    }


def load_gas_data():
    """Load gas data. Falls back to estimates if gas_data.json doesn't exist."""
    path = os.path.join(DATA_DIR, "gas_data.json")
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
            print("✅ gas_data.json loaded — using real on-chain data")
            return data, True
    
    print("⚠️  gas_data.json not found — using ESTIMATES (replace with real data!)")
    return {
        "commitDecision_avg": 75000,
        "submitBatch": {
            "10": 95000,
            "50": 98000,
            "100": 100000,
            "500": 102000,
            "1000": 105000,
        },
        "verifyDecision_avg": 45000,
    }, False


# ═══════════════════════════════════════════════════════════════
#  Fig 1: System Architecture (4-Layer)
# ═══════════════════════════════════════════════════════════════

def fig1_architecture():
    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    layers = [
        (6.5, "Layer 4: Verification Layer",  COLORS["light_green"], COLORS["tertiary"],
         "O(log n) Merkle proof verification + Tamper detection"),
        (4.8, "Layer 3: Blockchain Layer",     COLORS["light_blue"],  COLORS["primary"],
         "AgentAccountability.sol (Sepolia) — commitDecision / submitBatch"),
        (3.1, "Layer 2: Commitment Layer",     COLORS["light_yellow"], COLORS["accent"],
         "SHA-256 hashing + keccak256 Merkle tree construction"),
        (1.4, "Layer 1: Agent Layer",          COLORS["light_red"],   COLORS["secondary"],
         "LLM Agent (qwen2.5:7b) — 10 DeFi scenario risk analysis"),
    ]

    for y, title, bg, border, desc in layers:
        box = FancyBboxPatch((0.8, y - 0.5), 8.4, 1.2,
                             boxstyle="round,pad=0.1",
                             facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(box)
        ax.text(1.3, y + 0.25, title, fontsize=11, fontweight="bold", color=border, va="center")
        ax.text(1.3, y - 0.15, desc, fontsize=9, color="#374151", va="center")

    for y in [2.5, 3.9, 5.3]:
        ax.annotate("", xy=(5, y + 0.25), xytext=(5, y - 0.05),
                     arrowprops=dict(arrowstyle="->", color=COLORS["gray"], lw=1.5))

    ax.set_title("ChainMind: System Architecture", fontsize=14, fontweight="bold", pad=15)
    
    path = os.path.join(FIG_DIR, "fig1_architecture.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 1 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Fig 2: Merkle Tree Structure
# ═══════════════════════════════════════════════════════════════

def fig2_merkle_tree():
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.set_xlim(-1, 17)
    ax.set_ylim(-0.5, 5.5)
    ax.axis("off")

    leaf_labels = [r"$D_0$", r"$D_1$", r"$D_2$", r"$D_3$"]
    leaf_descs = [
        "keccak256(\ninH₀‖outH₀‖modH₀)", "keccak256(\ninH₁‖outH₁‖modH₁)",
        "keccak256(\ninH₂‖outH₂‖modH₂)", "keccak256(\ninH₃‖outH₃‖modH₃)"
    ]
    leaf_x = [2, 6, 10, 14]

    for x, label, desc in zip(leaf_x, leaf_labels, leaf_descs):
        box = FancyBboxPatch((x - 1.3, 0), 2.6, 1.0,
                             boxstyle="round,pad=0.08",
                             facecolor=COLORS["light_blue"], edgecolor=COLORS["primary"], lw=1.5)
        ax.add_patch(box)
        ax.text(x, 0.65, f"Leaf {label}", fontsize=9, fontweight="bold", ha="center", color=COLORS["primary"])
        ax.text(x, 0.3, desc, fontsize=6.5, ha="center", color="#374151")

    for x in [4, 12]:
        box = FancyBboxPatch((x - 1.2, 1.8), 2.4, 0.8,
                             boxstyle="round,pad=0.08",
                             facecolor=COLORS["light_yellow"], edgecolor=COLORS["accent"], lw=1.5)
        ax.add_patch(box)
        ax.text(x, 2.2, "keccak256(L‖R)", fontsize=8, ha="center", color=COLORS["accent"])

    box = FancyBboxPatch((6.8, 3.6), 2.4, 0.8,
                         boxstyle="round,pad=0.08",
                         facecolor=COLORS["light_green"], edgecolor=COLORS["tertiary"], lw=2)
    ax.add_patch(box)
    ax.text(8, 4.0, "Merkle Root", fontsize=10, fontweight="bold", ha="center", color=COLORS["tertiary"])

    for lx, px in [(2, 4), (6, 4), (10, 12), (14, 12)]:
        ax.plot([lx, px], [1.0, 1.8], color=COLORS["gray"], lw=1.2)
    for px in [4, 12]:
        ax.plot([px, 8], [2.6, 3.6], color=COLORS["gray"], lw=1.2)

    ax.annotate("Stored on-chain\n(submitBatch)", xy=(10.5, 4.0),
                fontsize=8, color=COLORS["tertiary"], fontstyle="italic",
                arrowprops=dict(arrowstyle="->", color=COLORS["tertiary"]),
                xytext=(13, 4.8))

    ax.set_title("Merkle Tree Construction from Agent Decisions", fontsize=12, fontweight="bold", pad=10)
    
    path = os.path.join(FIG_DIR, "fig2_merkle_tree.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 2 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Fig 3: Tree Construction Time Scaling
# ═══════════════════════════════════════════════════════════════

def fig3_construction_time(benchmarks):
    data = benchmarks["results"]
    ns = [d["n"] for d in data]
    times = [d["build_ms"] for d in data]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.loglog(ns, times, "o-", color=COLORS["primary"], markersize=7, linewidth=2, label="Measured")

    ref_ns = np.array(ns, dtype=float)
    ref_times = times[0] * ref_ns / ns[0]
    ax.loglog(ref_ns, ref_times, "--", color=COLORS["gray"], linewidth=1, alpha=0.6, label="O(n) reference")

    ax.set_xlabel("Number of Decisions")
    ax.set_ylabel("Construction Time (ms)")
    ax.set_title("Merkle Tree Construction Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    path = os.path.join(FIG_DIR, "fig3_construction_time.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 3 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Fig 4: Verification Time Scaling
# ═══════════════════════════════════════════════════════════════

def fig4_verification_time(benchmarks):
    data = benchmarks["results"]
    ns = [d["n"] for d in data]
    times = [d["verify_us"] for d in data]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.semilogx(ns, times, "s-", color=COLORS["secondary"], markersize=7, linewidth=2, label="Measured")

    ref_ns = np.array(ns, dtype=float)
    base_t = times[0]
    ref_times = base_t + (times[-1] - base_t) * np.log2(ref_ns / ns[0]) / np.log2(ns[-1] / ns[0])
    ax.semilogx(ref_ns, ref_times, "--", color=COLORS["gray"], linewidth=1, alpha=0.6, label="O(log n) reference")

    ax.set_xlabel("Number of Decisions")
    ax.set_ylabel("Verification Time (μs)")
    ax.set_title("Single Decision Verification Time")
    ax.legend()
    ax.grid(True, alpha=0.3)

    ax.annotate(f"{times[-1]}μs for 10K decisions",
                xy=(ns[-1], times[-1]), xytext=(ns[-2], times[-1] + 80),
                fontsize=9, arrowprops=dict(arrowstyle="->", color=COLORS["gray"]),
                color=COLORS["secondary"])

    path = os.path.join(FIG_DIR, "fig4_verification_time.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 4 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Fig 5: Proof Size Scaling
# ═══════════════════════════════════════════════════════════════

def fig5_proof_size(benchmarks):
    data = benchmarks["results"]
    ns = [d["n"] for d in data]
    sizes = [d["proof_bytes"] for d in data]
    depths = [d["depth"] for d in data]

    fig, ax1 = plt.subplots(figsize=(6, 4))

    ln1 = ax1.semilogx(ns, sizes, "D-", color=COLORS["tertiary"], markersize=7, linewidth=2, label="Proof Size")
    ax1.set_xlabel("Number of Decisions")
    ax1.set_ylabel("Proof Size (bytes)", color=COLORS["tertiary"])
    ax1.tick_params(axis="y", labelcolor=COLORS["tertiary"])

    ax2 = ax1.twinx()
    ln2 = ax2.semilogx(ns, depths, "^--", color=COLORS["accent"], markersize=6, linewidth=1.5, label="Tree Depth")
    ax2.set_ylabel("Tree Depth (= # hashes in proof)", color=COLORS["accent"])
    ax2.tick_params(axis="y", labelcolor=COLORS["accent"])

    lns = ln1 + ln2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="lower right")

    ax1.set_title("Proof Size & Tree Depth vs Decision Count")
    ax1.grid(True, alpha=0.3)

    path = os.path.join(FIG_DIR, "fig5_proof_size.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 5 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Fig 6: Gas Cost Comparison (Single vs Batch)
# ═══════════════════════════════════════════════════════════════

def fig6_gas_comparison(gas_data, is_real):
    batch_sizes = sorted(gas_data["submitBatch"].keys(), key=lambda x: int(x))
    single_gas = gas_data["commitDecision_avg"]

    batch_per_decision = []
    batch_labels = []
    for bs in batch_sizes:
        total = gas_data["submitBatch"][bs]
        per_d = total / int(bs)
        batch_per_decision.append(per_d)
        batch_labels.append(f"Batch\n{bs}")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(batch_sizes) + 1)
    width = 0.6

    bars_single = ax.bar(0, single_gas, width, color=COLORS["secondary"], alpha=0.85, label="Single commitDecision")
    bars_batch = ax.bar(x[1:], batch_per_decision, width, color=COLORS["primary"], alpha=0.85, label="Batch submitBatch (per decision)")

    ax.bar_label(bars_single, fmt="%.0f", fontsize=8, padding=3)
    ax.bar_label(bars_batch, fmt="%.0f", fontsize=8, padding=3)

    ax.set_xticks(x)
    ax.set_xticklabels(["Single\n(x1)"] + batch_labels)
    ax.set_ylabel("Gas per Decision")
    ax.set_title("Gas Cost: Single Commit vs Batch Submission")
    ax.legend(loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    if batch_per_decision:
        max_saving = (1 - batch_per_decision[-1] / single_gas) * 100
        ax.text(len(x) - 1, batch_per_decision[-1] + single_gas * 0.08,
                f"{max_saving:.0f}% cheaper\nthan single",
                fontsize=9, ha="center", color=COLORS["primary"], fontstyle="italic")

    if not is_real:
        ax.text(0.5, 0.95, "⚠ ESTIMATED DATA — replace with Remix measurements",
                transform=ax.transAxes, fontsize=8, ha="center", va="top",
                color="red", fontstyle="italic",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#FEE2E2", edgecolor="red", alpha=0.8))

    path = os.path.join(FIG_DIR, "fig6_gas_comparison.pdf")
    fig.savefig(path)
    fig.savefig(path.replace(".pdf", ".png"))
    plt.close(fig)
    print(f"  ✅ Fig 6 → {path}")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main():
    print("ChainMind — 论文图表生成")
    print(f"输出目录: {FIG_DIR}\n")

    benchmarks = load_benchmarks()
    gas_data, is_real_gas = load_gas_data()

    print("Generating figures...")
    fig1_architecture()
    fig2_merkle_tree()
    fig3_construction_time(benchmarks)
    fig4_verification_time(benchmarks)
    fig5_proof_size(benchmarks)
    fig6_gas_comparison(gas_data, is_real_gas)

    print(f"\n{'='*60}")
    print(f"  All 6 figures saved to {FIG_DIR}")
    print(f"  PDF (for LaTeX) + PNG (for preview)")
    if not is_real_gas:
        print(f"\n  ⚠ Fig 6 uses estimated gas data!")
        print(f"  → Do Remix experiments → create scripts/data/gas_data.json")
        print(f"  → Re-run: python generate_figures.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
