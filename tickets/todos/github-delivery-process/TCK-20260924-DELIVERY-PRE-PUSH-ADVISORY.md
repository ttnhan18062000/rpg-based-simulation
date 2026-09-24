---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
phase: open
date: 2026-09-24
tags: [delivery, hooks, process-improvement]
---

# TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY

## Title
Advisory pre-push check that says what it checked — commit subjects name real tickets,
`agent-monitoring/` is staged, and the branch is not a finished squash-merged one

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Three delivery rules in `CLAUDE.md` are mechanically checkable, are currently defended only by an
agent remembering to obey them, and each fails silently when skipped:

1. **Every commit subject references a real ticket** (Commit Convention). A subject naming no ticket,
   or naming a ticket file that does not exist, is invisible until someone greps for it later.
2. **`agent-monitoring/` is staged in every commit.** The monitoring hooks rewrite the current week's
   shard on nearly every tool call, so an unstaged shard is the default state, not an unusual one.
3. **A squash-merged branch is finished and is never pushed to again.** This one is subtle and
   expensive: because the repo squash-merges, a merged branch's own commits are never ancestors of
   `main`, so further commits pushed to it have **no path to `main`** while a naive
   `git diff origin/main...HEAD` makes it look like the whole original diff is being resubmitted. The
   rule exists precisely because the violation is hard to see by eye — and it is mechanically
   detectable.

This ticket adds an advisory check in the shape of the existing
`tools/agent-monitoring/cd_prefix_advisory_hook.py`, wired as a `PreToolUse` hook on `Bash`, which is
how this repo already does author-time advisories.

## Scope
1. **The advisory check module**, following `cd_prefix_advisory_hook.py`'s existing shape: read the
   hook payload from stdin, decide, print a short advisory, exit zero. Triggers on a `git push`
   command.
2. **Check A — commit subjects name a real ticket.** For each commit on the branch not yet on
   `origin/main`, extract the `TCK-` ID from the subject and confirm a matching ticket file exists in
   `tickets/` (any subdirectory — a ticket legitimately moves to `tickets/done/` during its own
   branch's life). Report subjects with no ID, and IDs with no file, as separate findings.
3. **Check B — `agent-monitoring/` staged.** Report if the current week's
   `agent-monitoring/data/YYYY-Www/*.jsonl` shards are dirty or untracked at push time.
4. **Check C — branch is not squash-merged-and-finished.** Detect the shape: the branch's tip is not
   an ancestor of `origin/main`, yet its content is already present there. The reliable discriminator
   is a suspiciously large three-dot `git diff origin/main...HEAD` against a small two-ref
   `git diff origin/main HEAD` — the first is ancestor-based and misleading after a squash, the second
   is content-based and correct. When it fires, the advisory must say what to do: cut a fresh branch
   off `origin/main`, never push further to this one.
5. **Output states what was checked, narrowly.** Each finding names the specific condition and the
   specific commit or file. Plan §6: these checks must not read as quality signals — a conforming
   push can still be wrong, and the output should not imply otherwise.

## Out of Scope
- **Blocking. Under any circumstance.** The hook prints and exits zero, always, for every finding and
  for every internal error. It must never return a blocking decision, never non-zero-exit, and never
  prevent a push. Settled decision, not an open question
  ([[feedback_agent_tooling_checks_proportionate]]). A test asserts the zero exit on deliberately
  non-conforming input.
- **A CI job asserting commit-subject traceability.** Explicitly declined — the one candidate for a
  genuine blocking check, and the decision was to hold the line at advisory everywhere.
- **Fixing anything it finds.** No auto-staging of `agent-monitoring/`, no rewriting of commit
  messages, no branch creation. Report only.
- **Rewriting history.** Never amend, rebase or reword.
- **Checking PR shape**, which needs a PR to exist. That is `pr_render.py --check`.
- **Validating ticket *content*.** Existence of the file is the check; `done-checker` owns whether
  its content is adequate.
- **Any network call.** The check must work offline against local refs, so it cannot be a source of
  the TLS-block failure mode this epic elsewhere defends against. `origin/main` is read from the local
  ref, not fetched.

## Acceptance Criteria
1. On a branch whose every unpushed commit subject names an existing ticket file, with shards staged,
   not squash-merged, the advisory prints nothing (or an explicit all-clear) and exits zero.
2. A commit subject with no `TCK-` ID is reported, naming that commit. Exit code zero.
3. A commit subject naming a `TCK-` ID with **no** matching file anywhere under `tickets/` is
   reported as a distinct finding from case 2. Exit code zero.
4. A ticket that has moved to `tickets/done/` during its own branch's life is **not** reported as
   missing — asserted by a fixture, since this is the most likely false positive.
5. A dirty or untracked current-week monitoring shard is reported. Exit code zero.
6. The squash-merged-and-finished shape is detected on a fixture reproducing it, and the advisory text
   names cutting a fresh branch as the action. **This is the criterion most likely to be faked by a
   test that reproduces the wrong shape** — the fixture must have the branch tip genuinely not an
   ancestor of `origin/main` while its content is present there, not merely a branch behind `main`.
7. **Exit code is zero in every case, including every finding and any internal error** — asserted by
   a test that feeds deliberately non-conforming input and asserts zero.
8. A malformed or empty hook payload causes no traceback and no blocking output.
9. Whatever registers the hook is consistent with the existing entries, and **a grep across `tests/`
   for files pinning `.claude/settings.json`'s hook count or message text was run first and its result
   recorded** — see Implementation Notes.
10. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — parent
- `TCK-20260924-DELIVERY-CONTRACT-AND-TEMPLATES` — **dependency**; the contract this advises against
- `TCK-20260924-DELIVERY-PR-RENDERER` — sibling; `--check` covers PR shape, this covers pre-push

## Related Docs
- `docs/plans/agent_infrastructure/github_delivery_process/plan.md` §3.4 (branch naming and the
  squash-merged-branch rule), §6 (checks must not read as quality signals)
- `CLAUDE.md` — Commit Convention, `## Worktree & Branch Isolation` (129), `### PR Lifecycle` (418),
  whose item 7 documents the squash-merge ancestor-loss shape in full. Do **not** edit `CLAUDE.md` in
  this ticket.
- `docs/guides/delivery_process.md` — created by the dependency

## Related Stored Artifacts
None yet.

## Related Code Areas
- `tools/agent-monitoring/cd_prefix_advisory_hook.py` — **the shape to follow**; an existing advisory
  `PreToolUse` hook on `Bash`, wired in `.claude/settings.json`
- `.claude/settings.json` — currently 12 hook entries across `PreToolUse`, `PostToolUse`,
  `SubagentStop`, `SessionStart`. **Shared config — see Implementation Notes.**
- `tickets/` — the ticket files check A resolves against

## Assumptions / Open Questions
1. **Whether a `PreToolUse` hook on `Bash` can reliably identify a `git push`** without firing on
   unrelated commands that merely mention pushing.
   `cd_prefix_advisory_hook.py` solved the analogous matching problem and its history is instructive:
   it originally matched only `&&`-joined commands, which turned out to be **2.3%** of its real target
   population, because the dominant shape is newline-separated. Its 15 tests all shared the regex's
   blind spot, so they confirmed the assumption rather than the behavior. **Measure the real
   distribution of `git push` command shapes in `agent-monitoring/data/*/tools.jsonl` before writing
   the matcher, and state the measured coverage.**
2. Whether Check C can be done cheaply enough for a pre-push hook. Both diffs are local, so probably
   yes; if not, gate it behind a cheap precondition rather than dropping it.
3. Whether an all-clear should print at all. Leaning no — a silent pass is the right default for an
   advisory that fires on every push.
4. Whether `git push` from a detached HEAD or a non-tracking branch needs special handling. This repo
   does run detached worktrees, so at minimum it must not traceback.

## Implementation Notes
**A shared-config edit needs a "who else pins this file" grep across `tests/`, not a
scoped-by-directory test run.** Confirmed repeat failure in this repo: editing `.claude/settings.json`
broke three tests in *unrelated* files that pin its hook count and message text, and an implementer
plus two independent verify passes all missed it because each ran tests scoped to the directory it had
changed. Grep `tests/` for the settings file, for hook counts, and for hook message strings **before**
editing, and record the result — including "found nothing".

Criterion 1 in Assumptions is the one to take seriously. The `cd` advisory shipped matching 2.3% of
its target population with 15 passing tests, because the tests shared the implementation's blind spot.
Passing tests confirmed the assumption, not reality. Measure the real corpus distribution of push
command shapes first; a test suite written from the same wrong mental model as the matcher cannot
detect the error.

Advisory means advisory. There is no failure mode of this check that justifies blocking a push — if
it is uncertain, it says less, not more.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
