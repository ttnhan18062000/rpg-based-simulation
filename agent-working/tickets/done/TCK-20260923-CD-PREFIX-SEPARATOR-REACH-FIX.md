---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260923-CD-PREFIX-SEPARATOR-REACH-FIX
phase: done
date: 2026-09-23
tags: [ai, agent-monitoring, observability, process-improvement]
---

# TCK-20260923-CD-PREFIX-SEPARATOR-REACH-FIX

## Title
`cd_prefix_advisory_hook.py`: widen the separator pattern — `&&`-only missed 97.7% of the
population it targeted

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
`agent-working-design`'s verify pass on `TCK-20260923-CD-PREFIX-ADVISORY-HOOK` found a real
defect: `_CD_PREFIX_PATTERN = r"^\s*cd\s+(\S+)\s*&&"` requires `&&` as the separator between the
`cd` and the following command. Measured against `origin/main@75ab942b4`, W30-W39 (24,943
cd-headed Bash calls): `&&`-only matched 583 (2.3%); widening to `&&`/`;`/newline matched 11,900
(47.7%). A further 13,039 (52.3%) are a bare `cd <path>` with nothing chained after — a different
pattern, correctly out of scope for a *prefix* nudge, but the dominant real form among the
prefixed calls is newline-separated (`cd <path>\n<command>`), not `&&`. Of the 11,900
separator-matched calls, 97.1% target a repo/worktree root — precisely the redundant shape the
ticket was built to catch. Independently re-verified before touching any code: 583/2.3%,
11,900/47.7%, 13,039/52.3%, 97.1% repo-root share — matches the peer's own numbers to within
single-digit counts (consistent with ordinary corpus growth between the two measurements, not a
methodology disagreement).

## Scope
- `tools/agent-monitoring/cd_prefix_advisory_hook.py`: widen `_CD_PREFIX_PATTERN` from
  `&&`-only to `(?:&&|;|\n)`. The exact-normalized-path-equality detection rule is unchanged —
  this fix widens *reach* (what counts as a prefixed `cd`), not *precision* (what counts as
  redundant).
- Advisory message text generalized from "`cd <path> &&` prefix" to "leading `cd <path>`" (no
  longer implies `&&` specifically).
- Module docstring: replaced the stale "(TCK to be filed — Batch B ticket 2 of 3...)" placeholder
  with the real ticket ID, and replaced the private-memory `[[feedback_agent_tooling_checks_
  proportionate]]` wikilink (unresolvable outside this session's own memory store) with a prose
  statement of the rule, citing `CLAUDE.md`'s Proactive Tool Use section — both flagged by the
  peer's verify pass as separate, minor issues, fixed in the same commit since they're in the same
  docstring block.
- Tests: 2 new positive cases (newline-separated — the dominant real shape — and `;`-separated),
  1 new negative case (newline-separated `cd` into a genuinely different directory, closing the
  same blind spot on the "must not flag" side).

## Out of Scope
- The bare-`cd`-with-nothing-chained-after case (52.3% of cd-headed calls) — a structurally
  different pattern (no prefix to advise on; the whole call IS the `cd`), not something a
  *prefix* nudge can address. Worth a sentence here since it's the largest single slice of `cd`
  calls, but not a gap in this ticket's own scope.
- Re-measuring the hook's actual behavioral effect post-fix — `bash_command_mix.py --ref
  origin/main` remains the standing instrument for any future before/after check.

## Acceptance Criteria
- [x] `_CD_PREFIX_PATTERN` matches `&&`, `;`, and newline-separated `cd <path>` prefixes.
- [x] Exact-normalized-path-equality rule unchanged (no loosening of the redundancy criterion —
      verified by the new negative test: a newline-separated `cd` into a *different* directory is
      still correctly unflagged).
- [x] Independently re-verified reach numbers from this session's own `--ref`-pinned measurement
      (matching the peer's numbers): `&&`-only 583/2.3%, widened 11,900/47.7%, bare 13,039/52.3%,
      97.1% repo-root share among widened matches.
- [x] Stale docstring placeholder and unresolvable private-memory wikilink both fixed.
- [x] All 18 tests pass (15 original + 3 new); manually verified end-to-end against the wired
      module with a real newline-separated payload.

## Related Tickets
- `TCK-20260923-CD-PREFIX-ADVISORY-HOOK` (done) — the ticket this amends; the defect was found
  during `agent-working-design`'s verify pass on that ticket, not during its own original
  implementation or test-writing.
- `TCK-20260923-BASH-COMMAND-MIX-BASELINE` / `TCK-20260923-BASH-MIX-REF-PINNING` (done) — the
  `--ref origin/main`-pinned measurement instrument used both to find and to independently
  re-verify this defect's reach numbers.

## Related Docs
None beyond the module's own docstring (updated in place).

## Related Stored Artifacts
None — hotfix tier, self-evident intent, no staging artifacts required per CLAUDE.md.

## Related Code Areas
- `tools/agent-monitoring/cd_prefix_advisory_hook.py`
- `tests/tools/test_cd_prefix_advisory_hook.py`

## Assumptions / Open Questions
None outstanding.

## Implementation Notes
This defect was caught by a peer session's verify pass, not by this session's own testing —
disclosed directly: the original 15 tests all exercised the `&&` shape exclusively, so the test
set shared the exact same blind spot as the regex it was testing, and gave false confidence. The
2 new positive tests target the shapes that actually appear in the real corpus (newline as the
dominant separator, `;` as a rare but real one) rather than only the originally-assumed shape —
the fix most directly aimed at not repeating this exact class of blind spot.

Before writing any fix, independently re-derived the peer's own reach numbers from a fresh
`--ref origin/main` read (script-based, matching `bash_command_mix.py::load_tools_rows_from_ref`'s
own approach) rather than accepting the report at face value — confirmed real and matching within
normal corpus-growth noise, not a peer's own measurement bug. Two additional, unrelated small
issues the peer flagged in the same docstring block (a stale "TCK to be filed" placeholder, and a
private-memory wikilink unresolvable to anyone reading only the repo) were fixed in the same
commit rather than deferred, since they were in the same touched lines and the peer explicitly
left the fix shape to this session's own judgment.

## Test Summary
- `pytest tests/tools/test_cd_prefix_advisory_hook.py -v` — 18 passed (15 original + 3 new).
- Manual end-to-end: piped a real newline-separated stdin payload (`cd <worktree-root>\necho hi`)
  through the fixed, wired module — fired correctly with the updated message text.
- Independent reach re-verification against `origin/main@75ab942b4`-pinned corpus (script-based,
  not just unit tests): 583/2.3% (`&&`-only), 11,900/47.7% (widened), 13,039/52.3% (bare),
  97.1% repo-root share — matches the peer's own independently-reported numbers.

## Files Changed
- `tools/agent-monitoring/cd_prefix_advisory_hook.py` — widened separator pattern, generalized
  advisory message text, fixed stale docstring placeholder and private-memory wikilink.
- `tests/tools/test_cd_prefix_advisory_hook.py` — 3 new tests (2 positive: newline/`;`-separated;
  1 negative: newline-separated into a different directory).

## Completion Summary
Fixed a real reach defect a peer session's verify pass found in `TCK-20260923-CD-PREFIX-ADVISORY-
HOOK`: the shipped hook's `&&`-only separator pattern matched only 2.3% of the `cd`-headed Bash
calls it was built to advise on, missing the dominant real shape (newline-separated, 47.7% of the
population once `&&`/`;` are included, 97.1% of which target a repo/worktree root — the exact
redundant-prefix pattern the ticket describes). Independently re-verified the peer's reach numbers
from a fresh `--ref`-pinned read before touching any code, confirming the defect was real rather
than a peer measurement error. Widened the separator regex to `(?:&&|;|\n)` while leaving the
exact-path-equality redundancy rule untouched, added tests for the shapes that were previously
blind-spotted on both the positive and negative sides, and fixed two smaller, unrelated docstring
issues (stale ticket-ID placeholder, unresolvable private-memory citation) flagged in the same
verify pass. No known material gap left unstated.
