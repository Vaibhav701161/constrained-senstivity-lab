"""Canonical, inspectable intermediate representation for external JSON contracts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

IR_VERSION = "contract-ir-v1"


class ContractIRError(ValueError):
    """Raised when a schema cannot be represented by the prototype IR."""


class UnsupportedSchemaError(ContractIRError):
    """Raised when a caller requires the initial supported schema subset."""


@dataclass(frozen=True, order=True)
class UnsupportedConstruct:
    """One schema feature recorded rather than silently discarded."""

    path: tuple[str, ...]
    keyword: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": list(self.path),
            "keyword": self.keyword,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PropertyIR:
    """Typed property metadata in declared generation order."""

    name: str
    required: bool
    json_type: str | None
    scalar_representation: str
    normalized_schema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "required": self.required,
            "json_type": self.json_type,
            "scalar_representation": self.scalar_representation,
            "schema": self.normalized_schema,
        }


@dataclass(frozen=True)
class ContractIR:
    """Normalized top-level object contract with stable serialization and hashing."""

    schema_dialect: str | None
    properties: tuple[PropertyIR, ...]
    required_fields: tuple[str, ...]
    external_field_order: tuple[str, ...]
    additional_properties: bool
    unsupported: tuple[UnsupportedConstruct, ...]
    version: str = IR_VERSION

    @classmethod
    def from_schema(cls, schema: Mapping[str, Any]) -> "ContractIR":
        if not isinstance(schema, Mapping):
            raise ContractIRError("schema must be a JSON object")
        if schema.get("type") != "object":
            raise ContractIRError("initial ContractIR requires a top-level object schema")

        raw_properties = schema.get("properties", {})
        if not isinstance(raw_properties, Mapping):
            raise ContractIRError("properties must be an object")
        raw_required = schema.get("required", [])
        if not isinstance(raw_required, list) or not all(
            isinstance(name, str) for name in raw_required
        ):
            raise ContractIRError("required must be an array of strings")
        if len(set(raw_required)) != len(raw_required):
            raise ContractIRError("required contains duplicate field names")

        unknown_required = sorted(set(raw_required) - set(raw_properties))
        if unknown_required:
            raise ContractIRError(
                f"required fields are not declared in properties: {unknown_required}"
            )

        additional = schema.get("additionalProperties", True)
        unsupported: list[UnsupportedConstruct] = []
        if not isinstance(additional, bool):
            unsupported.append(
                UnsupportedConstruct(
                    (),
                    "additionalProperties",
                    "schema-valued additionalProperties is outside the initial subset",
                )
            )
            additional = True

        root_allowed = {
            "$schema",
            "type",
            "title",
            "description",
            "properties",
            "required",
            "additionalProperties",
            "minProperties",
            "maxProperties",
        }
        _record_unknown_keywords(schema, (), root_allowed, unsupported)

        properties: list[PropertyIR] = []
        required_set = set(raw_required)
        for name, property_schema in raw_properties.items():
            if not isinstance(name, str):
                raise ContractIRError("property names must be strings")
            if not isinstance(property_schema, Mapping):
                raise ContractIRError(f"property {name!r} schema must be an object")
            normalized = _normalize_node(property_schema, ("properties", name), unsupported)
            json_type = property_schema.get("type")
            if not isinstance(json_type, str):
                json_type = None
            properties.append(
                PropertyIR(
                    name=name,
                    required=name in required_set,
                    json_type=json_type,
                    scalar_representation=_scalar_representation(property_schema),
                    normalized_schema=normalized,
                )
            )

        return cls(
            schema_dialect=(
                str(schema["$schema"]) if isinstance(schema.get("$schema"), str) else None
            ),
            properties=tuple(properties),
            required_fields=tuple(sorted(raw_required)),
            external_field_order=tuple(raw_properties),
            additional_properties=additional,
            unsupported=tuple(sorted(unsupported)),
        )

    @property
    def supported(self) -> bool:
        return not self.unsupported

    def require_supported(self) -> None:
        if self.unsupported:
            details = "; ".join(
                f"{_display_path(item.path)}:{item.keyword} ({item.reason})"
                for item in self.unsupported
            )
            raise UnsupportedSchemaError(details)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "schema_dialect": self.schema_dialect,
            "properties": [item.to_dict() for item in self.properties],
            "required_fields": list(self.required_fields),
            "external_field_order": list(self.external_field_order),
            "additional_properties": self.additional_properties,
            "unsupported": [item.to_dict() for item in self.unsupported],
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )

    @property
    def stable_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def _display_path(path: tuple[str, ...]) -> str:
    return "/" + "/".join(path) if path else "/"


def _record_unknown_keywords(
    schema: Mapping[str, Any],
    path: tuple[str, ...],
    allowed: set[str],
    unsupported: list[UnsupportedConstruct],
) -> None:
    for keyword in schema:
        if keyword not in allowed:
            reason = "keyword is outside the initial supported subset"
            if keyword == "$ref":
                value = schema[keyword]
                reason = (
                    "remote references are refused"
                    if isinstance(value, str) and not value.startswith("#")
                    else "local and recursive references are refused"
                )
            unsupported.append(UnsupportedConstruct(path, keyword, reason))


def _normalize_node(
    schema: Mapping[str, Any],
    path: tuple[str, ...],
    unsupported: list[UnsupportedConstruct],
) -> dict[str, Any]:
    json_type = schema.get("type")
    if not isinstance(json_type, str):
        unsupported.append(
            UnsupportedConstruct(
                path,
                "type",
                "a single explicit JSON type is required",
            )
        )

    common = {"type", "title", "description", "enum", "const"}
    scalar = {
        "string": {"pattern", "minLength", "maxLength", "format"},
        "integer": {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"},
        "number": {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf"},
        "boolean": set(),
        "null": set(),
    }
    if json_type == "object":
        allowed = common | {
            "properties",
            "required",
            "additionalProperties",
            "minProperties",
            "maxProperties",
        }
    else:
        allowed = common | scalar.get(str(json_type), set())
    _record_unknown_keywords(schema, path, allowed, unsupported)

    if "pattern" in schema:
        pattern = schema["pattern"]
        if not isinstance(pattern, str):
            unsupported.append(
                UnsupportedConstruct(path, "pattern", "pattern must be a string")
            )
        else:
            try:
                re.compile(pattern)
            except re.error as error:
                unsupported.append(
                    UnsupportedConstruct(path, "pattern", f"invalid regular expression: {error}")
                )

    normalized: dict[str, Any] = {}
    for key in sorted(schema):
        value = schema[key]
        if key == "required" and isinstance(value, list):
            normalized[key] = sorted(value)
        elif key == "properties" and isinstance(value, Mapping):
            normalized[key] = [
                {
                    "name": name,
                    "schema": _normalize_node(
                        child,
                        path + ("properties", str(name)),
                        unsupported,
                    )
                    if isinstance(child, Mapping)
                    else child,
                }
                for name, child in value.items()
            ]
        else:
            normalized[key] = _canonical_value(value)
    return normalized


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _canonical_value(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    return value


def _scalar_representation(schema: Mapping[str, Any]) -> str:
    json_type = schema.get("type")
    if json_type == "string":
        return "patterned_string" if "pattern" in schema else "string"
    if json_type == "integer":
        return "native_integer"
    if json_type == "number":
        return "native_number"
    if json_type == "boolean":
        return "native_boolean"
    if json_type == "object":
        return "object"
    if json_type == "array":
        return "array"
    return "unknown"
