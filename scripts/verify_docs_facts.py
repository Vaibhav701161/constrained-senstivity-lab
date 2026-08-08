#!/usr/bin/env python3
"""Verify headline documentation claims against frozen machine-readable evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def read_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{relative}: expected an object")
    return value


def text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def pp(value: float) -> str:
    return f"{100 * value:+.1f}"


def interval(values: list[float]) -> str:
    return f"[{100 * values[0]:.1f}, {100 * values[1]:.1f}]"


def require(path: str, expected: str, failures: list[str]) -> None:
    if expected not in text(path):
        failures.append(f"{path}: missing derived fact: {expected!r}")


def forbid(path: str, forbidden: str, failures: list[str]) -> None:
    if forbidden in text(path):
        failures.append(f"{path}: stale or misleading statement: {forbidden!r}")


def main() -> None:
    qwen = read_json(
        "experiments/corrected-replication/results/qwen2.5-7b-corrected/decision.json"
    )["paired_effect"]
    canonical = read_json(
        "experiments/canonical-schema-equivalence-correction/paired-summary.json"
    )["primary_contract_valid_effect"]
    tool = read_json("experiments/tool-call-gate/paired-summary.json")["subsets"][
        "primary"
    ]["primary_executable_effect"]
    replay = read_json("experiments/replay-validation.json")

    failures: list[str] = []
    expected_rows = sum(int(scope["replayed_rows"]) for scope in replay["scopes"])
    if replay.get("valid") is not True or expected_rows != replay.get("replayed_rows"):
        failures.append("experiments/replay-validation.json: invalid replay aggregate")

    qwen_fact = (
        f"{pp(float(qwen['accuracy_delta']))} pp, "
        f"CI {interval(qwen['exact_bootstrap_ci95'])}"
    )
    canonical_fact = (
        f"{pp(float(canonical['paired_difference']))} pp, "
        f"CI {interval(canonical['exact_paired_bootstrap_ci95'])}"
    )
    tool_fact = (
        f"{pp(float(tool['paired_difference']))} pp, "
        f"CI {interval(tool['exact_paired_bootstrap_ci95'])}"
    )
    for path in ("README.md", "docs/results/index.md"):
        require(path, qwen_fact, failures)
        require(path, canonical_fact, failures)
        require(path, tool_fact, failures)
        require(
            path,
            f"{canonical['treatment_only']} : {canonical['control_only']}",
            failures,
        )

    require("README.md", f"`{expected_rows}`-row replay", failures)
    require("docs/results/index.md", "398-row broad second-family matrix", failures)
    require("docs/results/index.md", "66-row tool-call matrix", failures)
    require("docs/index.md", "CI        [-12.7, -0.7]", failures)

    forbid(
        "docs/evidence-status.md",
        "remain byte-identical to the versions hashed",
        failures,
    )
    forbid("docs/index.md", "accepted experiment rows replayed", failures)
    forbid("README.md", "464 accepted", failures)

    generator = text("scripts/build_replication_gate_figures.py")
    canonical_source = (
        '"experiments/canonical-schema-equivalence-correction/paired-summary.json"'
    )
    if canonical_source not in generator:
        failures.append(
            "scripts/build_replication_gate_figures.py: central forest plot is not "
            "bound to the canonical Llama summary"
        )

    if failures:
        raise SystemExit("\n".join(failures))
    print(
        "documentation facts verified: "
        f"Qwen {qwen_fact}; canonical Llama {canonical_fact}; "
        f"tools {tool_fact}; replay {expected_rows} rows"
    )


if __name__ == "__main__":
    main()
