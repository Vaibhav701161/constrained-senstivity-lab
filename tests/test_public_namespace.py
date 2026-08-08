from __future__ import annotations

import constrained_sensitivity_lab as csl
import project_a


def test_branded_namespace_preserves_frozen_implementation_identity() -> None:
    assert csl.AnswerRepresentation is project_a.AnswerRepresentation
    assert csl.ConditionSpec is project_a.ConditionSpec
    assert csl.canonical_integer_string is project_a.canonical_integer_string
    assert csl.spec_for_condition is project_a.spec_for_condition
    assert csl.transduce_integer_object is project_a.transduce_integer_object


def test_branded_namespace_transduces_canonical_integer() -> None:
    assert csl.canonical_integer_string(-12) == "-12"
