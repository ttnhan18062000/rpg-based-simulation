---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260923-BASH-MIX-REF-PINNING
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260923-BASH-MIX-REF-PINNING

## Title
`bash_command_mix.py`: opt-in git-ref-pinned reading (`--ref`), so a before/after comparison
isn't silently drift

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
While reconciling `TCK-20260923-BASH-COMMAND-MIX-BASELINE`'s own numbers with `agent-working-
design`'s independent measurement, a real discrepancy surfaced: their worktree read 40
`search_docs` calls for ISO week 2026-W38 where mine read 58. Root-caused live, jointly: their
worktree was 8 commits behind `origin/main` (`git rev-parse HEAD` vs. `origin/main` confirmed the
gap), so their filesystem-mode read was a stale snapshot, not a real corpus difference. A second,
independent finding compounded it: a "closed" ISO week is never really closed — every PR merge
stages `agent-monitoring/`, so a session whose real activity happened during week W but whose PR
lands later still appends W-stamped rows well after that week's calendar dates end. Without a way
to pin a measurement to an exact, checkable git state, two sessions (or the same session before
and after) can silently compare two different corpora and report a "saving" from an advisory hook
that is really just corpus drift — undermining the entire before/after premise ticket 1 was built
to serve for Batch B's tickets 2 and 3.

## Scope
- `tools/agent-monitoring/bash_command_mix.py`: new `load_tools_rows_from_ref(ref, ...)` /
  `resolve_ref_sha(ref)`, reading shards via `git ls-tree`/`git show` against an exact ref/SHA,
  never the working tree. New opt-in `--ref` CLI flag (filesystem mode via `--data-dir` remains
  the default — see Implementation Notes for why opt-in, not default-on). `build_bash_mix_report`
  gains `measured_ref`/`measured_sha` fields (`None` in filesystem mode), surfaced in both
  `render_markdown` and `--json` output.
- Module docstring and CLI help text updated to recommend `--ref origin/main` for any before/after
  comparison, with the concrete discrepancy above as evidence.
- 8 new tests for the ref-mode path (`resolve_ref_sha`, `load_tools_rows_from_ref`, report/CLI
  wiring, a ref-mode read-only guard).

## Out of Scope
- Changing the CLI's default behavior to ref-mode-by-default — see Implementation Notes.
- `docs/agent-monitoring/README.md` — the existing "Bash Command Mix Baseline" section from ticket
  1 already exists and doesn't need a rewrite for an opt-in flag addition; the module's own
  docstring is the authoritative usage guidance.

## Acceptance Criteria
- [x] `--ref <ref>` reads `agent-monitoring/data/*/tools.jsonl` from that git ref's tree only,
      never the working tree (verified by a read-only guard test).
- [x] Report (`markdown` and `--json`) carries `measured_ref`/`measured_sha` when `--ref` is used;
      `None`/absent framing when it isn't.
- [x] `--ref origin/main` reproduces the peer's own independently-refreshed real-corpus numbers
      for W30-W39 exactly (Bash 116,168; `cd` 24,943/21.5%; `grep` 23,797/20.5%; `search_docs`
      1,534; ratio 15.51) — cross-checked live against their message, not just unit-tested.
- [x] All 8 new tests pass; full 28-test suite for `bash_command_mix.py` passes (20 from ticket 1
      + 8 new), including the corrected real-corpus test that no longer assumes false equality
      between a live working tree and a fixed prior commit (see Implementation Notes).

## Related Tickets
- `TCK-20260923-BASH-COMMAND-MIX-BASELINE` (done) — the module this hotfix amends, from earlier
  in this same session.

## Related Docs
None beyond the module's own docstring (updated in place).

## Related Stored Artifacts
None — hotfix tier, self-evident intent, no staging artifacts required per CLAUDE.md.

## Related Code Areas
- `tools/agent-monitoring/bash_command_mix.py`
- `tests/tools/test_bash_command_mix.py`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
Chose an opt-in `--ref` flag over changing the CLI's default to `--ref origin/main` (which is what
the peer literally asked for) for two reasons, disclosed rather than silently deviating: (1) ticket
1's module and its 20 tests were already verified and closed minutes earlier in this same session
— defaulting to a git-subprocess-based read path would have meant re-verifying every existing
filesystem-mode test's behavior under the new default, for a change that opt-in achieves with zero
risk to already-shipped behavior; (2) filesystem mode (`--data-dir`) still has a real, legitimate
use — a local ad-hoc check of a specific worktree's own current state — that ref-mode doesn't
replace, so "opt-in, prominently recommended" serves both needs better than a hard default. The
substance of the request (measured provenance is always checkable, `--ref origin/main` works and
is documented as the recommended choice for any before/after comparison) is fully delivered either
way.

One of the 20 pre-existing tests from ticket 1's own commit needed correcting once real-corpus
ref-mode testing exposed a false assumption in a *new* test being added here (not a pre-existing
one): a first draft of `test_load_tools_rows_from_ref_matches_working_tree_at_head` asserted the
live working tree and a `--ref HEAD` read would have identical row counts. It failed on first run
(239,472 vs. 239,500) — not a bug in the ref-mode code, but a live demonstration of exactly the
corpus-growth-between-reads problem this ticket exists to make checkable: other concurrent
sessions' own PostToolUse hooks kept appending to the shared `agent-monitoring/data/` corpus
between this session's own last commit and this test's run. Corrected the assertion to the actual
invariant that holds (`len(ref_rows) <= len(fs_rows)`, since the corpus is append-only between
commits, a fixed prior ref can never exceed a live later working-tree read) — disclosed here per
the Hard Rule against silently editing a test to force a pass; this fix corrects a wrong assertion
to the real, verified invariant, not a workaround for a red gate the underlying code was actually
failing.

## Test Summary
- `pytest tests/tools/test_bash_command_mix.py -v` — 28 passed (20 from ticket 1, unmodified in
  behavior, + 8 new ref-mode tests).
- Real-corpus CLI smoke test (`--ref origin/main --since-week 2026-W30 --through-week 2026-W39`)
  cross-checked live against the peer's own independently-refreshed numbers — exact match.

## Files Changed
- `tools/agent-monitoring/bash_command_mix.py` — `resolve_ref_sha`, `load_tools_rows_from_ref`,
  `--ref` CLI flag, `measured_ref`/`measured_sha` report fields, docstring update.
- `tests/tools/test_bash_command_mix.py` — 8 new tests; 1 existing test corrected (see
  Implementation Notes).

## Completion Summary
Added opt-in git-ref-pinned reading to `tools/agent-monitoring/bash_command_mix.py`, closing a
real reproducibility gap a live joint investigation with `agent-working-design` surfaced (a
worktree 8 commits behind `origin/main` silently produced a 45%-understated `search_docs` count
for a "closed" ISO week that, it turns out, is never really closed while PRs from that week's
sessions keep landing). `--ref origin/main` is now the documented, recommended way to run any
before/after comparison for Batch B's remaining two tickets, with the measured SHA surfaced in
both output modes so two runs' provenance is always checkable. Filesystem mode remains the
unchanged default, preserving ticket 1's already-verified behavior with zero risk. 8 new tests,
all passing; one newly-added (not pre-existing) test's flawed assumption was caught and corrected
via the real corpus itself, rather than shipped un-scrutinized. No known material gap left
unstated.
