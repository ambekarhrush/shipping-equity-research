# Shipping equity research

**Fleet value, finite-life cash flow and market-implied freight rates.**

Shipping equities can look inexpensive against vessel values while requiring demanding
future earnings. This project makes that comparison inspectable: start with individual
ships, follow their remaining cash flows, then solve the freight-rate assumption embedded
in the share price.

The first research case is **Star Bulk (SBLK), as of 9 October 2026**. The base scenario
produces **$32.99/share asset NAV** and **$26.55/share DCF**, against a **$29.70 close**.
These are conditional estimates, not a blended target or recommendation. The cash bridge,
remaining delivery payments and charter exposure need further review.

[Open the Excel model](outputs/sblk-2026-10-09/SBLK-valuation.xlsx) ·
[Read the executed notebook](notebooks/SBLK-research.ipynb) ·
[Research note](docs/RESEARCH_NOTE.md) ·
[Five-minute guide](docs/QUICK_START.md)

![Scenario comparison of asset NAV, finite-life DCF and the dated share price](outputs/sblk-2026-10-09/valuation.png)

## What the first release does

| Question | Model output |
| --- | --- |
| What is the fleet worth? | Vessel-level appraisals, remaining commitments and a common-equity NAV bridge. |
| What cash can it generate? | Twelve quarterly periods, annual fleet runoff, working capital, delivery payments and financing. |
| What rates justify the price? | A common open-rate multiplier, solved and repriced through the complete DCF. |
| What changes the conclusion? | Three coherent scenarios, freight/discount sensitivities and targeted notebook stresses. |
| Can the calculations be checked? | Independent Excel and Python implementations, source reconciliations and synthetic arithmetic tests. |

The reviewed register includes **135 operating vessels and three committed newbuilds**.
Excel and Python agree on **3,657 compared values** across all three scenarios, with a
maximum absolute difference below **$0.000002** in the cash schedules.
[Calculation evidence](outputs/sblk-2026-10-09/reconciliation.json) and
[verification details](docs/VERIFICATION.md) define the checks and their limits.

## Run it locally

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
uv sync --frozen --extra dev
uv run shipping-equity list
uv run shipping-equity validate SBLK
uv run shipping-equity run SBLK
uv run shipping-equity reconcile SBLK --evidence outputs/sblk-2026-10-09/excel-calculation-evidence.json
uv run python scripts/build_notebook.py
uv run pytest -q
```

Open `outputs/sblk-2026-10-09/report.html` in a browser for the local reading view.
The report, charts and CSVs regenerate offline from the committed inputs. GitHub displays
the notebook and README; download or clone the repository to open the HTML report locally.

The supplied Excel file is formula-driven. Change **Assumptions D5** to select Bear (1),
Base (2) or Bull (3); **D6** changes open charter rates and **D7** adjusts the discount rate.
Excel edits do not automatically update Python files or the saved report.
See the [workbook guide](docs/QUICK_START.md#using-excel) for the full reading order.

## Add another stock

Each company has its own six-file package under `data/companies/`. No ticker-specific
valuation equations are embedded in the Python engine.

```bash
uv run shipping-equity init-company GNK --name "Genco Shipping & Trading" --date 2026-10-09
# Fill the blank templates with reviewed, dated GNK inputs before running:
uv run shipping-equity validate GNK
uv run shipping-equity run GNK
```

The scaffold intentionally contains missing values. It never fills a new company with
Star Bulk's facts. Follow [Adding companies](docs/ADDING_COMPANIES.md) for field definitions,
source requirements and validation. The current economics support **dry bulk**; other
shipping segments need a reviewed extension. GNK and SB are future research cases, not
completed peer valuations.

## How it is organized

```text
data/companies/       Reviewed company facts, fleet, sources and assumptions
data/templates/       Blank inputs for the next company
src/shipping_equity/  Loading, fleet calendar, valuation, reconciliation and reporting
scripts/              Workbook authoring and executed-notebook generation
notebooks/            Research walkthrough with calculated outputs
outputs/              Dated workbook, report, charts, schedules and verification evidence
tests/fixtures/       Clearly separated synthetic company
docs/                 Research note, methodology, source audit and extension guide
```

Read [Methodology](docs/METHODOLOGY.md) for the equations and
[Source audit](docs/SOURCE_AUDIT.md) for the appraisal mismatch, date bridges and estimates.
The Excel authoring script uses `@oai/artifact-tool`, supplied by the Codex spreadsheet
runtime; it is a separate dependency from the portable Python workflow.
[Rebuilding Excel](docs/QUICK_START.md#rebuilding-the-workbook) explains that boundary.

## Research boundaries

This is a public-input snapshot with manually reviewed data, not an automated market-data
feed. Freight rates are explicit scenarios. There is no licensed FFA curve, reconstructed
charter book, full survey calendar, fleet-renewal financing model, completed peer comparison
or historical forecast validation. A passing arithmetic check does not validate an
investment thesis. See [release status](docs/BUILD_STATUS.md) for completed and deferred work.
