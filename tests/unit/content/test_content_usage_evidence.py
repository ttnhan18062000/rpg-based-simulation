"""
Tests for validate_matrix_evidence() — TCK-20260607-MATRIX-EVIDENCE-VALIDATOR.

Four tests:
1. Integration: all real matrix paths and node IDs are valid after ghost-node-ID corrections.
2. RUNTIME_AUTHORITATIVE with no evidence_tests is a violation.
3. DESIGN_ONLY with no evidence_tests is NOT a violation.
4. ::node_id suffix that does not exist in the file is a violation.
"""
from src.content.matrix import CONTENT_USAGE_MATRIX, ContentFamilyMatrixEntry
from src.content.validator import validate_matrix_evidence


def test_all_matrix_evidence_paths_exist():
    """Integration guard: all evidence_tests values in the real matrix resolve correctly."""
    violations = validate_matrix_evidence(CONTENT_USAGE_MATRIX)
    assert violations == [], (
        "Evidence path violations found in CONTENT_USAGE_MATRIX:\n" + "\n".join(violations)
    )


def test_missing_evidence_for_runtime_authoritative_is_violation():
    """RUNTIME_AUTHORITATIVE entries without evidence_tests must produce a violation."""
    fake_matrix = {
        "test/fake_runtime": ContentFamilyMatrixEntry(
            file_path="test/fake_runtime.yaml",
            schema_class="FakeSchema",
            repository_index="fake_runtime",
            validator_coverage="None",
            resolver_component="FakeResolver",
            compile_runtime_consumer="FakeRegistry",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests=None,
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="RUNTIME_AUTHORITATIVE",
            content_maturity="REDESIGNED-CORE",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert len(violations) >= 1
    assert "test/fake_runtime" in violations[0]


def test_missing_evidence_for_design_only_is_not_violation():
    """DESIGN_ONLY entries without evidence_tests must NOT produce a violation."""
    fake_matrix = {
        "test/fake_design": ContentFamilyMatrixEntry(
            file_path="test/fake_design.yaml",
            schema_class=None,
            repository_index=None,
            validator_coverage="None",
            resolver_component="None (Design-Only)",
            compile_runtime_consumer="None",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests=None,
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="DESIGN_ONLY",
            content_maturity="FUTURE-EXTENSION",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert violations == []


def test_ghost_node_id_is_violation():
    """A ::node_id suffix that does not exist in the referenced file is a violation."""
    fake_matrix = {
        "test/fake_ghost": ContentFamilyMatrixEntry(
            file_path="test/fake_ghost.yaml",
            schema_class="FakeSchema",
            repository_index="fake_ghost",
            validator_coverage="None",
            resolver_component="FakeResolver",
            compile_runtime_consumer="FakeRegistry",
            test_coverage="tests/unit/content/test_catalog.py",
            evidence_tests="tests/unit/core/test_registry_adapters.py::test_nonexistent_function_zzz",
            resolver_evidence=None,
            runtime_consumer_evidence=None,
            implementation_state="RUNTIME_AUTHORITATIVE",
            content_maturity="REDESIGNED-CORE",
        )
    }
    violations = validate_matrix_evidence(fake_matrix)
    assert len(violations) >= 1
    assert "test_nonexistent_function_zzz" in violations[0]
