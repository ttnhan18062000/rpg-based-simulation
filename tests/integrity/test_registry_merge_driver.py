"""Regression test for the docs/REGISTRY.yaml merge driver + post-merge regeneration hook
(TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX). Verifies, at the real git level, the
mechanism this ticket's own scratch-repo investigation proved by hand:

1. A per-path custom merge driver cannot safely regenerate synchronously -- git invokes it
   with no ordering guarantee relative to other paths in the same merge (the docs/ticket
   files the real registry is actually generated from). A first design that tried to
   regenerate inside the driver was confirmed, in that investigation, to silently produce
   an incomplete registry. The shipped fix instead: a trivial `true` merge driver (keeps
   git's own pre-seeded "ours" content, always succeeds, no conflict markers) plus a
   `post-merge` hook (tools/hooks/registry_post_merge_regen.sh, the REAL file under test
   here -- copied unmodified into the throwaway repo, not reimplemented) that regenerates
   only after every path in the merge is already resolved on disk.
2. With no local driver configured (the common state for a fresh clone -- merge drivers
   live in unversioned git config, never in .gitattributes alone), a real conflict on this
   path fails the merge loudly, never silently taking one side.

Uses a lightweight fixture generator (not the real tools/generate_registry.py) that mirrors
its exact CLI contract (`--check` exits 0 in-sync / 2 drift; no flag regenerates and writes)
-- this test proves the merge-time *mechanism* the real hook script drives, and is
deliberately decoupled from generate_registry.py's own internal logic so it does not need
updating every time that logic changes.
"""
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_HOOK_SCRIPT = REPO_ROOT / "tools" / "hooks" / "registry_post_merge_regen.sh"

_FIXTURE_GENERATOR = '''#!/usr/bin/env python3
"""Fixture stand-in for tools/generate_registry.py: mirrors its --check CLI contract
(exit 0 in-sync, exit 2 drift) closely enough for the real post-merge hook script to drive
it unmodified, without depending on the real generator's own internal logic."""
import sys
from pathlib import Path

entries = sorted(p.name for p in Path("entries").glob("*.txt"))
fresh = "\\n".join(f"entry:{e}" for e in entries) + "\\n"
output = Path("docs/REGISTRY.yaml")

if "--check" in sys.argv:
    if output.exists() and output.read_text() == fresh:
        print(f"In sync: {len(entries)} entries match {output}")
        sys.exit(0)
    print("DRIFT", file=sys.stderr)
    sys.exit(2)

output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(fresh)
print(f"Wrote {len(entries)} entries to {output}")
'''


def _run_git(args, cwd, check=True):
    result = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if check:
        assert result.returncode == 0, (
            f"git {' '.join(args)} failed: stdout={result.stdout!r} stderr={result.stderr!r}"
        )
    return result


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "entries").mkdir()
    _run_git(["init", "-q", "-b", "main"], cwd=repo)
    _run_git(["config", "user.email", "test@example.com"], cwd=repo)
    _run_git(["config", "user.name", "Test"], cwd=repo)
    (repo / "tools" / "generate_registry.py").write_text(_FIXTURE_GENERATOR)
    (repo / ".gitattributes").write_text("docs/REGISTRY.yaml merge=registry-regen\n")
    (repo / "entries" / "base.txt").write_text("base entry\n")
    subprocess.run(
        ["python3", "tools/generate_registry.py"], cwd=str(repo), check=True, capture_output=True,
    )
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "base"], cwd=repo)
    return repo


def _install_driver_and_hook(repo: Path) -> None:
    _run_git(["config", "merge.registry-regen.driver", "true"], cwd=repo)
    hooks_dir = Path(
        _run_git(
            ["rev-parse", "--path-format=absolute", "--git-path", "hooks"], cwd=repo,
        ).stdout.strip()
    )
    post_merge = hooks_dir / "post-merge"
    post_merge.write_text(REAL_HOOK_SCRIPT.read_text())
    post_merge.chmod(0o755)


def _add_entry_and_regenerate(repo: Path, name: str, content: str) -> None:
    (repo / "entries" / name).write_text(content)
    subprocess.run(
        ["python3", "tools/generate_registry.py"], cwd=str(repo), check=True, capture_output=True,
    )


def test_merge_with_driver_and_hook_installed_regenerates_correct_union(tmp_path):
    repo = _init_repo(tmp_path)
    _install_driver_and_hook(repo)

    _run_git(["checkout", "-q", "-b", "branch-a"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-a.txt", "ticket A closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "branch A closes a ticket"], cwd=repo)

    _run_git(["checkout", "-q", "main"], cwd=repo)
    _run_git(["checkout", "-q", "-b", "branch-b"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-b.txt", "ticket B closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "branch B closes a ticket"], cwd=repo)

    merge_result = _run_git(["merge", "branch-a", "--no-edit"], cwd=repo)
    assert merge_result.returncode == 0, (
        f"merge should succeed via the trivial driver, got: {merge_result.stdout!r} "
        f"{merge_result.stderr!r}"
    )

    registry_content = (repo / "docs" / "REGISTRY.yaml").read_text()
    assert "<<<<<<<" not in registry_content
    assert "entry:base.txt" in registry_content
    assert "entry:ticket-a.txt" in registry_content, (
        "the post-merge hook must regenerate against the FULLY merged tree -- a design that "
        "regenerates synchronously inside the merge driver itself was confirmed broken "
        "(see investigation.md): it ran before this file was materialized on disk and "
        "silently produced a registry missing this exact entry"
    )
    assert "entry:ticket-b.txt" in registry_content

    log = _run_git(["log", "--oneline", "-3"], cwd=repo).stdout
    assert "auto-regenerate docs/REGISTRY.yaml after merge" in log


def test_merge_with_no_driver_configured_fails_loudly(tmp_path):
    """Uninstalled state (no `make setup-merge-drivers` ever run -- the common state for a
    fresh clone, since merge drivers live in unversioned local git config, never in
    .gitattributes alone). Confirmed via direct, isolated probing (not assumed) that git's
    real fallback here is an ORDINARY 3-way merge attempt on the file -- not a special
    fatal abort. That is still exactly the required behavior: a genuine conflict with
    markers, requiring manual resolution, is loud and never silently picks a side. (An
    earlier draft of this investigation believed an uninstalled driver produces a hard
    `fatal: ... lacks command line` abort; that could not be reproduced under direct,
    isolated testing across several config states -- name-only, driver-unset, driver-empty,
    driver-pointing-at-a-nonexistent-script all fell back to this same ordinary conflict.
    Corrected here rather than asserting the unreproducible claim.)
    """
    repo = _init_repo(tmp_path)
    # Deliberately do NOT install the driver or hook.

    _run_git(["checkout", "-q", "-b", "branch-a"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-a.txt", "ticket A closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "branch A closes a ticket"], cwd=repo)

    _run_git(["checkout", "-q", "main"], cwd=repo)
    _run_git(["checkout", "-q", "-b", "branch-b"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-b.txt", "ticket B closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "branch B closes a ticket"], cwd=repo)

    merge_result = _run_git(["merge", "branch-a", "--no-edit"], cwd=repo, check=False)
    assert merge_result.returncode != 0, (
        "an uninstalled merge driver must fail the merge loudly, never silently take one side"
    )
    assert "CONFLICT" in merge_result.stdout, (
        f"expected an ordinary, loud merge conflict (git's real fallback for an "
        f"unconfigured merge= driver), got: stdout={merge_result.stdout!r} "
        f"stderr={merge_result.stderr!r}"
    )
    registry_content = (repo / "docs" / "REGISTRY.yaml").read_text()
    assert "<<<<<<<" in registry_content, (
        "must leave real conflict markers -- never silently resolve to one side's content"
    )


def test_rebase_and_cherry_pick_silently_take_one_side_no_post_merge_hook(tmp_path):
    """Disclosed gap, confirmed by direct request during PR review (agent-working-design):
    the driver+hook mechanism only closes the silent-one-sided-take failure mode for `git
    merge`. `git rebase` and `git cherry-pick` also invoke `.gitattributes`-declared merge
    drivers for their own internal 3-way conflict resolution, but neither is a `git merge`
    invocation, so `post-merge` never fires afterward -- the trivial `true` driver's
    "keep one side" resolution is never followed by a regeneration. Confirmed here for both:
    the file ends up on one side's content with zero conflict markers and zero indication
    anything was discarded, and no `auto-regenerate` commit follows. Not fixed by this ticket
    (would need a `pre-rebase`/sequencer-level safeguard, out of scope) -- the existing CI
    drift check remains the only backstop on these two paths. See the ticket's own
    Assumptions / Open Questions section for the full disclosure.
    """
    repo = _init_repo(tmp_path)
    _install_driver_and_hook(repo)

    _run_git(["checkout", "-q", "-b", "feature"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-feature.txt", "feature ticket closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "feature closes a ticket"], cwd=repo)
    feature_sha = _run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()

    _run_git(["checkout", "-q", "main"], cwd=repo)
    _add_entry_and_regenerate(repo, "ticket-main.txt", "main ticket closed\n")
    _run_git(["add", "-A"], cwd=repo)
    _run_git(["commit", "-q", "-m", "main closes a different ticket"], cwd=repo)

    # cherry-pick feature's commit onto main -- a real conflict on REGISTRY.yaml (both sides
    # regenerated independently with different entries and timestamps).
    cherry_result = _run_git(
        ["cherry-pick", feature_sha], cwd=repo, check=False,
    )
    registry_after_cherry_pick = (repo / "docs" / "REGISTRY.yaml").read_text()
    assert "<<<<<<<" not in registry_after_cherry_pick, (
        "the trivial driver never leaves conflict markers, on cherry-pick same as merge"
    )
    assert "entry:ticket-feature.txt" not in registry_after_cherry_pick, (
        "cherry-pick silently kept 'ours' (main's own content) -- feature's own entry, the "
        "very thing being cherry-picked, is silently dropped with no error and no markers"
    )
    log_after_cherry_pick = _run_git(["log", "--oneline", "-3"], cwd=repo).stdout
    assert "auto-regenerate docs/REGISTRY.yaml after merge" not in log_after_cherry_pick, (
        "post-merge must not have fired for a cherry-pick -- if this ever starts failing, "
        "git's own behavior changed and this disclosed gap may no longer apply"
    )
    if cherry_result.returncode != 0:
        _run_git(["cherry-pick", "--abort"], cwd=repo, check=False)

    # rebase feature onto main -- same real conflict, different command.
    _run_git(["checkout", "-q", "feature"], cwd=repo)
    rebase_result = _run_git(["rebase", "main"], cwd=repo, check=False)
    registry_after_rebase = (repo / "docs" / "REGISTRY.yaml").read_text()
    assert "<<<<<<<" not in registry_after_rebase
    assert "entry:ticket-feature.txt" not in registry_after_rebase, (
        "rebase silently kept the branch being rebased onto (main's content) -- feature's own "
        "entry is silently dropped with no error and no markers, same failure as cherry-pick"
    )
    log_after_rebase = _run_git(["log", "--oneline", "-3"], cwd=repo).stdout
    assert "auto-regenerate docs/REGISTRY.yaml after merge" not in log_after_rebase
    if rebase_result.returncode != 0:
        _run_git(["rebase", "--abort"], cwd=repo, check=False)


def test_gitattributes_declares_registry_regen_merge_driver():
    content = (REPO_ROOT / ".gitattributes").read_text()
    assert any(
        line.split() and line.split()[0] == "docs/REGISTRY.yaml"
        and "merge=registry-regen" in line.split()[1:]
        for line in content.splitlines()
    ), "docs/REGISTRY.yaml must declare merge=registry-regen in the real .gitattributes"


def test_real_hook_script_exists_and_is_executable():
    assert REAL_HOOK_SCRIPT.is_file()
    assert REAL_HOOK_SCRIPT.stat().st_mode & 0o111, "hook script must be executable (chmod +x)"
