#!/usr/bin/env python3
"""Fail closed when the Modal monthly cost approaches the free-credit reserve."""

from __future__ import annotations

import argparse
import json
import subprocess
from decimal import Decimal
from typing import Any


def billing_summary() -> dict[str, Any]:
    completed = subprocess.run(
        ["modal", "billing", "summary", "--json"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise ValueError("Modal billing summary was not a JSON object")
    return value


def evaluate(
    summary: dict[str, Any], *, free_credit: Decimal, reserve: Decimal
) -> dict[str, Any]:
    metered = Decimal(str(summary["metered_cost"]))
    billed = Decimal(str(summary["billed_cost"]))
    launch_ceiling = free_credit - reserve
    allowed = billed == 0 and metered < launch_ceiling
    return {
        "allowed": allowed,
        "metered_cost_usd": str(metered),
        "billed_cost_usd": str(billed),
        "free_credit_usd": str(free_credit),
        "reserve_usd": str(reserve),
        "launch_ceiling_usd": str(launch_ceiling),
        "remaining_before_reserve_usd": str(max(Decimal(0), launch_ceiling - metered)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--free-credit", type=Decimal, default=Decimal("30"))
    parser.add_argument("--reserve", type=Decimal, default=Decimal("3"))
    args = parser.parse_args()
    if args.free_credit <= 0 or args.reserve < 0 or args.reserve >= args.free_credit:
        raise SystemExit("invalid free-credit or reserve value")
    report = evaluate(
        billing_summary(), free_credit=args.free_credit, reserve=args.reserve
    )
    print(json.dumps(report, indent=2))
    if not report["allowed"]:
        raise SystemExit("Modal launch blocked by the free-credit safety gate")


if __name__ == "__main__":
    main()
