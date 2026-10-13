# Star Bulk: asset support does not settle the earnings question

**9 October 2026 snapshot · NASDAQ: SBLK · USD**

The base scenario estimates asset NAV of **$32.99/share**, above the **$29.70** close,
but finite-life DCF of **$26.55/share**, below it. At **0.90× estimated NAV**, the shares
show an asset discount under the selected marks. The operating model nevertheless needs
**5.55% higher open class rates** than the base vector to justify the price with all other
inputs fixed. This evidence does not support an unconditional Buy conclusion.

| Scenario | Asset NAV/share | DCF/share | 2027 UFCF | 2027 cash after financing |
| --- | ---: | ---: | ---: | ---: |
| Bear | $24.59 | $2.24 | $109.5m | −$96.4m |
| Base | $32.99 | $26.55 | $442.5m | $249.5m |
| Bull | $39.11 | $57.20 | $750.7m | $566.3m |

These are jointly specified economic scenarios, not confidence bounds. There are no
probability weights or mechanically averaged target prices. The dated price is corroborated
by [Stock Analysis](https://stockanalysis.com/stocks/sblk/history/) and
[ChartExchange](https://chartexchange.com/symbol/nasdaq-sblk/historical/).
All computed values are reproducible from [the result file](../outputs/sblk-2026-10-09/results.json).

## What supports the asset case

The 138-vessel committed register has $4,303.5m of joined appraisal values before scenario
adjustments. Asset NAV explicitly subtracts remaining delivery obligations and gross debt,
adds estimated available cash and operating working capital, and uses the completed
issuance-adjusted share count. Book value is not substituted for vessel market value.

The evidence is dated: June and August appraisals joined to the October fleet list.
They are not independent October broker marks or guaranteed liquidation proceeds.
See the [appraisal](https://www.sec.gov/Archives/edgar/data/1386716/000095015726000983/ex99-1.htm)
and the [October prospectus](https://www.sec.gov/Archives/edgar/data/1386716/000114036126039279/ny20083494x2_424b5.htm).

## What the cash-flow lens adds

Ships retire, corporate overhead consumes cash, and maintenance and delivery payments
must be funded. The DCF follows those cash flows to finite retirement rather than awarding
an aging fleet a perpetual terminal value. No unfinanced fleet replacement is assumed.
This makes the cash-flow result sensitive to earnings, operating costs, life assumptions
and the selected discount rate.

The base model uses class TCE of $26,000 Newcastlemax, $24,000 Capesize, $16,000 Post Panamax,
$17,000 Kamsarmax, $16,500 Ultramax and $14,500 Supramax per available day. It assumes 5%
off-hire, $5,300/day vessel opex, $460/day management, 25-year retirement and a 10% discount
rate. Both recurring costs and rates inflate at 2%. The implied-rate calculation preserves
this structure while raising the open rate vector by one common multiplier.

Under the bear case, minimum modeled cash headroom is **−$150.5m** against the illustrative
liquidity threshold. The no-refinancing, no-dividend financing path is not a claim that this
outcome will occur. It identifies a combination of rates, costs and repayment assumptions
that requires a capital-allocation or funding response. Exact maturity dates and covenant
definitions have not been reconstructed.

## What could change the view

The asset-discount observation would weaken with lower current vessel marks or unrecognized
claims. The operating case would improve with demonstrably sustainable rates above the base
vector, lower cash costs or value-accretive renewal that includes its financing costs.
It would weaken with extended off-hire, weaker earnings, higher upkeep or costly dilution.

The next useful evidence is the remaining Q4 delivery cash, subsequent reported cash and
charter coverage, updated vessel valuations, and a reviewed repayment schedule. These are
research checkpoints, not a verified catalyst calendar. No publication date is invented.
Peer claims must wait for comparable, dated GNK and SB inputs and consistent TCE definitions.

## What is established, and what is not

Historical TCE/cash bridges reconcile, and independently written Excel and Python schedules
agree. These establish arithmetic consistency. They do not validate the residual cash bridge,
charter-rate forecasts, appraisal adjustment or an investment horizon/target price.
The current output is a research framework and conditional valuation, with the remaining
evidence gaps listed in the [source audit](SOURCE_AUDIT.md).
