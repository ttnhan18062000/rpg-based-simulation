"""Tests for tools/context_packet_assembler.py — real ContextPacket assembly from
HybridResult, code_test_index.py records, and parity_ledger_entry fixtures.

Built for TCK-20260729-CONTEXT-PACKET-ASSEMBLY. No live ML dependency, no live
docs/REGISTRY.yaml/knowledge.db/graph.json reads — small hand-built fixtures only, following
tests/tools/test_hybrid_retrieval.py/tests/tools/test_retrieval_cache.py's established
conventions.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import code_test_index as cti  # noqa: E402
from tools import context_packet_assembler as cpa  # noqa: E402
from tools import hybrid_retrieval as hr  # noqa: E402
from tools import retrieval_cache as rc  # noqa: E402
from tools import validate_frontmatter as vf  # noqa: E402

RAW_TEXT_MARKER = "zzqfrobnicate_context_packet_leakage_marker"


# ---------------------------------------------------------------------------
# Shared fixtures mixing REGISTRY-backed and non-registry-backed candidate shapes (Step 2)
# ---------------------------------------------------------------------------

def _registry_backed_hybrid_result(
    *,
    doc_id: str = "doc-p0",
    authority: str = "P0",
    freshness: str = "active",
    rrf_score: float = 0.5,
    path: str = "docs/example_p0.md",
    text: str | None = None,
) -> hr.HybridResult:
    return hr.HybridResult(
        doc_id=doc_id,
        path=path,
        heading="Example Heading",
        section="",
        text=text if text is not None else f"{RAW_TEXT_MARKER} excerpt body for {doc_id}",
        rrf_score=rrf_score,
        dense_rank=1,
        lexical_rank=None,
        semantic_score=0.9,
        keyword_score=None,
        authority=authority,
        freshness=freshness,
        kind="doc",
    )


def _registry_index_fixture() -> dict[str, dict]:
    return {
        "docs/example_p0.md": {
            "authority": "P0",
            "status": "active",
            "last_verified": "2026-07-01",
        },
        "docs/example_p1.md": {
            "authority": "P1",
            "status": "active",
            "last_verified": "2026-06-01",
        },
    }


def _code_index_record_fixture(
    *, record_id: str = "node-1", module: str = "src.ai.example", symbol: str = "ExampleClass"
) -> dict:
    return {
        "id": record_id,
        "module": module,
        "symbol": symbol,
        "docstring": cti.DOCSTRING_GAP,
        "owned_component": 3,
        "associated_tests": cti.ASSOCIATED_TESTS_GAP,
    }


def _parity_ledger_fixture() -> dict:
    return {
        "id": "INFRA-999",
        "text": "fixture parity ledger entry, never a real producer output",
        "status": "legacy_verified",
        "priority": "P1",
    }


class TestFixtures:
    def test_fixture_mixes_registry_backed_and_non_registry_backed_kinds(self):
        registry_index = _registry_index_fixture()
        hr_candidate = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(), registry_index
        )
        code_candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())

        assert hr_candidate.authority in vf.AUTHORITY_VALUES
        assert hr_candidate.freshness in vf.STATUS_VALUES
        assert code_candidate.authority == hr.UNRATED
        assert code_candidate.freshness == hr.UNRATED


# ---------------------------------------------------------------------------
# AC1 — code_symbol candidate with no REGISTRY entry gets the unrated sentinel
# ---------------------------------------------------------------------------

class TestUnratedFallback:
    def test_code_symbol_candidate_with_no_registry_entry_gets_unrated_sentinel(self):
        candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[candidate],
        )
        entry = packet.included[0]
        assert entry["kind"] == "code_symbol"
        assert entry["authority"] == "unrated"
        assert entry["freshness"] == "unrated"
        assert entry["authority"] == hr.UNRATED


# ---------------------------------------------------------------------------
# AC2 — Decision B conflict resolution and tie-break
# ---------------------------------------------------------------------------

class TestConflictResolution:
    def _two_active_candidates(self):
        registry_index = _registry_index_fixture()
        p0 = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-p0", authority="P0", freshness="active", path="docs/example_p0.md"
            ),
            registry_index,
            subject_key="subject-x",
        )
        p1 = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-p1", authority="P1", freshness="active", path="docs/example_p1.md"
            ),
            registry_index,
            subject_key="subject-x",
        )
        return p0, p1

    def test_two_active_docs_same_subject_both_included(self):
        p0, p1 = self._two_active_candidates()
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[p0, p1],
        )
        source_ids = {entry["source_id"] for entry in packet.included}
        assert source_ids == {"doc-p0", "doc-p1"}

    def test_lower_ranked_entry_inclusion_reason_names_superseding_source_id(self):
        p0, p1 = self._two_active_candidates()
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[p0, p1],
        )
        p0_entry = next(e for e in packet.included if e["source_id"] == "doc-p0")
        p1_entry = next(e for e in packet.included if e["source_id"] == "doc-p1")
        assert p0_entry["inclusion_reason"] == "included"
        assert p1_entry["inclusion_reason"] == "superseded-by:doc-p0"

    def test_tiebreak_falls_back_to_last_verified_when_authority_equal(self):
        registry_index = {
            "docs/older.md": {
                "authority": "P1",
                "status": "active",
                "last_verified": "2026-01-01",
            },
            "docs/newer.md": {
                "authority": "P1",
                "status": "active",
                "last_verified": "2026-06-01",
            },
        }
        older = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-older", authority="P1", freshness="active", path="docs/older.md"
            ),
            registry_index,
            subject_key="subject-y",
        )
        newer = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-newer", authority="P1", freshness="active", path="docs/newer.md"
            ),
            registry_index,
            subject_key="subject-y",
        )
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[older, newer],
        )
        older_entry = next(e for e in packet.included if e["source_id"] == "doc-older")
        newer_entry = next(e for e in packet.included if e["source_id"] == "doc-newer")
        assert newer_entry["inclusion_reason"] == "included"
        assert older_entry["inclusion_reason"] == "superseded-by:doc-newer"

    def test_missing_last_verified_sorts_last_within_authority_tie(self):
        registry_index = {
            "docs/has-date.md": {
                "authority": "P1",
                "status": "active",
                "last_verified": "2026-01-01",
            },
            "docs/no-date.md": {"authority": "P1", "status": "active"},
        }
        has_date = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-has-date",
                authority="P1",
                freshness="active",
                path="docs/has-date.md",
            ),
            registry_index,
            subject_key="subject-z",
        )
        no_date = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-no-date", authority="P1", freshness="active", path="docs/no-date.md"
            ),
            registry_index,
            subject_key="subject-z",
        )
        assert no_date.last_verified is None
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[has_date, no_date],
        )
        has_date_entry = next(e for e in packet.included if e["source_id"] == "doc-has-date")
        no_date_entry = next(e for e in packet.included if e["source_id"] == "doc-no-date")
        assert has_date_entry["inclusion_reason"] == "included"
        assert no_date_entry["inclusion_reason"] == "superseded-by:doc-has-date"


# ---------------------------------------------------------------------------
# AC3 — exact contract field shape
# ---------------------------------------------------------------------------

class TestContractFieldShape:
    def test_included_entry_has_exactly_ten_contract_fields(self):
        candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[candidate],
        )
        assert set(packet.included[0].keys()) == {
            "source_id",
            "kind",
            "path",
            "heading_or_symbol",
            "hash",
            "authority",
            "freshness",
            "score",
            "inclusion_reason",
            "excerpt_budget",
        }

    def test_excluded_summary_entry_has_exactly_four_contract_fields(self):
        included_candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())
        excluded_candidate = cpa.candidate_from_code_index_record(
            _code_index_record_fixture(record_id="node-2")
        )
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[included_candidate],
            excluded=[(excluded_candidate, "below_budget_threshold")],
        )
        assert len(packet.excluded_summary) == 1
        assert set(packet.excluded_summary[0].keys()) == {
            "source_id",
            "kind",
            "reason",
            "count",
        }
        assert packet.excluded_summary[0]["count"] == 1

    def test_expansion_policy_is_a_marked_placeholder_not_real_escalation_logic(self):
        candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[candidate],
        )
        assert isinstance(packet.expansion_policy, str)
        assert "not_yet_resolved" in packet.expansion_policy
        for forbidden_field in ("max_expansions", "trigger", "threshold"):
            assert forbidden_field not in packet.expansion_policy


# ---------------------------------------------------------------------------
# AC4 — raw-text leakage and hash-integrity guards
# ---------------------------------------------------------------------------

class TestNoRawTextLeakage:
    def test_assembled_packet_never_contains_raw_fixture_text_anywhere(self):
        registry_index = _registry_index_fixture()
        hybrid_candidate = cpa.candidate_from_hybrid_result(
            _registry_backed_hybrid_result(
                doc_id="doc-p0", authority="P0", freshness="active", path="docs/example_p0.md"
            ),
            registry_index,
        )
        code_candidate = cpa.candidate_from_code_index_record(_code_index_record_fixture())
        packet = cpa.assemble_context_packet(
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[hybrid_candidate, code_candidate],
        )
        serialized = json.dumps(dataclasses.asdict(packet))
        assert RAW_TEXT_MARKER not in serialized

    def test_hash_field_is_sha256_of_excerpt_not_the_excerpt_itself(self):
        text = f"{RAW_TEXT_MARKER} excerpt body for doc-p0"
        registry_index = _registry_index_fixture()
        result = _registry_backed_hybrid_result(
            doc_id="doc-p0",
            authority="P0",
            freshness="active",
            path="docs/example_p0.md",
            text=text,
        )
        candidate = cpa.candidate_from_hybrid_result(result, registry_index)
        expected_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        assert candidate.hash == expected_hash
        assert candidate.hash != text
        assert text not in candidate.hash
        assert RAW_TEXT_MARKER not in candidate.hash


# ---------------------------------------------------------------------------
# parity_ledger_entry adapter — Decision A's parity branch (Scope item 2)
# ---------------------------------------------------------------------------

class TestParityLedgerEntryAdapter:
    def test_parity_ledger_entry_kind_uses_own_priority_and_status_not_registry_enum(self):
        entry = _parity_ledger_fixture()
        candidate = cpa.candidate_from_parity_ledger_fixture(entry)

        assert candidate.kind == "parity_ledger_entry"
        assert candidate.authority == entry["priority"]
        assert candidate.freshness == entry["status"]
        # "legacy_verified" is a value from the parity ledger's own 5-value status enum,
        # exclusive to it — never a member of REGISTRY's 4-value STATUS_VALUES.
        assert candidate.freshness not in vf.STATUS_VALUES

    def test_parity_ledger_entry_authority_not_coerced_into_registry_authority_values(self):
        entry = _parity_ledger_fixture()
        candidate = cpa.candidate_from_parity_ledger_fixture(entry)

        # Identity passthrough only -- no mapping/clamping table sits between the parity
        # entry's own `priority` field and the packet's `authority` field.
        assert candidate.authority == entry["priority"]


# ---------------------------------------------------------------------------
# AC5 — workflow-isolation guards and reverse-dependency guard
# ---------------------------------------------------------------------------

class TestWorkflowIsolationGuards:
    def test_module_not_referenced_by_any_claude_workflows_file(self):
        workflows_dir = _REPO_ROOT / ".claude" / "workflows"
        js_files = list(workflows_dir.glob("*.js"))
        assert js_files, "expected at least one .claude/workflows/*.js file to scan"
        for path in js_files:
            content = path.read_text(encoding="utf-8")
            assert "context_packet_assembler" not in content, (
                f"{path} references context_packet_assembler"
            )

    def test_module_does_not_import_any_claude_workflows_file(self):
        source = Path(cpa.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "workflows" not in alias.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert "workflows" not in node.module

    def test_assembler_does_not_import_contextpacket_from_retrieval_cache(self):
        source = Path(rc.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)

        class_names = {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}
        assert "ContextPacket" not in class_names

        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names.update(alias.name.rsplit(".", 1)[-1] for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported_names.update(alias.name for alias in node.names)
        assert "ContextPacket" not in imported_names
