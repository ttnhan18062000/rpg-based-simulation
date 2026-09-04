"""Tests for tools/agent-monitoring/retrieval_baseline_metrics.py
(TCK-20260728-RETRIEVAL-BASELINE-METRICS).

Mirrors tests/tools/test_agent_monitoring_manifest.py's design: inline-dict unit tests for each
section function (no file I/O), ast/source-text reuse guards proving this module composes
existing generate_retro.py/legacy_reader.py/manifest.py functions rather than reimplementing
them, and a dirty-tree-aware zero-mutation integration test against the REAL agent-monitoring/
corpus — never a tmp_path copy, which would make that assertion vacuous.
"""
import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MONITORING_TOOLS_DIR = _REPO_ROOT / "tools" / "agent-monitoring"
_MODULE_PATH = _MONITORING_TOOLS_DIR / "retrieval_baseline_metrics.py"
_REAL_AGENT_MONITORING_DIR = _REPO_ROOT / "agent-monitoring"

if str(_MONITORING_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_TOOLS_DIR))

import retrieval_baseline_metrics as rbm  # noqa: E402
from retrieval_baseline_metrics import (  # noqa: E402
    SEARCH_TOOL_NAMES,
    build_baseline_report,
    build_context_tokens_section,
    build_duration_section,
    build_gate_outcome_section,
    build_legacy_schema_notes,
    build_raw_investigation_count_section,
    build_review_rework_section,
    build_search_count_section,
    load_all_sources,
)
from generate_retro import load_data_glob  # noqa: E402

_MODULE_SOURCE = _MODULE_PATH.read_text()
_MODULE_AST = ast.parse(_MODULE_SOURCE)


def _imported_names() -> set:
    names = set()
    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.name)
    return names


# ---------------------------------------------------------------------------
# Reuse-not-reimplement guards
# ---------------------------------------------------------------------------

def test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader():
    imported = _imported_names()
    assert "_load_runs_and_events" in imported
    # DEFAULT_TOOLS_FILE is directory-valued (TCK-20260903-MONITORING-DATA-CONSUMERS-CORE),
    # so this module reuses generate_retro.py's multi-week-aware load_data_glob() rather than
    # the literal-file-only load_jsonl() (TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-
    # CONSTANTS — a bare load_jsonl(DEFAULT_TOOLS_FILE) raises IsADirectoryError).
    assert "load_data_glob" in imported
    assert "DEFAULT_TOOLS_FILE" in imported

    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.Import):
            assert node.names[0].name != "sqlite3", "must not connect to the index db directly"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            assert node.func.attr not in {"read_text", "read_bytes", "readlines"}, (
                "must not read a *.jsonl file directly — reuse load_jsonl/_load_runs_and_events"
            )


def test_baseline_report_reuses_classify_provenance_not_reimplemented():
    imported = _imported_names()
    assert "classify_provenance" in imported

    func_node = next(
        n for n in ast.walk(_MODULE_AST)
        if isinstance(n, ast.FunctionDef) and n.name == "build_legacy_schema_notes"
    )
    call_names = [
        n.func.id for n in ast.walk(func_node)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert "classify_provenance" in call_names


def test_baseline_report_tool_never_imports_writer_module():
    imported = _imported_names()
    banned_modules = {"writer", "record_run", "record_events", "post_tool_hook"}
    assert not (imported & banned_modules)

    for node in ast.walk(_MODULE_AST):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
            if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                assert node.args[1].value not in ("w", "a"), "must never open a file for writing"


# ---------------------------------------------------------------------------
# TCK-20260904-HOTFIX-RETRIEVAL-TOOLS-CONSUMERS-DEAD-CONSTANTS — load_all_sources() must read
# the FULL multi-week tools corpus (via load_data_glob), not crash with IsADirectoryError on the
# now-directory-valued DEFAULT_TOOLS_FILE, and not silently under-report by reading only one week.
# ---------------------------------------------------------------------------

def test_load_all_sources_tools_reads_across_multiple_week_folders(tmp_path, monkeypatch):
    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W01").mkdir(parents=True)
    (data_dir / "2026-W02").mkdir(parents=True)
    (data_dir / "2026-W01" / "tools.jsonl").write_text(
        json.dumps({"run_id": "TCK-A", "tool": "Read"}) + "\n"
    )
    (data_dir / "2026-W02" / "tools.jsonl").write_text(
        json.dumps({"run_id": "TCK-B", "tool": "Read"}) + "\n"
        + json.dumps({"run_id": "TCK-B", "tool": "Bash"}) + "\n"
    )

    monkeypatch.setattr(rbm, "_load_runs_and_events", lambda: ([], []))
    monkeypatch.setattr(rbm, "DEFAULT_TOOLS_FILE", data_dir)

    runs, events, tools = load_all_sources()

    assert runs == []
    assert events == []
    # Correct-data assertion, not just "doesn't crash": both week folders' rows are present.
    assert len(tools) == 3
    assert {t["run_id"] for t in tools} == {"TCK-A", "TCK-B"}
    read_section = build_raw_investigation_count_section(tools)
    assert read_section["total"] == 2
    assert read_section["per_run"] == {"TCK-A": 1, "TCK-B": 1}


def test_load_all_sources_uses_load_data_glob_directly_on_directory_valued_default(tmp_path):
    data_dir = tmp_path / "agent-monitoring" / "data"
    (data_dir / "2026-W10").mkdir(parents=True)
    (data_dir / "2026-W11").mkdir(parents=True)
    (data_dir / "2026-W10" / "tools.jsonl").write_text(
        json.dumps({"run_id": "TCK-C", "tool": "Edit"}) + "\n"
    )
    (data_dir / "2026-W11" / "tools.jsonl").write_text(
        json.dumps({"run_id": "TCK-D", "tool": "Edit"}) + "\n"
    )

    # Directly exercises the exact call shape load_all_sources() now uses
    # (load_data_glob(DEFAULT_TOOLS_FILE, "tools")) against a real directory, proving it neither
    # raises IsADirectoryError nor silently returns an empty/partial result.
    tools = load_data_glob(data_dir, "tools")
    assert len(tools) == 2
    assert {t["run_id"] for t in tools} == {"TCK-C", "TCK-D"}


# ---------------------------------------------------------------------------
# AC1 — context-tokens marked 'unavailable'
# ---------------------------------------------------------------------------

def test_baseline_report_context_tokens_marked_unavailable():
    section = build_context_tokens_section()
    assert section["status"] == "unavailable"
    assert "docs/agent-monitoring/schema.md" in section["citation"]


# ---------------------------------------------------------------------------
# AC2 — follow-up-search-count, derived with cited computation
# ---------------------------------------------------------------------------

def test_baseline_report_search_count_is_marked_or_derived_never_silent():
    section = build_search_count_section([])
    assert isinstance(section["total"], int)
    assert "tool" in section["derivation"]
    assert "SEARCH_TOOL_NAMES" in section["derivation"]


def test_baseline_report_search_count_derivation_matches_stated_fields():
    tools = [
        {"run_id": "TCK-A", "tool": "mcp__knowledge-search__search_docs"},
        {"run_id": "TCK-A", "tool": "ToolSearch"},
        {"run_id": "TCK-A", "tool": "Bash"},
        {"run_id": "TCK-B", "tool": "WebSearch"},
        {"run_id": "TCK-B", "tool": "mcp__knowledge-search__search_health"},
        {"run_id": "TCK-B", "tool": "Read"},
    ]
    section = build_search_count_section(tools)
    assert section["total"] == 3
    assert section["per_run"] == {"TCK-A": 2, "TCK-B": 1}
    assert SEARCH_TOOL_NAMES == {
        "mcp__knowledge-search__search_docs",
        "ToolSearch",
        "WebSearch",
    }


# ---------------------------------------------------------------------------
# AC-NEW — raw-investigation (Read) count, derived proxy for grep-equivalent effort
# ---------------------------------------------------------------------------

def test_baseline_report_raw_investigation_count_is_marked_or_derived_never_silent():
    section = build_raw_investigation_count_section([])
    assert isinstance(section["total"], int)
    assert section["total"] == 0
    assert section["derivation"]
    assert "tool" in section["derivation"]
    assert "Read" in section["derivation"]
    assert "Grep" in section["derivation"] or "Bash" in section["derivation"]


def test_baseline_report_raw_investigation_count_derivation_matches_stated_fields():
    tools = [
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Bash"},
        {"run_id": "TCK-B", "tool": "Read"},
        {"run_id": "TCK-B", "tool": "Edit"},
        {"run_id": None, "tool": "Read"},
        {"run_id": "TCK-B", "tool": "mcp__knowledge-search__search_docs"},
    ]
    section = build_raw_investigation_count_section(tools)
    assert section["total"] == 4
    assert section["per_run"] == {"TCK-A": 2, "TCK-B": 1, "unattributed": 1}


def test_baseline_report_raw_investigation_count_wired_into_report():
    runs = [{"run_id": "TCK-A", "final_status": "DONE"}]
    events = []
    tools = [
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Bash"},
        {"run_id": "TCK-A", "tool": "mcp__knowledge-search__search_docs"},
    ]
    report = build_baseline_report(runs, events, tools)
    assert report["raw_investigation_count"] == build_raw_investigation_count_section(tools)


def test_baseline_report_raw_investigation_count_ratio_never_silent_if_present():
    # Case A: search_total > 0 -> finite float ratio
    tools_with_search = [
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "mcp__knowledge-search__search_docs"},
    ]
    section = build_raw_investigation_count_section(tools_with_search)
    read_total = section["total"]
    search_total = build_search_count_section(tools_with_search)["total"]
    assert isinstance(section["read_to_search_ratio"], float)
    assert section["read_to_search_ratio"] == round(read_total / search_total, 4)

    # Case B: search_total == 0 -> explicit "undefined" marker string, never an exception
    tools_no_search = [
        {"run_id": "TCK-A", "tool": "Read"},
        {"run_id": "TCK-A", "tool": "Bash"},
    ]
    section_no_search = build_raw_investigation_count_section(tools_no_search)
    assert isinstance(section_no_search["read_to_search_ratio"], str)
    assert "undefined" in section_no_search["read_to_search_ratio"]


def test_baseline_report_raw_investigation_count_plausible_on_real_corpus():
    runs, events, tools = load_all_sources()
    section = build_raw_investigation_count_section(tools)
    assert isinstance(section["total"], int)
    assert section["total"] > 1000
    assert section["total"] == sum(section["per_run"].values())


# ---------------------------------------------------------------------------
# AC3 — phase-duration, flagged pause-contaminated
# ---------------------------------------------------------------------------

def test_baseline_report_flags_duration_pause_contaminated_only_when_a_real_gap_is_found():
    # TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT: real gap-aware computation via duration_utils.py,
    # not an unconditional flag on every row. TCK-A has a genuine >=30min idle gap (flagged);
    # TCK-D has the same 120s span fully covered by frequent events (not flagged, real active
    # time); TCK-B (duration_s=0) and TCK-C (no duration_s at all) are still excluded entirely.
    runs = [
        {
            "run_id": "TCK-A",
            "duration_s": 3600,
            "start_ts": "2026-01-01T00:00:00Z",
            "end_ts": "2026-01-01T01:00:00Z",
        },
        {"run_id": "TCK-B", "duration_s": 0},
        {"run_id": "TCK-C"},
        {
            "run_id": "TCK-D",
            "duration_s": 120,
            "start_ts": "2026-01-01T00:00:00Z",
            "end_ts": "2026-01-01T00:02:00Z",
        },
    ]
    events = [
        {"run_id": "TCK-D", "seq": 1, "ts": "2026-01-01T00:00:00Z", "phase": "Scope", "agent": "ticket-scoper"},
        {"run_id": "TCK-D", "seq": 2, "ts": "2026-01-01T00:01:00Z", "phase": "Implement", "agent": "implementer"},
    ]
    section = build_duration_section(runs, events)
    assert len(section["rows"]) == 2
    rows_by_id = {r["run_id"]: r for r in section["rows"]}

    row_a = rows_by_id["TCK-A"]
    assert row_a["duration_s"] == 3600
    assert row_a["idle_gap_s"] == 3600.0  # zero events -> entire 1hr span idle
    assert row_a["active_duration_s"] == 0.0
    assert row_a["flag"] == "pause-contaminated"
    assert "duration_utils.py" in row_a["note"]

    row_d = rows_by_id["TCK-D"]
    assert row_d["idle_gap_s"] == 0.0  # all gaps under the 30min pause threshold
    assert row_d["active_duration_s"] == 120.0
    assert "flag" not in row_d


def test_baseline_report_duration_section_uses_duration_utils_when_available():
    # Retired trip-wire (formerly test_baseline_report_would_prefer_gap_aware_view_if_available,
    # which asserted duration_utils.py did NOT exist and was designed to go red once it did,
    # forcing this exact update). Now a real positive assertion that build_duration_section
    # actually calls the shared duration_utils.compute_active_idle_split rather than reimplementing
    # gap detection inline.
    duration_utils_path = _MONITORING_TOOLS_DIR / "duration_utils.py"
    assert duration_utils_path.exists()
    source = _MODULE_PATH.read_text(encoding="utf-8")
    assert "from duration_utils import compute_active_idle_split" in source
    assert "compute_active_idle_split(" in source


# ---------------------------------------------------------------------------
# AC4 — test/gate outcome and review-rework, derived-proxy only
# ---------------------------------------------------------------------------

def test_baseline_report_gate_outcome_uses_final_status_and_reason_code_only():
    runs = [
        {"run_id": "TCK-A", "final_status": "DONE"},
        {"run_id": "TCK-B", "final_status": "NEEDS_CHANGES"},
        {"run_id": "TCK-C", "final_status": "IN_PROGRESS"},
    ]
    section = build_gate_outcome_section(runs)
    assert section["status_breakdown"] == {"DONE": 1, "NEEDS_CHANGES": 1, "IN_PROGRESS": 1}
    assert section["gate_fail_count"] == 1
    assert section["terminal_success_count"] == 1
    assert "derived proxy" in section["disclosure"]
    assert "not fabricated" in section["disclosure"]


def test_baseline_report_review_rework_proxy_requires_multi_record_same_run_id():
    runs = [
        {"run_id": "TCK-REWORKED", "final_status": "NEEDS_CHANGES", "start_ts": "2026-07-01T00:00:00Z"},
        {"run_id": "TCK-REWORKED", "final_status": "DONE", "start_ts": "2026-07-02T00:00:00Z"},
        {"run_id": "TCK-ABANDONED", "final_status": "BLOCKED", "start_ts": "2026-07-01T00:00:00Z"},
    ]
    section = build_review_rework_section(runs)
    assert section["reworked_run_ids"] == ["TCK-REWORKED"]
    assert section["count"] == 1
    assert "TCK-ABANDONED" not in section["reworked_run_ids"]


def test_baseline_report_review_rework_proxy_ignores_reason_code_alone():
    runs = [
        {
            "run_id": "TCK-SINGLE-RECORD",
            "final_status": "NEEDS_CHANGES",
            "reason_code": "architecture_violation",
            "start_ts": "2026-07-01T00:00:00Z",
        },
    ]
    section = build_review_rework_section(runs)
    assert section["reworked_run_ids"] == []
    assert section["count"] == 0
    assert "reason_code" in section["disclosure"]


# ---------------------------------------------------------------------------
# AC5 — zero mutation of agent-monitoring/*.jsonl
# ---------------------------------------------------------------------------

def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", "agent-monitoring/"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_baseline_report_tool_causes_zero_diff_on_real_corpus():
    assert _REAL_AGENT_MONITORING_DIR.is_dir()
    assert "tmp" not in str(_REAL_AGENT_MONITORING_DIR).lower()

    pre_porcelain = _porcelain_snapshot()

    runs, events, tools = load_all_sources()
    build_baseline_report(runs, events, tools)

    post_porcelain = _porcelain_snapshot()
    assert pre_porcelain == post_porcelain, (
        "retrieval_baseline_metrics mutated agent-monitoring/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )


def test_baseline_report_cli_runs_against_real_corpus_and_prints_json():
    result = subprocess.run(
        [sys.executable, str(_MODULE_PATH)], cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    report = json.loads(result.stdout)
    assert report["ticket_id"] == "TCK-20260728-RETRIEVAL-BASELINE-METRICS"
    assert report["context_tokens"]["status"] == "unavailable"
    assert set(report.keys()) == {
        "ticket_id", "generated_note", "context_tokens", "search_count", "duration",
        "gate_outcome", "review_rework", "legacy_schema_notes", "raw_investigation_count",
    }
