"""Tests for tools/code_test_index.py.

Fixtures are small, hand-built graphs -- never the live 41.9MB graphify-out/graph.json --
per staging_artifacts/TCK-20260729-DETERMINISTIC-CODE-INDEX/test_plan.md's Anti-Drift Test
Guards ("No test in this suite should assert on live graph.json's exact edge counts").
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import code_test_index as cti


def _admission_fixture_graph() -> dict:
    return {
        "nodes": [],
        "links": [
            {
                "relation": "imports",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source": "n1",
                "target": "n2",
                "source_file": "src/a/b.py",
                "source_location": "L1",
            },
            {
                "relation": "uses",
                "confidence": "INFERRED",
                "confidence_score": 0.5,
                "source": "n1",
                "target": "n3",
                "source_file": "src/a/b.py",
                "source_location": "L2",
            },
            {
                "relation": "calls",
                "confidence": "INFERRED",
                "confidence_score": 0.8,
                "source": "n1",
                "target": "n4",
                "source_file": "src/a/b.py",
                "source_location": "L3",
            },
            {
                "relation": "inherits",
                "confidence": "EXTRACTED",
                "confidence_score": 0.5,
                "source": "n5",
                "target": "n6",
                "source_file": "src/a/b.py",
                "source_location": "L4",
            },
            {
                "relation": "not_part_a",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source": "n7",
                "target": "n8",
                "source_file": "src/a/b.py",
                "source_location": "L5",
            },
        ],
    }


def _build_repo_with_real_symbol(tmp_path: Path) -> dict:
    src_dir = tmp_path / "src" / "sample_module"
    src_dir.mkdir(parents=True)
    (src_dir / "foo.py").write_text(
        '"""Module foo."""\n\n\ndef bar():\n    """Returns bar."""\n    return 1\n',
        encoding="utf-8",
    )
    tests_dir = tmp_path / "tests" / "unit" / "sample_module"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_foo.py").write_text(
        "def test_bar():\n    assert True\n", encoding="utf-8"
    )

    return {
        "nodes": [
            {
                "id": "sample_module_file",
                "label": "foo.py",
                "source_file": "src/sample_module/foo.py",
                "source_location": "L1",
                "community": 5,
            },
            {
                "id": "sample_bar",
                "label": "bar()",
                "source_file": "src/sample_module/foo.py",
                "source_location": "L4",
                "community": 5,
            },
            {
                "id": "orphan_symbol",
                "label": "orphan()",
                "source_file": "src/orphan/mod.py",
                "source_location": "L1",
                "community": 9,
            },
            {
                "id": "orphan_caller",
                "label": "caller()",
                "source_file": "src/orphan/mod.py",
                "source_location": "L5",
                "community": 9,
            },
        ],
        "links": [
            {
                "relation": "contains",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source": "sample_module_file",
                "target": "sample_bar",
                "source_file": "src/sample_module/foo.py",
                "source_location": "L4",
            },
            {
                "relation": "calls",
                "confidence": "EXTRACTED",
                "confidence_score": 1.0,
                "source": "orphan_caller",
                "target": "orphan_symbol",
                "source_file": "src/orphan/mod.py",
                "source_location": "L5",
            },
        ],
    }


def _chain_graph() -> dict:
    nodes = [
        {"id": "chain_a", "label": "a()", "source_file": "src/chain/a.py", "source_location": "L1", "community": 7},
        {"id": "chain_b", "label": "b()", "source_file": "src/chain/b.py", "source_location": "L1", "community": 7},
        {"id": "chain_c", "label": "c()", "source_file": "src/chain/c.py", "source_location": "L1", "community": 7},
        {"id": "chain_d", "label": "d()", "source_file": "src/chain/d.py", "source_location": "L1", "community": 7},
        {"id": "chain_e", "label": "e()", "source_file": "src/chain/e.py", "source_location": "L1", "community": 7},
    ]
    links = [
        {
            "relation": "contains", "confidence": "EXTRACTED", "confidence_score": 1.0,
            "source": "chain_a", "target": "chain_b",
            "source_file": "src/chain/a.py", "source_location": "L1",
        },
        {
            "relation": "calls", "confidence": "EXTRACTED", "confidence_score": 1.0,
            "source": "chain_b", "target": "chain_c",
            "source_file": "src/chain/b.py", "source_location": "L1",
        },
        {
            "relation": "calls", "confidence": "EXTRACTED", "confidence_score": 1.0,
            "source": "chain_c", "target": "chain_d",
            "source_file": "src/chain/c.py", "source_location": "L1",
        },
        {
            "relation": "calls", "confidence": "EXTRACTED", "confidence_score": 1.0,
            "source": "chain_d", "target": "chain_e",
            "source_file": "src/chain/d.py", "source_location": "L1",
        },
    ]
    return {"nodes": nodes, "links": links}


class TestAdmissionFilter:

    def test_admits_part_a_relation_with_confidence_score_1_0(self):
        admitted = list(cti.iter_admitted_edges(_admission_fixture_graph()))
        relations = {edge["relation"] for edge in admitted}
        assert relations == {"imports"}

    def test_rejects_inferred_edge_despite_allowlisted_relation_name(self):
        admitted = list(cti.iter_admitted_edges(_admission_fixture_graph()))
        assert all(edge["confidence_score"] == 1.0 for edge in admitted)
        assert not any(edge["relation"] == "uses" for edge in admitted)
        assert not any(edge["relation"] == "calls" for edge in admitted)

    def test_rejects_edge_where_confidence_label_and_confidence_score_disagree(self):
        graph_data = _admission_fixture_graph()
        mismatched = next(
            edge for edge in graph_data["links"] if edge["relation"] == "inherits"
        )
        assert mismatched["confidence"] == "EXTRACTED"
        assert mismatched["confidence_score"] != 1.0

        admitted = list(cti.iter_admitted_edges(graph_data))
        assert mismatched not in admitted
        assert not any(edge["relation"] == "inherits" for edge in admitted)

    def test_zero_occurrence_allowlist_relations_do_not_crash_builder(self, tmp_path):
        graph_data = {
            "nodes": [
                {
                    "id": "n1", "label": "mod.py",
                    "source_file": "src/x/mod.py", "source_location": "L1", "community": 1,
                },
                {
                    "id": "n2", "label": "func()",
                    "source_file": "src/x/mod.py", "source_location": "L2", "community": 1,
                },
            ],
            "links": [
                {
                    "relation": "contains", "confidence": "EXTRACTED", "confidence_score": 1.0,
                    "source": "n1", "target": "n2",
                    "source_file": "src/x/mod.py", "source_location": "L2",
                },
            ],
        }
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)
        assert len(records) == 2

        zero_occurrence = {
            "defines", "uses_static_prop", "references_constant", "bound_to",
            "listened_by", "includes", "uses_component", "binds_method",
        }
        relations_seen = {edge["relation"] for edge in admitted_edges}
        assert relations_seen.isdisjoint(zero_occurrence)


class TestRecordConstruction:

    def test_record_exposes_required_fields_or_explicit_gap_flag(self, tmp_path):
        graph_data = _build_repo_with_real_symbol(tmp_path)
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)

        for record in records:
            assert record["module"]
            assert record["symbol"]
            associated = record["associated_tests"]
            assert associated == cti.ASSOCIATED_TESTS_GAP or (
                isinstance(associated, list) and associated
            )

        bar_record = next(r for r in records if r["id"] == "sample_bar")
        assert bar_record["associated_tests"] == ["tests/unit/sample_module/test_foo.py"]

        orphan_record = next(r for r in records if r["id"] == "orphan_symbol")
        assert orphan_record["associated_tests"] == cti.ASSOCIATED_TESTS_GAP
        assert orphan_record["docstring"] == cti.DOCSTRING_GAP

    def test_docstring_and_owned_component_populated_from_real_mapping(self, tmp_path):
        graph_data = _build_repo_with_real_symbol(tmp_path)
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)

        bar_record = next(r for r in records if r["id"] == "sample_bar")
        assert bar_record["docstring"] == "Returns bar."
        assert bar_record["owned_component"] == 5
        assert bar_record["module"] == "src.sample_module.foo"


class TestByteIdenticalRebuild:

    def test_rebuild_is_byte_identical(self, tmp_path):
        graph_data = _build_repo_with_real_symbol(tmp_path)
        graph_path = tmp_path / "graph.json"
        graph_path.write_text(json.dumps(graph_data), encoding="utf-8")

        out1 = tmp_path / "out1.json"
        out2 = tmp_path / "out2.json"
        cti.build_index(graph_path, out1, tmp_path)
        cti.build_index(graph_path, out2, tmp_path)

        assert out1.read_bytes() == out2.read_bytes()
        assert out1.read_bytes()


class TestBoundedHopQuery:

    def test_query_by_changed_path_returns_bounded_hop_neighbors_only(self, tmp_path):
        graph_data = _chain_graph()
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)

        result = cti.query_by_path(records, admitted_edges, graph_data, "src/chain/a.py")
        ids = {record["id"] for record in result}
        assert ids == {"chain_a", "chain_b", "chain_c"}

        full_community_ids = {record["id"] for record in records if record["owned_component"] == 7}
        assert len(ids) < len(full_community_ids)

    def test_architectural_traversal_explicitly_requested_returns_full_community(self, tmp_path):
        graph_data = _chain_graph()
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)

        result = cti.query_by_path(
            records, admitted_edges, graph_data, "src/chain/a.py",
            architectural_traversal=True,
        )
        ids = {record["id"] for record in result}
        assert ids == {"chain_a", "chain_b", "chain_c", "chain_d", "chain_e"}

    def test_query_by_unknown_path_returns_empty(self, tmp_path):
        graph_data = _chain_graph()
        admitted_edges = list(cti.iter_admitted_edges(graph_data))
        records = cti.build_records(graph_data, admitted_edges, tmp_path)

        result = cti.query_by_path(records, admitted_edges, graph_data, "src/does/not/exist.py")
        assert result == []


class TestRequirementsPin:

    def test_requirements_knowledge_pins_graphifyy_version(self):
        content = (_REPO_ROOT / "requirements-knowledge.txt").read_text(encoding="utf-8")
        assert "graphifyy==0.8.39" in content
