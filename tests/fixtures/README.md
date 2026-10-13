# Standalone synthetic example

`SYNTH` is an invented one-vessel company, separate from all real-company inputs.
It exercises the same loader and valuation engine. All three cases deliberately match.

One 1,000-DWT vessel is acquired on 15 January 2027 and retired on 1 July 2027.
It operates for 167 ownership days, or 150.3 available days at 10% off-hire.
At $100/day TCE, revenue is $15,030. Operating and management costs total $4,175;
drydock and maintenance budgets each cost $1,670. Corporate overhead accrues for
the two active quarters, costing $1,810. A $1m payment and $10,000 scrap receipt
produce **−$984,295 total undiscounted unlevered cash flow**. Negative cash is preserved.

Asset NAV is ($1.8m fleet + $0.4m cash − $0.1m debt − $1m remaining payment)
/ 100,000 shares = **$11/share**. These deliberately unrealistic values make
the arithmetic transparent; they are not calibrated to a real vessel or stock.

Run `uv run shipping-equity --data-root tests/fixtures validate SYNTH`.
