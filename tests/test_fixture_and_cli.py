import json
from pathlib import Path

import pytest

from shipping_equity.cli import main
from shipping_equity.data import load_company
from shipping_equity.reconcile import reconcile
from shipping_equity.valuation import value_company

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_synthetic_cash_arithmetic():
    c = load_company(ROOT / "tests/fixtures/SYNTH")
    v = value_company(c)
    # Jan 15–Jun 30 inclusive: 76 + 91 ownership days, 90% availability.
    assert v.forecast.owned.sum() == 167
    assert v.forecast.available.sum() == pytest.approx(150.3)
    assert v.forecast.revenue.sum() == pytest.approx(15030)
    assert v.forecast.opex.sum() + v.forecast.management.sum() == 4175
    assert v.forecast.dock.sum() == 1670
    assert v.forecast.maintenance.sum() == 1670
    assert v.forecast.ga.sum() == 1810
    assert v.forecast.newbuild.sum() == 1000000
    assert v.forecast.scrap.sum() == 10000
    assert v.forecast.ufcf.sum() == pytest.approx(-984295)
    assert v.nav["nav_per_share"] == 11
    assert v.financing.repayment.sum() == 100000
    assert v.financing.closing_cash.iloc[-1] < 0  # Insolvency is not hidden by a floor.


def test_add_company_scaffolds_blank_inputs_without_copying_facts(tmp_path):
    assert (
        main(
            [
                "--data-root",
                str(tmp_path),
                "init-company",
                "NEW",
                "--name",
                "New Company",
                "--date",
                "2026-12-31",
                "--template",
                str(ROOT / "data/templates/dry_bulk"),
            ]
        )
        == 0
    )
    meta = json.loads((tmp_path / "NEW/company.json").read_text())
    assert meta["ticker"] == "NEW"
    assert meta["price"] is None
    assert "Star Bulk" not in "".join(p.read_text() for p in (tmp_path / "NEW").iterdir())
    with pytest.raises((ValueError, TypeError)):
        load_company(tmp_path / "NEW")


def test_changed_data_cannot_reuse_workbook_evidence(tmp_path):
    c = load_company(ROOT / "tests/fixtures/SYNTH")
    path = tmp_path / "stale.json"
    path.write_text(json.dumps({"input_sha256": "different"}))
    with pytest.raises(ValueError, match="stale"):
        reconcile(c, path)
