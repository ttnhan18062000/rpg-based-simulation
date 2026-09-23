"""Tests for tools/semantic_control_plane/ and the three registries it validates
(TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION).

Per the ticket's own AC: a validator only ever run against good data is indistinguishable from one
that does nothing. Every invariant below is proven failing on a deliberately broken fixture, never
just passing on a clean one -- and each fixture is invalid for exactly one invariant at a time, the
same structuring rule tests/unit/tools/test_mechanism_registry.py already establishes.
"""
from __future__ import annotations

import ast
import inspect
import subprocess
import sys
from pathlib import Path

import pytest

from tools.semantic_control_plane.rule_catalog import scan_rule_ids
from tools.semantic_control_plane.registry import (
    validate_all,
    validate_mechanism_causal_edges,
    validate_rule_classifications,
    validate_rule_mechanism_edges,
    consumers_of,
    producers_for,
)
from tools.semantic_control_plane import registry as _registry_module
from tools.semantic_control_plane import rule_catalog as _rule_catalog_module

REPO_ROOT = Path(__file__).resolve().parents[3]
_ARCHITECTURE_MD_PATH = (
    REPO_ROOT / "docs" / "plans" / "simulation_semantic_control_plane" / "architecture.md"
)


# ── Step 1: rule_id corpus parser ───────────────────────────────────────────────────────────


def test_rule_id_scanner_finds_known_rule_ids():
    ids = scan_rule_ids()
    assert "TERR-01" in ids
    assert any(i.startswith("LEARN-") for i in ids), "expected at least one LEARN- family id"


def test_rule_id_scanner_excludes_review_exports(tmp_path):
    canonical_dir = tmp_path / "places-culture"
    canonical_dir.mkdir()
    (canonical_dir / "territory.md").write_text(
        "# Territory\n\n## FOO-01 — a real rule heading\n", encoding="utf-8"
    )
    review_dir = tmp_path / "review-exports"
    review_dir.mkdir()
    (review_dir / "batch-review.md").write_text(
        "# Batch Review\n\n## BAR-02 — this looks like a rule heading but must be excluded\n",
        encoding="utf-8",
    )

    ids = scan_rule_ids(base_path=tmp_path)

    assert ids == {"FOO-01"}


# ── Schema 1: Rule -> Mechanism edges ───────────────────────────────────────────────────────


def test_rule_mechanism_edge_schema_accepts_valid_row():
    data = {
        "edges": [
            {
                "rule_id": "TERR-01",
                "mechanism_id": "regional_sovereignty",
                "edge_type": "CONSTRAINED_BY",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors == []


def test_rule_mechanism_edge_schema_accepts_empty_data():
    errors = validate_rule_mechanism_edges(
        {"edges": []}, known_rule_ids=set(), known_mechanism_ids=set()
    )
    assert errors == []


def test_validator_rejects_invalid_edge_type():
    data = {
        "edges": [
            {
                "rule_id": "TERR-01",
                "mechanism_id": "regional_sovereignty",
                # A plausible near-miss: schema 2's own vocabulary, not schema 1's.
                "edge_type": "PRODUCES_INPUT_FOR",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors
    assert any("PRODUCES_INPUT_FOR" in e for e in errors), errors


def test_validator_rejects_unresolved_rule_id():
    data = {
        "edges": [
            {
                "rule_id": "NOPE-99",
                "mechanism_id": "regional_sovereignty",
                "edge_type": "REALIZES",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors
    assert any("NOPE-99" in e for e in errors), errors


def test_validator_rejects_unresolved_mechanism_id():
    data = {
        "edges": [
            {
                "rule_id": "TERR-01",
                "mechanism_id": "nonexistent_mechanism",
                "edge_type": "REALIZES",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors
    assert any("nonexistent_mechanism" in e for e in errors), errors


def test_validator_rejects_duplicate_rule_mechanism_edge_type_triple():
    row = {
        "rule_id": "TERR-01",
        "mechanism_id": "regional_sovereignty",
        "edge_type": "REALIZES",
        "evidence": "synthetic test fixture",
        "date": "2026-09-23",
    }
    data = {"edges": [row, dict(row)]}
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors
    assert any("duplicate" in e.lower() for e in errors), errors


def test_rule_mechanism_edge_same_pair_different_edge_type_is_not_a_duplicate():
    data = {
        "edges": [
            {
                "rule_id": "TERR-01",
                "mechanism_id": "regional_sovereignty",
                "edge_type": "REALIZES",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            },
            {
                "rule_id": "TERR-01",
                "mechanism_id": "regional_sovereignty",
                "edge_type": "CONSTRAINED_BY",
                "evidence": "a second, distinct relation",
                "date": "2026-09-23",
            },
        ]
    }
    errors = validate_rule_mechanism_edges(
        data, known_rule_ids={"TERR-01"}, known_mechanism_ids={"regional_sovereignty"}
    )
    assert errors == []


# ── Schema 2: Mechanism -> Mechanism causal edges ───────────────────────────────────────────


def test_mechanism_causal_edge_schema_has_no_shared_edge_type_field():
    # Structural guard: the schema-2 validator's own executable body (not its prose docstring,
    # which explains the distinction in words) must never read an edge_type field -- proves the
    # two row shapes were never accidentally merged (roadmap.md names this exact mistake as
    # something an earlier draft already did).
    tree = ast.parse(inspect.getsource(validate_mechanism_causal_edges))
    func_node = tree.body[0]
    body_without_docstring = func_node.body[1:] if ast.get_docstring(func_node) else func_node.body
    body_source = "\n".join(ast.unparse(stmt) for stmt in body_without_docstring)
    assert "edge_type" not in body_source, body_source


def test_validator_rejects_unresolved_producer_mechanism_id():
    data = {
        "edges": [
            {
                "producer_mechanism_id": "nonexistent_mechanism",
                "consumer_mechanism_id": "combat_resolution",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_mechanism_causal_edges(
        data, known_mechanism_ids={"movement", "combat_resolution"}
    )
    assert errors
    assert any("nonexistent_mechanism" in e for e in errors), errors


def test_validator_rejects_unresolved_consumer_mechanism_id():
    data = {
        "edges": [
            {
                "producer_mechanism_id": "movement",
                "consumer_mechanism_id": "nonexistent_mechanism",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_mechanism_causal_edges(
        data, known_mechanism_ids={"movement", "combat_resolution"}
    )
    assert errors
    assert any("nonexistent_mechanism" in e for e in errors), errors


def test_validator_rejects_duplicate_directed_causal_pair():
    row = {
        "producer_mechanism_id": "movement",
        "consumer_mechanism_id": "combat_resolution",
        "evidence": "synthetic test fixture",
        "date": "2026-09-23",
    }
    data = {"edges": [row, dict(row)]}
    errors = validate_mechanism_causal_edges(
        data, known_mechanism_ids={"movement", "combat_resolution"}
    )
    assert errors
    assert any("duplicate" in e.lower() for e in errors), errors


def test_mechanism_causal_edge_reversed_pair_is_not_a_duplicate():
    data = {
        "edges": [
            {
                "producer_mechanism_id": "movement",
                "consumer_mechanism_id": "combat_resolution",
                "evidence": "forward fact",
                "date": "2026-09-23",
            },
            {
                "producer_mechanism_id": "combat_resolution",
                "consumer_mechanism_id": "movement",
                "evidence": "a distinct, reverse-direction fact",
                "date": "2026-09-23",
            },
        ]
    }
    errors = validate_mechanism_causal_edges(
        data, known_mechanism_ids={"movement", "combat_resolution"}
    )
    assert errors == []


def test_validator_rejects_self_producing_causal_edge():
    data = {
        "edges": [
            {
                "producer_mechanism_id": "movement",
                "consumer_mechanism_id": "movement",
                "evidence": "synthetic test fixture",
                "date": "2026-09-23",
            }
        ]
    }
    errors = validate_mechanism_causal_edges(data, known_mechanism_ids={"movement"})
    assert errors
    assert any("self" in e.lower() for e in errors), errors


def test_causal_edge_inverse_is_computed_not_stored():
    edges = [
        {
            "producer_mechanism_id": "movement",
            "consumer_mechanism_id": "combat_resolution",
            "evidence": "forward fact only",
            "date": "2026-09-23",
        }
    ]

    assert consumers_of("movement", edges) == ["combat_resolution"]
    assert producers_for("combat_resolution", edges) == ["movement"]

    # No row in the fixture itself stores the reverse direction -- the inverse answer above came
    # entirely from traversal, not from a hand-authored reverse row.
    assert not any(
        e.get("producer_mechanism_id") == "combat_resolution"
        and e.get("consumer_mechanism_id") == "movement"
        for e in edges
    )


# ── Schema 3: per-Rule realization classification ───────────────────────────────────────────


def test_rule_classification_schema_holds_one_record_per_rule():
    data = {
        "classifications": [
            {
                "rule_id": "TERR-01",
                "classification": "CONFLICTING",
                "evidence": "synthetic test fixture",
                "review_date": "2026-09-23",
            },
            {
                "rule_id": "LEARN-01",
                "classification": "UNKNOWN",
                "evidence": "synthetic test fixture",
                "review_date": "2026-09-23",
            },
        ]
    }
    errors = validate_rule_classifications(data, known_rule_ids={"TERR-01", "LEARN-01"})
    assert errors == []


def test_validator_rejects_invalid_classification_value():
    data = {
        "classifications": [
            {
                "rule_id": "TERR-01",
                "classification": "REJECTED",
                "evidence": "synthetic test fixture",
                "review_date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_classifications(data, known_rule_ids={"TERR-01"})
    assert errors
    assert any("REJECTED" in e for e in errors), errors


def test_validator_rejects_duplicate_rule_id_in_classification_registry():
    row = {
        "rule_id": "TERR-01",
        "classification": "CONFLICTING",
        "evidence": "synthetic test fixture",
        "review_date": "2026-09-23",
    }
    data = {"classifications": [row, dict(row)]}
    errors = validate_rule_classifications(data, known_rule_ids={"TERR-01"})
    assert errors
    assert any("duplicate" in e.lower() for e in errors), errors


def test_unknown_classification_is_accepted_and_preserved():
    data = {
        "classifications": [
            {
                "rule_id": "TERR-01",
                "classification": "UNKNOWN",
                "evidence": "synthetic test fixture",
                "review_date": "2026-09-23",
            }
        ]
    }
    errors = validate_rule_classifications(data, known_rule_ids={"TERR-01"})
    assert errors == []
    assert data["classifications"][0]["classification"] == "UNKNOWN"


def test_no_function_derives_classification_from_edges():
    # Cheap early-warning grep, not a hard static-analysis guard: no function in either module
    # has a name suggesting it derives a classification from edge data. The primary proof is the
    # human confirmation recorded in the ticket's own Implementation Notes -- see
    # staging_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/plan.md Step 4.
    for module in (_registry_module, _rule_catalog_module):
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and getattr(obj, "__module__", None) == module.__name__:
                lname = name.lower()
                assert not ("edge" in lname and "classif" in lname), (
                    f"{module.__name__}.{name} looks like it derives a classification from edge "
                    "data -- forbidden, see architecture.md §3/§4"
                )


# ── Cross-schema ─────────────────────────────────────────────────────────────────────────────


def test_all_three_schemas_pass_on_real_seed_data():
    errors = validate_all()
    assert errors == []


def test_all_four_terr_rules_have_a_classification_record():
    """TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE AC 1/AC 3: TERR-01/02/03/05 each have
    exactly one classification record; TERR-04 has none (it is not a real Rule ID)."""
    path = REPO_ROOT / "registries" / "rule_classifications.yaml"
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    records = data.get("classifications", []) or []
    rule_ids = [r["rule_id"] for r in records]

    for expected in ("TERR-01", "TERR-02", "TERR-03", "TERR-05"):
        assert rule_ids.count(expected) == 1, (
            f"expected exactly one classification record for {expected}, found "
            f"{rule_ids.count(expected)}"
        )
    assert "TERR-04" not in rule_ids


def test_terr04_never_appears_in_populated_registries():
    """Directly enforces the ticket's own Out of Scope line: TERR-04 is a stale citation, not a
    real Rule ID, and must never be written to either populated registry."""
    for filename in ("rule_mechanism_edges.yaml", "rule_classifications.yaml"):
        text = (REPO_ROOT / "registries" / filename).read_text(encoding="utf-8")
        assert "TERR-04" not in text, f"{filename} must never reference TERR-04"


def test_real_rule_mechanism_edges_have_nonempty_evidence_and_date():
    """AC 2: zero uncited edges -- every row's evidence is a non-empty string and date matches
    YYYY-MM-DD."""
    import re
    import yaml

    path = REPO_ROOT / "registries" / "rule_mechanism_edges.yaml"
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    edges = data.get("edges", []) or []
    assert edges, "expected at least one real edge to check"

    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for edge in edges:
        evidence = edge.get("evidence")
        assert isinstance(evidence, str) and evidence.strip(), (
            f"edge {edge.get('rule_id')} -> {edge.get('mechanism_id')} has empty evidence"
        )
        date = edge.get("date")
        assert isinstance(date, str) and date_re.match(date), (
            f"edge {edge.get('rule_id')} -> {edge.get('mechanism_id')} has invalid date {date!r}"
        )


def test_documented_cli_invocation_actually_runs():
    """The module docstring and all three registry file headers document
    `python3 tools/semantic_control_plane/registry.py` as the validation entry point -- run it for
    real, as a fresh subprocess with no pytest-inherited sys.path, so a missing sys.path bootstrap
    (which in-process imports like validate_all() above can never catch) doesn't go undetected."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tools" / "semantic_control_plane" / "registry.py")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "OK" in result.stdout


def test_architecture_md_no_longer_says_deliberately_undecided():
    text = _ARCHITECTURE_MD_PATH.read_text(encoding="utf-8")
    assert "Deliberately undecided" not in text


def test_architecture_md_section_3_names_chosen_schema():
    text = _ARCHITECTURE_MD_PATH.read_text(encoding="utf-8")
    section_3 = text.split("## 3.", 1)[1].split("## 4.", 1)[0]

    assert "registries/rule_mechanism_edges.yaml" in section_3
    assert "registries/mechanism_causal_edges.yaml" in section_3
    assert "registries/rule_classifications.yaml" in section_3
    # Still three distinct structures, not one collapsed description.
    assert section_3.count("registries/") >= 3
    assert "validate_all" in section_3
    assert "§7" in section_3
