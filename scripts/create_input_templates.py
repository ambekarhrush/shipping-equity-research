"""Maintain blank schema examples and a standalone, deliberately artificial fixture."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/companies/SBLK"
TEMPLATE = ROOT / "data/templates/dry_bulk"
FIXTURE = ROOT / "tests/fixtures/SYNTH"


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def write_csv(path, fields, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)


TEMPLATE.mkdir(parents=True, exist_ok=True)
FIXTURE.mkdir(parents=True, exist_ok=True)
meta = json.loads((SOURCE / "company.json").read_text())
for key in [
    "ticker",
    "name",
    "valuation_date",
    "information_cutoff",
    "statement_date",
    "price_date",
    "price",
    "quote_source",
    "forecast_end_year",
    "reported_operating_dwt",
    "history_label",
]:
    meta[key] = None
meta.update(
    evidence_status="Incomplete inputs. Do not use for valuation.", limitations=[], audit_notes=[]
)
write_json(TEMPLATE / "company.json", meta)
assumptions = json.loads((SOURCE / "assumptions.json").read_text())
for row in assumptions:
    row.update(
        bear=None, base=None, bull=None, rationale="Document the economic basis and evidence here."
    )
write_json(TEMPLATE / "assumptions.json", assumptions)
write_json(
    TEMPLATE / "sources.json",
    [
        {
            "id": "REPLACE",
            "title": "",
            "url": "",
            "published": None,
            "notes": "Provide a dated source and extraction location.",
        }
    ],
)
fields = {}
facts = []
for name in ["fleet", "financials", "debt"]:
    with (SOURCE / f"{name}.csv").open() as f:
        reader = csv.DictReader(f)
        fields[name] = reader.fieldnames
        rows = list(reader)
    blank = []
    if name == "financials":
        facts = rows
        blank = [
            {**{k: "" for k in fields[name]}, "key": row["key"], "unit": row["unit"]}
            for row in rows
        ]
    write_csv(TEMPLATE / f"{name}.csv", fields[name], blank)

# No fixture values are intended to resemble a real company.
meta.update(
    ticker="SYNTH",
    name="Synthetic one-vessel test",
    valuation_date="2026-12-31",
    information_cutoff="2026-12-31",
    statement_date="2026-12-31",
    price_date="2026-12-31",
    price=10,
    quote_source="SYNTH",
    forecast_end_year=2035,
    reported_operating_dwt=0,
    history_label="Synthetic year",
    evidence_status="Synthetic arithmetic fixture",
    limitations=["Invented arithmetic example. Not market data or an investment case."],
    class_order=["Kamsarmax"],
)
write_json(FIXTURE / "company.json", meta)
write_json(
    FIXTURE / "sources.json",
    [
        {
            "id": "SYNTH",
            "title": "Invented test inputs",
            "url": "",
            "published": "2026-12-31",
            "notes": "Entirely synthetic.",
        }
    ],
)
values = {
    "shares": 100000,
    "adjusted_shares": 100000,
    "share_price": 10,
    "cash": 400000,
    "bank_debt_gross": 100000,
    "adjusted_debt_carrying": 100000,
}
for row in facts:
    row.update(
        value=values.get(row["key"], 0),
        period="2026-12-31",
        source_id="SYNTH",
        source_location="tests/fixtures/README.md",
        status="synthetic",
        notes="Invented arithmetic fixture.",
    )
write_csv(FIXTURE / "financials.csv", fields["financials"], facts)
vessel = {k: "" for k in fields["fleet"]}
vessel.update(
    vessel_id="SYNTH-ONE",
    name="Synthetic One",
    vessel_class="Kamsarmax",
    dwt=1000,
    build_year=2002,
    delivery_date="2027-01-15",
    delivery_status="assumed",
    scrubber=0,
    appraisal_date="2026-12-31",
    appraisal_usd=1800000,
    remaining_capex_usd=1000000,
    source_id="SYNTH",
    notes="Invented late-life acquisition; no real vessel.",
)
write_csv(FIXTURE / "fleet.csv", fields["fleet"], [vessel])
repayment = {k: "" for k in fields["debt"]}
repayment.update(
    due_date="2027-06-30",
    principal_usd=100000,
    source_id="SYNTH",
    status="synthetic",
    notes="One assumed payment.",
)
write_csv(FIXTURE / "debt.csv", fields["debt"], [repayment])
drivers = {
    "wacc": 0.1,
    "asset_factor": 1,
    "retirement_age": 25,
    "offhire": 0.1,
    "opex": 20,
    "management": 5,
    "ga": 3650,
    "dock_budget": 3650,
    "maintenance": 3650,
    "scrap_per_dwt": 10,
    "remaining_capex_factor": 1,
    "ga_floor": 1,
    "interest": 0.1,
}
for row in assumptions:
    value = 100 if row["key"].startswith("tce_") else drivers.get(row["key"], 0)
    row.update(
        bear=value, base=value, bull=value, rationale="Invented standalone arithmetic fixture."
    )
write_json(FIXTURE / "assumptions.json", assumptions)
