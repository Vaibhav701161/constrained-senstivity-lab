"""Public import surface for Constrained Sensitivity Lab.

The implementation remains in ``project_a`` because accepted source manifests bind
that historical path. New integrations should import the branded namespace exposed
here.
"""

from project_a import (
    AnswerRepresentation,
    ConditionSpec,
    canonical_integer_string,
    spec_for_condition,
    transduce_integer_object,
)

__all__ = [
    "AnswerRepresentation",
    "ConditionSpec",
    "canonical_integer_string",
    "spec_for_condition",
    "transduce_integer_object",
]
