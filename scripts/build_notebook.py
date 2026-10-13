"""Generate and execute the research walkthrough using the installed local package."""

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
nb.cells = [
    md("""# Shipping equity research
## Star Bulk: assets, cash flows and implied freight rates

**Snapshot: 9 October 2026.** This walkthrough calculates from reviewed CSV/JSON inputs.
It does not read spreadsheet answers to produce valuations. Excel calculation evidence is
read only in the final reconciliation step.

The research question is whether dated fleet asset backing and sustainable cash generation
support the same conclusion. The output is conditional on disclosed assumptions;
the cash bridge, charter book and remaining newbuild payments are not fully observed.

Read the source notes before treating an output as an investment conclusion."""),
    code("""from pathlib import Path
import json
import pandas as pd
from IPython.display import display, Image
from shipping_equity.data import load_company
from shipping_equity.valuation import value_company, reverse_valuation
from shipping_equity.reconcile import reconcile

ROOT = Path.cwd()
if not (ROOT / 'data/companies').exists():
    ROOT = ROOT.parent
company = load_company(ROOT / 'data/companies/SBLK')
OUT = ROOT / 'outputs/sblk-2026-10-09'
print(company.metadata['name'], company.metadata['valuation_date'])
print('Input SHA-256:', company.fingerprint)"""),
    md("""## 1. Begin with the evidence

The October fleet register contains 135 operating vessels and three committed newbuilds.
The appraisal annexes use earlier effective dates; joining by individual vessel identity
excludes two sold ships. The appraisal's introductory vessel count conflicts with its rows.
The raw source IMO typo is retained, not silently corrected.

Source financial statements report USD thousands. Input CSVs convert them to USD exactly once.
Restricted cash is excluded from available cash. Completed share issuance and debt repayments
are bridged separately; unused ATM capacity is not treated as completed dilution."""),
    code("""display(pd.DataFrame(company.sources)[['id', 'published', 'title', 'url']])
display(company.fleet.groupby('vessel_class').agg(
    vessels=('vessel_id','count'), dwt=('dwt','sum'), appraisal_usd=('appraisal_usd','sum')))
f = company.facts
assert f['voyage_revenue'] - f['voyage_cost'] - f['charter_hire'] + f['realized_derivatives'] == f['tce_revenue']
assert f['opening_total_cash'] + f['cash_from_operations'] + f['cash_from_investing'] + f['cash_from_financing'] == f['closing_total_cash']
print('Historical TCE revenue and cash-flow bridges reconcile.')"""),
    md("""## 2. Make the scenarios explicit

TCE is time-charter-equivalent earnings in USD/day, applied to available vessel days.
Vessel costs accrue on ownership days. Off-hire is a fraction of those days.
The base model assumes open-market exposure; this is not a reconstructed charter book.
The rate vector is an editable scenario, not an FFA curve or a statistical forecast.

Corporate overhead scales with fleet activity, subject to a fixed-cost fraction while vessels
operate. Drydock cash uses a smoothed annual budget. Both rates and costs inflate at 2% in the
base scenario; changing this assumption requires economic judgment."""),
    code("""assumptions = pd.DataFrame(company.assumptions.values())
display(assumptions[['label','unit','bear','base','bull','rationale']])
cases = {case: value_company(company, case) for case in ['bear','base','bull']}
summary = pd.DataFrame({case: result.summary for case, result in cases.items()}).T
display(summary[['price','nav_per_share','dcf_per_share','price_nav','next_year_ufcf','next_year_equity_cash']].round(2))"""),
    md("""## 3. Two valuation lenses

Asset NAV adds unrestricted cash and operating working capital to fleet appraisals, then
subtracts gross debt, other claims and remaining committed delivery payments. Paid deposits
are not added again. This asset NAV excludes the present value of future corporate overhead.

The DCF forecasts twelve quarters and annual fleet runoff. Cash flows include maintenance,
delivery payments, working capital and scrap. Interest and principal belong in the separate
financing schedule; they are not deducted again in unlevered enterprise value.
There is no perpetual terminal value or unfinanced replacement fleet."""),
    code("""base = cases['base']
display(pd.Series(base.nav, name='USD unless per-share/ratio'))
display(base.forecast[['label','owned','available','revenue','operating','maintenance','newbuild','scrap','delta_wc','ufcf','pv']].head(12).round(2))
display(Image(filename=str(OUT / 'valuation.png')))"""),
    md("""The base result puts asset NAV above the $29.70 close, but DCF below it.
The two outputs are not averaged into a price target. NAV reflects dated asset marks;
DCF reflects explicit earnings, costs, overhead and finite lives. The wide scenario range
shows the model's exposure to operating and asset assumptions, not a statistical confidence interval.

The bear case also produces a financing shortfall under the assumed repayment schedule.
This is a prompt to examine refinancing, liquidity and capital actions. It is not a covenant
prediction or a distressed-equity valuation model."""),
    code("""display(base.financing.head(12).round(2))
display(summary[['minimum_cash_headroom']].round(2))
display(Image(filename=str(OUT / 'cash-and-fleet.png')))
assert abs(base.forecast.delta_wc.sum() + company.facts['operating_working_capital']) < 1e-6
assert base.forecast.owned.iloc[-1] == 0
assert abs(base.financing.closing_debt.iloc[-1]) < 1e-6"""),
    md("""## 4. Reverse the price

Solve one common multiplier on the open class-rate vector, with all other base assumptions
fixed. A bracketed bisection solver finds the root, then reprices it through the full model.
Working capital changes with earnings. With 100% fixed charter coverage, this parameter
would be unidentifiable rather than having a meaningful implied rate."""),
    code("""root = reverse_valuation(company)
display(root)
assert root['status'] == 'solved'
repriced = value_company(company, rate_multiplier=root['multiplier'])
assert abs(repriced.summary['dcf_per_share'] - company.facts['share_price']) < 1e-8
print(f"Implied open rates: {(root['multiplier'] - 1):.2%} above base under the fixed assumptions.")
display(pd.read_csv(OUT / 'sensitivity.csv').pivot(index='discount_adjustment', columns='rate_multiplier', values='dcf_per_share').round(2))"""),
    md("""## 5. Change one assumption at a time

These stresses expose mechanisms. A higher interest rate changes post-financing cash;
it does not change this unlevered DCF unless the discount-rate assumption also changes.
A weaker asset mark changes NAV but does not mechanically overwrite operating cash flows."""),
    code("""stresses = {
    'Base': {},
    'Kamsarmax rate -20%': {'tce_Kamsarmax': company.case()['tce_Kamsarmax'] * .8},
    'Off-hire +5 percentage points': {'offhire': company.case()['offhire'] + .05},
    'Vessel opex +10%': {'opex': company.case()['opex'] * 1.1},
    'Interest +2 percentage points': {'interest': company.case()['interest'] + .02},
    'Asset marks -20%': {'asset_factor': .8},
}
display(pd.DataFrame({name: value_company(company, overrides=overrides).summary
                      for name, overrides in stresses.items()}).T[
    ['nav_per_share','dcf_per_share','next_year_equity_cash','minimum_cash_headroom']].round(2))"""),
    md("""## 6. Reconcile the independent implementations

Excel was built first from formulas. This package independently implements the same
economic definitions. The comparison covers summary controls and every modeled cash-flow
and financing period across bear/base/bull. An input fingerprint rejects stale evidence.

This test checks arithmetic consistency. It does not establish that an assumption is true.
Native Excel checks are recorded separately in the verification document."""),
    code("""audit = reconcile(company, OUT / 'excel-calculation-evidence.json')
display({k: v for k, v in audit.items() if k not in ['controls','failures']})
assert audit['status'] == 'pass', audit['failures']
display(pd.DataFrame(audit['controls']).head(12))"""),
    md("""## 7. What would improve this research?

Update the cash bridge, remaining newbuild payments and vessel marks; reconstruct actual
charter coverage; replace approximate maturity dates and smoothed docking budgets with
reviewed schedules. Normalize Genco and Safe Bulkers before making relative-value claims.
Historical validation requires genuine as-of forecasts and later operating disclosures.

The current project supports additional dry-bulk stocks through independent data folders.
Use `shipping-equity init-company` and follow `docs/ADDING_COMPANIES.md`. Do not copy Star Bulk
facts into another ticker. Tankers, containers and LNG carriers require reviewed segment economics.
The separate `tests/fixtures/SYNTH` package is entirely invented and only tests arithmetic."""),
]
path = ROOT / "notebooks/SBLK-research.ipynb"
nbf.write(nb, path)
NotebookClient(
    nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
).execute()
nbf.write(nb, path)
print(f"Executed {path.relative_to(ROOT)}")
