"""Deterministic, serializable alignment plans for contract transformations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

PLAN_VERSION = "alignment-plan-v1"


class PlanError(ValueError):
    """Raised when an alignment plan is invalid or cannot be replayed."""


TRANSFORM_ORDER = {
    "integer_string": 10,
    "key_alias": 20,
    "scratch_field": 30,
    "field_order": 40,
    "canonical_whitespace": 50,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class TransformStep:
    """One versioned, path-scoped transformation with canonical parameters."""

    kind: str
    version: str
    path: tuple[str, ...]
    parameters_json: str

    @classmethod
    def create(
        cls,
        kind: str,
        *,
        version: str = "v1",
        path: tuple[str, ...] = (),
        parameters: Mapping[str, Any] | None = None,
    ) -> "TransformStep":
        if kind not in TRANSFORM_ORDER:
            raise PlanError(f"unknown transform kind: {kind}")
        if not version:
            raise PlanError("transform version must not be empty")
        if not all(isinstance(segment, str) and segment for segment in path):
            raise PlanError("transform path segments must be non-empty strings")
        return cls(
            kind=kind,
            version=version,
            path=path,
            parameters_json=_canonical_json(dict(parameters or {})),
        )

    @property
    def parameters(self) -> dict[str, Any]:
        value = json.loads(self.parameters_json)
        if not isinstance(value, dict):
            raise PlanError("transform parameters must decode to an object")
        return value

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "version": self.version,
            "path": list(self.path),
            "parameters": self.parameters,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "TransformStep":
        path = value.get("path", [])
        parameters = value.get("parameters", {})
        if not isinstance(path, list) or not isinstance(parameters, Mapping):
            raise PlanError("invalid serialized transform step")
        return cls.create(
            str(value.get("kind", "")),
            version=str(value.get("version", "")),
            path=tuple(str(segment) for segment in path),
            parameters=parameters,
        )


@dataclass(frozen=True)
class BackendRequirements:
    """Backend features that must be honored for a plan to be valid."""

    backend: str
    property_order: str
    whitespace_policy: str
    requires_buffering: bool
    capabilities: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.backend:
            raise PlanError("backend must not be empty")
        if self.property_order not in {"schema", "any"}:
            raise PlanError("property_order must be 'schema' or 'any'")
        if self.whitespace_policy not in {"canonical", "bounded", "any"}:
            raise PlanError("invalid whitespace policy")
        if len(set(self.capabilities)) != len(self.capabilities):
            raise PlanError("backend capabilities contain duplicates")

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "property_order": self.property_order,
            "whitespace_policy": self.whitespace_policy,
            "requires_buffering": self.requires_buffering,
            "capabilities": sorted(self.capabilities),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "BackendRequirements":
        capabilities = value.get("capabilities", [])
        if not isinstance(capabilities, list):
            raise PlanError("backend capabilities must be an array")
        return cls(
            backend=str(value.get("backend", "")),
            property_order=str(value.get("property_order", "")),
            whitespace_policy=str(value.get("whitespace_policy", "")),
            requires_buffering=bool(value.get("requires_buffering", False)),
            capabilities=tuple(str(item) for item in capabilities),
        )


@dataclass(frozen=True)
class RefusalReason:
    """Machine-readable explanation for a plan that must not execute."""

    code: str
    message: str
    path: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "path": list(self.path)}

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "RefusalReason":
        path = value.get("path", [])
        if not isinstance(path, list):
            raise PlanError("refusal path must be an array")
        return cls(
            code=str(value.get("code", "")),
            message=str(value.get("message", "")),
            path=tuple(str(segment) for segment in path),
        )


@dataclass(frozen=True)
class AlignmentPlan:
    """Replayable contract alignment decision and deterministic transducer spec."""

    external_schema_hash: str
    internal_schema_json: str
    transforms: tuple[TransformStep, ...]
    backend_requirements: BackendRequirements
    transducer_version: str
    refusal_reasons: tuple[RefusalReason, ...]
    provenance_json: str
    explanation: str
    version: str = PLAN_VERSION

    @classmethod
    def create(
        cls,
        *,
        external_schema_hash: str,
        internal_schema: Mapping[str, Any],
        transforms: tuple[TransformStep, ...],
        backend_requirements: BackendRequirements,
        transducer_version: str,
        provenance: Mapping[str, Any],
        explanation: str,
        refusal_reasons: tuple[RefusalReason, ...] = (),
    ) -> "AlignmentPlan":
        if len(external_schema_hash) != 64 or any(
            character not in "0123456789abcdef" for character in external_schema_hash
        ):
            raise PlanError("external schema hash must be a lowercase SHA-256 digest")
        if not transducer_version:
            raise PlanError("transducer version must not be empty")
        _validate_transform_order(transforms)
        return cls(
            external_schema_hash=external_schema_hash,
            internal_schema_json=_canonical_json(dict(internal_schema)),
            transforms=transforms,
            backend_requirements=backend_requirements,
            transducer_version=transducer_version,
            refusal_reasons=tuple(refusal_reasons),
            provenance_json=_canonical_json(dict(provenance)),
            explanation=explanation,
        )

    @property
    def internal_schema(self) -> dict[str, Any]:
        value = json.loads(self.internal_schema_json)
        if not isinstance(value, dict):
            raise PlanError("internal schema must decode to an object")
        return value

    @property
    def provenance(self) -> dict[str, Any]:
        value = json.loads(self.provenance_json)
        if not isinstance(value, dict):
            raise PlanError("provenance must decode to an object")
        return value

    @property
    def executable(self) -> bool:
        return not self.refusal_reasons

    def require_executable(self) -> None:
        if self.refusal_reasons:
            rendered = "; ".join(
                f"{reason.code}: {reason.message}" for reason in self.refusal_reasons
            )
            raise PlanError(f"alignment plan was refused: {rendered}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "external_schema_hash": self.external_schema_hash,
            "internal_schema": self.internal_schema,
            "transforms": [step.to_dict() for step in self.transforms],
            "backend_requirements": self.backend_requirements.to_dict(),
            "transducer_version": self.transducer_version,
            "refusal_reasons": [reason.to_dict() for reason in self.refusal_reasons],
            "provenance": self.provenance,
            "explanation": self.explanation,
        }

    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def stable_hash(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()

    @classmethod
    def from_json(cls, payload: str) -> "AlignmentPlan":
        try:
            value = json.loads(payload)
        except json.JSONDecodeError as error:
            raise PlanError(f"invalid plan JSON: {error}") from error
        if not isinstance(value, dict):
            raise PlanError("serialized plan must be an object")
        if value.get("version") != PLAN_VERSION:
            raise PlanError(f"unsupported plan version: {value.get('version')!r}")
        transforms = value.get("transforms", [])
        refusals = value.get("refusal_reasons", [])
        backend = value.get("backend_requirements")
        if (
            not isinstance(transforms, list)
            or not isinstance(refusals, list)
            or not isinstance(backend, Mapping)
            or not isinstance(value.get("internal_schema"), Mapping)
            or not isinstance(value.get("provenance"), Mapping)
        ):
            raise PlanError("serialized plan contains invalid field types")
        return cls.create(
            external_schema_hash=str(value.get("external_schema_hash", "")),
            internal_schema=value["internal_schema"],
            transforms=tuple(TransformStep.from_dict(item) for item in transforms),
            backend_requirements=BackendRequirements.from_dict(backend),
            transducer_version=str(value.get("transducer_version", "")),
            refusal_reasons=tuple(RefusalReason.from_dict(item) for item in refusals),
            provenance=value["provenance"],
            explanation=str(value.get("explanation", "")),
        )


def _validate_transform_order(transforms: tuple[TransformStep, ...]) -> None:
    ranks = [TRANSFORM_ORDER[step.kind] for step in transforms]
    if ranks != sorted(ranks):
        raise PlanError(
            "invalid transform ordering; expected integer, alias, scratch, order, whitespace"
        )
    identities = [(step.kind, step.path) for step in transforms]
    if len(set(identities)) != len(identities):
        raise PlanError("duplicate transform kind and path")
