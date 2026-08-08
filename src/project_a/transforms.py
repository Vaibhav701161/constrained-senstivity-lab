"""Conservative schema rewrites and deterministic reverse transduction."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Mapping, MutableMapping

from jsonschema import SchemaError, ValidationError, validate

from .contracts import CANONICAL_SIGNED_INTEGER_PATTERNS
from .plan import AlignmentPlan, PlanError, TransformStep


class TransformError(ValueError):
    """Typed failure raised before an unsafe transformed value can be returned."""

    def __init__(self, code: str, message: str, path: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.code = code
        self.path = path

    def __str__(self) -> str:
        location = "/" + "/".join(self.path) if self.path else "/"
        return f"{self.code} at {location}: {super().__str__()}"


@dataclass(frozen=True)
class IntegerStringTransform:
    """Map an external canonical integer string to an internal JSON integer."""

    path: tuple[str, ...]
    allow_narrowing_with_integer_assertion: bool = False

    def rewrite_schema(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(dict(schema))
        field_schema = _schema_at_field_path(result, self.path)
        if field_schema.get("type") != "string":
            raise TransformError(
                "not_string", "integer-string transform requires a string field", self.path
            )
        pattern = field_schema.get("pattern")
        if pattern not in CANONICAL_SIGNED_INTEGER_PATTERNS and not (
            self.allow_narrowing_with_integer_assertion and isinstance(pattern, str)
        ):
            raise TransformError(
                "unsupported_numeric_lexical_contract",
                "external string language is not the canonical signed-integer language; "
                "an explicit integer-domain assertion is required for narrowing",
                self.path,
            )
        preserved = {
            key: field_schema[key]
            for key in ("title", "description")
            if key in field_schema
        }
        field_schema.clear()
        field_schema.update({"type": "integer", **preserved})
        return result

    def to_external(self, value: MutableMapping[str, Any]) -> None:
        parent, field = _value_parent(value, self.path)
        if field not in parent:
            raise TransformError("missing_field", "integer field is missing", self.path)
        internal = parent[field]
        if isinstance(internal, bool) or not isinstance(internal, int):
            raise TransformError(
                "not_integer", "internal value must be an integer and not a boolean", self.path
            )
        parent[field] = str(internal)


@dataclass(frozen=True)
class KeyAliasTransform:
    """Bijectively rename keys inside one object scope and restore them later."""

    scope: tuple[str, ...]
    external_to_internal: tuple[tuple[str, str], ...]
    reserved_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        external = [pair[0] for pair in self.external_to_internal]
        internal = [pair[1] for pair in self.external_to_internal]
        if not self.external_to_internal:
            raise TransformError("empty_alias_map", "alias map must not be empty", self.scope)
        if any(not source or not target for source, target in self.external_to_internal):
            raise TransformError(
                "invalid_alias", "alias names must be non-empty", self.scope
            )
        if len(set(external)) != len(external):
            raise TransformError(
                "duplicate_external_alias", "external alias sources must be unique", self.scope
            )
        if len(set(internal)) != len(internal):
            raise TransformError(
                "alias_collision", "two external keys cannot share one internal alias", self.scope
            )
        collision = sorted(set(internal) & set(self.reserved_keys))
        if collision:
            raise TransformError(
                "reserved_key_collision",
                f"aliases collide with reserved keys: {collision}",
                self.scope,
            )

    @property
    def forward(self) -> dict[str, str]:
        return dict(self.external_to_internal)

    @property
    def inverse(self) -> dict[str, str]:
        return {target: source for source, target in self.external_to_internal}

    def rewrite_schema(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(dict(schema))
        object_schema = _schema_at_object_scope(result, self.scope)
        properties = object_schema.get("properties")
        if not isinstance(properties, dict):
            raise TransformError(
                "missing_properties", "alias scope has no properties object", self.scope
            )
        missing = sorted(set(self.forward) - set(properties))
        if missing:
            raise TransformError(
                "unknown_external_key", f"alias sources are absent: {missing}", self.scope
            )
        untouched = set(properties) - set(self.forward)
        collisions = sorted(untouched & set(self.inverse))
        if collisions:
            raise TransformError(
                "alias_collision",
                f"aliases collide with existing internal keys: {collisions}",
                self.scope,
            )
        object_schema["properties"] = {
            self.forward.get(name, name): child for name, child in properties.items()
        }
        required = object_schema.get("required", [])
        if isinstance(required, list):
            object_schema["required"] = [self.forward.get(name, name) for name in required]
        return result

    def to_external(self, value: MutableMapping[str, Any]) -> None:
        scoped = _value_at_object_scope(value, self.scope)
        missing = sorted(set(self.inverse) - set(scoped))
        if missing:
            raise TransformError(
                "missing_internal_alias", f"internal aliases are absent: {missing}", self.scope
            )
        external_names = set(self.forward)
        untouched = set(scoped) - set(self.inverse)
        collisions = sorted(untouched & external_names)
        if collisions:
            raise TransformError(
                "reverse_alias_collision",
                f"external names already exist during reconstruction: {collisions}",
                self.scope,
            )
        restored: dict[str, Any] = {}
        for name, item in scoped.items():
            restored[self.inverse.get(name, name)] = item
        scoped.clear()
        scoped.update(restored)


@dataclass(frozen=True)
class FieldOrderTransform:
    """Choose model-facing object order and restore an explicit external order."""

    scope: tuple[str, ...]
    internal_order: tuple[str, ...]
    external_order: tuple[str, ...]
    buffer_output: bool = True
    internal_to_external: tuple[tuple[str, str], ...] = ()
    internal_only: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        mapping = dict(self.internal_to_external)
        if len(mapping) != len(self.internal_to_external):
            raise TransformError(
                "duplicate_order_mapping",
                "internal order mapping contains duplicate sources",
                self.scope,
            )
        if len(set(mapping.values())) != len(mapping):
            raise TransformError(
                "order_mapping_collision",
                "two internal fields cannot map to one external order field",
                self.scope,
            )
        if len(set(self.internal_order)) != len(self.internal_order) or len(
            set(self.external_order)
        ) != len(self.external_order):
            raise TransformError("duplicate_order_field", "field order has duplicates", self.scope)
        projected = {
            mapping.get(name, name)
            for name in self.internal_order
            if name not in set(self.internal_only)
        }
        if projected != set(self.external_order):
            raise TransformError(
                "order_field_mismatch",
                "internal fields do not project exactly onto the external order",
                self.scope,
            )
        if (self.internal_order != self.external_order or mapping or self.internal_only) and not self.buffer_output:
            raise TransformError(
                "streaming_requires_buffer",
                "order restoration requires buffered output",
                self.scope,
            )

    def rewrite_schema(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(dict(schema))
        object_schema = _schema_at_object_scope(result, self.scope)
        properties = object_schema.get("properties")
        if not isinstance(properties, dict) or set(properties) != set(self.internal_order):
            raise TransformError(
                "order_schema_mismatch",
                "field order must cover every property in the scoped schema",
                self.scope,
            )
        object_schema["properties"] = {
            name: properties[name] for name in self.internal_order
        }
        return result

    def to_external(self, value: MutableMapping[str, Any]) -> None:
        scoped = _value_at_object_scope(value, self.scope)
        extras = set(scoped) - set(self.external_order)
        missing_required_for_order = set(self.external_order) - set(scoped)
        if extras:
            raise TransformError(
                "unexpected_field", f"fields are outside the order policy: {sorted(extras)}", self.scope
            )
        reordered = {
            name: scoped[name]
            for name in self.external_order
            if name not in missing_required_for_order
        }
        scoped.clear()
        scoped.update(reordered)


@dataclass(frozen=True)
class ScratchFieldTransform:
    """Add a bounded internal-only string field and remove it deterministically."""

    scope: tuple[str, ...]
    key: str
    allowed: bool
    max_length: int = 256

    def __post_init__(self) -> None:
        if not self.allowed:
            raise TransformError(
                "scratch_prohibited", "policy prohibits internal scratch content", self.scope
            )
        if not self.key or self.max_length <= 0:
            raise TransformError(
                "invalid_scratch_spec", "scratch key and positive bound are required", self.scope
            )

    def rewrite_schema(self, schema: Mapping[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(dict(schema))
        object_schema = _schema_at_object_scope(result, self.scope)
        properties = object_schema.get("properties")
        if not isinstance(properties, dict):
            raise TransformError(
                "missing_properties", "scratch scope has no properties object", self.scope
            )
        if self.key in properties:
            raise TransformError(
                "scratch_collision", "scratch key collides with an external key", self.scope
            )
        properties[self.key] = {"type": "string", "maxLength": self.max_length}
        required = object_schema.setdefault("required", [])
        if not isinstance(required, list):
            raise TransformError("invalid_required", "required must be an array", self.scope)
        required.append(self.key)
        return result

    def to_external(self, value: MutableMapping[str, Any]) -> None:
        scoped = _value_at_object_scope(value, self.scope)
        if self.key not in scoped:
            raise TransformError(
                "missing_scratch", "required internal scratch field is missing", self.scope
            )
        content = scoped[self.key]
        if not isinstance(content, str) or len(content) > self.max_length:
            raise TransformError(
                "invalid_scratch", "scratch content violates its internal bound", self.scope
            )
        del scoped[self.key]


@dataclass(frozen=True)
class WhitespacePolicy:
    """Canonical backend whitespace configuration included in plan provenance."""

    backend: str
    mode: str = "canonical"

    def __post_init__(self) -> None:
        if self.backend not in {"outlines", "xgrammar"}:
            raise TransformError("unsupported_backend", f"unsupported backend {self.backend!r}")
        if self.mode not in {"canonical", "bounded", "any"}:
            raise TransformError("invalid_whitespace_mode", f"invalid mode {self.mode!r}")

    def backend_options(self) -> dict[str, Any]:
        if self.backend == "xgrammar":
            return {
                "any_whitespace": self.mode == "any",
                "max_whitespace_cnt": 1 if self.mode == "bounded" else None,
                "separators": [",", ":"] if self.mode == "canonical" else None,
            }
        return {
            "whitespace_pattern": (
                "" if self.mode == "canonical" else r"[ ]?" if self.mode == "bounded" else None
            )
        }


@dataclass(frozen=True)
class PipelineResult:
    """Fail-closed finalization result for an internal object."""

    external_value: dict[str, Any] | None
    valid: bool
    error_code: str | None
    error: str | None


def build_internal_schema(
    external_schema: Mapping[str, Any], transforms: tuple[TransformStep, ...]
) -> dict[str, Any]:
    """Apply schema rewrites in the declared forward plan order."""

    schema = copy.deepcopy(dict(external_schema))
    for step in transforms:
        params = step.parameters
        if step.kind == "integer_string":
            schema = IntegerStringTransform(
                step.path,
                bool(params.get("allow_narrowing_with_integer_assertion", False)),
            ).rewrite_schema(schema)
        elif step.kind == "key_alias":
            schema = KeyAliasTransform(
                step.path,
                _alias_pairs(params),
                tuple(str(item) for item in params.get("reserved_keys", [])),
            ).rewrite_schema(schema)
        elif step.kind == "scratch_field":
            schema = ScratchFieldTransform(
                step.path,
                str(params.get("key", "")),
                bool(params.get("allowed", False)),
                int(params.get("max_length", 256)),
            ).rewrite_schema(schema)
        elif step.kind == "field_order":
            schema = FieldOrderTransform(
                step.path,
                tuple(str(item) for item in params.get("internal_order", [])),
                tuple(str(item) for item in params.get("external_order", [])),
                bool(params.get("buffer_output", True)),
                _alias_pairs_from_key(params, "internal_to_external"),
                tuple(str(item) for item in params.get("internal_only", [])),
            ).rewrite_schema(schema)
        elif step.kind == "canonical_whitespace":
            WhitespacePolicy(str(params.get("backend", "")), str(params.get("mode", "")))
        else:  # pragma: no cover - TransformStep validates this first.
            raise PlanError(f"unknown transform kind: {step.kind}")
    return schema


def execute_transducer(
    plan: AlignmentPlan,
    internal_value: Mapping[str, Any],
    external_schema: Mapping[str, Any],
) -> PipelineResult:
    """Validate internally, reverse every transform, and validate externally."""

    try:
        plan.require_executable()
        internal = copy.deepcopy(dict(internal_value))
        validate(instance=internal, schema=plan.internal_schema)

        # Reverse transformations in semantic dependency order. Whitespace affects
        # serialization only and does not modify the parsed JSON value.
        for step in reversed(plan.transforms):
            if step.kind != "scratch_field":
                continue
            params = step.parameters
            ScratchFieldTransform(
                step.path,
                str(params.get("key", "")),
                bool(params.get("allowed", False)),
                int(params.get("max_length", 256)),
            ).to_external(internal)
        for step in reversed(plan.transforms):
            if step.kind != "key_alias":
                continue
            params = step.parameters
            KeyAliasTransform(
                step.path,
                _alias_pairs(params),
                tuple(str(item) for item in params.get("reserved_keys", [])),
            ).to_external(internal)
        for step in reversed(plan.transforms):
            if step.kind == "integer_string":
                params = step.parameters
                IntegerStringTransform(
                    step.path,
                    bool(params.get("allow_narrowing_with_integer_assertion", False)),
                ).to_external(internal)
        for step in reversed(plan.transforms):
            if step.kind != "field_order":
                continue
            params = step.parameters
            FieldOrderTransform(
                step.path,
                tuple(str(item) for item in params.get("internal_order", [])),
                tuple(str(item) for item in params.get("external_order", [])),
                bool(params.get("buffer_output", True)),
                _alias_pairs_from_key(params, "internal_to_external"),
                tuple(str(item) for item in params.get("internal_only", [])),
            ).to_external(internal)

        validate(instance=internal, schema=dict(external_schema))
    except TransformError as error:
        return PipelineResult(None, False, error.code, str(error))
    except (SchemaError, ValidationError, PlanError, TypeError, ValueError) as error:
        return PipelineResult(None, False, type(error).__name__, f"{type(error).__name__}: {error}")
    return PipelineResult(internal, True, None, None)


def _alias_pairs(params: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    return _alias_pairs_from_key(params, "external_to_internal")


def _alias_pairs_from_key(
    params: Mapping[str, Any], key: str
) -> tuple[tuple[str, str], ...]:
    raw = params.get(key, {})
    if not isinstance(raw, Mapping):
        raise TransformError("invalid_alias_map", f"{key} must be an object")
    return tuple((str(source), str(target)) for source, target in raw.items())


def _schema_at_object_scope(
    schema: MutableMapping[str, Any], scope: tuple[str, ...]
) -> MutableMapping[str, Any]:
    current = schema
    for segment in scope:
        properties = current.get("properties")
        if not isinstance(properties, dict) or segment not in properties:
            raise TransformError("unknown_scope", "object scope does not exist", scope)
        child = properties[segment]
        if not isinstance(child, dict) or child.get("type") != "object":
            raise TransformError("scope_not_object", "scope does not select an object", scope)
        current = child
    return current


def _schema_at_field_path(
    schema: MutableMapping[str, Any], path: tuple[str, ...]
) -> MutableMapping[str, Any]:
    if not path:
        raise TransformError("empty_field_path", "field path must not be empty")
    parent = _schema_at_object_scope(schema, path[:-1])
    properties = parent.get("properties")
    if not isinstance(properties, dict) or path[-1] not in properties:
        raise TransformError("unknown_field", "field does not exist", path)
    field = properties[path[-1]]
    if not isinstance(field, dict):
        raise TransformError("invalid_field_schema", "field schema is not an object", path)
    return field


def _value_at_object_scope(
    value: MutableMapping[str, Any], scope: tuple[str, ...]
) -> MutableMapping[str, Any]:
    current = value
    for segment in scope:
        child = current.get(segment)
        if not isinstance(child, dict):
            raise TransformError("invalid_value_scope", "value scope is absent or not an object", scope)
        current = child
    return current


def _value_parent(
    value: MutableMapping[str, Any], path: tuple[str, ...]
) -> tuple[MutableMapping[str, Any], str]:
    if not path:
        raise TransformError("empty_field_path", "field path must not be empty")
    return _value_at_object_scope(value, path[:-1]), path[-1]
