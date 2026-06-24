"""
cost_sensitivity.py — Mainnet cost sensitivity analysis for ChainMind.

Addresses the NBC'26 reviewer minor comment: the single-point mainnet projection
($4.46/batch at 20 Gwei, $2,400 ETH) relies on volatile assumptions and should be
presented with a sensitivity analysis.

We sweep gas price in [10, 150] Gwei (bear -> congested) and ETH price in
[$2,500, $5,000] (bear -> bull) and report, for every combination:
  - submitBatch cost per batch (USD)         -> the quantity the paper projected
  - cost per decision under batching (USD)    -> at BATCH_SIZE decisions/batch
  - cost per decision if committed individually (USD)
  - savings of batching vs individual (%)     -> INVARIANT to price (key point)

Gas figures (paper-consistent):
  GAS_BATCH      = 93,000 gas   -- stated in paper Section 7.3 (submitBatch)
  GAS_INDIVIDUAL = 83,500 gas   -- derived from the Sepolia per-commit cost
                                   (~0.000218 ETH at the measured ~2.6 Gwei effective
                                   testnet price). This value reproduces BOTH headline
                                   reductions in the paper: 88.9% at batch size 10 and
                                   99.9% at batch size 1,000.

Outputs (written to paper/):
  paper/gas_sensitivity.png   -- annotated heatmap of per-batch USD cost
  paper/table_sensitivity.tex -- LaTeX sensitivity table (\\input-able)

Author: Kefan Liu
Project: ChainMind — NBC'26
Run:    python scripts/cost_sensitivity.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless backend (no display needed)
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# ----------------------------- parameters -----------------------------
GAS_BATCH = 93_000        # gas for one submitBatch tx (paper Sec. 7.3)
GAS_INDIVIDUAL = 83_500   # gas per commitDecision tx (derived; see module docstring)
BATCH_SIZE = 1_000        # decisions amortized into one daily batch (paper scenario)

GAS_PRICES = [10, 20, 30, 50, 75, 100, 150]   # Gwei: calm -> congested
ETH_PRICES = [2500, 3000, 3500, 4000, 5000]   # USD:  bear -> bull

OUT_FIG = "paper/gas_sensitivity.png"
OUT_TAB = "paper/table_sensitivity.tex"


def usd_cost(gas_units, gwei, eth_usd):
    """Cost in USD of consuming `gas_units` at `gwei` gas price and `eth_usd` ETH price."""
    eth = gas_units * gwei * 1e-9          # gas * (Gwei -> ETH/gas) = ETH
    return eth * eth_usd


# ----------------------------- compute grid -----------------------------
G = np.array(GAS_PRICES)
E = np.array(ETH_PRICES)

batch_per_batch = np.array([[usd_cost(GAS_BATCH, g, e) for e in ETH_PRICES]
                            for g in GAS_PRICES])
batch_per_dec = batch_per_batch / BATCH_SIZE
indiv_per_dec = np.array([[usd_cost(GAS_INDIVIDUAL, g, e) for e in ETH_PRICES]
                          for g in GAS_PRICES])
savings_pct = (1.0 - batch_per_dec / indiv_per_dec) * 100.0   # invariant ~99.9%

print("=" * 70)
print("ChainMind mainnet cost sensitivity")
print(f"GAS_BATCH={GAS_BATCH}, GAS_INDIVIDUAL={GAS_INDIVIDUAL}, BATCH_SIZE={BATCH_SIZE}")
print("=" * 70)
print("\nPer-batch submitBatch cost (USD), rows=Gwei, cols=ETH$:")
header = "Gwei\\ETH " + "".join(f"${e:>8}" for e in ETH_PRICES)
print(header)
for i, g in enumerate(GAS_PRICES):
    print(f"{g:>6}   " + "".join(f"{batch_per_batch[i, j]:>9.2f}" for j in range(len(ETH_PRICES))))

print("\nRange of per-batch cost: "
      f"${batch_per_batch.min():.2f}  ->  ${batch_per_batch.max():.2f}")
print("Range of per-decision cost (batch, N=%d): $%.5f  ->  $%.5f"
      % (BATCH_SIZE, batch_per_dec.min(), batch_per_dec.max()))
print("Savings vs individual: %.2f%% (min) .. %.2f%% (max)  -- invariant to price"
      % (savings_pct.min(), savings_pct.max()))
# sanity: reproduce paper's headline ($4.46 at 20 Gwei / $2400)
chk = usd_cost(GAS_BATCH, 20, 2400)
print("\nSanity check @ 20 Gwei / $2,400 ETH (paper point): $%.2f per batch, "
      "$%.5f per decision" % (chk, chk / BATCH_SIZE))


# ----------------------------- heatmap -----------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.6))
im = ax.imshow(batch_per_batch, cmap="YlOrRd", aspect="auto",
               norm=LogNorm(vmin=batch_per_batch.min(), vmax=batch_per_batch.max()))

ax.set_xticks(range(len(ETH_PRICES)))
ax.set_xticklabels([f"${e:,}" for e in ETH_PRICES])
ax.set_yticks(range(len(GAS_PRICES)))
ax.set_yticklabels([f"{g}" for g in GAS_PRICES])
ax.set_xlabel("ETH price (USD)", fontsize=11)
ax.set_ylabel("Gas price (Gwei)", fontsize=11)
ax.set_title("ChainMind submitBatch cost per batch (USD)\n"
             f"{GAS_BATCH:,} gas; per-decision = value / {BATCH_SIZE:,}", fontsize=11)

# annotate each cell with its dollar value
for i in range(len(GAS_PRICES)):
    for j in range(len(ETH_PRICES)):
        val = batch_per_batch[i, j]
        # white text on dark (expensive) cells, black on light (cheap) cells
        frac = (np.log10(val) - np.log10(batch_per_batch.min())) / \
               (np.log10(batch_per_batch.max()) - np.log10(batch_per_batch.min()))
        color = "white" if frac > 0.55 else "black"
        ax.text(j, i, f"${val:,.2f}", ha="center", va="center",
                color=color, fontsize=9)

cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("USD per batch (log scale)", fontsize=10)

# mark the paper's reference operating point (20 Gwei, ~$2,500 column)
ax.add_patch(plt.Rectangle((-0.5, 0.5), 1, 1, fill=False,
                           edgecolor="navy", lw=2, ls="--"))
ax.text(0.0, 0.5, "paper\npoint", ha="center", va="center",
        color="navy", fontsize=7, fontweight="bold")

fig.tight_layout()
fig.savefig(OUT_FIG, dpi=200, bbox_inches="tight")
print(f"\nWrote heatmap -> {OUT_FIG}")


# ----------------------------- LaTeX table -----------------------------
# Representative scenarios spanning bear -> bull market conditions.
scenarios = [(10, 2500), (20, 2500), (30, 3500), (50, 4000), (100, 5000), (150, 5000)]
rows = []
for g, e in scenarios:
    pb = usd_cost(GAS_BATCH, g, e)
    pd = pb / BATCH_SIZE
    pi = usd_cost(GAS_INDIVIDUAL, g, e)
    sv = (1 - pd / pi) * 100
    rows.append(
        f"{g} & {e:,} & {pb:.2f} & {pd:.5f} & {pi:.2f} & {sv:.2f} \\\\"
    )
body = "\n".join(rows)

tex = r"""\begin{table}[t]
\centering
\caption{Sensitivity of mainnet accountability cost to gas and ETH price.
Batch cost uses """ + f"{GAS_BATCH:,}" + r"""~gas (\texttt{submitBatch}); per-decision
columns assume """ + f"{BATCH_SIZE:,}" + r"""~decisions per batch. The savings of
Merkle batching over per-decision commits is \emph{invariant} to price (both scale
linearly), staying at $99.9\%$ across the entire range; only the absolute cost varies.}
\label{tab:cost_sensitivity}
\small
\begin{tabular}{rrrrrr}
\toprule
\textbf{Gas} & \textbf{ETH} & \textbf{Batch} & \textbf{Batch} & \textbf{Indiv.} & \textbf{Savings} \\
\textbf{(Gwei)} & \textbf{(USD)} & \textbf{/tx (\$)} & \textbf{/dec.\ (\$)} & \textbf{/dec.\ (\$)} & \textbf{(\%)} \\
\midrule
""" + body + r"""
\bottomrule
\end{tabular}
\end{table}
"""

with open(OUT_TAB, "w", encoding="utf-8") as f:
    f.write(tex)
print(f"Wrote LaTeX table -> {OUT_TAB}")
