"""Exact calendar overlap and finite remaining fleet lives."""

from __future__ import annotations

import pandas as pd


def forecast_periods(valuation_date: str, end_year: int) -> pd.DataFrame:
    start = pd.Timestamp(valuation_date) + pd.Timedelta(days=1)
    records = []
    for i in range(12):
        end = start + pd.offsets.QuarterEnd(0)
        records.append(
            {
                "start": start,
                "end": end,
                "label": f"Q{end.quarter}:{str(end.year)[-2:]}" + (" stub" if i == 0 else ""),
            }
        )
        start = end + pd.Timedelta(days=1)
    while start.year < end_year or (start.year == end_year and start.month == 1):
        end = start + pd.DateOffset(years=1) - pd.Timedelta(days=1)
        records.append({"start": start, "end": end, "label": end.strftime("%b-%y")})
        start = end + pd.Timedelta(days=1)
    periods = pd.DataFrame(records)
    periods["days"] = (periods.end - periods.start).dt.days + 1
    periods["t"] = (periods.end - pd.Timestamp(valuation_date)).dt.days / 365
    periods["mid_t"] = (
        (periods.start - pd.Timestamp(valuation_date)).dt.days + (periods.days - 1) / 2
    ) / 365
    return periods


def operating_days(
    delivery: pd.Timestamp, retirement: pd.Timestamp, start: pd.Timestamp, end: pd.Timestamp
) -> int:
    """Delivery inclusive, retirement exclusive, period endpoints inclusive."""
    return max(0, (min(end + pd.Timedelta(days=1), retirement) - max(start, delivery)).days)


def fleet_schedule(fleet: pd.DataFrame, periods: pd.DataFrame, retirement_age: int) -> pd.DataFrame:
    records = []
    for vessel in fleet.to_dict("records"):
        retire = pd.Timestamp(year=int(vessel["build_year"]) + retirement_age, month=7, day=1)
        if retire <= vessel["delivery_date"]:
            raise ValueError("Retirement occurs before delivery")
        if retire > periods.end.iloc[-1]:
            raise ValueError("Forecast horizon does not reach final retirement")
        for i, period in periods.iterrows():
            records.append(
                {
                    "period": i,
                    "vessel_id": vessel["vessel_id"],
                    "vessel_class": vessel["vessel_class"],
                    "days": operating_days(
                        vessel["delivery_date"], retire, period.start, period.end
                    ),
                    "retirement_dwt": vessel["dwt"] if period.start <= retire <= period.end else 0,
                    "delivery_capex": vessel["remaining_capex_usd"]
                    if period.start <= vessel["delivery_date"] <= period.end
                    else 0,
                }
            )
    return pd.DataFrame(records)
