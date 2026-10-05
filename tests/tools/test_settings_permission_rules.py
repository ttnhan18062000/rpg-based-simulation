"""Rule-test harness for the authority-class `ask`/`deny` permission rules in `.claude/settings.json`
(TCK-20261004-SESSION-LAYER-M5A-AUTHORITY-PERMISSION-RULES).

The harness applies each `Bash(<glob>)` rule to fixture commands with a plain `*` wildcard match
(a stand-in for the harness's matcher: it proves what each pattern's text covers, not how the
harness evaluates compound commands). Every authority class has a command that must match and
near-miss commands that must not, so a rule cannot silently drift to cover read-only work.
"""
import json
import re
from pathlib import Path

_SETTINGS_PATH = Path(__file__).parent.parent.parent / ".claude" / "settings.json"


def _rules(kind):
    permissions = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))["permissions"]
    out = []
    for rule in permissions.get(kind, []):
        match = re.fullmatch(r"Bash\((.*)\)", rule)
        if not match:
            continue  # a bare tool-name rule such as "Workflow"; covered by its own test below
        out.append(re.compile("^" + ".*".join(re.escape(part) for part in match.group(1).split("*")) + "$"))
    return out


def _hits(kind, command):
    return any(rule.match(command) for rule in _rules(kind))


MUST_ASK = {
    "merge": ["gh pr merge 5", "gh pr merge 5 --squash"],
    # `git push origin :branch` has no permission rule: the harness reads `Bash(git push * :*)` as a literal
    # prefix (it warns and never matches), so that form is covered by the guard hook (see test_session_classify.py).
    "remote branch deletion": [
        "git push origin --delete old-branch",
        "git push --delete origin old-branch",
        "gh api -X DELETE repos/o/r/git/refs/heads/old",
        "gh api --method DELETE repos/o/r/git/refs/heads/old",
    ],
    "force push": [
        "git push --force",
        "git push origin main --force-with-lease",
        "git push -f origin main",
    ],
    "worktree removal": ["git worktree remove ../other"],
    "shard removal": ["rm -f agent-working/agent-monitoring/data/2026-W41/x.runs.jsonl"],
}

MUST_NOT_ASK = [
    "git status",
    "git push origin feature-fix",
    "git push -u origin agent-working-next-4",
    "git push --dry-run origin main",
    "git push origin HEAD:refs/heads/agent-working-next-4",
    "gh pr view 5",
    "gh pr list",
    "gh pr checks 5",
    "gh api repos/o/r/pulls/5",
    "git worktree list",
    "rm -rf data/runs/some_run",
    "ls agent-working/agent-monitoring",
]


def test_each_authority_class_has_a_matching_ask_rule():
    for authority_class, commands in MUST_ASK.items():
        for command in commands:
            assert _hits("ask", command), f"{authority_class}: {command!r} is not covered by an ask rule"


def test_near_miss_read_only_commands_are_not_caught():
    for command in MUST_NOT_ASK:
        assert not _hits("ask", command), f"{command!r} must not be asked"
        assert not _hits("deny", command), f"{command!r} must not be denied"


def test_admin_merge_is_denied_and_plain_merge_is_not():
    assert _hits("deny", "gh pr merge 5 --admin")
    assert _hits("deny", "gh pr merge 5 --squash --admin")
    assert not _hits("deny", "gh pr merge 5")
    assert not _hits("deny", "gh pr merge 5 --squash")


def test_no_authority_rule_widens_the_allow_list():
    permissions = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))["permissions"]
    for rule in permissions["ask"] + permissions["deny"]:
        assert rule not in permissions["allow"], rule


def test_data_runs_removal_has_no_ask_rule_by_owner_decision():
    # Owner decision 2026-10-05: no ask rule for data/runs removal (the close-out uses it).
    assert not _hits("ask", "rm -rf data/runs/some_run")
    assert not _hits("ask", "rm -rf reports/release_proof/some_run")


# The three gaps the first version of this harness found were closed by the owner-approved corrected
# patterns (2026-10-05, confirmed directly in the implementer terminal).
def test_force_push_with_trailing_f_flag_is_asked():
    assert _hits("ask", "git push origin main -f")


def test_admin_flag_directly_after_merge_is_denied():
    assert _hits("deny", "gh pr merge --admin 5")


def test_rm_without_flags_on_monitoring_data_is_asked():
    assert _hits("ask", "rm agent-working/agent-monitoring/data/2026-W41/x.runs.jsonl")


def test_no_rule_mixes_a_wildcard_with_the_trailing_colon_star_prefix_syntax():
    """The harness warns at every session start about `Bash(... * ...:*)` and matches it as a literal prefix."""
    permissions = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))["permissions"]
    for kind in ("allow", "ask", "deny"):
        for rule in permissions.get(kind, []):
            inner = re.fullmatch(r"Bash\((.*)\)", rule)
            if inner and inner.group(1).endswith(":*"):
                assert "*" not in inner.group(1)[:-2], rule


def test_workflow_tool_needs_the_users_go():
    # Owner decision 2026-10-05: workflow_run is not visible to the Bash/Edit/Write guard, so it is asked here.
    assert "Workflow" in json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))["permissions"]["ask"]
