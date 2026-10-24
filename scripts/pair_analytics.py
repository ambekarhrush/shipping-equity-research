"""Long SBLK / short GNK: valuation at a dated close, freight exposure, FFA overlay and hedge statistics.

Reuses the reviewed company packages and the valuation engine; only the share price is refreshed.
Run: uv run python scripts/pair_analytics.py [--asof YYYY-MM-DD]   (after pair_fetch_prices.py)
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from shipping_equity.data import load_company
from shipping_equity.valuation import reverse_valuation, value_company

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "data" / "companies"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--asof", default="2026-10-23", help="Last price date used (YYYY-MM-DD)")
ASOF = parser.parse_args().asof
OUT = ROOT / "outputs" / f"pair-sblk-gnk-{ASOF}"
OUT.mkdir(parents=True, exist_ok=True)

px = pd.read_csv(ROOT / ".cache" / "pair" / "prices.csv", parse_dates=["date"])
px = px[px.date <= ASOF]
close = px.pivot(index="date", columns="ticker", values="close")
adj = px.pivot(index="date", columns="ticker", values="adj_close")
divs = px.pivot(index="date", columns="ticker", values="dividend").fillna(0)
asof = close.index[-1]
res = {"price_date": asof.strftime("%Y-%m-%d")}

# Cal-2027 FFAs on 15 Oct 2026 (Nortilus, citing Baltic Exchange): C5TC 31.3k, P5TC 16.8k, S10TC 15.7k/day,
# expressed as ratios to the models' base Capesize 24.0k, Kamsarmax 17.0k and Supramax 14.5k/day.
CAPE, PMX, SMX = 31.3 / 24.0, 16.8 / 17.0, 15.7 / 14.5
CAL27_SHAPE = {
    "Newcastlemax": CAPE,
    "Capesize": CAPE,
    "Post Panamax": PMX,
    "Kamsarmax": PMX,
    "Ultramax": SMX,
    "Supramax": SMX,
}
res["cal27_shape"] = CAL27_SHAPE
BUCKETS = {
    "cape": ("Newcastlemax", "Capesize"),
    "panamax": ("Post Panamax", "Kamsarmax"),
    "supramax": ("Ultramax", "Supramax"),
}
FFA = {"cape": 31300, "panamax": 16800, "supramax": 15700}  # Cal-2027 USD/day, 15 Oct 2026
NOTIONAL = 10_000_000  # illustrative: USD 10m long SBLK, USD 10m short GNK

# Valuation at the latest close (model inputs otherwise unchanged from the dated packages)
for t in ["SBLK", "GNK"]:
    c = load_company(PKG / t)
    price = float(close[t].iloc[-1])
    c.facts["share_price"] = price
    r = {"price": price, "model_date": c.metadata["valuation_date"]}
    for case in ["bear", "base", "bull"]:
        v = value_company(c, case)
        r[case] = {
            "nav_per_share": v.nav["nav_per_share"],
            "dcf_per_share": v.summary["dcf_per_share"],
            "next_year_equity_cash": v.summary["next_year_equity_cash"],
        }
    base = value_company(c, "base")
    up = value_company(c, "base", rate_multiplier=1.1)
    rv = reverse_valuation(c, "base", target_price=price)
    nav = base.nav
    cf = base.class_forecast
    y1 = cf[cf.period < 4]
    fleet = c.fleet[
        (c.fleet.disposal_date.fillna("") == "") & (c.fleet.delivery_status == "observed")
    ]
    age = (asof.year + asof.dayofyear / 365.25) - fleet.build_year
    a = c.case("base")
    ship_days = len(fleet) * 365
    r["cost_per_ship_day"] = {
        "opex": a["opex"],
        "management": a["management"],
        "ga": a["ga"] / ship_days,
        "all_in": a["opex"] + a["management"] + a["ga"] / ship_days,
    }
    r.update(
        {
            "shares": nav["shares"],
            "market_cap": price * nav["shares"],
            "fleet_value": nav["fleet_value"],
            "net_debt": nav["debt"] - nav["cash"],
            "price_nav": price / nav["nav_per_share"],
            "price_dcf": price / base.summary["dcf_per_share"],
            "implied_rate_uplift": rv["multiplier"] - 1,
            "dcf_per_share_per_10pct_rates": up.summary["dcf_per_share"]
            - base.summary["dcf_per_share"],
            "freight_elasticity": (up.summary["dcf_per_share"] - base.summary["dcf_per_share"])
            / price,
            "open_share_next_year": float(y1.open_revenue.sum() / y1.revenue.sum()),
            "vessels": int(len(fleet)),
            "dwt": float(fleet.dwt.sum()),
            "dwt_weighted_age": float((age * fleet.dwt).sum() / fleet.dwt.sum()),
            "scrubber_share_dwt": float((fleet.scrubber * fleet.dwt).sum() / fleet.dwt.sum()),
            "dwt_mix": (fleet.groupby("vessel_class").dwt.sum() / fleet.dwt.sum())
            .round(3)
            .to_dict(),
            "net_debt_to_fleet": (nav["debt"] - nav["cash"]) / nav["fleet_value"],
            "ttm_dividend": float(divs[t][divs.index > asof - pd.Timedelta(days=365)].sum()),
        }
    )
    r["ttm_yield"] = r["ttm_dividend"] / price

    # Curve-shaped tests: reshape the base vector by Cal-2027 FFAs (15 Oct 2026) relative to base index classes,
    # then solve the common multiplier on that shape that justifies the price. DCF is affine in the multiplier.
    def curve_vector(shape):
        return {f"tce_{k}": a[f"tce_{k}"] * shape[k] for k in c.metadata["class_order"]}

    def solve(ovr):
        v0 = value_company(c, "base", overrides=ovr, rate_multiplier=0).summary["dcf_per_share"]
        v1 = value_company(c, "base", overrides=ovr, rate_multiplier=1).summary["dcf_per_share"]
        return {"dcf_per_share": v1, "multiplier_to_price": (price - v0) / (v1 - v0)}

    r["curve_cal27"] = solve(curve_vector(CAL27_SHAPE))

    # Bucket sensitivities on the curve-shaped vector: equity value change per +10% in one bucket's rates
    curve = curve_vector(CAL27_SHAPE)
    v_curve = value_company(c, "base", overrides=curve).summary["equity_dcf"]
    sens = {}
    for b, classes in BUCKETS.items():
        bumped = {k: v * (1.1 if k[4:] in classes else 1.0) for k, v in curve.items()}
        sens[b] = value_company(c, "base", overrides=bumped).summary["equity_dcf"] - v_curve
    r["bucket_sens_per_10pct_usd"] = sens
    r["bucket_sens_per_usd_equity"] = {b: s / r["market_cap"] for b, s in sens.items()}
    r["curve_cape_only"] = solve(
        curve_vector(
            {k: (CAL27_SHAPE[k] if k in ("Capesize", "Newcastlemax") else 1.0) for k in CAL27_SHAPE}
        )
    )
    res[t] = r

# FFA overlay for a dollar-neutral pair: buy (+) or sell (-) Cal-2027 FFA days per bucket so that a
# parallel, permanent 10% move in that bucket's rates leaves pair value unchanged. Undiscounted FFA P&L.
net = {
    b: NOTIONAL
    * (res["SBLK"]["bucket_sens_per_usd_equity"][b] - res["GNK"]["bucket_sens_per_usd_equity"][b])
    for b in BUCKETS
}
res["overlay"] = {
    "notional_each_leg": NOTIONAL,
    "net_pair_sens_per_10pct": net,
    "ffa_days": {b: -net[b] / (0.1 * FFA[b]) for b in BUCKETS},
    "ffa_notional_usd": {b: -net[b] / 0.1 for b in BUCKETS},
}

# Scenario pair P&L (dollar-neutral, before overlay) on NAV and on curve-shaped DCF
res["scenario_pair"] = {}
for case in ["bear", "base", "bull"]:
    s, g = res["SBLK"], res["GNK"]
    res["scenario_pair"][case] = {
        "sblk_nav_ret": s[case]["nav_per_share"] / s["price"] - 1,
        "gnk_nav_ret": g[case]["nav_per_share"] / g["price"] - 1,
        "pair_nav_ret": (s[case]["nav_per_share"] / s["price"])
        - (g[case]["nav_per_share"] / g["price"]),
        "sblk_dcf_ret": s[case]["dcf_per_share"] / s["price"] - 1,
        "gnk_dcf_ret": g[case]["dcf_per_share"] / g["price"] - 1,
    }

# Price-based statistics on weekly total returns (vendor adjusted close; reference only)
wk = np.log(adj.resample("W-FRI").last()).diff().dropna()


def stats(w):
    b = np.cov(w.GNK, w.SBLK)[0, 1] / w.SBLK.var()
    resid = w.GNK - b * w.SBLK
    spread = w.SBLK - w.GNK  # dollar-neutral long SBLK / short GNK
    eq = spread.cumsum()
    return {
        "weeks": int(len(w)),
        "corr": float(w.SBLK.corr(w.GNK)),
        "beta_gnk_on_sblk": float(b),
        "beta_sblk_bdry": float(np.cov(w.SBLK, w.BDRY)[0, 1] / w.BDRY.var()),
        "beta_gnk_bdry": float(np.cov(w.GNK, w.BDRY)[0, 1] / w.BDRY.var()),
        "beta_sblk_spy": float(np.cov(w.SBLK, w.SPY)[0, 1] / w.SPY.var()),
        "beta_gnk_spy": float(np.cov(w.GNK, w.SPY)[0, 1] / w.SPY.var()),
        "vol_sblk": float(w.SBLK.std() * 52**0.5),
        "vol_gnk": float(w.GNK.std() * 52**0.5),
        "spread_vol_dollar_neutral": float(spread.std() * 52**0.5),
        "resid_vol": float(resid.std() * 52**0.5),
        "spread_max_drawdown": float((eq - eq.cummax()).min()),
    }


res["stats_3y"] = stats(wk[wk.index > asof - pd.DateOffset(years=3)])
res["stats_1y"] = stats(wk[wk.index > asof - pd.DateOffset(years=1)])

# Relative price: GNK total return over SBLK total return, rebased to 2025-01-02
ratio = (adj.GNK / adj.SBLK).dropna()
ratio = ratio / ratio.loc["2025-01-02"]
ratio.rename("ratio").to_frame().to_csv(OUT / "ratio.csv", index_label="date")
res["ratio_monthly"] = {
    d.strftime("%Y-%m"): round(float(v), 3)
    for d, v in ratio.resample("ME").last().loc["2025-01":].items()
}
res["close_path"] = {
    t: {
        d.strftime("%Y-%m-%d"): round(float(v), 2)
        for d, v in close[t].resample("ME").last().loc["2025-06":].items()
    }
    for t in ["SBLK", "GNK", "DSX", "BDRY"]
}

(OUT / "pair_results.json").write_text(json.dumps(res, indent=2, default=float) + "\n")
print("wrote", OUT / "pair_results.json")
