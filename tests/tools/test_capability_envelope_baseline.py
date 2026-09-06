"""Tests for tools/capability_envelope_baseline.py (TCK-20260904-CAPABILITY-ENVELOPE-BASELINE)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import capability_envelope_baseline as ceb  # noqa: E402
from capability_envelope_baseline import (  # noqa: E402
    FIELDS,
    add_entry,
    build_report,
    compute_diff,
    extract_entries,
    load_registry,
    load_settings_local,
    registry_path,
    seed_registry,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_REAL_SETTINGS_LOCAL_PATH = _REPO_ROOT / ".claude" / "settings.local.json"
_REAL_REGISTRY_PATH = _REPO_ROOT / "registries" / "capability_envelope_registry.jsonl"


# ---------------------------------------------------------------------------
# AC1 — schema covers all 4 settings.local.json fields
# ---------------------------------------------------------------------------


def test_baseline_schema_covers_all_four_settings_local_fields():
    settings = {
        "permissions": {"allow": ["Bash(git *)", "Read(//tmp/**)"]},
        "enableAllProjectMcpServers": True,
        "enabledMcpjsonServers": ["knowledge-search", "graphify"],
        "disabledMcpjsonServers": ["github"],
    }

    entries = extract_entries(settings)
    fields_seen = {field for field, _ in entries}

    assert fields_seen == FIELDS
    assert ("permissions.allow", "Bash(git *)") in entries
    assert ("enableAllProjectMcpServers", True) in entries
    assert ("enabledMcpjsonServers", "knowledge-search") in entries
    assert ("disabledMcpjsonServers", "github") in entries


# ---------------------------------------------------------------------------
# AC2 — real-corpus diff produces a real, non-stub report
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not _REAL_SETTINGS_LOCAL_PATH.exists(),
    reason=(
        ".claude/settings.local.json is git-ignored and machine-local (per-developer settings, "
        "never committed) -- it exists on some development machines but never in a fresh CI "
        "checkout. This test validates against real ambient local settings when present; "
        "test_diff_script_handles_missing_settings_local_json_gracefully covers the absent case."
    ),
)
def test_diff_script_runs_against_real_settings_local_json_produces_real_report():
    assert _REAL_REGISTRY_PATH.exists(), "seed step (plan Step 5) must have committed the registry"

    live_settings = load_settings_local(_REAL_SETTINGS_LOCAL_PATH)
    live_allow_count = len(live_settings["permissions"]["allow"])
    assert live_allow_count > 0

    report = build_report(_REAL_SETTINGS_LOCAL_PATH, root=_REPO_ROOT)

    assert report["status"] == "ok"
    allow_field = report["fields"]["permissions.allow"]
    total_reported = len(allow_field["in_envelope"]) + len(allow_field["out_of_envelope"])
    assert total_reported == live_allow_count


# ---------------------------------------------------------------------------
# Missing settings.local.json handled gracefully
# ---------------------------------------------------------------------------


def test_diff_script_handles_missing_settings_local_json_gracefully(tmp_path):
    missing_path = tmp_path / "settings.local.json"
    assert not missing_path.exists()

    report = build_report(missing_path, root=tmp_path)

    assert report["status"] == "no_local_file"
    assert report["fields"] == {}


# ---------------------------------------------------------------------------
# AC3 — audit-only / no-runtime-enforcement disclosure
# ---------------------------------------------------------------------------


def test_diff_script_output_states_audit_only_no_enforcement(tmp_path):
    missing_path = tmp_path / "settings.local.json"

    report = build_report(missing_path, root=tmp_path)

    assert "audit_only_disclaimer" in report
    assert report["audit_only_disclaimer"]
    assert "AUDIT-ONLY" in report["audit_only_disclaimer"]
    assert "AUDIT-ONLY" in ceb.__doc__ or "audit-only" in ceb.__doc__.lower()


# ---------------------------------------------------------------------------
# AC4 — positive/negative control cases
# ---------------------------------------------------------------------------


def _synthetic_settings():
    return {
        "permissions": {"allow": ["Bash(git *)", "Bash(pytest *)"]},
        "enableAllProjectMcpServers": True,
        "enabledMcpjsonServers": ["knowledge-search"],
        "disabledMcpjsonServers": ["github"],
    }


def test_clean_baseline_input_produces_empty_result(tmp_path):
    settings = _synthetic_settings()
    for field, value in extract_entries(settings):
        add_entry(field, value, root=tmp_path)
    registry = load_registry(tmp_path)

    result = compute_diff(settings, registry)

    for field_report in result["fields"].values():
        assert field_report["out_of_envelope"] == []


def test_out_of_envelope_entry_produces_flagged_result(tmp_path):
    settings = _synthetic_settings()
    for field, value in extract_entries(settings):
        add_entry(field, value, root=tmp_path)
    registry = load_registry(tmp_path)

    settings_with_extra = _synthetic_settings()
    settings_with_extra["permissions"]["allow"].append("Bash(rm -rf /)")

    result = compute_diff(settings_with_extra, registry)

    assert result["fields"]["permissions.allow"]["out_of_envelope"] == ["Bash(rm -rf /)"]
    for field, field_report in result["fields"].items():
        if field != "permissions.allow":
            assert field_report["out_of_envelope"] == []


# ---------------------------------------------------------------------------
# Duplicate/conflict governance
# ---------------------------------------------------------------------------


def test_baseline_registry_rejects_or_governs_duplicate_or_conflicting_entries(tmp_path):
    add_entry("permissions.allow", "Bash(git *)", root=tmp_path)

    with pytest.raises(ValueError, match="already registered"):
        add_entry("permissions.allow", "Bash(git *)", root=tmp_path)

    settings = _synthetic_settings()
    first_pass = seed_registry(_write_settings(tmp_path, settings), root=tmp_path)
    second_pass = seed_registry(_write_settings(tmp_path, settings), root=tmp_path)

    assert len(first_pass) >= 0
    assert second_pass == []


def _write_settings(tmp_path, settings):
    path = tmp_path / "settings.local.json"
    path.write_text(json.dumps(settings), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Read-only guard
# ---------------------------------------------------------------------------


def _porcelain_snapshot() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--", ".claude/", "registries/capability_envelope_registry.jsonl"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_diff_script_is_read_only_against_settings_local_json_and_baseline():
    pre_porcelain = _porcelain_snapshot()

    build_report(_REAL_SETTINGS_LOCAL_PATH, root=_REPO_ROOT)
    load_registry(_REPO_ROOT)

    post_porcelain = _porcelain_snapshot()
    assert pre_porcelain == post_porcelain, (
        "capability_envelope_baseline mutated .claude/ or registries/: "
        f"pre={pre_porcelain!r} post={post_porcelain!r}"
    )


# ---------------------------------------------------------------------------
# reviewed field — architecture-review fix (typed durable field, not note-string inference)
# ---------------------------------------------------------------------------


def test_seeded_entries_marked_unreviewed_and_manual_adds_marked_reviewed(tmp_path):
    settings = _synthetic_settings()
    seed_registry(_write_settings(tmp_path, settings), root=tmp_path)
    registry = load_registry(tmp_path)

    assert registry, "seed_registry should have appended at least one entry"
    for entry in registry.values():
        assert entry["reviewed"] is False

    added = add_entry("permissions.allow", "Bash(some-new-command *)", root=tmp_path)
    assert added["reviewed"] is True

    registry_after = load_registry(tmp_path)
    assert registry_after[("permissions.allow", "Bash(some-new-command *)")]["reviewed"] is True
