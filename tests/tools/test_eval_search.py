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

    def test_category_balance(self):
        with open(_QUERIES_PATH) as f:
            data = json.load(f)
        categories = [e.get("category", "") for e in data]
        semantic = categories.count("semantic")
        exact = categories.count("exact-term")
        cross = categories.count("cross-section")
        edge = categories.count("edge-case")
        assert semantic >= 15, f"Need ≥15 semantic queries, got {semantic}"
        assert exact >= 15, f"Need ≥15 exact-term queries, got {exact}"
        assert cross >= 5, f"Need ≥5 cross-section queries, got {cross}"
        assert edge >= 5, f"Need ≥5 edge-case queries, got {edge}"


# ── Metrics functions ─────────────────────────────────────────────────────────

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
