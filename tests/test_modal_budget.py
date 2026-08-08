from __future__ import annotations

from decimal import Decimal

from scripts.check_modal_budget import evaluate


def test_budget_gate_allows_cost_well_inside_free_credit() -> None:
    result = evaluate(
        {"metered_cost": "12.50", "billed_cost": "0.00"},
        free_credit=Decimal("30"),
        reserve=Decimal("3"),
    )
    assert result["allowed"] is True
    assert result["remaining_before_reserve_usd"] == "14.50"


def test_budget_gate_refuses_at_reserve_boundary() -> None:
    result = evaluate(
        {"metered_cost": "27.00", "billed_cost": "0.00"},
        free_credit=Decimal("30"),
        reserve=Decimal("3"),
    )
    assert result["allowed"] is False


def test_budget_gate_refuses_any_billed_cost() -> None:
    result = evaluate(
        {"metered_cost": "1.00", "billed_cost": "0.01"},
        free_credit=Decimal("30"),
        reserve=Decimal("3"),
    )
    assert result["allowed"] is False
