"""TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR: report-only planning-doc status drift sweep.

The fixtures freeze the two real drift cases found on 2026-09-30 (an `idea` doc and a "ready,
schedule later" item, each already shipped), so the tests keep proving the detector after the real
docs are resolved.
"""

import hashlib
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from gate_checks import planning_doc_staleness_check as pdsc  # noqa: E402

IDEA_DOC = """---
status: idea
layer: observability
date: 2026-07-28
tags: [idea]
---

# Idea: Distinguish Active Work Time from Idle/Session-Pause Gaps in Agent Monitoring Duration

## Problem
text
"""

STANDALONE = """---
status: active
layer: ai
date: 2026-09-04
tags: []
---

# Standalone items

## 2. Extend cost_proxy_score to implement-epic.js — SHIPPED (code) (was: Horizon 2 — ready, schedule later)

## 3. working_log.csv parser and cleanup (Horizon 2 — ready, schedule later)

## 4. Provider-portability conformance test (Horizon 2 — ready, schedule later)

## 5. Something not yet done at all (Horizon 2 — ready, schedule later)
"""


def _ticket(done: Path, tid: str, extra: str = "") -> None:
    (done / f"{tid}.md").write_text(f"# {tid}\n\n## Status\nDONE\n{extra}", encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    plans = tmp_path / "docs" / "plans"
    (plans / "agent_infrastructure" / "ai_first_hardening_epics").mkdir(parents=True)
    (plans / "archive").mkdir()
    (plans / "agent_infrastructure" / "idea_agent_monitoring_active_duration.md").write_text(IDEA_DOC)
    (plans / "agent_infrastructure" / "ai_first_hardening_epics" / "standalone_items.md").write_text(STANDALONE)
    done = tmp_path / "tickets" / "done"
    (done / "agent-monitoring-active-duration").mkdir(parents=True)
    _ticket(done / "agent-monitoring-active-duration", "TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT")
    _ticket(done, "TCK-20260904-WORKING-LOG-CSV-PARSER")
    _ticket(done, "TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST")
    return plans, done


def test_flags_both_confirmed_real_drift_cases(repo):
    plans, done = repo
    found = pdsc.find_stale_planning_docs(plans, done)
    pairs = {(Path(f.doc_path).name, f.matched_ticket_id) for f in found}
    assert ("idea_agent_monitoring_active_duration.md", "TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT") in pairs
    assert ("standalone_items.md", "TCK-20260904-WORKING-LOG-CSV-PARSER") in pairs
    assert ("standalone_items.md", "TCK-20260904-PROVIDER-PORTABILITY-CONFORMANCE-TEST") in pairs
    signals = {f.signal for f in found}
    assert signals == {"status: idea", "ready, schedule later"}


def test_unshipped_item_and_already_resolved_heading_are_not_flagged(repo):
    plans, done = repo
    _ticket(done, "TCK-20260904-EXTEND-COST-PROXY-SCORE-IMPLEMENT-EPIC")  # would match item 2 if not skipped
    found = pdsc.find_stale_planning_docs(plans, done)
    assert not any("Something not yet done" in f.matched_text for f in found)
    assert not any("cost_proxy_score" in f.matched_text for f in found)


def test_ticket_older_than_the_doc_is_not_a_match(repo):
    plans, done = repo
    _ticket(done, "TCK-20260709-AGENT-MONITORING-ACTIVE-DURATION-IDLE")  # predates the 2026-07-28 idea doc
    found = pdsc.find_stale_planning_docs(plans, done)
    assert "TCK-20260709-AGENT-MONITORING-ACTIVE-DURATION-IDLE" not in {f.matched_ticket_id for f in found}


def test_disposition_closure_did_not_ship_anything(repo):
    plans, done = repo
    _ticket(done, "TCK-20260904-WORKING-LOG-CSV-PARSER", "\n## Disposition\nWONT-DO\n")
    found = pdsc.find_stale_planning_docs(plans, done)
    assert "TCK-20260904-WORKING-LOG-CSV-PARSER" not in {f.matched_ticket_id for f in found}


def test_archive_subtree_is_skipped(repo):
    plans, done = repo
    (plans / "archive" / "idea_old.md").write_text(IDEA_DOC)
    found = pdsc.find_stale_planning_docs(plans, done)
    assert not any("/plans/archive/" in f.doc_path for f in found)


def test_detector_never_mutates_any_doc(repo):
    plans, done = repo

    def snapshot():
        return {
            str(p): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for root in (plans, done)
            for p in root.rglob("*.md")
        }

    before = snapshot()
    pdsc.find_stale_planning_docs(plans, done)
    assert pdsc.main(["--plans-dir", str(plans), "--done-dir", str(done)]) == 0
    assert snapshot() == before


def test_missing_directories_return_no_findings(tmp_path):
    assert pdsc.find_stale_planning_docs(tmp_path / "nope", tmp_path / "nada") == []


def test_cli_exits_zero_with_and_without_findings(repo, tmp_path, capsys):
    plans, done = repo
    assert pdsc.main(["--plans-dir", str(plans), "--done-dir", str(done)]) == 0
    assert "review, do not auto-edit" in capsys.readouterr().out
    empty = tmp_path / "empty_plans"
    empty.mkdir()
    assert pdsc.main(["--plans-dir", str(empty), "--done-dir", str(done)]) == 0
    assert "No planning docs" in capsys.readouterr().out
