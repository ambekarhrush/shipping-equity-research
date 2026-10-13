import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from shipping_equity.data import load_company

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "problem", ["duplicate", "missing_value", "future_source", "unknown_source", "future_appraisal"]
)
def test_bad_company_data_rejected(tmp_path, problem):
    folder = tmp_path / "TEST"
    shutil.copytree(ROOT / "data/companies/SBLK", folder)
    if problem == "future_source":
        p = folder / "sources.json"
        sources = json.loads(p.read_text())
        sources[0]["published"] = "2027-01-01"
        p.write_text(json.dumps(sources))
    else:
        p = folder / "fleet.csv"
        fleet = pd.read_csv(p, keep_default_na=False)
        if problem == "duplicate":
            fleet.loc[1, "vessel_id"] = fleet.loc[0, "vessel_id"]
        elif problem == "missing_value":
            fleet.loc[0, "appraisal_usd"] = float("nan")
        elif problem == "unknown_source":
            fleet.loc[0, "source_id"] = "NONEXISTENT"
        else:
            fleet.loc[0, "appraisal_date"] = "2027-01-01"
        fleet.to_csv(p, index=False)
    with pytest.raises(ValueError):
        load_company(folder)
