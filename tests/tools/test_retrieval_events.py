"""Tests for tools/retrieval_events.py — the new additive retrieval-event schema, its
emit_retrieval_event() writer-path integration, and the 3 wrap_*() instrumentation wrappers
around tools/hybrid_retrieval.py, tools/retrieval_cache.py, tools/context_packet_assembler.py.

Built for TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT. Every test that exercises
emit_retrieval_event() or any wrap_*() function passes an explicit tmp_path-scoped events_file —
never the real agent-monitoring/events.jsonl (test_plan.md's "No-real-run_id-pollution guard").
"""
from __future__ import annotations

import inspect
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

from tools import retrieval_events as re_mod  # noqa: E402

# Bare (not package-qualified) imports below, deliberately -- tools/retrieval_events.py's own
# wrap_*() functions import these 3 sibling modules by bare name (`from hybrid_retrieval import
# ...`, etc, relying on its own sys.path insert of tools/), which registers them in
# sys.modules under the bare name. A `from tools import hybrid_retrieval as hr`-style
# package-qualified import here would create a SECOND, distinct module object under
# `sys.modules["tools.hybrid_retrieval"]` -- monkeypatching that object (e.g.
# `hr._dense_candidates`) would silently not affect the bare-imported module the wrapper
# actually calls. Matching the wrapper's own bare-import style keeps both references to the same
# module object.
import hybrid_retrieval as hr  # noqa: E402
import retrieval_cache as rc  # noqa: E402
import context_packet_assembler as cpa  # noqa: E402
import record_events  # noqa: E402


# ---------------------------------------------------------------------------
# Step 1 — RETRIEVAL_EVENT_FIELDS field-shape constant
# ---------------------------------------------------------------------------

class TestFieldShapeConstant:
    def test_field_set_contains_exactly_expected_retrieval_fields(self):
        assert re_mod.RETRIEVAL_EVENT_FIELDS == frozenset(
            {
                "retrieval_version",
                "corpus_generation",
                "cache_level",
                "cache_status",
                "latency_ms",
                "candidate_count",
                "selected_count",
                "source_kind_counts",
                "authority_counts",
                "freshness_counts",
                "exclusion_reason_counts",
                "cited_source_hashes",
                "adequacy_verdict",
                "expansion_reason",
                "expansion_count",
                "scenario",
                "risk_tier",
                "retrieval_event_schema_version",
            }
        )

    def test_field_set_excludes_execution_id_provider_and_required_base_fields(self):
        assert "execution_id" not in re_mod.RETRIEVAL_EVENT_FIELDS
        assert "provider" not in re_mod.RETRIEVAL_EVENT_FIELDS
        assert not (re_mod.RETRIEVAL_EVENT_FIELDS & record_events.REQUIRED)

    def test_schema_version_constant_distinct_from_cache_key_version_constant(self):
        assert re_mod.retrieval_event_schema_version == 1
        assert rc.RETRIEVAL_VERSION == 1
        # Same value today is a coincidence, not a shared identity -- confirmed by them being
        # two entirely separate module-level names, never imported/aliased from one another.
        assert "retrieval_event_schema_version" not in dir(rc)
        assert "RETRIEVAL_VERSION" not in dir(re_mod)


class TestComputeAdequacyVerdict:
    def test_zero_selected_is_insufficient(self):
        assert re_mod.compute_adequacy_verdict(0, 0) == "insufficient"
        assert re_mod.compute_adequacy_verdict(0, 40) == "insufficient"

    def test_high_candidate_to_selected_ratio_is_noisy(self):
        assert re_mod.compute_adequacy_verdict(2, 10) == "noisy"  # 10 >= 5*2

    def test_reasonable_ratio_is_sufficient(self):
        assert re_mod.compute_adequacy_verdict(3, 10) == "sufficient"  # 10 < 5*3
        assert re_mod.compute_adequacy_verdict(5, 5) == "sufficient"


# ---------------------------------------------------------------------------
# Step 2 — emit_retrieval_event(): AC1/AC2
# ---------------------------------------------------------------------------

_ALL_RETRIEVAL_FIELDS_SAMPLE = {
    "retrieval_version": 1,
    "corpus_generation": "gen-1",
    "cache_level": rc.QUERY_CACHE_CATEGORY,
    "cache_status": rc.HIT,
    "latency_ms": 12.5,
    "candidate_count": 20,
    "selected_count": 4,
    "source_kind_counts": {"doc": 3, "ticket": 1},
    "authority_counts": {"P0": 2, "P1": 2},
    "freshness_counts": {"active": 4},
    "exclusion_reason_counts": {"doc:below_budget_threshold": 2},
    "cited_source_hashes": ["a" * 64, "b" * 64],
    "adequacy_verdict": "sufficient",
    "expansion_reason": "budget_exceeded",
    "expansion_count": 1,
    "scenario": "demo-scenario",
    "risk_tier": "low",
}


class TestEmitRetrievalEvent:
    def test_record_contains_all_base_and_retrieval_fields_and_round_trips(self, tmp_path):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        ok = re_mod.emit_retrieval_event(
            run_id="RETRIEVAL-EVENT-test",
            seq=1,
            phase="Retrieval",
            agent="hybrid-retrieval-wrapper",
            summary="AC1 round-trip test",
            status="ok",
            events_file=events_file,
            **_ALL_RETRIEVAL_FIELDS_SAMPLE,
        )
        assert ok is True

        lines = events_file.read_text().splitlines()
        assert len(lines) == 1
        written = json.loads(lines[0])

        for base_field, expected in {
            "run_id": "RETRIEVAL-EVENT-test",
            "seq": 1,
            "phase": "Retrieval",
            "agent": "hybrid-retrieval-wrapper",
            "summary": "AC1 round-trip test",
            "status": "ok",
        }.items():
            assert written[base_field] == expected
        assert "ts" in written and written["ts"]
        assert written["retrieval_event_schema_version"] == 1
        for field, expected in _ALL_RETRIEVAL_FIELDS_SAMPLE.items():
            assert written[field] == expected

    def test_missing_base_field_still_rejected_with_new_fields_present(self, tmp_path):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        with pytest.raises(ValueError) as exc_info:
            re_mod.emit_retrieval_event(
                run_id="RETRIEVAL-EVENT-test",
                seq=1,
                phase=None,
                agent="hybrid-retrieval-wrapper",
                summary="AC2 test",
                status="ok",
                events_file=events_file,
                **_ALL_RETRIEVAL_FIELDS_SAMPLE,
            )
        assert "phase" in str(exc_info.value)
        assert not events_file.exists()

    def test_unknown_retrieval_field_rejected_loudly(self, tmp_path):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        with pytest.raises(ValueError):
            re_mod.emit_retrieval_event(
                run_id="RETRIEVAL-EVENT-test",
                seq=1,
                phase="Retrieval",
                agent="hybrid-retrieval-wrapper",
                summary="unknown field test",
                status="ok",
                events_file=events_file,
                raw_prompt="this must never be accepted",
            )
        assert not events_file.exists()

    def test_record_events_required_set_immutability_guard(self):
        assert record_events.REQUIRED == {
            "run_id", "seq", "ts", "phase", "agent", "summary", "status",
        }

    def test_new_run_id_prefix_produces_no_vocabulary_warning(self, tmp_path, capsys):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        re_mod.emit_retrieval_event(
            run_id=re_mod.RUN_ID_HYBRID,
            seq=1,
            phase="Retrieval",
            agent=re_mod.AGENT_HYBRID,
            summary="vocab silence check",
            status="ok",
            events_file=events_file,
        )
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_default_events_file_is_record_events_events_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        re_mod.emit_retrieval_event(
            run_id="RETRIEVAL-EVENT-test",
            seq=1,
            phase="Retrieval",
            agent="hybrid-retrieval-wrapper",
            summary="default events_file test",
            status="ok",
        )
        written = (tmp_path / "agent-monitoring" / "events.jsonl").read_text()
        assert "default events_file test" in written

    def test_ts_override_is_used_verbatim(self, tmp_path):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        re_mod.emit_retrieval_event(
            run_id="RETRIEVAL-EVENT-test",
            seq=1,
            phase="Retrieval",
            agent="hybrid-retrieval-wrapper",
            summary="ts override test",
            status="ok",
            events_file=events_file,
            ts="2026-08-03T02:26:02Z",
        )
        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["ts"] == "2026-08-03T02:26:02Z"

    def test_ts_default_none_produces_fresh_utc_now_timestamp(self, tmp_path):
        events_file = tmp_path / "agent-monitoring" / "events.jsonl"
        before = datetime.now(timezone.utc)
        re_mod.emit_retrieval_event(
            run_id="RETRIEVAL-EVENT-test",
            seq=1,
            phase="Retrieval",
            agent="hybrid-retrieval-wrapper",
            summary="ts default test",
            status="ok",
            events_file=events_file,
        )
        after = datetime.now(timezone.utc)

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["ts"].endswith("Z")
        written_dt = datetime.fromisoformat(written["ts"].replace("Z", "+00:00"))
        assert before <= written_dt <= after


# ---------------------------------------------------------------------------
# Step 3 — AC3 structural schema guard
# ---------------------------------------------------------------------------

class TestSchemaExcludesRawTextAndIdentityFields:
    def test_no_execution_id_provider_or_raw_text_field(self):
        fields = re_mod.RETRIEVAL_EVENT_FIELDS
        assert "execution_id" not in fields
        assert "provider" not in fields
        prohibited_names = {"raw_prompt", "raw_text", "chunk_text", "retrieved_content", "payload"}
        assert not (fields & prohibited_names)

    def test_cited_source_hashes_is_the_only_content_adjacent_field_and_is_hash_shaped(self):
        content_adjacent = {
            f for f in re_mod.RETRIEVAL_EVENT_FIELDS
            if "text" in f or "content" in f or "hash" in f
        }
        assert content_adjacent == {"cited_source_hashes"}

        # Cross-reference: docs/observability/retrieval_retention_redaction_policy.md's MAY-list
        # is hash/ID/count/reason-code/score/latency/version/status categories, prose not
        # machine-readable -- this asserts the sample value's *shape* matches its "content hashes"
        # category (sha256-hex, matching context_packet_assembler.py's own hash convention), never
        # full text.
        sample_hashes = ["a" * 64, "0123456789abcdef" * 4]
        assert all(
            len(h) == 64 and all(c in "0123456789abcdef" for c in h) for h in sample_hashes
        )


# ---------------------------------------------------------------------------
# Step 5 — wrap_hybrid_retrieval(): AC4
# ---------------------------------------------------------------------------

def _make_docs_db(tmp_path: Path, rows: list[tuple]) -> sqlite3.Connection:
    db_path = tmp_path / "knowledge.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE knowledge_docs (
            rowid       INTEGER PRIMARY KEY,
            doc_id      TEXT NOT NULL,
            path        TEXT NOT NULL,
            text        TEXT NOT NULL,
            source_type TEXT NOT NULL,
            heading     TEXT NOT NULL DEFAULT '',
            section     TEXT NOT NULL DEFAULT ''
        )
        """
    )
    for rowid, doc_id, path, heading, section, text, source_type in rows:
        conn.execute(
            "INSERT INTO knowledge_docs (rowid, doc_id, path, text, source_type, heading, section) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (rowid, doc_id, path, text, source_type, heading, section),
        )
    conn.commit()
    return conn


class TestWrapHybridRetrieval:
    def test_wrapper_emits_exactly_one_retrieval_event(self, tmp_path, monkeypatch):
        conn = _make_docs_db(
            tmp_path,
            [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk"),
                (1, "doc-b", "docs/b.md", "B", "docs", "beta text", "doc_chunk"),
            ],
        )
        # Patch via sys.modules["hybrid_retrieval"], not the `hr` reference captured at this
        # file's collection time: tests/tools/test_hybrid_retrieval.py registers its own fresh
        # module object under that same sys.modules key during ITS collection (see its own
        # spec_from_file_location loader), which can happen after this file is collected —
        # leaving `hr` stale relative to what wrap_hybrid_retrieval()'s deferred `from
        # hybrid_retrieval import ...` resolves at call time. Re-fetching from sys.modules here
        # (at test-execution time, after all collection has finished) always matches.
        monkeypatch.setattr(
            sys.modules["hybrid_retrieval"], "_dense_candidates",
            lambda conn, query_vec_bytes, dense_candidate_k: [
                (0, "doc-a", "docs/a.md", "A", "docs", "alpha text", "doc_chunk", 0.1),
                (1, "doc-b", "docs/b.md", "B", "docs", "beta text", "doc_chunk", 0.2),
            ],
        )

        events_file = tmp_path / "events.jsonl"
        results = re_mod.wrap_hybrid_retrieval(
            seq=1,
            summary="hybrid wrapper AC4 test",
            events_file=events_file,
            conn=conn,
            query_vec_bytes=b"",
            query_tokens=[],
            bm25_obj=None,
            bm25_doc_ids=[],
            top_k=5,
        )
        conn.close()

        assert {r.doc_id for r in results} == {"doc-a", "doc-b"}

        lines = events_file.read_text().splitlines()
        assert len(lines) == 1
        written = json.loads(lines[0])
        assert written["phase"] == "Retrieval"
        assert written["agent"] == re_mod.AGENT_HYBRID
        assert written["run_id"].startswith("RETRIEVAL-EVENT-")
        assert written["selected_count"] == 2
        assert written["source_kind_counts"] == {"doc": 2}
        assert set(written["authority_counts"]) <= {hr.UNRATED}
        assert set(written["freshness_counts"]) <= {hr.UNRATED}
        assert written["latency_ms"] >= 0


# ---------------------------------------------------------------------------
# Step 6 — wrap_retrieval_cache_check(): AC5, parametrized over 3 levels x 3 outcomes
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _isolated_cache_db(tmp_path, monkeypatch):
    monkeypatch.setattr(rc, "CACHE_DB_PATH", tmp_path / "retrieval_cache.db")
    monkeypatch.setattr(rc, "_MANIFEST_PATH", tmp_path / "manifest.json")
    yield


class TestWrapRetrievalCacheCheck:
    def test_index_cache_hit_emits_correct_cache_status_and_level(self, tmp_path):
        rc.write_index_cache("hash-a", "emb-v1", "chunk-v1", source_id="doc-1")
        events_file = tmp_path / "events.jsonl"

        result = re_mod.wrap_retrieval_cache_check(
            rc.INDEX_CACHE_CATEGORY,
            seq=1,
            summary="index cache hit",
            events_file=events_file,
            content_hash="hash-a",
            embedding_version="emb-v1",
            chunking_version="chunk-v1",
        )
        assert result.status == rc.HIT

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["cache_level"] == rc.INDEX_CACHE_CATEGORY
        assert written["cache_status"] == rc.HIT

    def test_index_cache_miss_emits_correct_cache_status_and_level(self, tmp_path):
        events_file = tmp_path / "events.jsonl"

        result = re_mod.wrap_retrieval_cache_check(
            rc.INDEX_CACHE_CATEGORY,
            seq=1,
            summary="index cache miss",
            events_file=events_file,
            content_hash="hash-never-seen",
            embedding_version="emb-v1",
            chunking_version="chunk-v1",
        )
        assert result.status == rc.MISS

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["cache_level"] == rc.INDEX_CACHE_CATEGORY
        assert written["cache_status"] == rc.MISS

    def test_query_cache_stale_rejected_emits_correct_cache_status_and_level(self, tmp_path):
        rc.write_query_cache("player fatigue", {"top_k": 5}, "gen-1", 1, score=0.9)
        events_file = tmp_path / "events.jsonl"

        result = re_mod.wrap_retrieval_cache_check(
            rc.QUERY_CACHE_CATEGORY,
            seq=1,
            summary="query cache stale",
            events_file=events_file,
            query="player fatigue",
            filters={"top_k": 5},
            corpus_generation="gen-2",
            retrieval_version=1,
        )
        assert result.status == rc.STALE_REJECTED

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["cache_level"] == rc.QUERY_CACHE_CATEGORY
        assert written["cache_status"] == rc.STALE_REJECTED
        assert written["corpus_generation"] == "gen-2"
        assert written["retrieval_version"] == 1

    def test_packet_cache_hit_emits_correct_cache_status_and_level(self, tmp_path):
        rc.write_packet_cache("packet-1", ["h1", "h2"], "gen-1", "policy-1")
        events_file = tmp_path / "events.jsonl"

        result = re_mod.wrap_retrieval_cache_check(
            rc.PACKET_CACHE_CATEGORY,
            seq=1,
            summary="packet cache hit",
            events_file=events_file,
            packet_key_hash="packet-1",
            current_cited_hashes=["h1", "h2"],
            corpus_generation="gen-1",
            policy_version="policy-1",
        )
        assert result.status == rc.HIT

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["cache_level"] == rc.PACKET_CACHE_CATEGORY
        assert written["cache_status"] == rc.HIT

    def test_cache_status_values_are_the_imported_constants_not_re_literaled(self, tmp_path):
        events_file = tmp_path / "events.jsonl"
        re_mod.wrap_retrieval_cache_check(
            rc.INDEX_CACHE_CATEGORY,
            seq=1,
            summary="literal-reuse guard",
            events_file=events_file,
            content_hash="hash-x",
            embedding_version="emb-v1",
            chunking_version="chunk-v1",
        )
        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["cache_status"] in (rc.HIT, rc.MISS, rc.STALE_REJECTED)
        assert written["cache_status"] == rc.MISS


# ---------------------------------------------------------------------------
# Step 7 — wrap_context_packet_assembly()
# ---------------------------------------------------------------------------

class TestWrapContextPacketAssembly:
    def test_reason_code_and_hash_counts_match_wrapped_call_output(self, tmp_path):
        included_candidate = cpa.candidate_from_code_index_record(
            {
                "id": "node-1",
                "module": "src.ai.example",
                "symbol": "ExampleClass",
                "docstring": "d",
                "owned_component": 1,
                "associated_tests": "t",
            }
        )
        excluded_candidate = cpa.candidate_from_code_index_record(
            {
                "id": "node-2",
                "module": "src.ai.example",
                "symbol": "OtherClass",
                "docstring": "d",
                "owned_component": 1,
                "associated_tests": "t",
            }
        )

        events_file = tmp_path / "events.jsonl"
        packet = re_mod.wrap_context_packet_assembly(
            seq=1,
            summary="packet wrapper test",
            events_file=events_file,
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[included_candidate],
            excluded=[(excluded_candidate, "below_budget_threshold")],
        )

        expected_hashes = sorted(c["hash"] for c in packet.included)
        expected_reasons = {
            f'{row["kind"]}:{row["reason"]}': row["count"] for row in packet.excluded_summary
        }

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["phase"] == "Retrieval"
        assert written["agent"] == re_mod.AGENT_PACKET
        assert sorted(written["cited_source_hashes"]) == expected_hashes
        assert written["exclusion_reason_counts"] == expected_reasons
        assert written["selected_count"] == len(packet.included)
        assert written["corpus_generation"] == "gen-1"
        assert written["retrieval_version"] == 1

    def test_ts_override_is_forwarded_verbatim_to_emit_retrieval_event(self, tmp_path):
        included_candidate = cpa.candidate_from_code_index_record(
            {
                "id": "node-1",
                "module": "src.ai.example",
                "symbol": "ExampleClass",
                "docstring": "d",
                "owned_component": 1,
                "associated_tests": "t",
            }
        )

        events_file = tmp_path / "events.jsonl"
        re_mod.wrap_context_packet_assembly(
            seq=1,
            summary="ts override forwarding test",
            events_file=events_file,
            ts="2026-08-03T02:26:02Z",
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[included_candidate],
            excluded=[],
        )

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["ts"] == "2026-08-03T02:26:02Z"

    def test_ts_default_none_produces_fresh_utc_now_timestamp(self, tmp_path):
        included_candidate = cpa.candidate_from_code_index_record(
            {
                "id": "node-1",
                "module": "src.ai.example",
                "symbol": "ExampleClass",
                "docstring": "d",
                "owned_component": 1,
                "associated_tests": "t",
            }
        )

        events_file = tmp_path / "events.jsonl"
        before = datetime.now(timezone.utc)
        re_mod.wrap_context_packet_assembly(
            seq=1,
            summary="ts default forwarding test",
            events_file=events_file,
            packet_id="packet-1",
            corpus_generation="gen-1",
            retrieval_version=1,
            budget_requested=1000,
            included_candidates=[included_candidate],
            excluded=[],
        )
        after = datetime.now(timezone.utc)

        written = json.loads(events_file.read_text().splitlines()[0])
        assert written["ts"].endswith("Z")
        written_dt = datetime.fromisoformat(written["ts"].replace("Z", "+00:00"))
        assert before <= written_dt <= after


# ---------------------------------------------------------------------------
# AC3 -- ts signature/forwarding assertions for wrap_hybrid_retrieval() and
# wrap_retrieval_cache_check(), the two wrappers not covered by a full
# override/default invocation test per the ticket's Scope (full invocation coverage lives on
# emit_retrieval_event() and wrap_context_packet_assembly() above).
# ---------------------------------------------------------------------------

class TestTsKeywordSignatureAndForwarding:
    def test_wrap_hybrid_retrieval_accepts_optional_keyword_only_ts(self):
        sig = inspect.signature(re_mod.wrap_hybrid_retrieval)
        assert sig.parameters["ts"].kind == inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters["ts"].default is None

    def test_wrap_retrieval_cache_check_accepts_optional_keyword_only_ts(self):
        sig = inspect.signature(re_mod.wrap_retrieval_cache_check)
        assert sig.parameters["ts"].kind == inspect.Parameter.KEYWORD_ONLY
        assert sig.parameters["ts"].default is None

    def test_wrap_hybrid_retrieval_forwards_ts_to_emit_retrieval_event(self):
        source = inspect.getsource(re_mod.wrap_hybrid_retrieval)
        assert "ts=ts" in source

    def test_wrap_retrieval_cache_check_forwards_ts_to_emit_retrieval_event(self):
        source = inspect.getsource(re_mod.wrap_retrieval_cache_check)
        assert "ts=ts" in source
