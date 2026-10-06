"""Tests for tools/test_architecture/slow_regression_report.py (TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED).

Proves the mechanism reports a seeded failure: JUnit fixtures go in, a fake client records what would
have been posted to GitHub."""

from pathlib import Path

from tools.test_architecture import slow_regression_report as srr

KNOWN = [
    {"match": "tests.perf.test_perf_combat*", "ticket": "TCK-PERF"},
    {"match": "tests.regression.test_gone*", "ticket": "TCK-GONE"},
]
ARGS = dict(repo="o/r", run_id="111", sha="a" * 40)
ALL_STEPS = set(srr.EXPECTED_STEPS)


class FakeClient:
    def __init__(self, issue=None):
        self.issue = issue
        self.created = []
        self.updated = []
        self.comments = []
        self.closed = []

    def find_open_issue(self):
        return self.issue

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


def _issue_with(failing, number=7):
    body = srr.render_body(failing, KNOWN, "o/r", "100", "b" * 40)
    return {"number": number, "body": body}


def _state(client):
    return srr.parse_state(client.updated[-1][2])


def test_seeded_new_failure_yields_a_new_comment_with_the_test_id():
    previous = {"tests.perf.test_perf_combat::test_a": "slow tests"}
    client = FakeClient(_issue_with(previous))
    failing = {**previous, "tests.unit.x::test_seeded": "slow tests"}
    srr.run_report(client, failing, ALL_STEPS, KNOWN, **ARGS)
    assert len(client.comments) == 1
    text = client.comments[0][1]
    assert text.startswith("NEW: ") and "tests.unit.x::test_seeded" in text
    assert "111" in text and "a" * 40 in text


def test_unchanged_set_posts_no_comment_but_refreshes_last_seen():
    previous = {"tests.perf.test_perf_combat::test_a": "slow tests"}
    client = FakeClient(_issue_with(previous))
    message = srr.run_report(client, dict(previous), ALL_STEPS, KNOWN, **ARGS)
    assert client.comments == []
    assert len(client.updated) == 1 and "Last seen: run [111]" in client.updated[0][2]
    assert "unchanged" in message


def test_fixed_test_yields_a_fixed_comment():
    previous = {"tests.a::t1": "slow tests", "tests.a::t2": "slow tests"}
    client = FakeClient(_issue_with(previous))
    srr.run_report(client, {"tests.a::t1": "slow tests"}, ALL_STEPS, KNOWN, **ARGS)
    assert len(client.comments) == 1
    assert client.comments[0][1].startswith("FIXED: ") and "tests.a::t2" in client.comments[0][1]
    assert client.closed == []


def test_empty_set_closes_the_issue():
    client = FakeClient(_issue_with({"tests.a::t1": "slow tests"}))
    srr.run_report(client, {}, ALL_STEPS, KNOWN, **ARGS)
    assert client.closed == [7]
    assert "FIXED" in client.comments[0][1]


def test_unmapped_red_is_flagged_unowned_and_mapped_red_names_its_ticket():
    body = srr.render_body(
        {"tests.perf.test_perf_combat::test_a": "slow tests", "tests.other::test_b": "slow tests"},
        KNOWN, "o/r", "111", "a" * 40,
    )
    assert "`TCK-PERF`" in body
    line = next(line for line in body.splitlines() if "tests.other::test_b" in line and line.startswith("- ["))
    assert "**UNOWNED**" in line


def test_first_run_creates_the_issue_with_the_full_set_and_posts_no_comments():
    client = FakeClient(issue=None)
    failing = {f"tests.a::t{i}": "slow tests" for i in range(16)}
    srr.run_report(client, failing, ALL_STEPS, KNOWN, **ARGS)
    assert client.comments == []
    assert len(client.created) == 1
    title, body = client.created[0]
    assert title == "Slow regression: 16 failing on main"
    assert srr.parse_state(body) == failing


def test_nothing_failing_and_no_issue_does_nothing():
    client = FakeClient(issue=None)
    srr.run_report(client, {}, ALL_STEPS, KNOWN, **ARGS)
    assert client.created == [] and client.comments == [] and client.closed == []


def test_mapping_that_is_not_failing_is_listed_as_stale_not_an_error():
    body = srr.render_body({"tests.perf.test_perf_combat::test_a": "slow tests"}, KNOWN, "o/r", "1", "a" * 40)
    assert "Stale mappings" in body and "`tests.regression.test_gone*` — `TCK-GONE`" in body


def test_junit_failure_error_and_strict_xpass_are_red_but_skip_xfail_and_pass_are_not(tmp_path):
    _junit(tmp_path / "slow_tests.xml", [
        ("c", "t_fail", "fail"), ("c", "t_error", "error"), ("c", "t_xpass", "xpass"),
        ("c", "t_skip", "skip"), ("c", "t_ok", "pass"),
    ])
    failing, seen = srr.parse_junit_dir(tmp_path)
    assert sorted(failing) == ["c::t_error", "c::t_fail", "c::t_xpass"]
    assert seen == {"slow tests"}
    assert set(failing.values()) == {"slow tests"}


def test_per_invocation_corpus_files_map_to_one_step(tmp_path):
    _junit(tmp_path / "corpus_1.xml", [("w", "a", "fail")])
    _junit(tmp_path / "corpus_2.xml", [("w", "b", "pass")])
    _junit(tmp_path / "legacy_regression.xml", [("l", "c", "fail")])
    failing, seen = srr.parse_junit_dir(tmp_path)
    assert failing == {"w::a": "corpus diversity", "l::c": "legacy regression"}
    assert seen == {"corpus diversity", "legacy regression"}


def test_missing_step_carries_its_failures_over_and_never_closes_the_issue():
    previous = {"w::a": "corpus diversity", "c::b": "slow tests"}
    client = FakeClient(_issue_with(previous))
    # The corpus step wrote no JUnit file this run, the others ran and are clean.
    srr.run_report(client, {}, {"slow tests", "legacy regression"}, KNOWN, **ARGS)
    assert client.closed == []
    assert _state(client) == {"w::a": "corpus diversity"}
    assert "FIXED: `c::b`" in client.comments[0][1]
    assert "corpus diversity" in client.comments[0][1]


def test_truncated_junit_file_counts_as_a_missing_step(tmp_path):
    (tmp_path / "slow_tests.xml").write_text("<testsuites><testsuite>", encoding="utf-8")
    failing, seen = srr.parse_junit_dir(tmp_path)
    assert failing == {} and seen == set()


def test_unreadable_state_block_refreshes_without_comments():
    client = FakeClient({"number": 3, "body": "someone edited this by hand"})
    srr.run_report(client, {"w::a": "slow tests"}, ALL_STEPS, KNOWN, **ARGS)
    assert client.comments == [] and len(client.updated) == 1


def test_known_reds_file_is_loadable_and_every_entry_has_a_ticket():
    known = srr.load_known_reds(Path(srr.__file__).with_name("slow_known_reds.yaml"))
    assert known and all(e["match"] and e["ticket"].startswith("TCK-") for e in known)
