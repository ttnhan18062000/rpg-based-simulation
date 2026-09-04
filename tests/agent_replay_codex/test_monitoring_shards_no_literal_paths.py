"""Architecture guard: no call site may reintroduce a literal, single-file
runs.jsonl/events.jsonl path join outside monitoring_shards.py
(TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION).

Before this ticket, 6 of the 7 call sites built `<agent_monitoring_dir> / "runs.jsonl"` (or
"events.jsonl") directly, bypassing the shard-aware helper entirely for those 2 sources — the
exact defect class this ticket fixes. This static check greps the 7 call-site source files for
that literal path-join pattern (a `/` immediately followed by the quoted filename) and fails if
it reintroduces the pattern anywhere outside monitoring_shards.py itself, so a future edit can't
silently re-hardcode single-file resolution at one of these sites again.
"""
from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_CALL_SITE_FILES = (
    "tests/agent_codex_pilot_executor/conftest.py",
    "tests/agent_codex_posttool_adapter/conftest.py",
    "tests/agent_codex_realrepo_pilot_harness/conftest.py",
    "tools/agent_replay_codex/provenance_check.py",
    "tools/agent_codex_pilot_guardrails/config_toggle.py",
    "tools/agent_codex_realrepo_pilot_harness/proofs.py",
    "tools/agent_codex_pilot_guardrails/ticket_selection.py",
)

_LITERAL_PATH_JOIN = re.compile(r"""/\s*["']((runs|events)\.jsonl)["']""")


def test_conftest_snapshot_functions_cover_all_three_sources_via_generalized_helper():
    offenders = []
    for relative_path in _CALL_SITE_FILES:
        text = (_REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for match in _LITERAL_PATH_JOIN.finditer(text):
            offenders.append(f"{relative_path}: {match.group(0)!r}")

    assert offenders == [], (
        "literal single-file runs.jsonl/events.jsonl path construction found outside "
        f"monitoring_shards.py: {offenders}"
    )
