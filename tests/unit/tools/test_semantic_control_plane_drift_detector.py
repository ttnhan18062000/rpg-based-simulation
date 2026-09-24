"""Tests for tools/semantic_control_plane/mapping_drift_check.py.

TCK-20260924-M2-MAPPING-DRIFT-DETECTION. Report-only drift detector answering "has the world
moved under a Rule<->Mechanism mapping entry since a human last reviewed it?" -- two of
`roadmap.md` M2's three drift classes (cited-code-changed-since-review, verdict-changed-since-
review); drift class 2 (split/merge) is consciously descoped, see the ticket's own Assumptions/
Open Questions and Implementation Notes.

Per this corpus's own established discipline (`test_mechanism_registry_changed_code_check.py`,
`test_semantic_control_plane_schema.py`): every implemented drift class gets a fixture proving it
FIRES, not just a clean-data pass.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tools.semantic_control_plane.mapping_drift_check import (
    check_cited_code_drift,
    check_drift_from_git,
    check_verdict_drift,
    main,
)
from tools.mechanism_registry.registry import VALID_VERDICTS

REPO_ROOT = Path(__file__).resolve().parents[3]


def _edge_row(rule_id="TERR-99", mechanism_id="fake_mechanism", edge_type="REALIZES", date="2026-09-20"):
    return {"rule_id": rule_id, "mechanism_id": mechanism_id, "edge_type": edge_type, "date": date}


# ---------------------------------------------------------------------------
# Purity guard
# ---------------------------------------------------------------------------


def test_pure_core_takes_no_git_dependency():
    """check_cited_code_drift and check_verdict_drift must have no subprocess/git call reachable
    from their own code path -- they answer a per-row-date question, not a two-ref diff, and must
    never shell out. Checked via `co_names` (names the bytecode actually references as globals/
    attributes), not a raw substring scan of the source -- a substring scan would also match the
    word "git" appearing harmlessly inside each function's own docstring prose. Also run against
    plain dicts/strings with a synthetic (non-real) mechanism_id to prove they don't secretly
    depend on the real committed registry either."""
    for fn in (check_cited_code_drift, check_verdict_drift):
        referenced_names = set(fn.__code__.co_names)
        assert "subprocess" not in referenced_names
        assert not any("git" in name.lower() for name in referenced_names)

    row = _edge_row()
    cited_findings = check_cited_code_drift(
        [row],
        mechanism_cited_paths={"fake_mechanism": ["src/fake/module.py"]},
        file_last_commit_dates={"src/fake/module.py": "2026-09-19"},
    )
    assert cited_findings == []

    verdict_findings = check_verdict_drift(
        [row],
        review_time_verdicts={"fake_mechanism": "observed"},
        current_verdicts={"fake_mechanism": "observed"},
    )
    assert verdict_findings == []


# ---------------------------------------------------------------------------
# Drift class 1 -- cited-code-changed-since-review
# ---------------------------------------------------------------------------


def test_drift_class_1_fires_on_planted_stale_citation():
    row = _edge_row(date="2026-09-20")
    findings = check_cited_code_drift(
        [row],
        mechanism_cited_paths={"fake_mechanism": ["src/fake/module.py"]},
        file_last_commit_dates={"src/fake/module.py": "2026-09-21"},  # after the row's own date
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "TERR-99"
    assert findings[0].mechanism_id == "fake_mechanism"
    assert findings[0].changed_paths == ["src/fake/module.py"]


def test_drift_class_1_silent_when_cited_file_unchanged_since_review():
    row = _edge_row(date="2026-09-20")
    findings = check_cited_code_drift(
        [row],
        mechanism_cited_paths={"fake_mechanism": ["src/fake/module.py"]},
        file_last_commit_dates={"src/fake/module.py": "2026-09-20"},  # same day, not after
    )
    assert findings == []


def test_drift_class_1_silent_when_no_cited_paths_resolved():
    row = _edge_row(date="2026-09-20")
    findings = check_cited_code_drift(
        [row], mechanism_cited_paths={}, file_last_commit_dates={},
    )
    assert findings == []


# ---------------------------------------------------------------------------
# Drift class 3 -- verdict-changed-since-review
# ---------------------------------------------------------------------------


def test_drift_class_3_fires_on_planted_verdict_change():
    row = _edge_row(date="2026-09-20")
    findings = check_verdict_drift(
        [row],
        review_time_verdicts={"fake_mechanism": "observed"},
        current_verdicts={"fake_mechanism": "contradicted"},
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "TERR-99"
    assert findings[0].mechanism_id == "fake_mechanism"
    assert findings[0].old_verdict == "observed"
    assert findings[0].new_verdict == "contradicted"


def test_drift_class_3_silent_when_verdict_unchanged_since_review():
    row = _edge_row(date="2026-09-20")
    findings = check_verdict_drift(
        [row],
        review_time_verdicts={"fake_mechanism": "observed"},
        current_verdicts={"fake_mechanism": "observed"},
    )
    assert findings == []


def test_drift_class_3_review_time_recovery_uses_commit_not_bare_date_string(tmp_path, monkeypatch):
    """Plants two commits on the SAME calendar date touching rule_mechanism_edges.yaml (distinct
    wall-clock timestamps, same --date=short value) and asserts the anchor-commit resolution picks
    the most-recent-on/before-date one deterministically -- documents and tests the tie-break rule
    explicitly rather than leaving it implicit, per the ticket's own "not blocking" open question."""
    import tools.semantic_control_plane.mapping_drift_check as drift_check

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "registries").mkdir()
    (repo / "src").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    def _write_registries(mechanisms, edges):
        with open(repo / "registries" / "mechanisms.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"mechanisms": mechanisms}, f)
        with open(repo / "registries" / "rule_mechanism_edges.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump({"edges": edges}, f)

    def _commit(message, hour):
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        date_str = f"2026-09-20T{hour:02d}:00:00"
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@test.com",
             "commit", "-q", "-m", message],
            cwd=repo, check=True,
            env={**os.environ, "GIT_AUTHOR_DATE": date_str, "GIT_COMMITTER_DATE": date_str},
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True,
        ).stdout.strip()

    mechanism = {
        "id": "fake_mechanism",
        "implemented_by": [],
        "verified": {
            "instrument": "code_trace", "verdict": "observed",
            "date": "2026-09-20", "note": "seed",
        },
    }
    edge = _edge_row(date="2026-09-20")
    _write_registries([mechanism], [edge])
    first_sha = _commit("first commit, morning", hour=8)

    mechanism_later = dict(mechanism, verified={
        "instrument": "code_trace", "verdict": "contradicted",
        "date": "2026-09-20", "note": "same-day re-review",
    })
    # rule_mechanism_edges.yaml itself must also change between commits, since the anchor commit
    # is resolved from THAT file's own git history, not mechanisms.yaml's.
    edge_later = dict(edge, evidence="re-reviewed same day")
    _write_registries([mechanism_later], [edge_later])
    second_sha = _commit("second commit, same calendar day, afternoon", hour=18)

    assert first_sha != second_sha

    monkeypatch.setattr(drift_check, "_REPO_ROOT", repo)
    anchor = drift_check._anchor_commit_for_row_date("2026-09-20")
    assert anchor == second_sha

    verdict = drift_check._verdict_at_commit(anchor, "fake_mechanism")
    assert verdict == "contradicted"


# ---------------------------------------------------------------------------
# Report-only guarantee
# ---------------------------------------------------------------------------


def test_report_only_exits_zero_with_findings_present(monkeypatch, capsys):
    import tools.semantic_control_plane.mapping_drift_check as drift_check
    from tools.semantic_control_plane.mapping_drift_check import (
        CitedCodeDriftFinding,
        VerdictDriftFinding,
    )

    monkeypatch.setattr(
        drift_check, "check_drift_from_git",
        lambda: (
            [CitedCodeDriftFinding(
                rule_id="TERR-99", mechanism_id="fake_mechanism", edge_type="REALIZES",
                row_date="2026-09-20", changed_paths=["src/fake/module.py"],
            )],
            [VerdictDriftFinding(
                rule_id="TERR-99", mechanism_id="fake_mechanism", row_date="2026-09-20",
                old_verdict="observed", new_verdict="contradicted",
            )],
        ),
    )

    exit_code = main([])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "1 cited-code drift finding(s)" in out
    assert "1 verdict drift finding(s)" in out


# ---------------------------------------------------------------------------
# Read-only guard -- registries unchanged after a run
# ---------------------------------------------------------------------------


def test_registries_still_validate_clean_after_running_detector():
    from tools.semantic_control_plane.registry import validate_all

    before = validate_all()
    check_drift_from_git()
    after = validate_all()

    assert before == []
    assert after == []


# ---------------------------------------------------------------------------
# Status-vocabulary guard
# ---------------------------------------------------------------------------


def test_detector_status_words_resolve_to_status_axis_model_vocabulary():
    """Every old_verdict/new_verdict value the detector ever echoes must be a member of
    VALID_VERDICTS -- never a minted term. Runs the real, live wrapper against M1's actual data,
    since VerdictDriftFinding's own verdicts come straight from MechanismRegistry.get_verification()."""
    _cited_code_findings, verdict_findings = check_drift_from_git()
    for finding in verdict_findings:
        if finding.old_verdict is not None:
            assert finding.old_verdict in VALID_VERDICTS
        if finding.new_verdict is not None:
            assert finding.new_verdict in VALID_VERDICTS


# ---------------------------------------------------------------------------
# Live run against M1's Territory mapping
# ---------------------------------------------------------------------------


def test_live_run_against_territory_mapping_reports_or_records_finding():
    cited_code_findings, verdict_findings = check_drift_from_git()
    assert isinstance(cited_code_findings, list)
    assert isinstance(verdict_findings, list)


def test_make_target_runs_clean():
    result = subprocess.run(
        ["make", "semantic-control-plane-drift-check"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
