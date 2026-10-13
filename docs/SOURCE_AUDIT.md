# Source audit: SBLK

**Information cutoff:** end of 9 October 2026. Reviewed on 12 October 2026.
This is an end-of-day research snapshot, not an intraday reconstruction of what was
available at the precise market close. Monetary input CSVs use USD.

## Evidence ledger

| Source | Use | Important qualification |
| --- | --- | --- |
| [H1 2026 interim filing](https://www.sec.gov/Archives/edgar/data/1386716/000095015726000860/sblk-20260630.htm) | Financial statements, TCE bridge, cash flow, debt, liquidity and newbuild commitments. | Statement date 30 June; original financial tables are USD thousands. |
| [Filed Arrow appraisal](https://www.sec.gov/Archives/edgar/data/1386716/000095015726000983/ex99-1.htm) | Individual vessel market-value evidence. | Effective dates 30 June and 21 August; charter-free desktop appraisal, not October executable sale prices. |
| [9 October prospectus](https://www.sec.gov/Archives/edgar/data/1386716/000114036126039279/ny20083494x2_424b5.htm) | Updated fleet, completed issuance, adjusted capitalization and unused ATM programs. | Known transaction bridges are separated from undisclosed intervening cash movements. |
| [Stock Analysis history](https://stockanalysis.com/stocks/sblk/history/) and [ChartExchange history](https://chartexchange.com/symbol/nasdaq-sblk/historical/) | $29.70 closing price for 9 October. | Secondary sources; closes agree, volume differs and is not used. Pages can roll forward. |

The machine-readable [source ledger](../data/companies/SBLK/sources.json) records IDs and
publication dates. CSV source-location fields identify the relevant tables or notes.
Only normalized individual facts are included; raw downloaded filings and vendor archives
are excluded from the repository.

## Fleet reconciliation

The operating prospectus register contains **135 vessels and 13,504,552 DWT**. Three
committed newbuilds add 246,000 DWT. The appraisal register joined to those 138 records
totals **$4,303.5m** before any scenario adjustment.

The appraisal introduction says 133 owned vessels, but Annex A contains 135 numeric vessel
rows, including Pendulum and Star Eva. Annex B contains five additional vessels. Joining
the individual appraisal rows to the October prospectus excludes the two disposals and
avoids treating the source's introductory count as authoritative arithmetic.

Explicit name mappings cover the appraisal spelling `Star Magnaminus`, the SBI/Star
Macarena, Lambada, Capoeira and Carioca names, `Roberta`, and `Stardust` capitalization.
The source IMO for Star Kingfisher contains a letter (`9441S348`). It is retained in
`source_imo`; the model uses stable local vessel IDs rather than guessing the corrected IMO.

## Observed bridges and estimated balances

| Item | Treatment |
| --- | --- |
| June unrestricted cash | $498.165m. Restricted cash of $67.117m is excluded. |
| Completed equity proceeds | Add $116m and 4.4m shares. Resulting share count: 116,071,386. |
| Subsequent dividend | Subtract $100.8m. |
| Debt reduction | Subtract $92.223m from both cash and gross debt. |
| Opening gross debt | $949.072m after payments; carrying value is $944.355m after $4.717m issuance costs. |
| Residual cash bridge | **Assumed** $50m / $100m / $150m in bear/base/bull. Includes net intervening operations, asset transactions, delivery cash and restricted-cash movements not separately bridged. |
| Base valuation-date cash | **Estimated** $521.142m, not an observed October cash balance. |
| Operating working capital | **Estimated October proxy:** $26.595m, derived from June operating balances. |
| Remaining newbuild cash | **Estimated** $24.407m each for three future deliveries, based on the June $122.035m total across five vessels. |
| Future delivery date | **Assumed** 31 December 2026 for the three disclosed Q4 deliveries. |
| ATM capacity | $116.37111m across the disclosed programs; no completed issuance is assumed from capacity alone. |

The Deutsche program cover/detail gives $41.37111m although one body passage repeats $75m.
The model uses the cover/detail together with the separate $75m Jefferies capacity.
Base ATM draw and fees-paid-on-unused-capacity are zero. Potential dilution is an editable scenario.

## Historical controls

TCE revenue reconciles to $498.725m:

`$638.564m voyage revenue − $110.373m voyage costs − $27.103m charter hire − $2.363m realized derivatives`

The denominator is 23,202 available days. The disclosed rounded TCE is $21,495/day.
A malformed text-rendering occurrence is not used in place of the specific reconciliation
table. Removing the disclosed $27m bunker gain is one explicit normalization, not a claim
to have fully estimated mid-cycle earnings. Charter hire is not deducted twice.

Cash reconciles: $501.934m opening cash + $262.275m operating − $17.317m investing
− $181.610m financing = $565.282m closing cash, including restricted cash.

## Approximations that matter

The debt schedule allocates the completed repayment to the earliest disclosed maturity
bucket and uses annual assumed payment dates. The “thereafter” amount is assigned to 2033.
These choices reconcile principal but do not establish the exact debt-service calendar.

Appraisals are charter-free. Actual vessel charter coverage and net charter-in economics
have not been reconstructed; the base open-fleet assumption and zero net charter-in value
are material simplifications. The base other-claims adjustment is zero and requires review.
Drydocking is a smoothed cash budget; scrap uses DWT rather than lightweight steel tonnage.

Priority updates are current cash and restricted-cash movements, exact delivery balances,
the charter book, current vessel marks, and the debt/drydock calendars. These are research
gaps, not errors that can be cured by displaying more decimal places.
