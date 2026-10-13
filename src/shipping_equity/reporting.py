"""Readable, local research artifacts. All results come from the shared Python engine."""

from __future__ import annotations

import html
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from shipping_equity.data import Company
from shipping_equity.valuation import reverse_valuation, value_company


def write_report(company: Company, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    cases = {name: value_company(company, name) for name in ["bear", "base", "bull"]}
    base = cases["base"]
    root = reverse_valuation(company)
    sensitivity = []
    for adjustment in [-0.02, -0.01, 0, 0.01, 0.02]:
        for rate in [0.8, 0.9, 1, 1.1, 1.2]:
            result = value_company(company, rate_multiplier=rate, discount_adjustment=adjustment)
            sensitivity.append(
                {
                    "rate_multiplier": rate,
                    "discount_adjustment": adjustment,
                    "dcf_per_share": result.summary["dcf_per_share"],
                }
            )
    pd.DataFrame(sensitivity).to_csv(output / "sensitivity.csv", index=False)
    summaries = pd.DataFrame({name: result.summary for name, result in cases.items()}).T
    summaries.index.name = "case"
    summaries.to_csv(output / "scenarios.csv")
    for name, result in cases.items():
        result.forecast.to_csv(output / f"{name}-cash-flow.csv", index=False)
        result.financing.to_csv(output / f"{name}-financing.csv", index=False)
    base.class_forecast.to_csv(output / "base-class-forecast.csv", index=False)
    evidence = {
        "ticker": company.metadata["ticker"],
        "valuation_date": company.metadata["valuation_date"],
        "input_sha256": company.fingerprint,
        "status": company.metadata["evidence_status"],
        "cases": {name: result.summary for name, result in cases.items()},
        "reverse": root,
    }
    (output / "results.json").write_text(json.dumps(evidence, indent=2) + "\n")
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.labelcolor": "#243d55",
            "text.color": "#142c46",
            "axes.edgecolor": "#c5cfd9",
            "figure.facecolor": "#ffffff",
        }
    )
    fig, ax = plt.subplots(figsize=(10, 4.7), layout="constrained")
    x = np.arange(3)
    for shift, key, label, color in [
        (-0.19, "nav_per_share", "Asset NAV", "#9ab0c5"),
        (0.19, "dcf_per_share", "Remaining-life DCF", "#214e76"),
    ]:
        bars = ax.bar(x + shift, summaries[key], width=0.36, label=label, color=color)
        ax.bar_label(bars, fmt="$%.2f", padding=4, fontsize=10)
    ax.axhline(
        company.facts["share_price"],
        color="#a05a25",
        linestyle="--",
        linewidth=1.5,
        label=f"Market close ${company.facts['share_price']:.2f}",
    )
    ax.set_xticks(x, ["Bear", "Base", "Bull"])
    ax.set_ylabel("USD per common share")
    ax.set_title(
        "Asset backing and cash generation give different answers",
        loc="left",
        pad=22,
        fontweight="bold",
        fontsize=14,
    )
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.13), ncol=3, frameon=False, fontsize=10)
    ax.margins(y=0.20)
    ax.grid(axis="y", color="#edf1f5")
    ax.set_axisbelow(True)
    fig.savefig(output / "valuation.png", dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    short = base.forecast.iloc[:12]
    axes[0].bar(short.label, short.ufcf / 1e6, color="#214e76")
    axes[0].set_ylabel("Unlevered cash flow, USD millions")
    axes[0].tick_params(axis="x", rotation=55, labelsize=9)
    axes[0].set_title("First three years", loc="left", fontweight="bold")
    active = base.forecast.owned / base.forecast.days
    axes[1].fill_between(base.forecast.end, active, color="#d8e3ed")
    axes[1].plot(base.forecast.end, active, color="#214e76")
    axes[1].set_ylabel("Average operating vessels in each period")
    axes[1].set_title("Fleet retires without replacement", loc="left", fontweight="bold")
    fig.savefig(output / "cash-and-fleet.png", dpi=160)
    plt.close(fig)
    esc = html.escape
    rows = "".join(
        f"<tr><th>{name.title()}</th><td>${r.summary['nav_per_share']:.2f}</td>"
        f"<td>${r.summary['dcf_per_share']:.2f}</td><td>{r.summary['price_nav']:.2f}×</td>"
        f"<td>${r.summary['next_year_ufcf'] / 1e6:,.1f}m</td></tr>"
        for name, r in cases.items()
    )
    limitations = "".join(f"<li>{esc(note)}</li>" for note in company.metadata["limitations"])
    sources = "".join(
        f"<li><a href='{esc(s['url'], quote=True)}'>{esc(s['title'])}</a>"
        f" <span class='muted'>Published {esc(s['published'])}</span></li>"
        for s in company.sources
    )
    root_text = (
        f"{abs(root['multiplier'] - 1) * 100:.1f}% {'higher' if root['multiplier'] >= 1 else 'lower'}"
        if root["status"] == "solved"
        else "an unavailable change in"
    )
    nav_relation = "below" if base.summary["price"] < base.summary["nav_per_share"] else "above"
    dcf_relation = "below" if base.summary["price"] < base.summary["dcf_per_share"] else "above"
    rate_rows = "".join(
        f"<tr><th>{esc(cls)}</th><td>${company.case()['tce_' + cls]:,.0f}/day</td></tr>"
        for cls in company.metadata["class_order"]
    )
    matrix = pd.DataFrame(sensitivity).pivot(
        index="discount_adjustment", columns="rate_multiplier", values="dcf_per_share"
    )
    matrix.index = [f"{company.case()['wacc'] + v:.0%}" for v in matrix.index]
    matrix.columns = [f"{v:.1f}× rates" for v in matrix.columns]
    sensitivity_html = matrix.to_html(float_format=lambda v: f"${v:.2f}", border=0)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(company.metadata["name"])} | Shipping equity research</title>
<style>
:root{{--ink:#142c46;--muted:#54677a;--line:#dce4eb;--paper:#f3f6f8;--blue:#214e76}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);font:16px/1.6 system-ui,-apple-system,sans-serif;color:var(--ink)}}
header{{background:var(--ink);color:white;padding:48px max(6vw,24px) 42px}}header .eyebrow{{color:#b9cddd;letter-spacing:.12em;font-size:12px;text-transform:uppercase}}h1{{font-size:clamp(32px,5vw,52px);line-height:1.12;margin:16px 0}}header p{{max-width:800px;color:#d2dde6}}
nav{{padding:14px max(6vw,24px);background:white;border-bottom:1px solid var(--line);display:flex;gap:26px;flex-wrap:wrap}}a{{color:var(--blue);text-underline-offset:3px}}nav a{{text-decoration:none;font-size:14px}}
main{{max-width:1140px;margin:32px auto;padding:0 24px}}section{{background:white;border:1px solid var(--line);border-radius:10px;padding:30px;margin:24px 0;scroll-margin-top:16px}}h2{{font-size:25px;margin:0 0 14px;line-height:1.25}}h3{{font-size:17px;margin:24px 0 8px}}p{{max-width:920px}}.muted{{color:var(--muted);font-size:14px}}.cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}.card{{background:white;border:1px solid var(--line);border-radius:10px;padding:24px}}.card strong{{display:block;font-size:34px;margin:8px 0}}.card span{{font-size:14px;color:var(--muted)}}
.notice{{border-left:4px solid #ac7539;padding:12px 18px;background:#faf5ed;font-size:14px}}img{{display:block;width:100%;height:auto;margin:18px 0}}table{{border-collapse:collapse;width:100%;font-size:14px;margin:20px 0}}td,th{{text-align:right;padding:12px 10px;border-bottom:1px solid var(--line)}}th:first-child{{text-align:left}}thead{{background:#edf2f6}}.table-wrap{{overflow-x:auto}}li{{margin:9px 0}}code{{background:#edf2f6;padding:3px 6px;border-radius:4px;font-size:13px}}footer{{padding:15px 0 40px;color:var(--muted);font-size:13px}}@media(max-width:680px){{.cards{{grid-template-columns:1fr}}section{{padding:20px}}header{{padding-top:32px}}}}
</style></head><body>
<header><div class="eyebrow">Shipping equity research · {esc(company.metadata["ticker"])}</div>
<h1>{esc(company.metadata["name"])}</h1><p>What is the fleet worth, what cash can it generate, and what freight rates justify the share price?</p>
<div class="muted" style="color:#c0d1df">Snapshot {esc(company.metadata["valuation_date"])} · USD · Base case selected · Public inputs and explicit scenarios</div></header>
<nav aria-label="Report sections"><a href="#view">Research view</a><a href="#cases">Valuation</a><a href="#cash">Cash flow</a><a href="#rates">Implied rates</a><a href="#evidence">Evidence</a></nav>
<main><div class="cards"><div class="card">Market close<strong>${base.summary["price"]:.2f}</strong><span>Dated share price</span></div>
<div class="card">Asset NAV<strong>${base.summary["nav_per_share"]:.2f}</strong><span>Per share · excludes overhead PV</span></div>
<div class="card">Remaining-life DCF<strong>${base.summary["dcf_per_share"]:.2f}</strong><span>Per share · includes operating overhead</span></div></div>
<section id="view"><h2>Read the two valuation lenses together</h2><p>The base scenario places the share price {nav_relation} estimated fleet asset NAV and {dcf_relation} the value supported by modeled remaining-life cash flows. This is a conditional research result. The gap does not establish mispricing: asset marks, the cash bridge, future rates and fleet renewal can change the conclusion.</p>
<div class="notice">{esc(company.metadata["evidence_status"])}. Peer valuations and historical forecast validation are not included in this release.</div>
<h3>Start here</h3><p>Open <a href="{esc(company.metadata["ticker"])}-valuation.xlsx">the Excel model</a>, read <strong>Summary</strong>, then use <strong>Assumptions D5</strong> to switch cases. Blue text on pale yellow cells marks editable assumptions. NAV, Cash Flow and Debt explain the result; Sources and Checks let you audit it.</p>
<p class="muted">This HTML report is a saved Python run. Excel edits recalculate Excel only. Change the reviewed input files and rerun the command to refresh this report and the notebook.</p></section>
<section id="cases"><h2>Three explicit scenarios</h2><p>Each case changes freight rates, vessel marks, costs, off-hire, retirement age, financing and discount assumptions together. These are scenario values, not probabilities or price targets.</p><img src="valuation.png" alt="Scenario chart comparing asset NAV, remaining-life DCF and market price">
<div class="table-wrap"><table><thead><tr><th>Case</th><th>NAV / share</th><th>DCF / share</th><th>Price / NAV</th><th>Next-year UFCF</th></tr></thead><tbody>{rows}</tbody></table></div>
<h3>DCF sensitivity</h3><p class="muted">Rows vary the total discount rate; columns multiply all open class rates. Other base assumptions stay fixed. Values are USD per share.</p><div class="table-wrap">{sensitivity_html}</div></section>
<section id="cash"><h2>Cash flows end when the fleet retires</h2><p>The forecast starts the day after valuation, models twelve quarters, then runs annually through retirement. Delivery payments, maintenance, drydocking, working capital and scrap proceeds are explicit. No perpetual terminal value or unfunded replacement fleet is assumed.</p><img src="cash-and-fleet.png" alt="Quarterly free cash flow and finite fleet runoff">
<p>Base next-year unlevered free cash flow is <strong>${base.summary["next_year_ufcf"] / 1e6:,.1f}m</strong>. Cash after assumed debt repayments and interest is <strong>${base.summary["next_year_equity_cash"] / 1e6:,.1f}m</strong>, before dividends. It is not a dividend forecast.</p></section>
<section id="rates"><h2>What does the market price require?</h2><p>Under the fixed base assumptions, the reverse valuation requires <strong>{root_text} open charter rates</strong> relative to the base vector. The Python solution is repriced through the full model, including the extra working capital associated with higher revenues.</p><div class="table-wrap"><table><thead><tr><th>Vessel class</th><th>Base open TCE</th></tr></thead><tbody>{rate_rows}</tbody></table></div><p class="muted">TCE means time-charter-equivalent earnings after voyage costs. These USD/day inputs are scenarios, not Baltic index points or a licensed forward curve.</p></section>
<section id="evidence"><h2>Evidence and remaining research</h2><ul>{limitations}</ul><h3>Source documents</h3><ul>{sources}</ul><h3>Reproduce and inspect</h3><p><code>uv run shipping-equity run {esc(company.metadata["ticker"])}</code></p><p>Inspect <a href="results.json">machine-readable results</a>, <a href="scenarios.csv">scenario values</a>, <a href="base-cash-flow.csv">the base cash schedule</a> and <a href="reconciliation.json">Excel–Python reconciliation</a>.</p></section>
<footer>Input fingerprint: <code>{company.fingerprint[:16]}</code> · Research snapshot; no live prices or automatic filing updates.</footer></main></body></html>"""
    (output / "report.html").write_text(page)
    return evidence
