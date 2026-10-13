"""Independent Python valuation. Does not read spreadsheet answers."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from shipping_equity.data import Company, validate_assumptions
from shipping_equity.fleet import fleet_schedule, forecast_periods


@dataclass
class Valuation:
    case: str
    nav: dict[str, float]
    summary: dict[str, float]
    forecast: pd.DataFrame
    financing: pd.DataFrame
    vessel_days: pd.DataFrame
    class_forecast: pd.DataFrame


def asset_nav(company: Company, a: dict[str, float]) -> dict[str, float]:
    f = company.facts
    atm_capacity = f["atm_capacity"]
    if a["atm_draw"] > atm_capacity:
        raise ValueError("Hypothetical issuance exceeds documented ATM capacity")
    shares = (
        f["shares"] + f["equity_issued"] + a["additional_shares"] + a["atm_draw"] / f["share_price"]
    )
    cash = f["cash"] + f["equity_proceeds"] - f["subsequent_dividend"] - f["debt_payments"]
    cash += a["bridge_cash"] + a["atm_draw"] * (1 - a["atm_fee"])
    debt = f["bank_debt_gross"] + f["finance_leases"] - f["debt_payments"]
    fleet_value = float(company.fleet.appraisal_usd.sum()) * a["asset_factor"]
    capex = float(company.fleet.remaining_capex_usd.sum()) * a["remaining_capex_factor"]
    equity = fleet_value + cash - debt - a["extra_claims"] - capex + f["operating_working_capital"]
    return {
        "fleet_value": fleet_value,
        "cash": cash,
        "debt": debt,
        "other_claims": a["extra_claims"],
        "remaining_capex": capex,
        "shares": shares,
        "equity_nav": equity,
        "nav_per_share": equity / shares,
        "price_nav": f["share_price"] / (equity / shares),
    }


def value_company(
    company: Company,
    case: str = "base",
    *,
    overrides: dict[str, float] | None = None,
    rate_multiplier: float = 1,
    discount_adjustment: float = 0,
) -> Valuation:
    a = company.case(case)
    for key, value in (overrides or {}).items():
        if key not in a:
            raise ValueError(f"Unknown assumption {key}")
        a[key] = value
    validate_assumptions(a)
    if rate_multiplier < 0 or not np.isfinite(rate_multiplier):
        raise ValueError("Rate multiplier must be finite and nonnegative")
    discount = a["wacc"] + discount_adjustment
    if not np.isfinite(discount) or discount <= 0:
        raise ValueError("Discount rate must be positive")
    p = forecast_periods(company.metadata["valuation_date"], company.metadata["forecast_end_year"])
    detail = fleet_schedule(company.fleet, p, int(a["retirement_age"]))
    nav = asset_nav(company, a)
    if not np.isclose(company.debt.principal_usd.sum(), nav["debt"], atol=1, rtol=0):
        raise ValueError("Debt schedule does not reconcile to opening gross financial debt")
    records = []
    for cls in company.metadata["class_order"]:
        days = (
            detail[detail.vessel_class == cls]
            .groupby("period")
            .days.sum()
            .reindex(p.index, fill_value=0)
        )
        for i, period in p.iterrows():
            owned = float(days.loc[i])
            available = owned * (1 - a["offhire"])
            growth = (1 + a["inflation"]) ** period.mid_t
            open_rate = a["tce_" + cls] * rate_multiplier * growth
            fixed_rate = a["fixed_tce"] * growth
            open_revenue = available * (1 - a["fixed_share"]) * open_rate
            revenue = open_revenue + available * a["fixed_share"] * fixed_rate
            records.append(
                {
                    "period": i,
                    "vessel_class": cls,
                    "owned": owned,
                    "available": available,
                    "revenue": revenue,
                    "open_revenue": open_revenue,
                    "opex": owned * a["opex"] * growth,
                    "management": owned * a["management"] * growth,
                    "dock": owned / 365 * a["dock_budget"] * growth,
                    "maintenance": owned / 365 * a["maintenance"] * growth,
                }
            )
    classes = pd.DataFrame(records)
    forecast = classes.groupby("period").sum(numeric_only=True)
    forecast = p.join(forecast)
    growth = (1 + a["inflation"]) ** forecast.mid_t
    fleet_utilization = forecast.owned / (forecast.days * len(company.fleet))
    forecast["ga"] = np.where(
        forecast.owned > 0,
        a["ga"]
        * forecast.days
        / 365
        * (a["ga_floor"] + (1 - a["ga_floor"]) * fleet_utilization)
        * growth,
        0,
    )
    forecast["operating"] = forecast.revenue - forecast[["opex", "management", "dock", "ga"]].sum(
        axis=1
    )
    forecast["tax"] = forecast.revenue * a["tax_on_revenue"]
    grouped = detail.groupby("period")
    forecast["newbuild"] = grouped.delivery_capex.sum() * a["remaining_capex_factor"]
    forecast["scrap"] = grouped.retirement_dwt.sum() * a["scrap_per_dwt"]
    forecast["wc"] = forecast.revenue / forecast.days * 365 * a["working_capital"]
    forecast["delta_wc"] = forecast.wc.diff()
    forecast.loc[0, "delta_wc"] = (
        forecast.wc.to_numpy(dtype=float)[0] - company.facts["operating_working_capital"]
    )
    forecast["ufcf"] = (
        forecast.operating
        - forecast.tax
        - forecast.maintenance
        - forecast.newbuild
        + forecast.scrap
        - forecast.delta_wc
    )
    forecast["discount"] = (1 + discount) ** (-forecast.t)
    forecast["pv"] = forecast.ufcf * forecast.discount
    forecast["open_wc"] = forecast.open_revenue / forecast.days * 365 * a["working_capital"]
    forecast["delta_open_wc"] = forecast.open_wc.diff().fillna(forecast.open_wc.iloc[0])
    forecast["open_pv"] = (
        forecast.open_revenue * (1 - a["tax_on_revenue"]) - forecast.delta_open_wc
    ) * forecast.discount
    enterprise = float(forecast.pv.sum())
    equity = enterprise + nav["cash"] - nav["debt"] - nav["other_claims"]
    debt_balance, cash_balance = nav["debt"], nav["cash"]
    financing = []
    for row in forecast.to_dict("records"):
        payments = company.debt[
            (company.debt.due_date >= row["start"]) & (company.debt.due_date <= row["end"])
        ]
        principal = min(debt_balance, float(payments.principal_usd.sum()))
        ending = debt_balance - principal
        interest = (debt_balance + ending) / 2 * a["interest"] * row["days"] / 365
        equity_cash = row["ufcf"] - principal - interest
        minimum = company.facts["minimum_unrestricted_liquidity"] if row["owned"] > 0 else 0
        financing.append(
            {
                "opening_debt": debt_balance,
                "repayment": principal,
                "closing_debt": ending,
                "interest": interest,
                "ufcf": row["ufcf"],
                "equity_cash": equity_cash,
                "opening_cash": cash_balance,
                "closing_cash": cash_balance + equity_cash,
                "mincash": minimum,
                "headroom": cash_balance + equity_cash - minimum,
            }
        )
        debt_balance, cash_balance = ending, cash_balance + equity_cash
    financing_frame = pd.DataFrame(financing)
    year = pd.Timestamp(company.metadata["valuation_date"]).year + 1
    mask = forecast.start.dt.year == year
    summary = {
        "price": company.facts["share_price"],
        "nav_per_share": nav["nav_per_share"],
        "price_nav": nav["price_nav"],
        "enterprise_value": enterprise,
        "equity_dcf": equity,
        "dcf_per_share": equity / nav["shares"],
        "next_year_revenue": float(forecast.loc[mask, "revenue"].sum()),
        "next_year_ufcf": float(forecast.loc[mask, "ufcf"].sum()),
        "next_year_equity_cash": float(financing_frame.loc[mask, "equity_cash"].sum()),
        "minimum_cash_headroom": float(financing_frame.headroom.min()),
    }
    return Valuation(case, nav, summary, forecast, financing_frame, detail, classes)


def reverse_valuation(
    company: Company,
    case: str = "base",
    target_price: float | None = None,
    bounds: tuple[float, float] = (0, 3),
    tolerance: float = 1e-8,
) -> dict:
    """Bracketed bisection, independent of the workbook's affine solution."""
    target = company.facts["share_price"] if target_price is None else target_price
    if not np.isfinite(target) or target < 0 or bounds[0] < 0 or bounds[1] <= bounds[0]:
        raise ValueError("Invalid target price or root bracket")
    # Compute two full valuations. Cash flows are affine in a single common rate multiplier.
    v0 = value_company(company, case, rate_multiplier=0).summary["dcf_per_share"]
    v1 = value_company(company, case, rate_multiplier=1).summary["dcf_per_share"]
    slope = v1 - v0
    lo, hi = bounds
    if abs(slope) < 1e-12:
        return {
            "status": "unidentified",
            "multiplier": None,
            "residual": None,
            "reason": "No open-rate exposure under the selected assumptions",
        }
    if (v0 + slope * lo - target) * (v0 + slope * hi - target) > 0:
        return {
            "status": "outside_bounds",
            "multiplier": None,
            "residual": None,
            "reason": f"No solution inside {bounds}",
        }
    for iteration in range(100):
        mid = (lo + hi) / 2
        error = v0 + slope * mid - target
        if abs(error) < tolerance:
            break
        if error * slope > 0:
            hi = mid
        else:
            lo = mid
    # Reprice through the complete model rather than accepting the linear interpolation.
    repriced = value_company(company, case, rate_multiplier=mid).summary["dcf_per_share"]
    return {
        "status": "solved",
        "multiplier": mid,
        "residual": repriced - target,
        "iterations": iteration + 1,
        "bounds": list(bounds),
    }
