"""Tests for tools/test_architecture/slow_regression_report.py (TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED).

Proves the mechanism reports a seeded failure and decides the run's verdict: JUnit fixtures go in, a fake client
records what would have been posted to GitHub."""

import datetime as dt
import subprocess
from pathlib import Path

import pytest

from tools.test_architecture import slow_regression_report as srr

TODAY = dt.date(2026, 10, 7)
NOW = dt.datetime(2026, 10, 7, 12, 0, tzinfo=dt.timezone.utc)
WEEK_MARKER = srr.DIGEST_MARKER_FMT.format(week="2026-W41")


def _entry(match, ticket="TCK-X", owner="someone", kind="broken", added="2026-10-01", expires="2026-12-01"):
    return {"match": match, "ticket": ticket, "owner": owner, "added_on": added, "expires_on": expires, "kind": kind}


KNOWN = [
    _entry("tests.perf.test_perf_combat*", "TCK-PERF", "perf-owner"),
    _entry("tests.regression.test_gone*", "TCK-GONE"),
    _entry("tests.old.test_expired*", "TCK-OLD", expires="2026-10-06"),
]
KW = dict(repo="o/r", run_id="111", sha="a" * 40, today=TODAY, now=NOW)
ALL_STEPS = set(srr.EXPECTED_STEPS)


def _issue(body, number=7, user=srr.BOT_LOGIN, labels=(srr.LABEL,), created_at="2026-10-07T01:00:00+00:00"):
    return {"number": number, "body": body, "user_login": user, "labels": list(labels), "created_at": created_at}


class FakeClient:
    def __init__(self, issues=None, comments=None):
        self.issues = issues or []
        self.comment_bodies = [WEEK_MARKER] if comments is None else comments
        self.created = []
        self.updated = []
        self.comments = []
        self.closed = []

    def list_issues(self):
        return self.issues

    def list_comment_bodies(self, number):
        return self.comment_bodies

    def create_issue(self, title, body):
        self.created.append((title, body))

    def update_issue(self, number, title, body):
        self.updated.append((number, title, body))

    def comment(self, number, text):
        self.comments.append((number, text))

    def close_issue(self, number):
        self.closed.append(number)


def _junit(path: Path, cases):
    """cases: (classname, name, kind) with kind in pass|fail|error|skip|xpass."""
    items = []
    for classname, name, kind in cases:
        inner = {
            "pass": "",
            "fail": '<failure message="boom">x</failure>',
            "error": '<error message="boom">x</error>',
            "skip": '<skipped message="xfail"/>',
            "xpass": '<failure message="[XPASS(strict)] why">x</failure>',
        }[kind]
        items.append(f'<testcase classname="{classname}" name="{name}">{inner}</testcase>')
    path.write_text(f'<testsuites><testsuite>{"".join(items)}</testsuite></testsuites>', encoding="utf-8")


def _body(failing, first_seen=None, known=KNOWN):
    return srr.render_body(failing, known, "o/r", "100", "b" * 40, first_seen or {}, TODAY)


def _issue_with(failing, first_seen=None, number=7):
    return _issue(_body(failing, first_seen), number=number)


def _state(client):
    return srr.parse_state(client.updated[-1][2])


def _run(client, failing, steps=ALL_STEPS, known=KNOWN, **extra):
    return srr.run_report(client, failing, steps, known, unmeasured=extra.pop("unmeasured", None), **{**KW, **extra})


MAPPED = "tests.perf.test_perf_combat::test_a"
REAL_KNOWN_REDS = Path(srr.__file__).with_name("slow_known_reds.yaml")
CORPUS = "tests.unit.worldassembly.test_corpus_diversity::test_"


# ── NEW / FIXED / unchanged / closed / first run ─────────────────────────────────────────────


def test_seeded_new_failure_yields_a_new_comment_with_the_test_id():
    previous = {MAPPED: "slow tests"}
    client = FakeClient([_issue_with(previous)])
    result = _run(client, {**previous, "tests.unit.x::test_seeded": "slow tests"})
    assert len(client.comments) == 1
    text = client.comments[0][1]
    assert text.startswith("NEW: ") and "tests.unit.x::test_seeded" in text
    assert "111" in text and "a" * 40 in text
    assert result.exit_code == 1  # that new id matches no entry: UNOWNED


def test_a_new_mapped_red_comments_but_does_not_fail_the_job():
    previous = {MAPPED: "slow tests"}
    client = FakeClient([_issue_with(previous)])
    result = _run(client, {**previous, "tests.perf.test_perf_combat::test_b": "slow tests"})
    assert client.comments[0][1].startswith("NEW: ")
    assert result.exit_code == 0 and result.reasons == []


def test_unchanged_set_posts_no_comment_but_refreshes_last_seen():
    previous = {MAPPED: "slow tests"}
    client = FakeClient([_issue_with(previous)])
    result = _run(client, dict(previous))
    assert client.comments == []
    assert len(client.updated) == 1 and "Last seen: run [111]" in client.updated[0][2]
    assert "unchanged" in result.message


def test_fixed_test_yields_a_fixed_comment():
    previous = {MAPPED: "slow tests", "tests.perf.test_perf_combat::test_b": "slow tests"}
    client = FakeClient([_issue_with(previous)])
    _run(client, {MAPPED: "slow tests"})
    assert len(client.comments) == 1
    assert client.comments[0][1].startswith("FIXED: ") and "test_b" in client.comments[0][1]
    assert client.closed == []


def test_empty_set_closes_the_issue():
    client = FakeClient([_issue_with({MAPPED: "slow tests"})])
    result = _run(client, {})
    assert client.closed == [7]
    assert "FIXED" in client.comments[0][1]
    assert result.exit_code == 0


def test_first_run_creates_the_issue_with_the_full_set_and_posts_no_comments():
    client = FakeClient([])
    failing = {f"tests.perf.test_perf_combat::t{i}": "slow tests" for i in range(16)}
    result = _run(client, failing)
    assert client.comments == []
    assert len(client.created) == 1
    title, body = client.created[0]
    assert title == "Slow regression: 16 failing on main"
    assert srr.TRACKER_MARKER in body
    assert srr.parse_state(body)["failing"] == failing
    assert result.exit_code == 0


def test_nothing_failing_and_no_issue_does_nothing():
    client = FakeClient([])
    result = _run(client, {})
    assert client.created == [] and client.comments == [] and client.closed == []
    assert result.exit_code == 0


# ── known-reds mapping ───────────────────────────────────────────────────────────────────────


def test_unmapped_red_is_flagged_unowned_and_mapped_red_names_its_ticket():
    body = _body({MAPPED: "slow tests", "tests.other::test_b": "slow tests"})
    assert "`TCK-PERF`" in body
    line = next(line for line in body.splitlines() if "tests.other::test_b" in line and line.startswith("- ["))
    assert "**UNOWNED**" in line


def test_mapping_that_is_not_failing_is_listed_as_stale_not_an_error():
    body = _body({MAPPED: "slow tests"})
    assert "Stale mappings" in body and "`tests.regression.test_gone*` — `TCK-GONE`" in body


def test_the_real_known_reds_file_is_loadable_and_lints_clean():
    known = srr.load_known_reds(REAL_KNOWN_REDS)
    assert known
    assert srr.lint_known_reds(known) == []
    assert not any(e["match"].startswith("tests.perf.test_perf_combat") for e in known)  # combat[500] passed


@pytest.mark.parametrize(
    "anchor, ticket",
    [
        ("frontier_marches_seed42_200t_narrative", "TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE"),
        ("frontier_extended_seed42_200t_narrative", "TCK-20261001-FRONTIER-MARCHES-NARRATIVE-ANCHOR-ZERO-SCORE-REBASELINE"),
        ("urban_political_seed42_1000t_social", "TCK-20261007-SIMQ-SOCIAL-ANCHOR-FAMILY-STEP-RISE-BISECT-THEN-REBASELINE"),
        ("unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative", "TCK-20261001-SIMQ-UNIT-SELFMODEL-PILOT-ECONOMY-ANCHOR-REBASELINE"),
        ("simq_routing_test_seed42_1000t_cognition", "TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED"),
    ],
)
def test_real_file_resolves_each_corpus_anchor_to_its_own_entry_not_the_catch_all(anchor, ticket):
    # owner_of() is first-match: a step-change anchor must reach its family entry, a class-(c) one the catch-all.
    known = srr.load_known_reds(REAL_KNOWN_REDS)
    entry = srr.owner_of(f"{CORPUS}{anchor}_grade_stability", known)
    assert entry is not None and entry["ticket"] == ticket
    assert (entry["kind"] == "flaky") == (ticket == "TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED")


def test_real_file_keeps_the_corpus_catch_all_last():
    known = srr.load_known_reds(REAL_KNOWN_REDS)
    assert known[-1]["match"] == "tests.unit.worldassembly.test_corpus_diversity*"
    assert known[-1]["kind"] == "flaky"


def test_lint_rejects_a_bracket_because_fnmatch_reads_it_as_a_character_class():
    exact = "tests.perf.test_perf_movement::test_x[5000]"
    assert srr.owner_of(exact, [_entry(exact)]) is None  # why: the exact id does not match itself
    problems = srr.lint_known_reds([_entry(exact)])
    assert any("'[' is a character class" in p for p in problems), problems
    assert srr.lint_known_reds([_entry("tests.perf.test_perf_movement::test_x?5000?")]) == []


def test_lint_rejects_a_catch_all_placed_before_a_narrower_entry():
    entries = [_entry("tests.unit.x*", "TCK-ALL"), _entry("tests.unit.x::test_one", "TCK-ONE")]
    problems = srr.lint_known_reds(entries)
    assert any("tests.unit.x::test_one: shadowed by the earlier entry 'tests.unit.x*'" in p for p in problems), problems
    assert srr.lint_known_reds(list(reversed(entries))) == []


@pytest.mark.parametrize(
    "mutate, expected",
    [
        (lambda e: e.pop("owner"), "missing owner"),
        (lambda e: e.pop("ticket"), "missing ticket"),
        (lambda e: e.update(expires_on="2026-13-40"), "not an ISO date"),
        (lambda e: e.update(added_on="yesterday"), "not an ISO date"),
        (lambda e: e.update(expires_on="2026-09-01", added_on="2026-10-01"), "expires_on is before added_on"),
        (lambda e: e.update(kind="sometimes"), "kind must be one of"),
    ],
)
def test_lint_rejects_a_bad_entry(mutate, expected):
    entry = _entry("tests.x*")
    mutate(entry)
    problems = srr.lint_known_reds([entry])
    assert any(expected in p for p in problems), problems


def test_expired_entry_lists_under_expired_and_its_failing_tests_count_as_red():
    failing = {"tests.old.test_expired::test_a": "slow tests"}
    body = _body(failing)
    assert "### EXPIRED" in body and "tests.old.test_expired::test_a" in body
    client = FakeClient([_issue_with(failing)])
    result = _run(client, failing)
    assert result.exit_code == 1
    assert any("EXPIRED" in r for r in result.reasons)


def test_an_entry_on_its_expiry_date_is_still_in_date():
    known = [_entry("tests.x*", expires=TODAY.isoformat())]
    assert srr.classify({"tests.x::t": "slow tests"}, known, TODAY) == ([], [])


# ── JUnit parsing and carry-over ─────────────────────────────────────────────────────────────


def test_junit_failure_error_and_strict_xpass_are_red_but_skip_xfail_and_pass_are_not(tmp_path):
    _junit(tmp_path / "slow_tests.xml", [
        ("c", "t_fail", "fail"), ("c", "t_error", "error"), ("c", "t_xpass", "xpass"),
        ("c", "t_skip", "skip"), ("c", "t_ok", "pass"),
    ])
    failing, seen, _measured = srr.parse_junit_dir(tmp_path)
    assert sorted(failing) == ["c::t_error", "c::t_fail", "c::t_xpass"]
    assert seen == {"slow tests"}
    assert set(failing.values()) == {"slow tests"}


def test_per_invocation_corpus_files_map_to_one_step(tmp_path):
    _junit(tmp_path / "corpus_1.xml", [("w", "a", "fail")])
    _junit(tmp_path / "corpus_2.xml", [("w", "b", "pass")])
    _junit(tmp_path / "legacy_regression.xml", [("l", "c", "fail")])
    failing, seen, _measured = srr.parse_junit_dir(tmp_path)
    assert failing == {"w::a": "corpus diversity", "l::c": "legacy regression"}
    assert seen == {"corpus diversity", "legacy regression"}


def test_missing_step_carries_its_failures_over_never_closes_the_issue_and_is_red():
    previous = {"tests.perf.test_perf_combat::a": "corpus diversity", "tests.perf.test_perf_combat::b": "slow tests"}
    client = FakeClient([_issue_with(previous)])
    result = _run(client, {}, steps={"slow tests", "legacy regression"})
    assert client.closed == []
    assert _state(client)["failing"] == {"tests.perf.test_perf_combat::a": "corpus diversity"}
    assert "FIXED: `tests.perf.test_perf_combat::b`" in client.comments[0][1]
    assert "corpus diversity" in client.comments[0][1]
    assert result.exit_code == 1 and any("no JUnit result" in r for r in result.reasons)


def test_truncated_junit_file_counts_as_a_missing_step(tmp_path):
    (tmp_path / "slow_tests.xml").write_text("<testsuites><testsuite>", encoding="utf-8")
    failing, seen, _measured = srr.parse_junit_dir(tmp_path)
    assert failing == {} and seen == set()


def test_unreadable_state_block_refreshes_without_comments():
    client = FakeClient([_issue(srr.TRACKER_MARKER + "\nsomeone edited this by hand")])
    _run(client, {MAPPED: "slow tests"})
    assert client.comments == [] and len(client.updated) == 1


def test_expected_node_ids_map_to_junit_ids():
    assert srr.node_to_junit_id("tests/unit/worldassembly/test_corpus_diversity.py::test_a") == (
        "tests.unit.worldassembly.test_corpus_diversity::test_a"
    )
    assert srr.node_to_junit_id("tests/x/test_y.py::TestC::test_f[p-1]") == "tests.x.test_y.TestC::test_f[p-1]"


def test_expected_anchor_without_a_result_is_neither_fixed_nor_dropped(tmp_path):
    """3 expected anchors, 2 XMLs written; the third (red in the issue) has no result this run."""
    mod = "tests/unit/worldassembly/test_corpus_diversity.py"
    (tmp_path / "corpus_expected.txt").write_text("\n".join(f"{mod}::test_{n}" for n in "abc") + "\n", encoding="utf-8")
    cls = "tests.unit.worldassembly.test_corpus_diversity"
    _junit(tmp_path / "corpus_1.xml", [(cls, "test_a", "pass")])
    _junit(tmp_path / "corpus_2.xml", [(cls, "test_b", "fail")])
    failing, seen, measured = srr.parse_junit_dir(tmp_path)
    unmeasured = srr.load_expected_ids(tmp_path) - measured
    assert unmeasured == {f"{cls}::test_c"}

    known = [_entry("tests.unit.worldassembly.test_corpus_diversity*", "TCK-C", kind="flaky")]
    previous = {f"{cls}::test_b": "corpus diversity", f"{cls}::test_c": "corpus diversity"}
    client = FakeClient([_issue(_body(previous, known=known))])
    result = _run(client, failing, known=known, unmeasured=unmeasured)
    assert client.comments == []  # nothing new, nothing FIXED
    assert _state(client)["failing"] == previous  # test_c carried over, not dropped
    assert client.closed == []
    assert result.exit_code == 1 and any("no result" in r for r in result.reasons)


def test_unmeasured_ids_keep_an_otherwise_empty_issue_open():
    previous = {"tests.perf.test_perf_combat::c": "corpus diversity"}
    client = FakeClient([_issue_with(previous)])
    _run(client, {}, unmeasured={"tests.perf.test_perf_combat::c"})
    assert client.closed == [] and _state(client)["failing"] == previous


# ── rank 1: tracker selection ────────────────────────────────────────────────────────────────


def test_a_human_created_labelled_issue_is_ignored():
    human = _issue(_body({MAPPED: "slow tests"}) , user="a-human")
    client = FakeClient([human])
    _run(client, {MAPPED: "slow tests"})
    assert len(client.created) == 1 and client.updated == []  # a new tracker, the human issue untouched


def test_an_issue_without_the_label_is_ignored():
    client = FakeClient([_issue(_body({MAPPED: "slow tests"}), labels=("other",))])
    _run(client, {MAPPED: "slow tests"})
    assert len(client.created) == 1


def test_two_marked_bot_issues_are_an_error():
    client = FakeClient([_issue_with({MAPPED: "slow tests"}, number=1), _issue_with({MAPPED: "slow tests"}, number=2)])
    with pytest.raises(srr.TrackerError, match="#1, #2"):
        _run(client, {MAPPED: "slow tests"})


def test_an_unmarked_bot_issue_is_not_a_tracker():
    # The legacy-adoption path is gone (issue #390 carries the marker since run 37604139091): a bot-created,
    # labelled issue with a state block but no marker is ignored, and a marked tracker is created instead.
    unmarked = _body({MAPPED: "slow tests"}).replace(srr.TRACKER_MARKER + "\n", "")
    assert srr.TRACKER_MARKER not in unmarked and srr.parse_state(unmarked) is not None
    client = FakeClient([_issue(unmarked, number=390)])
    result = _run(client, {MAPPED: "slow tests"})
    assert client.updated == [] and len(client.created) == 1
    assert srr.TRACKER_MARKER in client.created[0][1]
    assert not result.warnings


def test_the_marked_issue_is_chosen_and_an_unmarked_one_beside_it_is_left_alone():
    unmarked = _body({MAPPED: "slow tests"}).replace(srr.TRACKER_MARKER + "\n", "")
    client = FakeClient([_issue(unmarked, number=1), _issue_with({MAPPED: "slow tests"}, number=2)])
    result = _run(client, {MAPPED: "slow tests"})
    assert [u[0] for u in client.updated] == [2] and client.created == []
    assert not result.warnings


# ── rank 3: digest and first_seen ────────────────────────────────────────────────────────────


def test_digest_is_posted_once_per_iso_week():
    previous = {MAPPED: "slow tests"}
    seen = {MAPPED: "2026-10-07T01:00:00+00:00"}
    client = FakeClient([_issue_with(previous, seen)], comments=[])
    _run(client, dict(previous))
    digests = [c for c in client.comments if WEEK_MARKER in c[1]]
    assert len(digests) == 1
    text = digests[0][1]
    assert "TCK-PERF" in text and "perf-owner" in text and "tracked since" in text and MAPPED in text

    again = FakeClient([_issue_with(previous, seen)], comments=[text])
    _run(again, dict(previous))
    assert [c for c in again.comments if "slow-regression-digest" in c[1]] == []


def test_digest_is_posted_again_in_the_next_week():
    previous = {MAPPED: "slow tests"}
    next_monday = dt.datetime(2026, 10, 12, 3, 0, tzinfo=dt.timezone.utc)
    client = FakeClient([_issue_with(previous)], comments=[WEEK_MARKER])
    srr.run_report(client, dict(previous), ALL_STEPS, KNOWN, "o/r", "112", "c" * 40, today=next_monday.date(), now=next_monday)
    assert any(srr.DIGEST_MARKER_FMT.format(week="2026-W42") in c[1] for c in client.comments)


def test_digest_flags_unowned_and_expired_rows():
    failing = {"tests.old.test_expired::t": "slow tests", "tests.other::u": "slow tests"}
    text = srr.render_digest(failing, KNOWN, {}, TODAY, "2026-W41")
    assert "EXPIRED" in text and "UNOWNED" in text


def test_first_seen_is_carried_forward_and_new_ids_get_the_run_time():
    previous = {MAPPED: "slow tests"}
    seen = {MAPPED: "2026-10-01T00:00:00+00:00"}
    client = FakeClient([_issue_with(previous, seen)])
    failing = {**previous, "tests.perf.test_perf_combat::new": "slow tests"}
    _run(client, failing)
    first_seen = _state(client)["first_seen"]
    assert first_seen[MAPPED] == "2026-10-01T00:00:00+00:00"
    assert first_seen["tests.perf.test_perf_combat::new"] == NOW.isoformat()


def test_a_state_without_first_seen_is_seeded_from_the_issues_created_at():
    previous = {MAPPED: "slow tests"}
    old_style = srr.TRACKER_MARKER + "\n```json\n" + '{"failing": {"%s": "slow tests"}}' % MAPPED + "\n```"
    client = FakeClient([_issue(old_style, created_at="2026-10-07T00:25:00+00:00")])
    _run(client, {**previous, "tests.perf.test_perf_combat::new": "slow tests"})
    first_seen = _state(client)["first_seen"]
    assert first_seen[MAPPED] == "2026-10-07T00:25:00+00:00"
    assert first_seen["tests.perf.test_perf_combat::new"] == NOW.isoformat()


# ── rank 4: exit semantics ───────────────────────────────────────────────────────────────────


def test_every_red_mapped_and_in_date_is_a_green_run_even_though_a_step_failed():
    """The job conclusion comes from the reporter: step outcomes are 'failure' (continue-on-error), the verdict is not."""
    failing = {MAPPED: "slow tests", "tests.perf.test_perf_combat::b": "slow tests"}
    client = FakeClient([_issue_with(failing)])
    result = _run(client, dict(failing))
    assert result.exit_code == 0 and result.reasons == []


def test_a_first_appearance_unowned_red_fails_the_run():
    client = FakeClient([])
    result = _run(client, {"tests.brand.new::t": "slow tests"})
    assert client.created and result.exit_code == 1
    assert any("UNOWNED" in r for r in result.reasons)


class RaisingClient(FakeClient):
    def list_issues(self):
        raise subprocess.CalledProcessError(1, ["gh"], stderr="HTTP 403: Resource not accessible by integration")


def _main(tmp_path, factory, extra=()):
    return srr.main(
        ["--junit-dir", str(tmp_path), "--repo", "o/r", "--run-id", "1", "--sha", "a" * 40, *extra],
        client_factory=factory,
    )


def test_a_github_error_is_not_swallowed(tmp_path, capsys):
    _junit(tmp_path / "slow_tests.xml", [("c", "t", "fail")])
    code = _main(tmp_path, lambda repo: RaisingClient())
    out = capsys.readouterr().out
    assert code == 1
    assert out.startswith("::error title=slow_regression_report::") and "HTTP 403" in out


def test_main_reports_an_ambiguous_tracker_as_an_error(tmp_path, capsys):
    _junit(tmp_path / "slow_tests.xml", [("c", "t", "fail")])
    two = FakeClient([_issue_with({"c::t": "slow tests"}, number=1), _issue_with({"c::t": "slow tests"}, number=2)])
    assert _main(tmp_path, lambda repo: two) == 1
    assert "::error title=slow_regression_report::more than one open tracker" in capsys.readouterr().out


def test_main_exits_zero_when_every_step_ran_and_nothing_fails(tmp_path, capsys):
    for name in ("corpus_1", "slow_tests", "legacy_regression"):
        _junit(tmp_path / f"{name}.xml", [("c", "t", "pass")])
    assert _main(tmp_path, lambda repo: FakeClient([])) == 0


def test_main_fails_on_a_lint_problem_in_the_known_reds_file(tmp_path, capsys):
    bad = tmp_path / "known.yaml"
    bad.write_text("known_reds:\n  - match: 'x*'\n    ticket: TCK-1\n", encoding="utf-8")
    _junit(tmp_path / "slow_tests.xml", [("c", "t", "pass")])
    code = _main(tmp_path, lambda repo: FakeClient([]), extra=["--known-reds", str(bad)])
    assert code == 1 and "::error title=slow_known_reds::" in capsys.readouterr().out
