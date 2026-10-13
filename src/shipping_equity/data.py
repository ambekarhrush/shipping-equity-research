"""Load one reviewed company package. No network access or ticker-specific math."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


@dataclass
class Company:
    metadata: dict
    fleet: pd.DataFrame
    facts: dict[str, float]
    assumptions: dict[str, dict]
    debt: pd.DataFrame
    sources: list[dict]
    fingerprint: str

    def case(self, name: str = "base") -> dict[str, float]:
        if name not in {"bear", "base", "bull"}:
            raise ValueError("Case must be bear, base or bull")
        return {key: float(row[name]) for key, row in self.assumptions.items()}


def load_company(folder: Path) -> Company:
    paths = [
        folder / name
        for name in [
            "company.json",
            "fleet.csv",
            "financials.csv",
            "assumptions.json",
            "debt.csv",
            "sources.json",
        ]
    ]
    for path in paths:
        if not path.is_file():
            raise ValueError(f"Missing company input: {path.name}")
    metadata = json.loads(paths[0].read_text())
    if metadata["schema_version"] != 1 or metadata["currency"] != "USD":
        raise ValueError("Only schema v1 and USD inputs are supported")
    if metadata["segment"] != "dry_bulk":
        raise ValueError("This engine supports dry bulk; other segments need reviewed economics")
    valuation = pd.Timestamp(metadata["valuation_date"])
    cutoff = pd.Timestamp(metadata["information_cutoff"])
    if cutoff > valuation or pd.Timestamp(metadata["price_date"]) != valuation:
        raise ValueError("Information cutoff and price date must match valuation policy")
    fleet = pd.read_csv(paths[1], keep_default_na=False)
    facts_frame = pd.read_csv(paths[2], keep_default_na=False)
    assumptions = json.loads(paths[3].read_text())
    debt = pd.read_csv(paths[4], keep_default_na=False)
    sources = json.loads(paths[5].read_text())
    source_ids = {s["id"] for s in sources}
    if len(source_ids) != len(sources):
        raise ValueError("Duplicate source IDs")
    for source in sources:
        if pd.Timestamp(source["published"]) > cutoff:
            raise ValueError("Source published after information cutoff")
    if fleet.empty or fleet.vessel_id.duplicated().any():
        raise ValueError("Empty fleet or duplicate vessel IDs")
    numeric = ["dwt", "build_year", "appraisal_usd", "remaining_capex_usd"]
    if not np.isfinite(fleet[numeric].to_numpy(dtype=float)).all():
        raise ValueError("Missing/nonfinite fleet inputs")
    if (fleet[["dwt", "appraisal_usd"]] <= 0).any().any():
        raise ValueError("DWT and appraisal values must be positive")
    if (fleet.remaining_capex_usd < 0).any():
        raise ValueError("Remaining capex cannot be negative")
    if not set(fleet.vessel_class).issubset(metadata["class_order"]):
        raise ValueError("Unmapped vessel class")
    if (fleet.disposal_date != "").any():
        raise ValueError(
            "Future sales need an explicit sale-proceeds module; do not treat as scrap"
        )
    for key in ["delivery_date", "appraisal_date"]:
        fleet[key] = pd.to_datetime(fleet[key], errors="raise")
        if fleet[key].isna().any():
            raise ValueError(f"Missing {key}")
    if (fleet.appraisal_date > cutoff).any():
        raise ValueError("Appraisal after cutoff")
    if ((fleet.delivery_date > valuation) & (fleet.delivery_status != "assumed")).any():
        raise ValueError("Future delivery cannot be marked observed")
    if ((fleet.delivery_date <= valuation) & (fleet.remaining_capex_usd != 0)).any():
        raise ValueError("Delivered vessel has unexplained remaining delivery capex")
    if facts_frame.key.duplicated().any() or len({a["key"] for a in assumptions}) != len(
        assumptions
    ):
        raise ValueError("Duplicate financial input or assumption")
    if not np.isfinite(facts_frame.value.to_numpy(dtype=float)).all():
        raise ValueError("Missing/nonfinite financial input")
    for ids in list(fleet.source_id) + list(facts_frame.source_id) + list(debt.source_id):
        if not set(ids.split(";")).issubset(source_ids):
            raise ValueError("Unknown source reference")
    if (pd.to_datetime(facts_frame.period) > cutoff).any():
        raise ValueError("Observed financial input after cutoff")
    debt["due_date"] = pd.to_datetime(debt.due_date)
    if (
        not np.isfinite(debt.principal_usd.to_numpy(dtype=float)).all()
        or (debt.principal_usd < 0).any()
    ):
        raise ValueError("Invalid debt principal schedule")
    if (debt.due_date <= valuation).any():
        raise ValueError("Opening debt schedule contains already-due principal")
    fingerprint = hashlib.sha256(
        b"".join(p.name.encode() + p.read_bytes() for p in paths)
    ).hexdigest()
    result = Company(
        metadata,
        fleet,
        dict(zip(facts_frame.key, facts_frame.value)),
        {a["key"]: a for a in assumptions},
        debt,
        sources,
        fingerprint,
    )
    for name in ["bear", "base", "bull"]:
        validate_assumptions(result.case(name))
    return result


def validate_assumptions(a: dict[str, float]) -> None:
    if not all(np.isfinite(value) for value in a.values()):
        raise ValueError("Assumptions must be finite")
    for key in [
        "fixed_share",
        "offhire",
        "tax_on_revenue",
        "ga_floor",
        "atm_fee",
        "working_capital",
    ]:
        if not 0 <= a[key] <= 1:
            raise ValueError(f"{key} must be between zero and one")
    if a["offhire"] == 1 or a["wacc"] <= 0 or a["retirement_age"] < 1:
        raise ValueError("Need operating days, positive discount rate and retirement age")
    if int(a["retirement_age"]) != a["retirement_age"]:
        raise ValueError("Retirement age must be a whole year")
    if a["inflation"] <= -1:
        raise ValueError("Inflation must exceed -100%")
    for key, value in a.items():
        if key not in {"bridge_cash", "extra_claims", "inflation"} and value < 0:
            raise ValueError(f"{key} cannot be negative")
