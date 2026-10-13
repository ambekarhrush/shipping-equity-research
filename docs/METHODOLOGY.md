# Model definitions

All calculations use USD. Presentation can scale cash values to millions. The model begins
the day after the valuation date, includes both ends of each reporting period, and excludes
the retirement day from operating days. The first twelve periods are quarters; later periods
are consecutive years. Cash flows are discounted at period end on an actual/365 basis.

## Fleet economics

For each vessel and period:

`ownership days = max(0, min(period end + 1 day, retirement) − max(period start, delivery))`

Retirement is 1 July in build year plus assumed retirement age. The midyear convention is
explicit because exact construction dates are not supplied. Available days equal ownership
days × (1 − off-hire). Rates apply to available days; vessel operating and management costs
apply to ownership days. Charter-fixed and open earnings are blended by the selected fixed
fraction. Annual inflation applies to rates and recurring costs at the period midpoint.

Drydock and maintenance are separate annual per-vessel cash budgets prorated by ownership
days. They do not purport to be a vessel survey schedule. Corporate overhead equals the
annual budget × period days / 365 × [fixed fraction + variable fraction × active fleet share].
It stops when no vessels operate. The denominator is the full committed fleet register.

Opening working capital uses the reviewed financial proxy. Closing working capital is the
selected ratio of annualized period TCE revenue. Changes enter cash flow once; the balance
is released when operations end. This is an explicit simplified requirement, not a full
receivables, inventories and payables forecast.

## NAV

`asset NAV = adjusted fleet value + unrestricted cash + operating working capital − gross debt − other claims − remaining delivery payments`

Available cash bridges the last statement through separately documented equity proceeds,
dividends and debt repayments, plus an estimated residual cash bridge. Do not put the same
cash flow into both a named bridge and the residual. Restricted cash is not added separately.
Appraised newbuild values are included once and remaining payments deducted once; paid
deposits are not added as another asset. Asset NAV excludes future corporate overhead.

Completed issuance changes shares and cash. Hypothetical ATM issuance adds net proceeds
after fees and divides gross proceeds by the observed share price to estimate new shares.
Additional shares without proceeds can represent dilution; they must be explicitly set.

## Cash flow and DCF

`UFCF = TCE revenue − vessel opex − management − drydock − corporate overhead − cash tax − maintenance − delivery payments + scrap − change in operating working capital`

Cash tax is a scenario fraction of TCE revenue, not an earnings-based corporate tax model.
Scrap is a proxy in USD per DWT; it is not a steel price per lightweight tonne. Nominal scrap
proceeds are fixed by that input. There is no exit-sale value alongside continued operations.

`enterprise value = sum(UFCF / (1 + discount rate)^years)`

`equity DCF = enterprise value + unrestricted cash − gross debt − other claims`

The forecast must reach the final retirement. No perpetual terminal value is used.
Operating working capital is already invested/released within DCF, so it is not added to
equity a second time. Committed newbuild payments enter the cash forecast, not a second
equity deduction. Corporate overhead explains part of the difference from asset NAV.

## Financing and liquidity

Debt payments follow the reviewed principal schedule. Interest uses the period's average
opening/closing debt balance, the scenario cash interest rate and actual/365 period length.
This approximates within-period interest, especially for a large end-period repayment.

`cash after financing = UFCF − principal repayments − cash interest`

Cash is retained; no future dividends, refinancing, revolver draws or replacement investment
are assumed. A liquidity shortfall stays negative. Minimum cash is an illustrative disclosed
threshold, not a reconstruction of every covenant or guarantee. A negative DCF equity value
is an analytical shortfall and is not a modeled market price with limited-liability optionality.

## Reverse valuation and sensitivities

One parameter multiplies the entire open class-rate vector. Costs, fleet, discount rate and
other case inputs stay fixed. Working capital and revenue-based tax change consistently.
Python brackets 0–3 times base rates and uses bisection, then reprices through the complete
model. If no solution exists inside the bracket, it reports that status. With no open rate
exposure, the parameter is unidentifiable.

The Excel solution uses the affine relationship between rates and cash flow, including the
working-capital derivative. Its repricing identity is checked independently by Python.
Excel's 5×5 native data table varies its actual rate multiplier and discount adjustment.
The HTML sensitivity grid independently runs the complete Python model at each combination.

## Module boundaries

| Module | Responsibility |
| --- | --- |
| `data.py` | Load the six-file package, validate evidence and assumptions, fingerprint inputs. |
| `fleet.py` | Calendar periods, vessel overlap, delivery payments and retirement events. |
| `valuation.py` | Asset NAV, operating forecast, financing, DCF and reverse valuation. |
| `reconcile.py` | Compare independently computed schedules to Excel formula evidence. |
| `reporting.py` | Tables, plots and the local HTML reading view. |
| `cli.py` | Discover, scaffold, validate and run companies. |

The Excel builder loads normalized inputs, never Python valuation answers. The notebook
imports the independent Python package. Both implementations can agree while sharing a
bad assumption; source review and future operating validation remain separate work.
