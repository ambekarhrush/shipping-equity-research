# Verification record

Local checks performed on 12 October 2026 for the 9 October SBLK input snapshot.

## Independent calculations

[Reconciliation JSON](../outputs/sblk-2026-10-09/reconciliation.json) records **3,657 values**
across three scenarios: valuation controls, every cash-flow period, every financing period
and implied rates. Maximum absolute difference is approximately **0.00000191 USD**; the
cash tolerance is 0.0001 USD. Reverse-rate multiplier tolerance is 1e-8.

Excel formulas and Python code were implemented separately from the same normalized inputs.
The comparison consumes the workbook author's formula-calculation evidence, not merely
formula strings or manually copied displayed totals. Input fingerprints reject stale evidence.

## Native Microsoft Excel

The workbook was opened in Microsoft Excel for Mac and the case selector changed from
Base to Bear. The displayed results updated to $24.59 NAV/share and $2.24 DCF/share.
The recalculated file was saved and read back without modifying it.

[Native Excel evidence](../outputs/sblk-2026-10-09/native-excel-bear.json) records **1,244 values**,
including the cash and financing schedules, valuation controls, reverse valuation and
**all 25 native two-input data-table cells**. Each sensitivity cell was compared with a
complete Python valuation. The native `dataTable` object survived export and Excel save.
No formula errors were found in that saved scenario.

Temporary UI edits were discarded. The delivered workbook is restored to Base, D6 = 1.00
and D7 = 0.00. The artifact calculation engine separately checks a 10% rate edit and restore,
selected versus unselected blank assumptions, an explicit zero class rate, and zero common
rate-multiplier behavior. These boundaries are not all separately certified in native Excel.
No LibreOffice or Google Sheets compatibility claim is made.

## Automated economics and input tests

**23 tests pass locally.** The tests cover date overlap and leap days, source cash/TCE/share
bridges, capex/scrap/working-capital uniqueness, debt and cash identities, dilution, no-open
exposure, reverse repricing, invalid assumptions, source dates, missing/duplicate data,
forecast horizons, independent company identities, blank company scaffolding and stale
reconciliation evidence. A standalone invented company checks hand-calculated cash flows
and NAV without relying on Star Bulk's numerical answers.

```bash
uv run ruff check src tests scripts
uv run ruff format --check src tests scripts
uv run mypy src
uv run pytest -q
uv run shipping-equity validate SBLK
uv run shipping-equity --data-root tests/fixtures validate SYNTH
uv run shipping-equity reconcile SBLK --evidence outputs/sblk-2026-10-09/excel-calculation-evidence.json
```

The research notebook was executed successfully with eight code cells and no error outputs.
Its charts and scenarios come from the independent Python model. The Python report command
and source-validation commands ran against the included inputs without network access.

## Presentation and scope

All ten workbook sheet previews were visually reviewed, including source, calendar and
check sheets. Main summary values were also inspected in native Excel. Exported chart
images were reviewed for labels, units and appropriate period normalization. The local
HTML report was inspected in Safari, including its reading layout and sensitivity table.
README/documentation and report-relative links resolve to existing files.

Passing arithmetic, input checks and visual review are distinct from validating assumptions.
This release has no historical forecast accuracy, peer-relative-value, market-performance
or measured productivity claim. Hosted CI must be assessed from an actual run, not this
workflow configuration.
