"""Tests for tools/eval_search.py — mocks subprocess to avoid a live index."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_QUERIES_PATH = _REPO_ROOT / "tools" / "eval" / "queries.json"

# Load eval_search via importlib so we can run without installing the package.
import importlib.util

_ES_PATH = _REPO_ROOT / "tools" / "eval_search.py"
spec = importlib.util.spec_from_file_location("eval_search", _ES_PATH)
_mod = importlib.util.module_from_spec(spec)
sys.modules["eval_search"] = _mod
spec.loader.exec_module(_mod)

# Stale doc_ids confirmed (TCK-20260728-EVAL-FIXTURE-REPAIR investigation) to no longer
# resolve against the live index's actual (buggy but unchanged-here) doc_id scheme.
_KNOWN_STALE_DOC_IDS = {
    "engine/contracts/replay_contract",
    "engine/contracts/scheduler_contract",
    "engine/contracts/observability_contract",
    "engine/contracts/infrastructure_overview",
    "architecture/adr-004-simulation-watchdog",
    "architecture/adr-005-performance-optimization",
    "engine/contracts/progression_package",
}

_VALID_SOURCE_LIFECYCLE_ASSUMPTIONS = {"current", "superseded", "archived", "volatile"}

_CATEGORY_MINIMUMS = {
    "semantic": 15,
    "exact-term": 15,
    "cross-section": 5,
    "edge-case": 5,
    "doc/exact-id": 3,
    "policy-vs-superseded": 3,
    "ticket-history": 3,
    "symbol-to-test": 3,
    "changed-path": 3,
    "provider/workflow/monitoring": 3,
    "no-result": 3,
}


# ── queries.json schema ───────────────────────────────────────────────────────

class TestQueriesJson:
    def test_file_exists(self):
        assert _QUERIES_PATH.exists(), f"queries.json missing at {_QUERIES_PATH}"

    def test_has_40_entries(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        assert len(data) >= 40, f"Expected ≥40 queries, got {len(data)}"

    def test_required_keys(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        for i, entry in enumerate(data):
            assert "query" in entry, f"Entry {i} missing 'query'"
            assert "expected_doc_ids" in entry, f"Entry {i} missing 'expected_doc_ids'"
            assert "notes" in entry, f"Entry {i} missing 'notes'"
            assert isinstance(entry["expected_doc_ids"], list), f"Entry {i}: expected_doc_ids must be list"
            assert isinstance(entry["query"], str), f"Entry {i}: query must be str"
            assert "allowable_alternatives" in entry, f"Entry {i} missing 'allowable_alternatives'"
            assert isinstance(entry["allowable_alternatives"], list), f"Entry {i}: allowable_alternatives must be list"
            assert all(isinstance(x, str) for x in entry["allowable_alternatives"]), \
                f"Entry {i}: allowable_alternatives elements must be str"
            assert "source_lifecycle_assumption" in entry, f"Entry {i} missing 'source_lifecycle_assumption'"
            assert isinstance(entry["source_lifecycle_assumption"], str) and entry["source_lifecycle_assumption"], \
                f"Entry {i}: source_lifecycle_assumption must be a non-empty str"
            assert entry["source_lifecycle_assumption"] in _VALID_SOURCE_LIFECYCLE_ASSUMPTIONS, \
                f"Entry {i}: source_lifecycle_assumption {entry['source_lifecycle_assumption']!r} not in {_VALID_SOURCE_LIFECYCLE_ASSUMPTIONS}"
            assert "context_budget" in entry, f"Entry {i} missing 'context_budget'"
            assert isinstance(entry["context_budget"], int) and entry["context_budget"] > 0, \
                f"Entry {i}: context_budget must be a positive int"

    def test_new_fields_present_all_entries(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        for i, entry in enumerate(data):
            assert isinstance(entry.get("allowable_alternatives"), list), \
                f"Entry {i}: allowable_alternatives missing or wrong type"
            assert entry.get("source_lifecycle_assumption") in _VALID_SOURCE_LIFECYCLE_ASSUMPTIONS, \
                f"Entry {i}: source_lifecycle_assumption missing or invalid"
            assert isinstance(entry.get("context_budget"), int) and entry["context_budget"] > 0, \
                f"Entry {i}: context_budget missing or not a positive int"

    def test_no_stale_expected_doc_ids(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        all_ids = set()
        for entry in data:
            all_ids.update(entry.get("expected_doc_ids", []))
        stale_present = all_ids & _KNOWN_STALE_DOC_IDS
        assert not stale_present, f"Stale doc_ids still present in queries.json: {stale_present}"

    def test_category_balance(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        categories = [e.get("category", "") for e in data]
        for name, minimum in _CATEGORY_MINIMUMS.items():
            count = categories.count(name)
            assert count >= minimum, f"Need ≥{minimum} {name!r} queries, got {count}"
        unknown = set(categories) - set(_CATEGORY_MINIMUMS)
        assert not unknown, f"Unregistered category values found in queries.json: {unknown}"


# ── Metrics functions ─────────────────────────────────────────────────────────

class TestStripAnchor:
    def test_strips_body_anchor(self):
        assert _mod._strip_anchor("architecture/world_repository_layout#body-000") == "architecture/world_repository_layout"

    def test_strips_heading_anchor(self):
        assert _mod._strip_anchor("mechanics/02_combat_laws#damage-formula-001") == "mechanics/02_combat_laws"

    def test_bare_id_passthrough(self):
        assert _mod._strip_anchor("TCK-20260523-WORLD-REPO-INIT") == "TCK-20260523-WORLD-REPO-INIT"

    def test_hit_matches_anchored_result_against_bare_expected(self):
        # Reproduces the real bug: knowledge_docs.doc_id is chunk-level (anchored),
        # but queries.json's expected_doc_ids are document-level (bare).
        assert _mod._hit(["architecture/world_repository_layout#body-000"], {"architecture/world_repository_layout"}, k=5) is True

    def test_reciprocal_rank_matches_anchored_result_against_bare_expected(self):
        assert _mod._reciprocal_rank(["other#body-000", "target/doc#h2-slug-003"], {"target/doc"}) == pytest.approx(0.5)


class TestReciprocalRank:
    def test_rank_1_is_1(self):
        assert _mod._reciprocal_rank(["a", "b", "c"], {"a"}) == pytest.approx(1.0)

    def test_rank_2_is_half(self):
        assert _mod._reciprocal_rank(["x", "a", "c"], {"a"}) == pytest.approx(0.5)

    def test_rank_3_is_third(self):
        assert _mod._reciprocal_rank(["x", "y", "a"], {"a"}) == pytest.approx(1 / 3)

    def test_no_hit_is_zero(self):
        assert _mod._reciprocal_rank(["x", "y", "z"], {"a"}) == pytest.approx(0.0)

    def test_empty_results_is_zero(self):
        assert _mod._reciprocal_rank([], {"a"}) == pytest.approx(0.0)


class TestHit:
    def test_hit_in_top_k(self):
        assert _mod._hit(["a", "b", "c"], {"b"}, k=3) is True

    def test_no_hit_in_top_k(self):
        assert _mod._hit(["a", "b", "c"], {"d"}, k=3) is False

    def test_hit_outside_top_k_excluded(self):
        assert _mod._hit(["a", "b", "c", "target"], {"target"}, k=3) is False

    def test_empty_results_no_hit(self):
        assert _mod._hit([], {"a"}, k=5) is False


# ── _run_query parsing ────────────────────────────────────────────────────────

class TestRunQuery:
    def test_parses_tab_separated_output(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.stdout = (
            "mechanics/02_combat_laws\tdocs/mechanics/02_combat_laws.md\tDamage Formula\tmechanics\t0.85\t0.80\t0.60\tsome text\n"
            "engine/kernel\tdocs/engine/kernel.md\tTick Loop\tengine\t0.70\t0.65\t0.40\tother text\n"
        )
        monkeypatch.setattr(_mod.subprocess, "run", lambda *a, **kw: mock_result)
        result = _mod._run_query("damage formula", top_k=5)
        assert result == ["mechanics/02_combat_laws", "engine/kernel"]

    def test_empty_output_returns_empty_list(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.stdout = ""
        monkeypatch.setattr(_mod.subprocess, "run", lambda *a, **kw: mock_result)
        result = _mod._run_query("zzz_nonexistent", top_k=5)
        assert result == []

    def test_skips_blank_lines(self, monkeypatch):
        mock_result = MagicMock()
        mock_result.stdout = "\nmechanics/02_combat_laws\tdocs/file.md\th\ts\t0.9\t0.8\t0.5\ttext\n\n"
        monkeypatch.setattr(_mod.subprocess, "run", lambda *a, **kw: mock_result)
        result = _mod._run_query("test", top_k=5)
        assert result == ["mechanics/02_combat_laws"]


# ── evaluate exit codes ───────────────────────────────────────────────────────

class TestEvaluateExitCode:
    def _make_queries(self, n: int) -> list[dict]:
        return [{"query": f"q{i}", "expected_doc_ids": ["target/doc"], "category": "semantic", "notes": "test"} for i in range(n)]

    def test_exit_0_when_all_hit(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["target/doc"] * top_k)
        qs = self._make_queries(5)
        result = _mod.evaluate(qs, top_k=10, threshold=0.80)
        assert result == 0

    def test_exit_0_when_hits_are_anchored_chunk_ids(self, monkeypatch, tmp_path):
        # Real-world bug reproduction: _run_query returns anchored chunk ids
        # (as knowledge_search.py actually does post-chunking), expected_doc_ids
        # stays bare (as queries.json actually does) — must still count as a hit.
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["target/doc#body-000"] * top_k)
        qs = self._make_queries(5)
        result = _mod.evaluate(qs, top_k=10, threshold=0.80)
        assert result == 0

    def test_exit_1_when_no_hits(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["other/doc"] * top_k)
        qs = self._make_queries(5)
        result = _mod.evaluate(qs, top_k=10, threshold=0.80)
        assert result == 1

    def test_zero_result_counted(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        counts = []
        def mock_run(q, top_k=10):
            return []
        monkeypatch.setattr(_mod, "_run_query", mock_run)
        qs = [{"query": "x", "expected_doc_ids": [], "category": "edge-case", "notes": "t"}]
        _mod.evaluate(qs, top_k=10, threshold=0.0)

    def test_report_saved_to_reports_dir(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["target/doc"])
        qs = self._make_queries(3)
        _mod.evaluate(qs, top_k=10, threshold=0.80)
        report_files = list(tmp_path.glob("eval_search_*.json"))
        assert len(report_files) == 1
        report = json.loads(report_files[0].read_text())
        assert "metrics" in report
        assert "per_query" in report
        assert len(report["per_query"]) == 3

    def test_no_result_queries_excluded_from_recall_denominator(self, monkeypatch, tmp_path):
        # Regression test for the Recall@5/Recall@10 denominator bug: before the fix,
        # `total = len(queries)` included no-result (empty expected_doc_ids) queries in
        # the denominator, capping the achievable Recall@5 below 1.0 even when every
        # answerable query hits. 3 answerable + 2 no-result queries, all answerable
        # queries hit -> recall must be 1.0, not 3/5.
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["target/doc"])
        qs = self._make_queries(3) + [
            {"query": "nr1", "expected_doc_ids": [], "category": "no-result", "notes": "t"},
            {"query": "nr2", "expected_doc_ids": [], "category": "no-result", "notes": "t"},
        ]
        _mod.evaluate(qs, top_k=10, threshold=0.80)
        report_files = list(tmp_path.glob("eval_search_*.json"))
        report = json.loads(report_files[0].read_text())
        assert report["metrics"]["recall_at_5"] == pytest.approx(1.0)
        assert report["metrics"]["recall_at_10"] == pytest.approx(1.0)

    def test_avg_duplicate_rate_in_saved_report(self, monkeypatch, tmp_path):
        monkeypatch.setattr(_mod, "_REPORTS_DIR", tmp_path)
        monkeypatch.setattr(_mod, "_run_query", lambda q, top_k=10: ["target/doc", "target/doc"])
        qs = self._make_queries(3)
        _mod.evaluate(qs, top_k=10, threshold=0.80)
        report_files = list(tmp_path.glob("eval_search_*.json"))
        report = json.loads(report_files[0].read_text())
        assert "avg_duplicate_rate" in report["metrics"]
        assert report["metrics"]["avg_duplicate_rate"] == pytest.approx(0.5)

    def test_threshold_default_unchanged(self, monkeypatch, tmp_path):
        # Locks in AC6: the 0.80 Recall@5 gate's pass/fail meaning is unchanged by
        # this ticket's denominator fix or new categories/metric.
        captured_threshold = {}
        monkeypatch.setattr(_mod, "_DB_PATH", tmp_path / "knowledge.db")
        (tmp_path / "knowledge.db").write_text("")
        monkeypatch.setattr(_mod, "_QUERIES_PATH", _QUERIES_PATH)

        def fake_evaluate(queries, top_k=10, threshold=0.80):
            captured_threshold["value"] = threshold
            return 0

        monkeypatch.setattr(_mod, "evaluate", fake_evaluate)
        monkeypatch.setattr(sys, "argv", ["eval_search.py"])
        _mod.main()
        assert captured_threshold["value"] == 0.80


# ── duplicate_rate metric ─────────────────────────────────────────────────────

class TestDuplicateRate:
    def test_no_duplicates_is_zero(self):
        assert _mod._duplicate_rate(["a", "b", "c"]) == pytest.approx(0.0)

    def test_all_duplicates(self):
        assert _mod._duplicate_rate(["a", "a", "a"]) == pytest.approx(2 / 3)

    def test_partial_duplicates_after_anchor_strip(self):
        assert _mod._duplicate_rate(["a#h1-000", "a#h2-001", "b"]) == pytest.approx(1 / 3)

    def test_empty_results_is_zero(self):
        assert _mod._duplicate_rate([]) == 0.0


# ── main() no-index guard ─────────────────────────────────────────────────────

class TestMainNoIndex:
    def test_exits_1_without_traceback_when_index_missing(self, monkeypatch, tmp_path, capsys):
        fake_db = tmp_path / "nonexistent.db"
        monkeypatch.setattr(_mod, "_DB_PATH", fake_db)
        result = _mod.main.__wrapped__ if hasattr(_mod.main, "__wrapped__") else _mod.main
        # Call main with sys.argv stubbed
        monkeypatch.setattr(sys, "argv", ["eval_search.py"])
        exit_code = _mod.main()
        captured = capsys.readouterr()
        assert exit_code == 1
        assert "knowledge index" in captured.err.lower() or "make knowledge-index" in captured.err
