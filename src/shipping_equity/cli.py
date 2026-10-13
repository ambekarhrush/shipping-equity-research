"""Small, offline command line interface for reviewed company packages."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from shipping_equity.data import load_company
from shipping_equity.reconcile import reconcile
from shipping_equity.reporting import write_report
from shipping_equity.valuation import value_company


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path("data/companies"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="List available research snapshots")
    for command in ["validate", "run", "reconcile"]:
        p = sub.add_parser(command)
        p.add_argument("ticker")
        if command != "validate":
            p.add_argument("--output", type=Path)
        if command == "reconcile":
            p.add_argument("--evidence", type=Path, required=True)
    new = sub.add_parser("init-company", help="Create blank inputs; no inherited company facts")
    new.add_argument("ticker")
    new.add_argument("--name", required=True)
    new.add_argument("--date", required=True, help="YYYY-MM-DD valuation date")
    new.add_argument("--template", type=Path, default=Path("data/templates/dry_bulk"))
    args = parser.parse_args(argv)
    if args.command == "list":
        for path in sorted(args.data_root.glob("*/company.json")):
            meta = json.loads(path.read_text())
            print(f"{meta['ticker']:8} {meta['valuation_date']}  {meta['name']}")
        return 0
    ticker = args.ticker.upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,14}", ticker):
        parser.error("Use a ticker containing letters, numbers, dots or hyphens")
    folder = args.data_root / ticker
    try:
        if args.command == "init-company":
            if folder.exists():
                raise ValueError(f"Company folder already exists: {folder}")
            from datetime import date

            date.fromisoformat(args.date)
            shutil.copytree(args.template, folder)
            path = folder / "company.json"
            meta = json.loads(path.read_text())
            meta.update(
                ticker=ticker,
                name=args.name,
                valuation_date=args.date,
                information_cutoff=args.date,
                price_date=args.date,
            )
            path.write_text(json.dumps(meta, indent=2) + "\n")
            print(f"Created {folder}. Complete the blank inputs using docs/ADDING_COMPANIES.md.")
            return 0
        company = load_company(folder)
        if args.command == "validate":
            for case in ["bear", "base", "bull"]:
                value_company(company, case)
            print(f"{ticker}: input validation and all three valuation scenarios passed")
            return 0
        output = (
            args.output
            or Path("outputs") / f"{ticker.lower()}-{company.metadata['valuation_date']}"
        )
        output.mkdir(parents=True, exist_ok=True)
        if args.command == "run":
            write_report(company, output)
            print(f"Research report: {output / 'report.html'}")
            return 0
        result = reconcile(company, args.evidence)
        (output / "reconciliation.json").write_text(json.dumps(result, indent=2) + "\n")
        print(f"{result['status']}: {result['cells_compared']} independently compared values")
        return 0 if result["status"] == "pass" else 1
    except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
        parser.exit(1, f"Cannot {args.command} {ticker}: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
