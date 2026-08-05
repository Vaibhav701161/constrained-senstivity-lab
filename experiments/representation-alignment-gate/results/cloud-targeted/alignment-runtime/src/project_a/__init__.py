"""Contract-preserving structured-generation primitives."""

from .schema_variants import AnswerRepresentation, ConditionSpec, spec_for_condition
from .transducer import canonical_integer_string, transduce_integer_object

__all__ = [
    "AnswerRepresentation",
    "ConditionSpec",
    "canonical_integer_string",
    "spec_for_condition",
    "transduce_integer_object",
]
