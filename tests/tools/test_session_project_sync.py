"""TCK-20261112-PROJECT-SYNC-DRY-RUN: the ticket-state Project plan is derived by pure functions from fixtures. No network, no real
repository: git and gh answers are canned."""
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from tools.agent_working_paths import TICKETS
from tools.sessions import project_sync as ps

T = TICKETS.as_posix()
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
CFG = {"pilot_lanes": ["rpg"], "pilot_start": "2026-11-12", "done_window_days": 14, "stale_host_hours": 24}
HOST = "u24desktop"


def copy(tid="TCK-20261112-X", folder="inprogress", title="A title", tier="hotfix", blocked=False, date="2026-11-12"):
    return ps.TicketCopy(tid, folder, f"{T}/{folder}/{tid}.md", title, tier, blocked, date)


def branch(copies, name="rpg-batch", host=HOST, seat="rpg-implementer", domain="rpg"):
    return ps.BranchFact(host, name, f"/wt/{name}", seat, domain, tuple(copies))


def pr(copies, number=7):
    return ps.PrFact(number, f"https://github.com/o/r/pull/{number}", frozenset(c.path for c in copies))


def derive(tid="TCK-20261112-X", main=(), branches=(), prs=(), current=None, host=HOST):
    return ps.derive_item(tid, list(main), list(branches), None if prs is None else list(prs), current, host, "abc123 @ now")


def test_rule1_a_ticket_in_done_on_main_is_done():
    item, _ = derive(main=[copy(folder="done")], branches=[branch([copy()])], prs=[pr([copy()])])
    assert item["Status"] == "Done"


def test_rule2_an_open_pr_that_adds_the_ticket_is_in_review_with_its_url():
    c = copy()
    item, _ = derive(branches=[branch([c])], prs=[pr([c], 12)])
    assert item["Status"] == "In review" and item["PR"] == "https://github.com/o/r/pull/12"


def test_rule3_blocked_in_a_copy_that_exists_only_on_a_branch():
    item, _ = derive(branches=[branch([copy(blocked=True, title="Branch only")])])
    assert item["Status"] == "Blocked" and item["Title"] == "TCK-20261112-X: Branch only" and item["Tier"] == "hotfix"


def test_rule3_blocked_on_main_with_no_branch_copy():
    item, _ = derive(main=[copy(folder="todos", blocked=True)])
    assert item["Status"] == "Blocked"


def test_rule4_a_branch_copy_in_inprogress_is_in_progress_with_seat_and_branch():
    item, _ = derive(branches=[branch([copy()])])
    assert item["Status"] == "In progress" and item["Seat"] == "rpg-implementer" and item["Branch"] == f"{HOST}:rpg-batch"
    assert item["Host"] == HOST and item["Domain"] == "rpg"


def test_rule5_todos_only_is_to_do_and_an_orphaned_inprogress_ticket_is_a_finding():
    item, findings = derive(main=[copy(folder="todos")])
    assert item["Status"] == "To do" and findings == []
    item, findings = derive(main=[copy(folder="inprogress")])
    assert item["Status"] == "To do" and any("orphaned in-progress" in f for f in findings)


def test_a_ticket_in_two_folders_on_main_is_reported_and_takes_the_higher_status():
    item, findings = derive(main=[copy(folder="todos"), copy(folder="done")])
    assert item["Status"] == "Done" and any("two folders" in f for f in findings)


def test_a_squash_merged_branch_never_shows_in_progress():
    item, _ = derive(main=[copy(folder="done")], branches=[branch([copy()])])
    assert item["Status"] == "Done"


def test_filing_a_ticket_in_todos_on_a_branch_is_to_do_not_in_progress():
    item, _ = derive(branches=[branch([copy(folder="todos")])])
    assert item["Status"] == "To do" and item["Branch"] == f"{HOST}:rpg-batch {ps.FILING_SUFFIX}"


def test_an_open_pr_that_adds_a_todos_ticket_is_to_do_not_in_review():
    c = copy(folder="todos")
    item, _ = derive(branches=[branch([c])], prs=[pr([c])])
    assert item["Status"] == "To do" and item["PR"] == ""


def test_an_unrecorded_seat_comes_from_the_branch_prefix_else_unknown():
    assert ps.attribute("rpg-hit-wake", []) == ("rpg (seat not recorded)", "rpg")
    assert ps.attribute("freemeal", []) == ("unknown", "")
    assert ps.attribute("x-y", [("rpg-implementer", "rpg"), ("rpg-planner", "rpg")]) == ("rpg-implementer/rpg-planner", "rpg")


def test_sync_hash_is_stable_ignores_source_and_a_hand_edit_is_reported_then_overwritten():
    item, _ = derive(branches=[branch([copy()])])
    assert item["Sync hash"] == ps.sync_hash({**item, "Source": "other run"})
    assert ps.hand_edits(item, item) == []
    edited = {**item, "Status": "Done"}  # someone moved it by hand; the stored hash no longer matches
    lines = ps.hand_edits(edited, item)
    assert lines == [f"hand edit: TCK-20261112-X Status 'Done' -> 'In progress'"]
    plan = _plan({"TCK-20261112-X": [copy()]}, [branch([copy()])], [edited])
    assert plan.hand_edits == lines and plan.updates and plan.updates[0][1] == ["Status"]
    assert plan.updates[0][0]["Status"] == "In progress"


def _plan(main, branches, items=(), prs=(), done_at=lambda p: None):
    index = {tid: [(c.folder, c.path) for c in cs] for tid, cs in main.items()}
    loaded = {c.path: c for cs in main.values() for c in cs}
    return ps.build_plan(index, lambda p: loaded[p], list(branches), None if prs is None else list(prs), list(items), HOST,
                         "abc @ now", CFG, done_at, NOW)


def test_items_without_an_id_or_without_a_ticket_file_are_archived_and_old_done_items_age_out():
    stray = {"Title": "hand made", "Ticket ID": ""}
    ghost = {"Title": "x", "Ticket ID": "TCK-20260101-GONE"}
    done_item, _ = derive("TCK-20261101-OLD", main=[copy("TCK-20261101-OLD", "done")])
    plan = _plan({"TCK-20261101-OLD": [copy("TCK-20261101-OLD", "done")]}, [], [stray, ghost, done_item],
                 done_at=lambda p: datetime(2026, 11, 1, tzinfo=timezone.utc))
    reasons = dict(plan.archives)
    assert "no Ticket ID" in reasons["hand made"] and "no ticket file" in reasons["TCK-20260101-GONE"]
    assert "Done more than 14 days ago" in reasons["TCK-20261101-OLD"]


def test_a_done_ticket_from_before_the_pilot_gets_no_item_but_one_after_it_does():
    old, new = copy("TCK-OLD-1", "done"), copy("TCK-NEW-1", "done")
    branches = [branch([copy("TCK-OLD-1"), copy("TCK-NEW-1")])]
    dates = {old.path: datetime(2026, 11, 5, tzinfo=timezone.utc), new.path: datetime(2026, 11, 15, tzinfo=timezone.utc)}
    plan = _plan({"TCK-OLD-1": [old], "TCK-NEW-1": [new]}, branches, done_at=dates.get)
    assert [i["Ticket ID"] for i in plan.creates] == ["TCK-NEW-1"]


def test_only_pilot_lane_branches_make_candidates():
    plan = _plan({"TCK-A-1": [copy("TCK-A-1", "todos")]}, [branch([copy("TCK-A-1")], name="eng-x", seat="eng", domain="eng")])
    assert plan.creates == []


def test_a_ticket_in_progress_on_ubuntu_and_in_review_through_a_pr_from_u24_is_in_review_keeping_both_hosts():
    c = copy()
    current, _ = derive(branches=[branch([c], name="rpg-ub", host="ubuntu", seat="rpg-implementer-ubuntu")], host="ubuntu")
    item, _ = derive(main=[], branches=[branch([c])], prs=[pr([c])], current=current)
    assert item["Status"] == "In review"
    assert item["Branch"] == f"{HOST}:rpg-batch, ubuntu:rpg-ub" and item["Host"] == f"{HOST}, ubuntu"
    # the same item with no PR keeps ubuntu's branch as rule-4 evidence even when this host has no branch
    item2, _ = derive(branches=[], prs=[], current=current)
    assert item2["Status"] == "In progress" and item2["Branch"] == "ubuntu:rpg-ub" and item2["Host"] == "ubuntu"


def test_a_filing_entry_from_another_host_is_not_progress_evidence():
    current = {"Branch": f"ubuntu:rpg-x {ps.FILING_SUFFIX}", "Host": "ubuntu"}
    item, _ = derive(main=[copy(folder="todos")], current=current)
    assert item["Status"] == "To do"


def test_apply_and_init_exit_2_when_the_project_number_is_0_and_nothing_runs(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: pytest.fail("a reader ran"))
    for flag in ("--apply", "--init"):
        assert ps.main(["--root", str(tmp_path), flag]) == 2  # no registries/session_project.yaml there: built-in project.number 0
    assert "project.number is 0" in capsys.readouterr().err


def test_flag_combinations_are_refused(monkeypatch, tmp_path):
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: pytest.fail("a reader ran"))
    for argv in (["--init", "--apply"], ["--apply", "--items", "x.json"], ["--replace-status-options"]):
        assert ps.main(["--root", str(tmp_path), *argv]) == 2


@pytest.mark.parametrize("cmd", [
    ["git", "push", "origin", "x"], ["git", "worktree", "remove", "/wt"], ["git", "fetch"], ["git", "checkout", "main"],
    ["gh", "pr", "create"], ["gh", "pr", "merge", "1"], ["gh", "api", "-X", "POST", "repos/o/r/issues"], ["gh", "api", "x", "-f", "a=b"],
    ["rm", "-rf", "/"],
    # joined spellings (P1a): none may slip past by prefix
    ["gh", "api", "--method=POST", "repos/o/r/issues"], ["gh", "api", "-XPOST", "repos/o/r/issues"],
    ["gh", "api", "-X=POST", "repos/o/r/issues"], ["gh", "api", "repos/o/r/issues", "-fk=v"],
    ["gh", "api", "repos/o/r/issues", "--field=k=v"], ["gh", "api", "repos/o/r/issues", "--raw-field=k=v"],
    ["gh", "api", "repos/o/r/issues", "--input=body.json"], ["gh", "api", "repos/o/r/issues", "--unknown-flag"],
    ["gh", "api", "graphql", "-f", "query=mutation{x}"], ["gh", "api", "graphql"], ["gh", "api"], ["gh", "api", "repos/a", "repos/b"],
    ["gh", "api", "repos/o/r/pulls", "--jq"],
])
def test_the_guard_refuses_every_write_verb(cmd):
    with pytest.raises(ps.WriteRefused):
        ps._guard(cmd)


@pytest.mark.parametrize("cmd", [
    ["git", "--no-optional-locks", "status", "--porcelain"], ["git", "ls-tree", "-r", "origin/main"], ["git", "worktree", "list"],
    ["gh", "pr", "list", "--state", "open"], ["gh", "api", "--paginate", "repos/{owner}/{repo}/pulls/1/files"],
    ["gh", "api", "--paginate", "repos/{owner}/{repo}/pulls/1/files", "--jq", ".[].filename"],
    ["gh", "api", "repos/o/r/pulls", "-H", "Accept: application/json", "-q", ".[]"],
])
def test_the_guard_lets_read_verbs_through(cmd):
    ps._guard(cmd)


def fake_runner(answers):
    calls = []

    def run(args, cwd=None):
        calls.append(args)
        key = next((k for k in answers if k in " ".join(args)), None)
        out = answers[key] if key else ""
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    run.calls = calls
    return run


def test_an_uncommitted_ticket_file_in_a_worktree_is_read_from_disk_and_a_committed_one_with_git_show(tmp_path):
    new = f"{T}/inprogress/TCK-20261112-NEW.md"
    committed = f"{T}/inprogress/TCK-20261112-OLD.md"
    (tmp_path / T / "inprogress").mkdir(parents=True)
    (tmp_path / new).write_text("---\ndate: 2026-11-12\n---\n# T\n\n## Title\nNew one\n\n## Tier\nStandard\n\n## Status\nBLOCKED\n")
    run = fake_runner({
        "merge-base": "base123\n",
        "diff --name-status": f"D\t{T}/done/TCK-20260101-GONE.md\nA\tdocs/not_a_ticket.md\n",
        "status --porcelain": f" M {committed}\0?? {new}\0 D {T}/todos/TCK-20260102-DELETED.md\0",
        "show HEAD:": "## Title\nCommitted one\n\n## Tier\nhotfix\n",
    })
    copies = {c.id: c for c in ps._worktree_ticket_copies(tmp_path, run)}
    assert set(copies) == {"TCK-20261112-NEW", "TCK-20261112-OLD"}
    assert copies["TCK-20261112-NEW"].title == "New one" and copies["TCK-20261112-NEW"].blocked and copies["TCK-20261112-NEW"].tier == "standard"
    assert copies["TCK-20261112-OLD"].title == "Committed one" and copies["TCK-20261112-OLD"].folder == "inprogress"
    assert any("--no-optional-locks" in c for c in run.calls)


def test_detached_worktrees_are_skipped_counted_and_reported_when_they_change_a_ticket(tmp_path, monkeypatch):
    entries = [{"worktree": str(tmp_path / "a")}, {"worktree": str(tmp_path / "b"), "branch": "refs/heads/rpg-hit-wake"}]
    infos = {str(tmp_path / "a"): SimpleNamespace(path=tmp_path / "a", branch=None, prunable=False, is_main=False, last_activity=0.0),
             str(tmp_path / "b"): SimpleNamespace(path=tmp_path / "b", branch="rpg-hit-wake", prunable=False, is_main=False, last_activity=0.0)}
    monkeypatch.setattr(ps, "load_roster", lambda root: SimpleNamespace(roles=[]))
    monkeypatch.setattr(ps, "main_checkout", lambda root: tmp_path / "main")
    monkeypatch.setattr(ps.st, "state_root", lambda root: tmp_path / "state")
    monkeypatch.setattr(ps, "worktree_entries", lambda root: entries)
    monkeypatch.setattr(ps, "inspect_worktree", lambda e, main, prr, szr: infos[e["worktree"]])
    monkeypatch.setattr(ps, "_worktree_ticket_copies", lambda wt, run: [copy()])
    notes: list[str] = []
    facts, detached = ps.read_branch_facts(tmp_path, HOST, notes)
    assert detached == 1 and [f.branch for f in facts] == ["rpg-hit-wake"] and facts[0].seat == "rpg (seat not recorded)"
    assert any(n.startswith("unattributed: detached worktree") and "TCK-20261112-X" in n for n in notes)


def test_a_pr_list_that_hits_the_limit_says_some_prs_may_be_missing():
    listing = json.dumps([{"number": i, "url": f"u{i}"} for i in range(ps.PR_LIMIT)])
    notes: list[str] = []
    prs = ps.read_open_prs(Path("."), notes, fake_runner({"pr list": listing, "pulls": f"{T}/inprogress/TCK-A-1.md\nsrc/x.py\n"}))
    assert len(prs) == ps.PR_LIMIT and prs[0].paths == frozenset({f"{T}/inprogress/TCK-A-1.md"})
    assert any("some PRs may be missing" in n for n in notes)


def test_a_failing_gh_skips_rule_2_with_a_note():
    notes: list[str] = []
    run = lambda args, cwd=None: SimpleNamespace(returncode=1, stdout="", stderr="no")  # noqa: E731
    assert ps.read_open_prs(Path("."), notes, run) is None and any("rule 2" in n for n in notes)


def test_the_registry_file_has_the_pilot_settings_and_no_field_ids():
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / ps.CONFIG_REL).read_text(encoding="utf-8"))
    assert cfg["pilot_lanes"] == ["rpg"] and cfg["done_window_days"] == 14 and cfg["stale_host_hours"] == 24
    assert "PVTF" not in json.dumps(cfg, default=str) and "field" not in json.dumps(list(cfg)).lower()


def test_an_unstaged_only_change_with_a_leading_space_is_the_first_porcelain_entry_and_is_kept(tmp_path):
    ticket = f"{T}/done/TCK-20261110-A-NON-FLIGHT-MOVE.md"
    (tmp_path / T / "done").mkdir(parents=True)
    (tmp_path / ticket).write_text("## Title\nNon flight\n")
    run = fake_runner({"merge-base": "b\n", "diff --name-status": "", "status --porcelain": f" M {ticket}\0"})
    assert [c.id for c in ps._worktree_ticket_copies(tmp_path, run)] == ["TCK-20261110-A-NON-FLIGHT-MOVE"]


def test_a_renamed_porcelain_entry_skips_its_source_and_a_real_repo_agrees(tmp_path):
    import subprocess

    def git(*a):
        subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *a], cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / T / "todos").mkdir(parents=True)
    (tmp_path / T / "done").mkdir(parents=True)
    old = tmp_path / T / "todos" / "TCK-20261111-MOVED.md"
    old.write_text("## Title\nMoved\n")
    done = tmp_path / T / "done" / "TCK-20261110-DONE-ONE.md"
    done.write_text("## Title\nDone one\n")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "i")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    done.write_text("## Title\nDone one changed\n")  # unstaged only: ` M` is the first porcelain entry
    git("mv", str(old), str(tmp_path / T / "done" / "TCK-20261111-MOVED.md"))
    copies = {c.id: c.folder for c in ps._worktree_ticket_copies(tmp_path, ps.run_command)}
    assert copies == {"TCK-20261110-DONE-ONE": "done", "TCK-20261111-MOVED": "done"}


def test_seat_names_only_a_branch_that_works_the_ticket_never_one_that_only_filed_it():
    worker = branch([copy()], name="rpg-work", seat="rpg (unmapped)")
    filer = branch([copy(folder="todos")], name="rpg-planner-seat", seat="rpg-planner")
    item, _ = derive(branches=[worker, filer])
    assert item["Seat"] == "rpg (unmapped)" and item["Status"] == "In progress"
    assert f"{HOST}:rpg-planner-seat {ps.FILING_SUFFIX}" in item["Branch"] and f"{HOST}:rpg-work" in item["Branch"]
    todo, _ = derive(branches=[filer])
    assert todo["Status"] == "To do" and todo["Seat"] == ""


# ---------------------------------------------------------------- P1a: seat label, Stale, entry point, host


def test_a_leased_worktree_keeps_its_recorded_seat_over_the_unrecorded_label():
    assert ps.attribute("rpg-x", [("rpg-implementer", "rpg")]) == ("rpg-implementer", "rpg")


DAY = 86400.0
STALE_BEFORE = NOW.timestamp() - 14 * DAY
OLD, FRESH = STALE_BEFORE - DAY, STALE_BEFORE + 5 * DAY


def aged(copies, activity, name="rpg-batch"):
    return ps.BranchFact(HOST, name, f"/wt/{name}", "rpg (seat not recorded)", "rpg", tuple(copies), activity)


def derive_stale(main=(), branches=(), prs=(), current=None):
    return ps.derive_item("TCK-20261112-X", list(main), list(branches), list(prs), current, HOST, "abc @ now", STALE_BEFORE)


def test_a_working_branch_older_than_the_window_is_stale_and_a_fresh_one_is_in_progress():
    assert derive_stale(branches=[aged([copy()], OLD)])[0]["Status"] == "Stale"
    assert derive_stale(branches=[aged([copy()], FRESH)])[0]["Status"] == "In progress"
    assert derive_stale(branches=[aged([copy()], 0.0)])[0]["Status"] == "In progress"  # unknown age is never stale


def test_one_fresh_working_branch_keeps_the_ticket_in_progress():
    both = [aged([copy()], OLD, "rpg-old"), aged([copy()], FRESH, "rpg-new")]
    assert derive_stale(branches=both)[0]["Status"] == "In progress"


def test_a_stale_branch_with_an_open_pr_stays_in_review_and_a_blocked_ticket_stays_blocked():
    c = copy()
    assert derive_stale(branches=[aged([c], OLD)], prs=[pr([c])])[0]["Status"] == "In review"
    assert derive_stale(branches=[aged([copy(blocked=True)], OLD)])[0]["Status"] == "Blocked"


def test_a_fresh_filing_branch_does_not_keep_an_abandoned_working_branch_in_progress():
    filing = aged([copy(folder="todos")], FRESH, "rpg-filing")
    assert derive_stale(branches=[aged([copy()], OLD), filing])[0]["Status"] == "Stale"


def test_a_fresh_entry_from_another_host_keeps_a_stale_local_branch_in_progress():
    current = {"Branch": "ubuntu:rpg-other"}
    assert derive_stale(branches=[aged([copy()], OLD)], current=current)[0]["Status"] == "In progress"


def test_the_file_runs_as_a_script(tmp_path):
    import subprocess
    import sys
    script = Path(ps.__file__)
    out = subprocess.run([sys.executable, str(script), "--help"], cwd=tmp_path, capture_output=True, text=True, check=False)
    assert out.returncode == 0 and "dry run" in out.stdout.lower()


def test_the_host_default_comes_from_the_host_names_map_else_the_hostname(monkeypatch, capsys, tmp_path):
    seen = []
    monkeypatch.setattr(ps, "read_branch_facts", lambda root, host, notes, run=None: (seen.append(host) or [], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: [])
    monkeypatch.setattr(ps, "read_main_index", lambda root, run=None, ref="origin/main": {})
    monkeypatch.setattr(ps, "origin_info", lambda root, run=None, ref="origin/main": ("0" * 40, None))
    (tmp_path / "registries").mkdir()
    (tmp_path / ps.CONFIG_REL).write_text("host_names:\n  big-host-name: short\n", encoding="utf-8")
    for hostname, expected in (("big-host-name", "short"), ("other", "other")):
        monkeypatch.setattr(ps.socket, "gethostname", lambda h=hostname: h)
        assert ps.main(["--root", str(tmp_path)]) == 0
        assert seen[-1] == expected
    capsys.readouterr()


def test_the_registry_file_maps_this_hosts_long_name_and_sets_the_stale_window():
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / ps.CONFIG_REL).read_text(encoding="utf-8"))
    assert cfg["stale_branch_days"] == 14 and cfg["host_names"]["u24desktop-Virtual-Machine"] == "u24desktop"


def test_two_items_without_an_id_and_one_title_are_both_archived_by_their_own_ids():
    a = {"Title": "hand made", "Ticket ID": "", "_item_id": "I1"}
    b = {"Title": "hand made", "Ticket ID": "", "_item_id": "I2"}
    plan = _plan({}, [], [a, b])
    assert plan.archives == [("hand made", "no Ticket ID")] * 2 and plan.archive_item_ids == ["I1", "I2"]


def test_a_duplicate_ticket_id_keeps_one_item_and_archives_the_other():
    c = copy("TCK-20261112-DUP", "inprogress")
    derived, _ = derive("TCK-20261112-DUP", main=[c], branches=[branch([c])])
    matching = {**derived, "_item_id": "GOOD"}
    stale = {**derived, "Sync hash": "not-the-hash", "Status": "Blocked", "_item_id": "BAD"}
    plan = _plan({"TCK-20261112-DUP": [c]}, [branch([c])], [stale, matching])
    assert plan.archives == [("TCK-20261112-DUP", "duplicate Ticket ID")] and plan.archive_item_ids == ["BAD"]
    assert any("duplicate Ticket ID" in f for f in plan.findings) and not plan.updates


def test_done_item_on_the_board_with_an_unreadable_done_date_gets_a_note():
    c = copy("TCK-20261112-D", "done")
    item, _ = derive("TCK-20261112-D", main=[c])
    plan = _plan({"TCK-20261112-D": [c]}, [], [item], done_at=lambda p: None)
    assert "done date unreadable: TCK-20261112-D" in plan.notes and not plan.updates and not plan.archives


def test_updates_carry_the_live_item_and_draft_ids():
    c = copy("TCK-20261112-U", "inprogress")
    derived, _ = derive("TCK-20261112-U", main=[c], branches=[branch([c])])
    live = {**derived, "Status": "To do", "_item_id": "ITEM", "_draft_id": "DRAFT"}
    plan = _plan({"TCK-20261112-U": [c]}, [branch([c])], [live])
    assert plan.updates[0][0]["_item_id"] == "ITEM" and plan.updates[0][0]["_draft_id"] == "DRAFT"


def test_a_failed_per_pr_files_call_marks_the_pr_list_incomplete_and_notes_it():
    listing = json.dumps([{"number": 7, "url": "u7"}])
    def run(args, cwd):
        return SimpleNamespace(returncode=1 if "pulls" in " ".join(args) else 0, stdout=listing if "list" in args else "", stderr="")
    notes = []
    prs = ps.read_open_prs(Path("."), notes, run)
    assert prs is not None and prs.complete is False and len(prs) == 1 and any("PR #7" in n for n in notes)


@pytest.mark.parametrize("prs", [None, ps.PrList()])
def test_apply_is_refused_with_nothing_written_when_the_open_prs_are_not_fully_known(monkeypatch, tmp_path, capsys, prs):
    from tools.sessions import project_client as pc
    if prs is not None:
        prs.complete = False
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "session_project.yaml").write_text("project: {owner: o, number: 1}\n")
    monkeypatch.setattr(ps, "_client", lambda cfg, notes=None: SimpleNamespace(list_items=lambda: [], load_project=lambda: pytest.fail("wrote")))
    monkeypatch.setattr(ps, "origin_info", lambda root: ("abc", None))
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: ([], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: prs)
    monkeypatch.setattr(pc, "apply_plan", lambda *a, **k: pytest.fail("wrote"))
    assert ps.main(["--root", str(tmp_path), "--apply"]) == 1
    assert "nothing written" in capsys.readouterr().err


# ---- P1c: Layer, Priority, Epic, Tags
TICKET_TEXT = """---
status: active
layer: combat
tags: [zeta, combat, unknownthing]
---

# X

## Title
A title

## Tier
standard

## Priority
P1
"""


def test_parse_copy_reads_layer_priority_and_tags():
    c = ps.parse_copy(f"{T}/inprogress/TCK-20261114-A.md", TICKET_TEXT)
    assert (c.layer, c.priority, c.tags) == ("combat", "P1", ("zeta", "combat", "unknownthing"))


def test_layer_priority_and_tags_are_validated_ordered_and_empty_or_unknown_values_give_a_finding():
    c = ps.TicketCopy("TCK-20261114-A", "inprogress", f"{T}/inprogress/TCK-20261114-A.md", "t", "hotfix", layer="nolayer", priority="P9",
                      tags=("zeta", "combat", "unknownthing"))
    extras = ps.Extras(frozenset({"combat"}), ("combat", "zeta"), None)
    item, findings = ps.derive_item("TCK-20261114-A", [c], [], None, None, HOST, "s", None, extras)
    assert item["Layer"] == "" and item["Priority"] == "" and item["Tags"] == "combat zeta unknownthing"  # registry order, unknown last
    assert any("layer 'nolayer'" in f for f in findings) and any("priority 'P9'" in f for f in findings) and any("unknownthing" in f for f in findings)
    ok = ps.TicketCopy("TCK-20261114-A", "inprogress", c.path, "t", "hotfix", layer="combat", priority="P2")
    item, findings = ps.derive_item("TCK-20261114-A", [ok], [], None, None, HOST, "s", None, extras)
    assert (item["Layer"], item["Priority"]) == ("combat", "P2") and not [f for f in findings if "layer" in f or "priority" in f]


def _epic_world():
    def tk(tid, state, folder, tier="hotfix"):
        path = f"{T}/{state}/{folder}/{tid}.md" if folder else f"{T}/{state}/{tid}.md"
        return ps.TicketCopy(tid, state, path, "t", tier)
    copies = [tk("TCK-20261101-SOMETHING-EPIC", "todos", "grp", "epic"), tk("TCK-20261101-CHILD", "todos", "grp"),
              tk("TCK-20261102-NOEPIC-CHILD", "done", "bare"), tk("TCK-20261103-FLAT", "done", None), tk("TCK-20261104-TWICE", "done", None)]
    index = {c.id: [(c.folder, c.path)] for c in copies}
    loaded = {c.path: c for c in copies}
    seqs = {"todos/grp": {"TCK-20261103-FLAT", "TCK-20261104-TWICE"}, "done/other": {"TCK-20261104-TWICE"}}
    return copies, ps.make_epic_resolver(index, lambda p: loaded[p], seqs)


def test_epic_rule_a_uses_the_folders_tier_epic_ticket_or_the_folder_name_and_an_epic_is_its_own_epic():
    copies, resolve = _epic_world()
    by = {c.id: c for c in copies}
    assert resolve("TCK-20261101-CHILD", by["TCK-20261101-CHILD"].path, "hotfix") == ("TCK-20261101-SOMETHING-EPIC", [])  # name need not contain -EPIC-
    assert resolve("TCK-20261101-SOMETHING-EPIC", by["TCK-20261101-SOMETHING-EPIC"].path, "epic") == ("TCK-20261101-SOMETHING-EPIC", [])
    assert resolve("TCK-20261102-NOEPIC-CHILD", by["TCK-20261102-NOEPIC-CHILD"].path, "hotfix") == ("bare", [])  # done/<folder>/, no epic -> folder name


def test_epic_rule_b_sequence_md_links_a_flat_ticket_and_an_ambiguous_one_is_standalone_with_a_note():
    copies, resolve = _epic_world()
    by = {c.id: c for c in copies}
    assert resolve("TCK-20261103-FLAT", by["TCK-20261103-FLAT"].path, "hotfix") == ("TCK-20261101-SOMETHING-EPIC", [])
    value, notes = resolve("TCK-20261104-TWICE", by["TCK-20261104-TWICE"].path, "hotfix")
    assert value == "standalone" and "todos/grp" in notes[0] and "done/other" in notes[0]


def test_epic_rule_c_is_standalone_and_sequence_ids_come_from_order_or_anywhere():
    _, resolve = _epic_world()
    assert resolve("TCK-20261199-NONE", f"{T}/inprogress/TCK-20261199-NONE.md", "hotfix") == ("standalone", [])
    assert ps.sequence_ids("# S\n\n## Order\n1. TCK-20261101-A\n\n## Notes\nTCK-20261102-B\n") == {"TCK-20261101-A"}
    assert ps.sequence_ids("# S\n\n## Dependency Notes\n- TCK-20261101-A then TCK-20261102-B\n") == {"TCK-20261101-A", "TCK-20261102-B"}


def test_a_p1_hash_is_not_a_hand_edit_it_is_updated_once_and_carries_v2():
    c = copy("TCK-20261112-M", "inprogress")
    derived, _ = derive("TCK-20261112-M", main=[c], branches=[branch([c])])
    v1_fields = {k: v for k, v in derived.items() if k in ps.HASH_FIELDS_V1}
    live = {**v1_fields, "Sync hash": ps.sync_hash(v1_fields, "v1"), "_item_id": "I", "_draft_id": "D"}
    assert ps.hand_edits(live, derived) == [] and not ps.sync_hash(v1_fields, "v1").startswith("v2:")
    plan = _plan({"TCK-20261112-M": [c]}, [branch([c])], [live])
    assert plan.hand_edits == [] and plan.updates and plan.updates[0][0]["Sync hash"].startswith("v2:")
    # a v2 value is checked against the v2 fields only
    v2 = {**derived, "Sync hash": derived["Sync hash"], "_item_id": "I"}
    assert ps.hand_edits(v2, derived) == []
    assert ps.hand_edits({**v2, "Layer": "tampered"}, derived)


def test_a_priority_with_trailing_explanation_takes_its_leading_p_value():
    c = ps.TicketCopy("TCK-20261114-A", "inprogress", f"{T}/inprogress/TCK-20261114-A.md", "t", "hotfix", priority="P2 (RAISED FROM P3 BY SOMEONE)")
    item, _ = ps.derive_item("TCK-20261114-A", [c], [], None, None, HOST, "s", None, ps.Extras())
    assert item["Priority"] == "P2"
