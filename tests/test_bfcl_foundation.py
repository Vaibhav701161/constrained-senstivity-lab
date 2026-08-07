from __future__ import annotations

import hashlib

import pytest

from scripts.fetch_bfcl_foundation import raw_url, verify_bytes


def test_raw_url_is_bound_to_the_exact_checkpoint() -> None:
    url = raw_url(
        "https://github.com/ShishirPatil/gorilla.git",
        "abc123",
        "berkeley-function-call-leaderboard/data.json",
    )
    assert url == (
        "https://raw.githubusercontent.com/ShishirPatil/gorilla/abc123/"
        "berkeley-function-call-leaderboard/data.json"
    )


def test_download_hash_check_fails_closed() -> None:
    payload = b"pinned artifact"
    verify_bytes(payload, hashlib.sha256(payload).hexdigest())
    with pytest.raises(ValueError, match="source hash mismatch"):
        verify_bytes(payload, "0" * 64)
