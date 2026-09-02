"""Tests for the SelfModel keep/cut decision record added to
docs/architecture/cognition_domain_ownership.md by
TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION.
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_OWNERSHIP_DOC = _REPO_ROOT / "docs" / "architecture" / "cognition_domain_ownership.md"


def test_cognition_domain_ownership_records_self_model_decision():
    text = _OWNERSHIP_DOC.read_text(encoding="utf-8")
    assert "SelfModel" in text
    assert "CUT" in text
    assert "TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION" in text
