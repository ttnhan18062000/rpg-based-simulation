"""TCK-20261001-POST-MERGE-MAIN-INTEGRITY-REPORT: one planted defect per check on a fixture ref, a clean
ref reporting nothing, and a dirty working tree proving the tool reads the ref, not the tree.
Every fixture is a throwaway git repo under tmp_path."""
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

_TOOLS = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
sys.path.insert(0, str(_TOOLS))

import main_integrity_report as mir  # noqa: E402

TODAY = date(2026, 10, 1)  # ISO week 2026-W39 is finished, 2026-W40 is not
CSV_HEADER = "timestamp,ticket_id,title,status,summary,artifacts_path\n"


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)})


def _w(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _clean_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _w(repo, "tickets/done/TCK-20260920-GOOD.md", "# t\n\nEvidence: `stored_artifacts/TCK-20260920-GOOD/plan.md`\n")
    _w(repo, "stored_artifacts/TCK-20260920-GOOD/plan.md", "plan\n")
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n")
    _w(repo, "agent-monitoring/data/2026-W39/runs.jsonl", json.dumps({"run_id": "R1", "start_ts": "2026-09-22T10:00:00Z", "final_status": "DONE"}) + "\n")
    _w(repo, "agent-monitoring/data/2026-W39/events.jsonl", json.dumps({"run_id": "R1", "seq": 1, "ts": "2026-09-22T10:01:00Z"}) + "\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "clean")
    return repo


def _report(repo, **kw):
    return mir.build_report("HEAD", repo, today=TODAY, **kw)


def test_clean_ref_reports_nothing(tmp_path):
    repo = _clean_repo(tmp_path)
    report = _report(repo)
    assert report["total"] == 0 and all(v == [] for v in report["findings"].values())
    assert "RESULT: clean" in mir.render(report, 20)
    assert report["sha"] in mir.render(report, 20)  # labelled as a snapshot of the ref and SHA


def test_each_planted_defect_is_reported_with_its_ticket_or_path(tmp_path):
    repo = _clean_repo(tmp_path)
    # working_log: a closed ticket with no row, and one with two rows
    _w(repo, "tickets/done/TCK-20260921-NOROW.md", "# t\n")
    _w(repo, "tickets/done/TCK-20260922-TWOROWS.md", "# t\n")
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n"
       "2026-09-22T00:00:00Z,TCK-20260922-TWOROWS,t,DONE,s,\n2026-09-22T01:00:00Z,TCK-20260922-TWOROWS,t,DONE,s,\n")
    # shards: a leftover per-batch shard in a finished week, and one in the current week (not reported)
    _w(repo, "agent-monitoring/data/2026-W39/b1.tools.jsonl", "{}\n")
    _w(repo, "agent-monitoring/data/2026-W40/b2.tools.jsonl", "{}\n")
    # cited evidence: a ticket citing a path that is not at the ref (the gitignored .json case)
    _w(repo, "tickets/done/TCK-20260923-CITES.md", "# t\n\n`stored_artifacts/TCK-20260923-CITES/evidence.json`\n")
    # event seq: duplicate seq for a run
    _w(repo, "agent-monitoring/data/2026-W39/events.jsonl",
       json.dumps({"run_id": "R1", "seq": 1}) + "\n" + json.dumps({"run_id": "R1", "seq": 1}) + "\n")
    # duplicate runs: three identical-outcome records of one execution beyond the ratchet ceiling
    dup = {"run_id": "TCK-D", "execution_id": "e1", "start_ts": "2026-09-22T10:00:00Z", "end_ts": "2026-09-22T10:05:00Z",
           "workflow": "implement-ticket", "tier": "standard", "final_status": "DONE", "agent_count": 3}
    dup2 = {**dup, "run_id": "TCK-D2", "execution_id": "e2"}
    _w(repo, "agent-monitoring/data/2026-W39/runs.jsonl", "".join(json.dumps(r) + "\n" for r in (dup, dup, dup2, dup2)))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "planted")
    f = _report(repo)["findings"]
    assert any("TCK-20260921-NOROW: no DONE working-log row" in x for x in f["working_log"])
    assert any("TCK-20260922-TWOROWS: 1 identical duplicate" in x for x in f["working_log"])
    assert not any("GOOD" in x for x in f["working_log"])
    assert [x for x in f["shards"] if "b1.tools.jsonl" in x] and not any("W40" in x for x in f["shards"])
    assert any("TCK-20260923-CITES" in x and "evidence.json" in x for x in f["cited_evidence"])
    assert any(x == "R1: duplicate event seq" for x in f["event_seq"])
    assert f["duplicate_runs"], f


def test_working_tree_is_never_read_a_dirty_tree_does_not_change_a_clean_ref_report(tmp_path):
    repo = _clean_repo(tmp_path)
    before = _report(repo)
    # dirty the tree: delete a tracked file, edit the CSV, add an untracked closed ticket and a shard
    (repo / "stored_artifacts/TCK-20260920-GOOD/plan.md").unlink()
    _w(repo, "tickets/working_log.csv", CSV_HEADER)
    _w(repo, "tickets/done/TCK-20260925-UNTRACKED.md", "# t\n")
    _w(repo, "agent-monitoring/data/2026-W39/dirty.runs.jsonl", "{}\n")
    assert _report(repo) == before and before["total"] == 0


def test_cli_exits_zero_by_default_and_nonzero_only_with_strict(tmp_path):
    repo = _clean_repo(tmp_path)
    _w(repo, "tickets/done/TCK-20260921-NOROW.md", "# t\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "defect")
    # the CLI is anchored to this checkout's REPO_ROOT, so exercise main() against the fixture repo
    mir.REPO_ROOT = repo
    try:
        assert mir.main(["--ref", "HEAD", "--today", "2026-10-01"]) == 0
        assert mir.main(["--ref", "HEAD", "--today", "2026-10-01", "--strict"]) == 1
    finally:
        mir.REPO_ROOT = Path(mir.__file__).resolve().parent.parent.parent


def test_since_date_limits_ticket_checks(tmp_path):
    repo = _clean_repo(tmp_path)
    _w(repo, "tickets/done/TCK-20260101-OLD.md", "# t\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "old")
    assert any("TCK-20260101-OLD" in x for x in _report(repo)["findings"]["working_log"])
    assert _report(repo, since_date="20260901")["findings"]["working_log"] == []


# --- positive controls for the false-positive shapes found in review of the first reading ---

def test_progress_rows_before_the_closing_done_row_are_not_a_finding(tmp_path):
    repo = _clean_repo(tmp_path)
    _w(repo, "tickets/done/TCK-20260924-PROGRESS.md", "# t\n")
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n"
       "2026-09-24T00:00:00Z,TCK-20260924-PROGRESS,t,BLOCKED,first block,\n2026-09-24T01:00:00Z,TCK-20260924-PROGRESS,t,BLOCKED,second block,\n"
       "2026-09-24T02:00:00Z,TCK-20260924-PROGRESS,t,DONE,s,\n"
       "2026-09-25T02:00:00Z,TCK-20260924-PROGRESS,fix round 2,DONE,s2,\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "progress rows")
    assert _report(repo)["findings"]["working_log"] == []
    # control: the same ticket with only BLOCKED rows IS reported (no closing DONE row)
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n"
       "2026-09-24T00:00:00Z,TCK-20260924-PROGRESS,t,BLOCKED,s,\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "no done row")
    assert any("TCK-20260924-PROGRESS: no DONE" in x for x in _report(repo)["findings"]["working_log"])


def test_a_cited_path_with_a_line_suffix_is_checked_as_the_file_not_reported(tmp_path):
    repo = _clean_repo(tmp_path)
    _w(repo, "tickets/done/TCK-20260926-LINECITE.md", "# t\n\nSee `stored_artifacts/TCK-20260920-GOOD/plan.md:199` and `stored_artifacts/TCK-20260920-GOOD/plan.md:10-20`.\n")
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n"
       "2026-09-26T00:00:00Z,TCK-20260926-LINECITE,t,DONE,s,\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "line cite")
    assert _report(repo)["findings"]["cited_evidence"] == []
    # control: a line suffix on a file that really is absent is still reported, under the stripped name
    _w(repo, "tickets/done/TCK-20260926-LINECITE.md", "# t\n\n`stored_artifacts/TCK-20260920-GOOD/missing.md:5`\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "absent file with line")
    assert any("missing.md, which does not exist" in x for x in _report(repo)["findings"]["cited_evidence"])


def test_a_bare_directory_citation_is_skipped_but_a_missing_file_is_not(tmp_path):
    repo = _clean_repo(tmp_path)
    _w(repo, "tickets/done/TCK-20260927-DIRCITE.md", "# t\n\n`stored_artifacts/TCK-20260927-FIRST-WAVE/` and `stored_artifacts/TCK-20260927-DIRCITE/evidence.json`\n")
    _w(repo, "tickets/working_log.csv", CSV_HEADER + "2026-09-20T00:00:00Z,TCK-20260920-GOOD,t,DONE,s,\n"
       "2026-09-27T00:00:00Z,TCK-20260927-DIRCITE,t,DONE,s,\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "dir cite")
    findings = _report(repo)["findings"]["cited_evidence"]
    assert len(findings) == 1 and "evidence.json" in findings[0] and "FIRST-WAVE" not in findings[0]
