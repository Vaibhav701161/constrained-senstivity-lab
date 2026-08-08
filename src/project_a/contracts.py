"""Canonical contract fragments shared by experiments and runtime transforms."""

from __future__ import annotations

from typing import Any

CANONICAL_SIGNED_INTEGER_PATTERN = r"^-?(?:0|[1-9][0-9]*)$"

# The second spelling is language-equivalent and remains accepted for historical
# caller schemas. New schemas always emit CANONICAL_SIGNED_INTEGER_PATTERN.
CANONICAL_SIGNED_INTEGER_PATTERNS = frozenset(
    {
        CANONICAL_SIGNED_INTEGER_PATTERN,
        r"^-?(?:0|[1-9]\d*)$",
    }
)


def canonical_integer_string_schema(
    *, title: str | None = None, description: str | None = None
) -> dict[str, Any]:
    """Return the single canonical signed-integer string schema fragment."""

    schema: dict[str, Any] = {
        "type": "string",
        "pattern": CANONICAL_SIGNED_INTEGER_PATTERN,
    }
    if title is not None:
        schema["title"] = title
    if description is not None:
        schema["description"] = description
    return schema
