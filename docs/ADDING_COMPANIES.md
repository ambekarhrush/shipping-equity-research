# Adding another dry-bulk company

The company is data; the valuation engine is shared. Add a separate folder and source ledger.
Do not copy another company's numerical assumptions without reviewing and documenting them.

## Create the package

```bash
uv run shipping-equity init-company GNK --name "Genco Shipping & Trading" --date 2026-10-09
```

This creates blank inputs in `data/companies/GNK/` and refuses to overwrite an existing folder.
It deliberately does not download data or produce a valuation from missing facts.

| File | What to supply |
| --- | --- |
| `company.json` | Identity, USD currency, dry-bulk segment, valuation/price/cutoff dates, horizon, class order, reported DWT and limitations. |
| `sources.json` | Unique IDs, document titles, URLs, publication dates and source-definition notes. |
| `fleet.csv` | Stable vessel IDs, class, DWT, build year, delivery, appraisal date/value, remaining payments and evidence status. |
| `financials.csv` | Reviewed financial facts in stated units, each with period, source ID, exact location, status and notes. |
| `debt.csv` | Remaining principal and explicit assumed or observed payment dates. |
| `assumptions.json` | Bear/base/bull numerical drivers, units and the rationale for each range. |

Zero means **reviewed and zero**. A missing value means **not reviewed**. Never use zero
as a convenient substitute for an unknown cash balance, charter position or liability.

## Normalize definitions before numbers

Use USD, not USD thousands, in normalized financial and fleet values. Shares are individual
shares, not millions. Rates are USD/day, fractions are 0–1, appraisal factors are multiples.
ISO dates are `YYYY-MM-DD`. The current price must match the valuation date. Source
publication dates must not exceed the end-of-day information cutoff.

Use the six standard dry-bulk classes in the template and keep unused classes with zero
vessels for the standard Excel layout. The Python engine can calculate a subset of classes.
Every present class requires its `tce_<class>` driver. A new class taxonomy requires a
review of the workbook layout as well as the economic definitions.

`financials.csv` contains a named contract used by both implementations. The blank template
retains all required keys and units. In particular:

- `cash` excludes restricted cash. `bridge_cash` is a separate assumption for unreported net
  cash changes, excluding the named equity, dividend and debt-payment bridges.
- `bank_debt_gross` plus `finance_leases`, less completed `debt_payments`, must match the
  remaining debt schedule. Carrying-value deductions stay separate from principal.
- `shares` plus completed `equity_issued` must match `adjusted_shares`. Unused `atm_capacity`
  is not issuance. Hypothetical draw adds both fee-adjusted cash and new shares.
- `operating_working_capital` is the opening operating asset/liability balance. Do not count
  it again within `extra_claims`. Keep the gross cash/debt classification consistent.
- Reconcile company TCE definitions to voyage revenue, voyage costs, charter hire and
  derivatives. Review the available-day denominator and nonrecurring gains separately.

All source IDs in CSVs must exist in the ledger; multiple IDs are separated by semicolons.
Vessel IDs must be unique and stable. Preserve source typos in a source field and document
the mapping; do not silently invent an IMO. Future delivery dates must be labeled assumed.

## Respect the model boundary

Retirement occurs on 1 July of build year plus the case's retirement age. Forecast end year
must extend beyond the last retirement in every case. `remaining_capex_usd` is paid once at
delivery; already delivered vessels must have zero remaining delivery payments.

The current engine rejects planned disposals: selling a ship requires an explicit sale
price and proceeds module, not treating a sale as scrap. It assumes no fleet renewal after
committed deliveries. Class rates share one fixed/open fraction and one fixed rate; a
company with material heterogeneous contract cover requires a charter-book extension.
Tankers, containers and LNG carriers are intentionally rejected by the segment check.

## Validate and publish the evidence

```bash
uv run shipping-equity validate GNK
uv run shipping-equity run GNK
uv run python scripts/export_workbook_inputs.py GNK
# With the spreadsheet authoring runtime:
node scripts/build_workbook.mjs
uv run shipping-equity reconcile GNK --evidence outputs/gnk-2026-10-09/excel-calculation-evidence.json
```

Review the generated files and reproduce source totals before writing an investment view.
The SBLK notebook is a company research narrative; a new company's notebook should explain
its own evidence and economics while importing the same calculation package. The shared
report and output folder are generated automatically. Keep raw vendor archives, credentials
and proprietary freight curves out of Git history.
