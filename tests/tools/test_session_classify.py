"""Classifier table for tools/sessions/classify.py (TCK-20261004-SESSION-LAYER-M5B-ROLE-CONDITIONAL-PRETOOLUSE-HOOK).

Every authority class has matching fixtures and near-miss fixtures; indirection fixtures must classify as
uncertain (-> ask), never as a silent pass.
"""
import pytest

from tools.sessions.classify import classify

BASH = "Bash"


def _actions(command):
    return set(classify(BASH, {"command": command}).actions)


@pytest.mark.parametrize("command,expected", [
    ("git commit -m x", {"commit"}),
    ("git push origin branch", {"push"}),
    ("git push -u origin feature-x", {"push"}),
    ("git -c user.name=x push", {"push"}),
    ("git push --delete origin old", {"push", "delete_remote_branch"}),
    ("git push origin :old", {"push", "delete_remote_branch"}),
    ("git push -d origin old", {"push", "delete_remote_branch"}),
    ("gh pr create --title t", {"open_pr"}),
    ("gh pr merge 5 --squash", {"merge"}),
    ("gh pr merge --admin 5", {"merge"}),
    ("gh api -X DELETE repos/o/r/git/refs/heads/x", {"delete_remote_branch"}),
    ("gh api --method DELETE repos/o/r/git/refs/heads/x", {"delete_remote_branch"}),
    ("cd x && git commit -m y && git push", {"commit", "push"}),
    ("GIT_AUTHOR_NAME=a git commit -m y", {"commit"}),
    ("sed -i 's/a/b/' CLAUDE.md", {"governing_file_edit"}),
    ("echo x >> .claude/settings.json", {"governing_file_edit"}),
    ("cp x registries/session_authority.yaml", {"authority_file_edit"}),
])
def test_authority_commands_are_classified(command, expected):
    result = classify(BASH, {"command": command})
    assert expected <= set(result.actions)
    assert not result.uncertain


@pytest.mark.parametrize("command", [
    "git status", "git diff HEAD~1", "git log --oneline", "git fetch origin",
    "git push-pull-notes", "git branch -a", "git add -A", "git checkout -b x",
    "gh pr view 5", "gh pr list", "gh pr checks 5", "gh api repos/o/r/pulls/5",
    "ls", "cat CLAUDE.md", "grep -n x .claude/settings.json", "git diff .claude/settings.json",
    "head registries/session_authority.yaml", "python3 -m pytest tests/tools",
    "rm -rf data/runs/x", "git worktree list",
])
def test_near_misses_are_not_authority_class(command):
    result = classify(BASH, {"command": command})
    assert not result.is_authority, (command, result)


@pytest.mark.parametrize("command", [
    "bash -c 'git push origin x'",
    "sh -c \"gh pr merge 5\"",
    "eval 'git push'",
    "$GIT push origin x",
    "${GH} pr merge 5",
    "echo $(git push origin x)",
    "xargs git push < branches.txt",
])
def test_indirection_is_uncertain_so_it_asks(command):
    result = classify(BASH, {"command": command})
    assert result.uncertain and result.is_authority, command


def test_a_refspec_push_is_a_push_but_not_a_remote_branch_deletion():
    assert _actions("git push origin HEAD:refs/heads/x") == {"push"}
    assert _actions("git push -u origin x") == {"push"}


def test_unparseable_quote_with_authority_word_is_uncertain():
    assert classify(BASH, {"command": "git push 'origin"}).uncertain


def test_unparseable_text_without_authority_words_is_not():
    assert not classify(BASH, {"command": "echo 'unterminated"}).is_authority


@pytest.mark.parametrize("tool,tool_input,expected", [
    ("Edit", {"file_path": "/repo/CLAUDE.md"}, {"governing_file_edit"}),
    ("Write", {"file_path": ".claude/settings.json"}, {"governing_file_edit"}),
    ("MultiEdit", {"file_path": "/repo/.claude/settings.json"}, {"governing_file_edit"}),
    ("NotebookEdit", {"notebook_path": "/repo/CLAUDE.md"}, {"governing_file_edit"}),
    ("Edit", {"file_path": "/repo/.claude/hooks/x.py"}, {"governing_file_edit"}),
    ("Edit", {"file_path": "/repo/registries/session_authority.yaml"}, {"authority_file_edit"}),
    ("Write", {"file_path": "registries/session_authority.yaml"}, {"authority_file_edit"}),
])
def test_governed_paths_are_classified(tool, tool_input, expected):
    assert set(classify(tool, tool_input).actions) == expected


@pytest.mark.parametrize("tool,tool_input", [
    ("Edit", {"file_path": "/repo/src/x.py"}),
    ("Write", {"file_path": "/repo/docs/CLAUDE.md.bak"}),
    ("Edit", {"file_path": "/repo/registries/session_roles.yaml"}),
    ("Read", {"file_path": "/repo/CLAUDE.md"}),
    ("Grep", {"pattern": "git push"}),
    ("Workflow", {}),
])
def test_other_tools_and_paths_are_not_authority_class(tool, tool_input):
    assert not classify(tool, tool_input).is_authority


def test_classifier_never_raises_on_odd_input():
    for tool_input in (None, {}, {"command": None}, {"command": 5}, {"file_path": None}):
        classify(BASH, tool_input)
        classify("Edit", tool_input)


def test_git_C_still_classifies_the_subcommand_but_is_uncertain_about_the_branch():
    """`git -C ../other commit` acts on a repository whose branch is not the call's cwd (TCK-20261006-GUARD-OWN-
    BRANCH-GIT-ALLOWED), so the guard must ask instead of trusting the cwd's branch."""
    result = classify(BASH, {"command": "git -C ../other commit -m x"})
    assert set(result.actions) == {"commit"} and result.uncertain


@pytest.mark.parametrize("command", [
    "git push origin main", "git push origin HEAD:main", "git push origin +x:main", "git push origin refs/heads/main",
    "git push --all", "git push --mirror", "git push -u origin main",
])
def test_push_to_the_default_branch_is_push_default_branch(command):
    result = classify(BASH, {"command": command})
    assert {"push", "push_default_branch"} <= set(result.actions) and not result.uncertain


@pytest.mark.parametrize("command", [
    "git push -u origin feature-x", "git push origin HEAD:feature-x", "git push --force-with-lease origin feature-x",
    "git push -o ci.skip origin feature-x", "git push --tags", "git push origin feature-x:other",
])
def test_push_to_another_branch_is_a_plain_push(command):
    result = classify(BASH, {"command": command})
    assert set(result.actions) == {"push"} and not result.push_implicit and not result.uncertain


@pytest.mark.parametrize("command", ["git push", "git push origin", "git push origin HEAD", "git push --force-with-lease", "git push -u origin"])
def test_push_without_an_explicit_target_is_flagged_for_the_guard_to_resolve(command):
    result = classify(BASH, {"command": command})
    assert set(result.actions) == {"push"} and result.push_implicit


def test_default_branches_parameter_widens_what_counts_as_default():
    assert "push_default_branch" not in classify(BASH, {"command": "git push origin trunk"}).actions
    assert "push_default_branch" in classify(BASH, {"command": "git push origin trunk"}, ("main", "trunk")).actions


def test_branch_switch_in_the_same_command_makes_commit_or_push_uncertain():
    assert classify(BASH, {"command": "git checkout main && git commit -m x"}).uncertain
    assert classify(BASH, {"command": "git switch main; git push"}).uncertain
    assert not classify(BASH, {"command": "git checkout -b x"}).is_authority
