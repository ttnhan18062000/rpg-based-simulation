"""TCK-20260930-CITED-EVIDENCE-PATH-GITIGNORE-CHECK: report-only cited-evidence tracking check."""

import inspect
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))

from gate_checks import done_checker_static as dcs  # noqa: E402
from gate_checks.cited_evidence_advisory import cited_paths, check_cited_evidence_paths  # noqa: E402

TID = "TCK-20990101-EXAMPLE"


def _git(root, *args):
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    """A throwaway git repo carrying the real .gitignore rule pair for stored_artifacts JSON."""
    _git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text(
        "stored_artifacts/**/*.json\n!stored_artifacts/**/manifest.json\n", encoding="utf-8"
    )
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    (tmp_path / "stored_artifacts" / "T").mkdir(parents=True)
    return tmp_path


def _ticket(root, body):
    (root / "tickets" / "inprogress" / f"{TID}.md").write_text(f"# {TID}\n\n{body}\n", encoding="utf-8")


def _file(root, rel, tracked):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x", encoding="utf-8")
    if tracked:
        _git(root, "add", "-f", rel)


def test_ignored_json_path_warns_naming_path_and_rule(repo):
    _file(repo, "stored_artifacts/T/table.json", tracked=False)
    _ticket(repo, "Evidence: `stored_artifacts/T/table.json`")
    status, ev = check_cited_evidence_paths(TID, "standard", root=repo)
    assert status == "WARN"
    assert "stored_artifacts/T/table.json" in ev
    assert "stored_artifacts/**/*.json" in ev


def test_all_tracked_paths_are_ok(repo):
    _file(repo, "stored_artifacts/T/table.jsonl", tracked=True)
    _file(repo, "stored_artifacts/T/manifest.json", tracked=True)
    _ticket(repo, "`stored_artifacts/T/table.jsonl` and `stored_artifacts/T/manifest.json`")
    status, ev = check_cited_evidence_paths(TID, "standard", root=repo)
    assert status == "OK", ev


def test_force_added_json_is_not_flagged(repo):
    _file(repo, "stored_artifacts/T/forced.json", tracked=True)
    _ticket(repo, "`stored_artifacts/T/forced.json`")
    assert check_cited_evidence_paths(TID, root=repo)[0] == "OK"


def test_untracked_not_ignored_path_warns_differently(repo):
    _file(repo, "stored_artifacts/T/notes.md", tracked=False)
    _ticket(repo, "`stored_artifacts/T/notes.md`")
    status, ev = check_cited_evidence_paths(TID, root=repo)
    assert status == "WARN" and "not tracked" in ev and "gitignored" not in ev


def test_staging_citation_is_checked_at_its_migrated_stored_path(repo):
    _file(repo, "stored_artifacts/T/table.json", tracked=False)
    _ticket(repo, "`staging_artifacts/T/table.json`")
    status, ev = check_cited_evidence_paths(TID, root=repo)
    assert status == "WARN" and "stored_artifacts/T/table.json" in ev


def test_missing_wildcard_and_placeholder_citations_are_skipped(repo):
    _ticket(
        repo,
        "`stored_artifacts/T/gone.json` `stored_artifacts/**/*.json` `tickets/done/{ticket_id}.md` "
        f"`tickets/inprogress/{TID}.md` `stored_artifacts/T/`",
    )
    status, ev = check_cited_evidence_paths(TID, root=repo)
    assert status == "NA", ev


def test_missing_ticket_is_na_and_git_failure_degrades_to_warn(tmp_path):
    assert check_cited_evidence_paths(TID, root=tmp_path)[0] == "NA"
    (tmp_path / "tickets" / "inprogress").mkdir(parents=True)
    (tmp_path / "stored_artifacts" / "T").mkdir(parents=True)
    (tmp_path / "stored_artifacts" / "T" / "a.md").write_text("x")
    _ticket(tmp_path, "`stored_artifacts/T/a.md`")  # not a git repo: git exits 128
    status, ev = check_cited_evidence_paths(TID, root=tmp_path)
    assert status == "WARN" and "could not run git" in ev


def test_cited_paths_extraction_order_and_dedup():
    text = "`tickets/a.md` prose `stored_artifacts/x/y.jsonl` `tickets/a.md` `docs/z.md` `plain.md`"
    assert cited_paths(text) == ["tickets/a.md", "stored_artifacts/x/y.jsonl"]


def test_advisory_never_enters_precheck_or_changes_exit_code(monkeypatch, capsys):
    assert "cited_evidence_tracked" not in inspect.getsource(dcs.run_static_precheck)
    assert "cited_evidence_tracked" not in inspect.getsource(dcs.run_finalize_selfcheck)
    monkeypatch.setattr(
        dcs, "run_advisory_checks",
        lambda t, tier: [{"condition": "cited_evidence_tracked", "status": "WARN", "evidence": "ignored"}],
    )
    monkeypatch.setattr(dcs, "run_finalize_selfcheck", lambda *a, **k: [])
    rc = dcs.main(["--ticket-id", TID, "--tier", "standard", "--part", "finalize"])
    out = capsys.readouterr().out
    assert "[advisory] cited_evidence_tracked: WARN" in out
    assert rc == 0 and "RESULT: PASS" in out


def test_run_advisory_checks_includes_the_check_with_advisory_statuses_only():
    results = dcs.run_advisory_checks("TCK-20990101-NO-SUCH-TICKET", "hotfix")
    by = {r["condition"]: r for r in results}
    assert by["cited_evidence_tracked"]["status"] in {"OK", "WARN", "NA"}
