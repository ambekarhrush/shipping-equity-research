"""Build and execute a compact, company-neutral research notebook."""

from __future__ import annotations

import argparse
from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker")
    args = parser.parse_args()
    ticker = args.ticker.upper()
    md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
    nb = nbf.v4.new_notebook()
    nb.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    nb.cells = [
        md(f"""# {ticker} shipping-equity research

This executed notebook reads the reviewed company package and calculates independently of
the Excel workbook. It compares broker-anchored asset backing, finite-life cash flow and
the freight-rate assumptions implied by the dated share price. Results are scenarios, not
price targets or recommendations."""),
        code(f"""from pathlib import Path
import pandas as pd
from IPython.display import display, Image
from shipping_equity.data import load_company
from shipping_equity.valuation import value_company, reverse_valuation
from shipping_equity.reconcile import reconcile

ROOT = Path.cwd()
company = load_company(ROOT / 'data/companies/{ticker}')
OUT = ROOT / f"outputs/{{company.metadata['ticker'].lower()}}-{{company.metadata['valuation_date']}}"
print(company.metadata['name'], company.metadata['valuation_date'])
print('Evidence status:', company.metadata['evidence_status'])
print('Input SHA-256:', company.fingerprint)"""),
        md("""## Evidence and fleet

The source register distinguishes observed facts from estimates. Vessel values may use an
aggregate market anchor allocated across ships for runoff mechanics; read the audit notes
before interpreting vessel-level numbers."""),
        code("""display(pd.DataFrame(company.sources)[['id','published','title','url']])
display(company.fleet.groupby('vessel_class').agg(
    vessels=('vessel_id','count'), dwt=('dwt','sum'), fleet_value=('appraisal_usd','sum')))
display(pd.Series(company.metadata.get('audit_notes', []), name='Audit notes'))"""),
        md("""## Scenario outputs

Asset NAV and DCF answer different questions. NAV applies the selected mark to the fleet
and bridges cash, debt and claims. DCF models operating cash through each ship's retirement,
with no perpetual terminal value or unfinanced replacement fleet."""),
        code("""cases = {name: value_company(company, name) for name in ['bear','base','bull']}
summary = pd.DataFrame({name: result.summary for name, result in cases.items()}).T
display(summary[['price','nav_per_share','dcf_per_share','price_nav','next_year_ufcf','minimum_cash_headroom']].round(2))
display(Image(filename=str(OUT / 'valuation.png')))"""),
        md("""## Assumptions and reverse valuation

The reverse valuation changes one common multiplier across open class rates and reprices
the full model, including working capital. It does not estimate a probability distribution."""),
        code("""assumptions = pd.DataFrame(company.assumptions.values())
display(assumptions[['label','unit','bear','base','bull','rationale']])
root = reverse_valuation(company)
display(root)
if root['status'] == 'solved':
    repriced = value_company(company, rate_multiplier=root['multiplier'])
    assert abs(repriced.summary['dcf_per_share'] - company.facts['share_price']) < 1e-8"""),
        md("""## Cash flow, financing and reconciliation

Financing is kept separate from unlevered enterprise value. Excel and Python use independent
implementations; reconciliation establishes arithmetic agreement, not assumption accuracy."""),
        code("""base = cases['base']
display(base.forecast[['label','owned','available','revenue','operating','maintenance','newbuild','scrap','delta_wc','ufcf','pv']].head(12).round(2))
display(base.financing.head(12).round(2))
audit = reconcile(company, OUT / 'excel-calculation-evidence.json')
display({k: v for k, v in audit.items() if k not in ['controls','failures']})
assert audit['status'] == 'pass', audit['failures']
display(Image(filename=str(OUT / 'cash-and-fleet.png')))"""),
        md("""## Research limits

The limitations below are part of the model output. Update the reviewed input package as
new filings, fleet transactions, debt balances and independent vessel marks become available."""),
        code("""display(pd.Series(company.metadata['limitations'], name='Limitations'))"""),
    ]
    path = ROOT / "notebooks" / f"{ticker}-research.ipynb"
    nbf.write(nb, path)
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}).execute()
    nbf.write(nb, path)
    print(f"Executed {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
