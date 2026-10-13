"""Compare independently computed schedules with workbook calculation evidence."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shipping_equity.data import Company
from shipping_equity.valuation import reverse_valuation, value_company


def reconcile(company: Company, evidence_path: Path) -> dict:
    evidence = json.loads(evidence_path.read_text())
    if evidence.get("input_sha256") != company.fingerprint:
        raise ValueError(
            "Workbook evidence is stale: regenerate it from the current company inputs"
        )
    comparisons = []
    mapping = {
        "Market price": "price",
        "Asset NAV per share": "nav_per_share",
        "Price / asset NAV": "price_nav",
        "Operating enterprise value": "enterprise_value",
        "DCF equity value": "equity_dcf",
        "DCF equity per share": "dcf_per_share",
        f"{int(company.metadata['valuation_date'][:4]) + 1} TCE cash revenue": "next_year_revenue",
        f"{int(company.metadata['valuation_date'][:4]) + 1} unlevered free cash flow": "next_year_ufcf",
        f"{int(company.metadata['valuation_date'][:4]) + 1} cash after financing": "next_year_equity_cash",
    }

    def compare(label, expected, actual, tolerance=0.0001):
        x, y = np.array(expected, dtype=float), np.array(actual, dtype=float)
        if x.shape != y.shape:
            raise ValueError(f"Reconciliation shape mismatch: {label}")
        error = float(np.max(np.abs(x - y)))
        comparisons.append(
            {
                "control": label,
                "cells": int(x.size),
                "max_abs_difference": error,
                "tolerance": tolerance,
                "pass": bool(np.isfinite(error) and error <= tolerance),
            }
        )

    for case, workbook in evidence["cases"].items():
        result = value_company(company, case)
        for label, key in mapping.items():
            compare(case + " / " + key, workbook["summary"][label], result.summary[key])
        for key, values in workbook["forecast"].items():
            compare(case + " / cash flow / " + key, values, result.forecast[key].to_numpy())
        for key, values in workbook["financing"].items():
            compare(case + " / financing / " + key, values, result.financing[key].to_numpy())
        root = reverse_valuation(company, case)
        if root["status"] != "solved":
            raise ValueError("Workbook root requires a valid Python bracketed solution")
        compare(
            case + " / implied rates",
            workbook["summary"]["Implied open-rate multiplier"],
            root["multiplier"],
            1e-8,
        )
    failures = [row for row in comparisons if not row["pass"]]
    return {
        "status": "pass" if not failures else "fail",
        "input_sha256": company.fingerprint,
        "engine": "Independent Python vs artifact-tool Excel formula calculation",
        "cells_compared": sum(row["cells"] for row in comparisons),
        "max_absolute_difference": max(row["max_abs_difference"] for row in comparisons),
        "controls": comparisons,
        "failures": failures,
    }
