"""Genco total return relative to Star Bulk, with the Diana tender dates marked.

Run: uv run python scripts/pair_figure.py [--asof YYYY-MM-DD]   (after pair_analytics.py)
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INK, MUTED, RULE, ACCENT = "#1B1F24", "#5B6470", "#D9DDE3", "#1F4E79"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--asof", default="2026-10-23")
OUT = ROOT / "outputs" / f"pair-sblk-gnk-{parser.parse_args().asof}"

ratio = pd.read_csv(OUT / "ratio.csv", parse_dates=["date"], index_col="date").ratio.loc[
    "2025-01-01":
]
events = [
    ("2026-05-04", "Tender launched\n$23.50 cash"),
    ("2026-07-24", "Tender expires,\n31.6% tendered"),
    ("2026-08-14", "Diana withdraws"),
]

plt.rcParams.update({"font.family": "sans-serif", "font.size": 7.5})
fig, ax = plt.subplots(figsize=(7.1, 2.0), dpi=300)
ax.plot(ratio.index, ratio.values, color=ACCENT, lw=1.2)
ax.axhline(1, color=RULE, lw=0.8, zorder=0)
for i, (d, label) in enumerate(events):
    x = pd.Timestamp(d)
    ax.axvline(x, color=MUTED, lw=0.6, ls=":")
    ax.text(
        x,
        0.905 - 0.03 * i,
        label.replace("\n", " ") + " ",
        color=MUTED,
        fontsize=6.3,
        va="center",
        ha="right",
    )
last = ratio.index[-1]
ax.annotate(
    f"{ratio.iloc[-1]:.2f}\n{last:%d %b}",
    (last, ratio.iloc[-1]),
    xytext=(6, -3),
    textcoords="offset points",
    fontsize=6.5,
    color=INK,
    va="center",
)
ax.set_xlim(ratio.index[0], last + pd.Timedelta(days=40))
for s in ["top", "right"]:
    ax.spines[s].set_visible(False)
for s in ["left", "bottom"]:
    ax.spines[s].set_color(MUTED)
ax.tick_params(colors=MUTED, labelsize=6.5)
ax.set_ylabel("GNK / SBLK, 2 Jan 2025 = 1", color=MUTED, fontsize=6.5)
fig.tight_layout(pad=0.3)
out = OUT / "relative.png"
fig.savefig(out)
print("wrote", out)
