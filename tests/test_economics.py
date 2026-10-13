from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shipping_equity.data import load_company
from shipping_equity.fleet import operating_days
from shipping_equity.valuation import asset_nav, reverse_valuation, value_company

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def company():
    return load_company(ROOT / "data/companies/SBLK")


def test_delivery_and_retirement_day_boundaries():
    t = pd.Timestamp
    assert operating_days(t("2026-01-15"), t("2026-01-25"), t("2026-01-01"), t("2026-01-31")) == 10
    assert operating_days(t("2026-02-01"), t("2050-01-01"), t("2026-01-01"), t("2026-01-31")) == 0
    assert operating_days(t("2020-01-01"), t("2026-01-01"), t("2026-01-01"), t("2026-01-31")) == 0
    assert operating_days(t("2024-02-01"), t("2050-01-01"), t("2024-02-01"), t("2024-02-29")) == 29


def test_source_reconciliation(company):
    f = company.facts
    assert (
        f["voyage_revenue"] - f["voyage_cost"] - f["charter_hire"] + f["realized_derivatives"]
        == f["tce_revenue"]
    )
    assert (
        f["opening_total_cash"]
        + f["cash_from_operations"]
        + f["cash_from_investing"]
        + f["cash_from_financing"]
        == f["closing_total_cash"]
    )
    assert f["shares"] + f["equity_issued"] == f["adjusted_shares"]
    assert len(company.fleet) == 138
    assert (
        company.fleet[company.fleet.delivery_date <= pd.Timestamp("2026-10-09")].dwt.sum()
        == 13504552
    )


def test_hand_checked_nav_and_cash_bridge(company):
    a = company.case()
    nav = asset_nav(company, a)
    assert nav["cash"] == 498165000 + 116000000 - 100800000 - 92223000 + 100000000
    assert nav["debt"] == 1030086000 + 11209000 - 92223000
    assert nav["remaining_capex"] == 3 * 24407000
    assert nav["shares"] == 116071386
    assert nav["nav_per_share"] == pytest.approx(
        (
            company.fleet.appraisal_usd.sum()
            + nav["cash"]
            - nav["debt"]
            - 73221000
            + company.facts["operating_working_capital"]
        )
        / 116071386
    )


def test_capex_scrap_and_working_capital_counted_once(company):
    v = value_company(company)
    assert v.forecast.newbuild.sum() == pytest.approx(v.nav["remaining_capex"])
    assert v.forecast.scrap.sum() == pytest.approx(company.fleet.dwt.sum() * 70)
    assert v.forecast.owned.iloc[-1] == 0
    assert v.forecast.delta_wc.sum() == pytest.approx(-company.facts["operating_working_capital"])
    assert np.allclose(
        v.forecast.ufcf,
        v.forecast.operating
        - v.forecast.tax
        - v.forecast.maintenance
        - v.forecast.newbuild
        + v.forecast.scrap
        - v.forecast.delta_wc,
    )


def test_financing_does_not_change_unlevered_dcf(company):
    base = value_company(company)
    high = value_company(company, overrides={"interest": 0.12})
    assert high.summary["dcf_per_share"] == base.summary["dcf_per_share"]
    assert high.summary["next_year_equity_cash"] < base.summary["next_year_equity_cash"]
    assert base.financing.repayment.sum() == pytest.approx(base.nav["debt"])
    assert base.financing.closing_debt.iloc[-1] == 0
    assert np.allclose(
        base.financing.closing_cash, base.financing.opening_cash + base.financing.equity_cash
    )


def test_reverse_price_includes_working_capital(company):
    root = reverse_valuation(company)
    assert root["status"] == "solved"
    v = value_company(company, rate_multiplier=root["multiplier"])
    assert v.summary["dcf_per_share"] == pytest.approx(company.facts["share_price"], abs=1e-8)
    assert reverse_valuation(company, target_price=1e8)["status"] == "outside_bounds"


def test_full_fixed_coverage_has_no_open_rate_sensitivity(company):
    for driver in company.assumptions["fixed_share"]:
        if driver in ["bear", "base", "bull"]:
            company.assumptions["fixed_share"][driver] = 1
    assert reverse_valuation(company)["status"] == "unidentified"
    lo = value_company(company, rate_multiplier=0.1)
    hi = value_company(company, rate_multiplier=2)
    assert lo.summary == hi.summary


def test_issuance_adds_cash_and_shares(company):
    a = company.case()
    before = asset_nav(company, a)
    a["atm_draw"] = 29700000
    after = asset_nav(company, a)
    assert after["shares"] - before["shares"] == 1000000
    assert after["cash"] - before["cash"] == pytest.approx(29700000 * 0.98)
    a["atm_draw"] = company.facts["atm_capacity"] + 1
    with pytest.raises(ValueError, match="capacity"):
        asset_nav(company, a)


@pytest.mark.parametrize(
    "override",
    [
        {"offhire": 1},
        {"fixed_share": -1},
        {"retirement_age": 25.5},
        {"opex": float("nan")},
        {"unknown": 1},
    ],
)
def test_invalid_assumptions_fail(company, override):
    with pytest.raises(ValueError):
        value_company(company, overrides=override)


def test_company_identity_is_not_in_economics(company):
    before = value_company(company).summary
    other = deepcopy(company)
    other.metadata["ticker"] = "TEST"
    other.metadata["name"] = "Synthetic identity fixture"
    other.fleet["vessel_id"] = "TEST-" + other.fleet.index.astype(str)
    assert value_company(other).summary == before


def test_horizon_and_maturity_failure(company):
    company.metadata["forecast_end_year"] = 2030
    with pytest.raises(ValueError, match="horizon"):
        value_company(company)
    company.metadata["forecast_end_year"] = 2056
    company.debt.loc[0, "principal_usd"] += 1e6
    with pytest.raises(ValueError, match="reconcile"):
        value_company(company)
