---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY
phase: done
date: 2026-09-24
tags: [delivery, hooks, process-improvement]
---

# TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY

## Title
Advisory pre-push check that says what it checked — commit subjects name real tickets,
`agent-monitoring/` is staged, and the branch is not a finished squash-merged one

## Status
DONE

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
- `python3 -m pytest tests/tools/test_delivery_pre_push_advisory.py -v` (repo venv): **16 passed** —
  one per Acceptance Criterion (AC1–AC9) plus regression-prone paths, including a real throwaway
  git repo reproducing Check C's exact ancestor-vs-content shape (AC6) rather than a faked-output
  fixture.
- `python3 -m pytest tests/tools/test_delivery_pre_push_advisory.py
  tests/tools/test_settings_json_hooks_wiring.py tests/tools/test_bash_secret_scan_hook.py
  tests/tools/test_settings_json_edit_write_hook_sidecar_scope.py
  tests/docs/test_subsystem_ownership_lifecycle_doc.py -q` — every file the AC9 grep found: **52
  passed**. This run also caught a count-based pin AC9's own keyword grep missed —
  `test_bash_secret_scan_hook.py::test_new_bash_secret_scan_hook_entry_registered` asserts
  `len(bash_entries) == 3` via a locally-computed filtered list, which doesn't literally contain
  "settings.json" or a `PreToolUse[N]` index pattern, so a keyword grep alone would not have
  surfaced it — only actually running the test did. Bumped to `== 4`. Recorded here as a real,
  slightly humbling finding: grep narrows the search, it does not replace running the tests.
- Full regression: `python3 -m pytest tests/tools/ -m "not slow"` — **2977 passed, 1 failed** (on
  the first run). The 1 failure,
  `test_agent_monitoring_manifest.py::test_manifest_run_against_real_corpus_produces_zero_diff`, is
  a transient shared-worktree race (it hashes `agent-monitoring/*.jsonl` before/after
  `build_manifest()`, and this repo's worktree is shared by multiple live concurrent sessions right
  now) — confirmed by re-running it alone immediately after, where it **passed**. Not a regression
  from this ticket, which touches no file under `agent-monitoring/`. Reported per Gate Integrity
  rather than silently re-run to green or touched.

## Files Changed
- `tools/delivery/pre_push_advisory_hook.py` (new) — the advisory hook module and CLI.
- `tests/tools/test_delivery_pre_push_advisory.py` (new) — 16 tests.
- `.claude/settings.json` — one new `Bash` `PreToolUse` entry appended at index 6, committed only
  after direct user confirmation of the literal diff.
- `tests/tools/test_settings_json_hooks_wiring.py` — bumped the pinned `PreToolUse` count 6 → 7.
- `tests/tools/test_bash_secret_scan_hook.py` — bumped the pinned Bash-matcher-entry count 3 → 4
  (found by running the test, not by the AC9 grep alone — see Test Summary).
- `staging_artifacts/TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY/{investigation,plan,test_plan}.md` (new).

## Completion Summary
Built `tools/delivery/pre_push_advisory_hook.py`, a `PreToolUse` `Bash` advisory hook firing on
`git push` and checking three mechanically-verifiable delivery rules: every unpushed commit
subject names a real ticket file (searched recursively across `tickets/`, so a ticket that moved to
`done/` mid-branch is not a false positive), the current ISO week's monitoring shard is staged, and
the branch is not a finished, squash-merged one (detected via the exact ancestor-vs-content
discriminator `docs/guides/delivery_process.md`'s "PR Lifecycle" step 7 describes, reproduced
against a real throwaway git repo rather than a faked fixture, per AC6's own warning). The matcher
regex was derived from measuring 322 real `git push` invocations in this repo's own corpus
(77.6% bare, 19.9% newline-chained, 2.5% `&&`/`;`-chained) rather than assumed — the same
measure-first discipline the `cd`-prefix advisory hook's own history (a matcher that covered only
2.3% of its target for months) exists to teach. The mandatory AC9 grep before editing
`.claude/settings.json` found two index-pinning tests (untouched by construction, since the new
entry was appended at the end) and, on actually running the tests rather than trusting the grep
alone, a third count-based pin the grep's own keyword search could not have found — both this and
the two index pins are resolved with zero weakened assertions. The `.claude/settings.json` edit was
committed only after the literal diff was shown to and approved directly by the user, same as every
other governing-file edit in this batch.

The one test failure surfaced during the full regression run
(`test_manifest_run_against_real_corpus_produces_zero_diff`) is a transient race from another live
session sharing this worktree writing to `agent-monitoring/data/2026-W39/tools.jsonl` mid-run,
confirmed by an immediate clean re-run in isolation — not a regression from this ticket, reported
rather than silently dismissed or retried into green. `data_runs_clean` is expected to FAIL again on
this close for the same pre-existing, not-this-ticket's-own reason as the prior four closes in this
batch.
