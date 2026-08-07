from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/select_outlines_parity.py"


def test_selection_contains_all_discordants_and_frozen_concordants(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.jsonl"
    dataset.write_text(
        "".join(json.dumps({"id": f"item-{index}"}) + "\n" for index in range(30)),
        encoding="utf-8",
    )
    summary = tmp_path / "summary.json"
    summary.write_text(
        json.dumps(
            {
                "datasets": {
                    "fresh": {
                        "repaired_item_ids": ["item-2", "item-9"],
                        "newly_broken_item_ids": ["item-21"],
                    }
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "selected.jsonl"
    manifest = tmp_path / "manifest.json"
    command = [
        sys.executable,
        str(SCRIPT),
        "--dataset",
        str(dataset),
        "--paired-summary",
        str(summary),
        "--concordant-count",
        "5",
        "--out-dataset",
        str(output),
        "--out-manifest",
        str(manifest),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
    first = json.loads(manifest.read_text(encoding="utf-8"))
    subprocess.run(command, check=True, capture_output=True, text=True)
    second = json.loads(manifest.read_text(encoding="utf-8"))
    assert first == second
    assert first["selected_count"] == 8
    assert set(first["discordant_item_ids"]) == {"item-2", "item-9", "item-21"}
    assert len(first["random_concordant_item_ids"]) == 5
    assert first["selected_item_ids"] == sorted(
        first["selected_item_ids"], key=lambda item: int(item.split("-")[1])
    )
