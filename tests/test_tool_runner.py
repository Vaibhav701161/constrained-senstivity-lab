from __future__ import annotations

from pathlib import Path

from scripts.run_tool_call_pilot import condition_name, tool_run_config


def config(tmp_path: Path, representation: str) -> dict:
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text('{"id":"item"}\n', encoding="utf-8")
    return tool_run_config(
        model="model",
        revision="revision",
        dataset=dataset,
        representation=representation,
        seed=0,
        max_new_tokens=192,
        dtype="float32",
        device_map_auto=True,
        runner_sha256="runner",
        runtime_sha256="runtime",
    )


def test_conditions_are_explicit() -> None:
    assert condition_name("external-integer-strings") == "xgrammar_tool_external_integer_strings"
    assert condition_name("internal-integers") == "xgrammar_tool_internal_integers"


def test_paired_configs_differ_only_on_registered_representation(tmp_path: Path) -> None:
    control = config(tmp_path, "external-integer-strings")
    treatment = config(tmp_path, "internal-integers")
    allowed = {
        "condition",
        "representation",
        "model_uses_integers",
        "transducer_version",
    }
    assert {
        key for key in control if control.get(key) != treatment.get(key)
    } == allowed
