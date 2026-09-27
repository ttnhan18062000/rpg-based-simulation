"""Single source of truth for "what identifier does this monitoring write/read belong to"
(TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX).

Replaces five independent, drifted copies of a per-identifier `agent-monitoring/data/<week>/
<id>.<kind>.jsonl` write-target formula (`record_run.py`, `record_events.py`,
`retrieval_events.py`, `post_tool_hook.py`, `shadow_reviewer_events.py`) -- two of which
(`record_hand_orchestrated_closure.py`, `shadow_reviewer_events.py`) never adopted per-identifier
branching at all and always wrote to the shared file, and one of which (`post_tool_hook.py`) keyed
by a different field (`ticket_id`) than the rest (`run_id`), a divergence this module also closes
by giving every call site the same one identifier.

Re-keyed from per-ticket to per-PR/batch (the user's design decision, 2026-09-25): the unit of
squash-merge-conflict avoidance is the branch/PR, not the ticket -- multiple tickets on one branch
are already sequential commits on that one branch and never conflict with each other; the real
conflict is between two DIFFERENT branches' concurrent monitoring writes at merge time. A per-ticket
key was finer-grained than the actual failure mode requires (a 14-ticket batch should produce 3
files total, not ~42).

`resolve_batch_identifier()` deliberately never shells out to `git` -- `post_tool_hook.py` fires on
every tool call (confirmed zero existing subprocess use anywhere in that file) and a `git
rev-parse`/`git symbolic-ref` call per invocation would be a new, real cost on the hottest path in
the whole system. Reads `.git` (or, in this repo's normal git-worktree mode, the gitlink file it
points at) and the resolved real gitdir's `HEAD` file directly instead -- two small file reads, no
subprocess.

`git rev-parse --abbrev-ref HEAD` returns the literal string `"HEAD"` on a detached HEAD, which a
naive implementation could mistake for a real branch name and use as a filename prefix. Reading
`HEAD`'s raw content directly instead makes attached (`ref: refs/heads/<name>`) and detached (a raw
40-hex-char SHA) unambiguous.

`.claude/current_batch` is a shared, single-file-per-worktree sidecar, the same *shape* as
`.claude/current_run` -- a file whose contamination history is real (that sidecar kept logging
against an already-closed ticket for two days after close, because it is shared across
concurrently-running sessions). That bug does not carry over here, and the reason is the
granularity, not luck: `run_id` is session-scoped -- two sessions in one worktree legitimately
have different run_ids, so a shared file is wrong by construction for that field. A batch/PR
identifier is branch-scoped, and every session operating in one worktree shares that worktree's one
current branch -- so a shared sidecar is the *correct* granularity for this field, not an accident
repeating the same mistake.

The sidecar is **refreshed on every successful attached-HEAD resolution, never written once and
left stale**. A write-once design would go stale the moment the worktree switches to a new branch
-- and CLAUDE.md explicitly sanctions exactly that (the same-directory-fresh-branch fallback when
one worktree picks up a second unit of work) as a normal, documented path, not an edge case. A
stale sidecar would silently route a new branch's rows into the previous PR's file -- worse than
the bug this module fixes, since wrong attribution looks correct until someone checks. Attached
resolution is always authoritative; the sidecar exists purely as a cache for when HEAD is
detached, and is overwritten every time a real branch name is available again.

`detached-<sha>` is a deliberate **last-resort, intentionally-fragmenting** label -- a new file per
distinct SHA a truly-detached, sidecar-and-reflog-less session visits. This is accepted as a rare
degraded mode, not something to "optimize away" by trying to make it stable across detaches
without a real branch name to anchor to.

**TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-WORKTREE**: the sidecar only covers
"a worktree in which a monitoring hook ran while attached, at some point after this module
shipped" -- not "a worktree that was ever attached to a real branch even once," which is what an
earlier version of this docstring claimed. A worktree sitting on a detached HEAD every time a hook
has ever run on it never gets a chance to write the sidecar, and stayed in the `detached-<sha>`
branch permanently rather than rarely (observed live: a worktree attached to 20+ real branches over
its life, `.claude/current_batch` still absent). Closed by inserting a reflog-recovery step between
the sidecar and `detached-<sha>`: `<gitdir>/logs/HEAD` is a plain file recording every `checkout:
moving from ... to <branch>` this worktree has ever done, and its most recent entry names the last
branch this worktree was validly attached to -- read with the same no-subprocess discipline as
every other step here, and written to the sidecar on success so the guarantee this docstring states
now actually holds: any worktree with at least one real branch checkout anywhere in its reflog
resolves to that branch, not only one seeded by a hook run after this fix landed. Not validated
against `refs/heads/` -- the sidecar is for attribution, not a live git operation, so a branch
already squash-merged and deleted is still the correct historical attribution for rows written
under it.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

_REFLOG_CHECKOUT_RE = re.compile(r"checkout: moving from \S+ to (\S+)$")

_HEAD_REF_PREFIX = "ref: refs/heads/"

# In-process memoization only -- each post_tool_hook.py / record_hand_orchestrated_closure.py
# invocation is its own process, so this only helps a caller that resolves more than once within
# one run (record_hand_orchestrated_closure.py does, once per file kind).
_cache: dict[str, str] = {}


def sanitize_for_filename(identifier: str) -> str:
    """Branch names may contain `/` (e.g. `feature/foo`), not valid as a bare filename component
    without creating subdirectories under `agent-monitoring/data/<week>/`. Replaces `/` with `-`,
    matching this project's own `TCK-`-style hyphen-separated naming convention. A real, disclosed
    lossy mapping (two differently-slashed names could collide after sanitizing) -- accepted: no
    local branch name in this repo's real history contains `/` today."""
    return identifier.replace("/", "-")


def _real_gitdir(cwd: Path) -> Path | None:
    """Resolve the real git directory for `cwd`, handling both a plain `.git` directory (a normal
    checkout) and a `.git` gitlink FILE containing `gitdir: <path>` (this repo's normal mode --
    every session in this project runs through a `.claude/worktrees/*` checkout)."""
    git_path = cwd / ".git"
    if git_path.is_dir():
        return git_path
    if git_path.is_file():
        try:
            text = git_path.read_text(encoding="utf-8").strip()
        except OSError:
            return None
        if text.startswith("gitdir: "):
            gitdir = Path(text[len("gitdir: "):].strip())
            return gitdir if gitdir.is_absolute() else (cwd / gitdir)
    return None


def _branch_from_head_file(cwd: Path) -> str | None:
    """Returns the current branch name if HEAD is attached, or None if detached or unresolvable.
    Never returns the literal string `"HEAD"` -- unlike `git rev-parse --abbrev-ref HEAD`, which
    does exactly that on a detached HEAD."""
    gitdir = _real_gitdir(cwd)
    if gitdir is None:
        return None
    head_path = gitdir / "HEAD"
    try:
        content = head_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if content.startswith(_HEAD_REF_PREFIX):
        return content[len(_HEAD_REF_PREFIX):].strip()
    return None  # detached HEAD: raw SHA, no "ref: " prefix


def _short_sha_from_head_file(cwd: Path) -> str:
    gitdir = _real_gitdir(cwd)
    if gitdir is None:
        return "unknown"
    try:
        content = (gitdir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return "unknown"
    return content[:12] if content else "unknown"


_RAW_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


def _branch_from_reflog(gitdir: Path) -> str | None:
    """Last-resort recovery for a detached HEAD with no sidecar: the most recent `checkout:
    moving from ... to <name>` entry in `gitdir/logs/HEAD` whose `<name>` is a real branch name,
    not a raw SHA -- the last branch this worktree was validly attached to before whatever
    detached it. Plain file read, no subprocess, matching every other step in this module.

    A detach itself (`git checkout --detach <sha>`) writes its own `checkout: moving from
    <branch> to <sha>` entry -- the exact shape this function searches for, with the detach
    target standing in as `<name>`. Skipping any target that looks like a raw hex SHA is not an
    edge case, it's the common case: the entry immediately preceding "why we're detached right
    now" is always exactly this shape, and returning it as a "recovered branch" would be worse
    than the bug this ticket fixes -- silently mislabeling a batch as its own commit SHA.

    Returns None if the file is absent, empty, or has no real-branch checkout-to entry at all
    (e.g. a fresh worktree, or a reflog pruned by `gc.reflogExpire`). Deliberately not validated
    against `refs/heads/` beyond the SHA-shape check -- see this module's own docstring: a deleted
    branch's name is still the correct historical attribution for rows already written under it."""
    reflog_path = gitdir / "logs" / "HEAD"
    try:
        lines = reflog_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for line in reversed(lines):
        match = _REFLOG_CHECKOUT_RE.search(line)
        if match and not _RAW_SHA_RE.match(match.group(1)):
            return match.group(1)
    return None


_SIDECAR_PATH_NAME = ".claude/current_batch"


def _read_sidecar(cwd: Path) -> str | None:
    path = cwd / _SIDECAR_PATH_NAME
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return value or None


def _write_sidecar(cwd: Path, identifier: str) -> None:
    path = cwd / _SIDECAR_PATH_NAME
    try:
        existing = path.read_text(encoding="utf-8").strip()
    except OSError:
        existing = None
    if existing == identifier:
        return  # avoid a needless write when nothing changed
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(identifier, encoding="utf-8")
    except OSError:
        pass  # never let a sidecar-write failure break the caller's real monitoring write


def resolve_batch_identifier(cwd: Path | None = None) -> str:
    """Returns the sanitized identifier every monitoring write/read for this PR/batch should key
    on. Resolution order:

    1. Live branch name, read directly from `.git`'s real HEAD file (no subprocess).
    2. If detached (no branch resolvable): the `.claude/current_batch` sidecar, self-healed by
       step 1 whenever it *does* resolve a real branch -- so a later detached call in the same
       worktree recovers the last known real identifier instead of degrading immediately.
    3. If the sidecar is also empty (TCK-20260927-MONITORING-BATCH-SIDECAR-UNSEEDED-ON-DETACHED-
       WORKTREE: a worktree that has never had a hook run while attached never gets one written):
       the worktree's own `logs/HEAD` reflog, whose most recent `checkout: moving to <branch>`
       entry names the last branch this worktree was validly attached to. Seeds the sidecar on
       success, same as step 1, so later calls in the same worktree are cheap again.
    4. If all three are unavailable (a genuinely fresh worktree, never on a named branch, no
       sidecar, no reflog entry either): a clearly-labeled `detached-<sha>` identifier, with a
       printed warning. Never returns an empty string or any value that collapses onto the bare
       shared filename.
    """
    resolved_cwd = cwd if cwd is not None else Path.cwd()
    cache_key = str(resolved_cwd)
    if cache_key in _cache:
        return _cache[cache_key]

    branch = _branch_from_head_file(resolved_cwd)
    if branch:
        identifier = sanitize_for_filename(branch)
        _write_sidecar(resolved_cwd, identifier)
        _cache[cache_key] = identifier
        return identifier

    sidecar_value = _read_sidecar(resolved_cwd)
    if sidecar_value:
        _cache[cache_key] = sidecar_value
        return sidecar_value

    gitdir = _real_gitdir(resolved_cwd)
    reflog_branch = _branch_from_reflog(gitdir) if gitdir is not None else None
    if reflog_branch:
        identifier = sanitize_for_filename(reflog_branch)
        _write_sidecar(resolved_cwd, identifier)
        _cache[cache_key] = identifier
        return identifier

    short_sha = _short_sha_from_head_file(resolved_cwd)
    identifier = f"detached-{short_sha}"
    print(
        f"WARNING: monitoring_batch_identifier: HEAD is detached, no {_SIDECAR_PATH_NAME} sidecar "
        "exists, and the reflog has no recoverable branch checkout -- falling back to "
        f"{identifier!r}. This never collapses to the shared monitoring file, but the batch is "
        "not identified by its real branch/PR name.",
        file=sys.stderr,
    )
    _cache[cache_key] = identifier
    return identifier


def resolve_write_target(kind: str, iso_week: str | None = None, cwd: Path | None = None) -> Path:
    """`agent-monitoring/data/<ISO-week>/<batch-identifier>.<kind>.jsonl` -- the one write-target
    formula every call site (`record_run.py`, `record_events.py`, `retrieval_events.py`,
    `record_hand_orchestrated_closure.py`, `post_tool_hook.py`, `shadow_reviewer_events.py`) now
    shares, replacing five independently-drifted copies of this same computation.

    `iso_week` is deliberately a caller-supplied parameter, not computed here: every call site
    already computes its own `datetime.now(timezone.utc).strftime("%G-W%V")` (several under a
    test suite that freezes that call's own module-local `datetime` import to test week-boundary
    behavior deterministically) -- computing it internally here instead would silently break
    every one of those freezes, since patching e.g. `record_run.datetime` has no effect on a
    `datetime.now()` call inside this different module. This function resolves WHO (the batch
    identifier); the caller still decides WHEN.

    `cwd` is used to resolve the batch identifier (the `.git` lookup) and, when explicitly
    given (tests, pointing at a scratch repo), anchors the returned path there too. When omitted
    (every real call site), identifier resolution uses the real process `Path.cwd()` but the
    returned path stays relative -- `Path("agent-monitoring/data") / ...` -- matching every
    existing call site's own convention (all of them already assume cwd is the repo root)."""
    identifier_cwd = cwd if cwd is not None else Path.cwd()
    week = iso_week if iso_week is not None else datetime.now(timezone.utc).strftime("%G-W%V")
    identifier = resolve_batch_identifier(identifier_cwd)
    base = cwd if cwd is not None else Path(".")
    return base / "agent-monitoring" / "data" / week / f"{identifier}.{kind}.jsonl"
