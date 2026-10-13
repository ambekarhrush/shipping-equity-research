# Five-minute guide

## Read the result

Open the [local report](../outputs/sblk-2026-10-09/report.html) after downloading or cloning
the repository. It begins with the dated share price, asset NAV and remaining-life DCF.
The [research note](RESEARCH_NOTE.md) explains why the two valuation methods differ.
The [executed notebook](../notebooks/SBLK-research.ipynb) shows the calculations and stresses.

## Using Excel

Open the [workbook](../outputs/sblk-2026-10-09/SBLK-valuation.xlsx) in Microsoft Excel.
Allow normal calculation. The workbook has no macros or external data connections.

1. **Summary:** the three research questions and their calculated answers.
2. **Assumptions:** one authoritative case selector in D5. Enter 1, 2 or 3.
   Active assumptions sit above the three case inputs. Blue inputs on pale yellow are editable.
3. **NAV:** follow appraisal values, cash, claims, delivery payments and shares to equity NAV.
4. **Cash Flow / Debt:** trace operating earnings, investment, financing and retained cash.
5. **Fleet / Days:** inspect individual vessel evidence and calendar overlaps.
6. **Historical / Sources / Checks:** inspect reported-history bridges, source locations and controls.

**A useful demonstration:** keep D5 at 2, raise D6 from 1.00 to 1.10, and return to Summary.
DCF rises as open freight earnings increase; NAV stays the same. Restore D6 to 1.00.
Then change the base asset-value factor from 1.00 to 0.90. NAV falls; operating DCF stays
unchanged. Restore the input. This separates earnings assumptions from asset marks.

The native two-input sensitivity table is **Assumptions L8:Q13**. Columns vary D6 and rows
vary D7, an additive discount-rate adjustment. Its center corresponds to the selected case
at a 1.00 rate multiplier and zero discount adjustment. Excel must calculate data tables.

Cells with green formulas link across sheets; black formulas calculate within a sheet.
Large cash figures display in **USD millions**, with raw source amounts in USD. TCE is
USD/day. Negative amounts use parentheses. A blank selected case input is an error;
an explicit zero is a valid input where economically appropriate.

Changes in Excel remain in Excel. To change the reproducible research case, update the
CSV/JSON source package, rerun Python, and rebuild Excel. Reconciliation rejects stale
workbook evidence after any input-file change. It does not certify unsaved Excel edits.

## Python commands

Run from the repository root:

```bash
uv sync --frozen --extra dev
uv run shipping-equity validate SBLK
uv run shipping-equity run SBLK
uv run shipping-equity reconcile SBLK --evidence outputs/sblk-2026-10-09/excel-calculation-evidence.json
uv run python scripts/build_notebook.py
```

`run` writes a report, charts, scenarios, a sensitivity table and all three cash/financing
schedules to `outputs/<ticker>-<date>/`. Pass `--output PATH` to use a different folder.
It makes no network requests. It does not refresh source documents or write an Excel file.

## Rebuilding the workbook

The supplied `.xlsx` is usable without an authoring runtime. Rebuilding it requires Node
and `@oai/artifact-tool` from the Codex spreadsheet runtime. That package is not installed
by `uv sync`. Do not substitute a library that caches answers without preserving formulas.

In an environment with that runtime available:

```bash
uv run python scripts/export_workbook_inputs.py SBLK
node scripts/build_workbook.mjs
uv run shipping-equity reconcile SBLK --evidence outputs/sblk-2026-10-09/excel-calculation-evidence.json
```

The builder derives dates, row counts, labels and source references from the selected
company package. It exports formula-calculation evidence and sheet previews. Close the
workbook before rebuilding. Validate it in the intended spreadsheet application afterward,
including scenario changes and native data-table behavior.
