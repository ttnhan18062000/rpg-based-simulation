---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS
artifact_type: investigation
tags: [content, determinism]
---

# Investigation — TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Context scan
`mcp__knowledge-search__search_docs` and `graphify query` run first, per CLAUDE.md's mandatory
Context Scan. Surfaced `test_grade_regression.py`'s own real structure (`_within_band()`,
`_within_score_tolerance()`, `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS`, `_load_calibration_report()`)
and prior SimQ-anchor tickets (`TCK-20260630-SIMQ-ANCHORS`, `TCK-20260707-...`,
`TCK-20260805-SIMQ-GRADE-ORDER-F-BAND-GAP`) establishing the band-tolerance mechanism this ticket
builds on, not replaces.

## User decision (this session)
Given two other tickets landed the same day (`TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE`
and the profile-sweep contention-detection hotfix) already established this session's pattern for
resource-heavy work under shared-machine contention, the user was asked to choose the
`grade_anchors.json` fix direction up front. **Chosen: add a flagging gate only** — not a batch
regeneration of all 81 anchors. This explicitly does not resolve the 61 already-confirmed-drifted
anchors; it is scoped to stopping *new* silent drift going forward, with regeneration left as a
separate, explicitly-deferred follow-up requiring per-anchor human review (the ticket's own
Assumptions section already flags that curated thresholds shouldn't be batch-copied without
eyeballing the biggest swings).

## Root cause, confirmed more precisely than the ticket's own framing
The ticket's Request Summary attributes the 61/81 drift to "M2's 15-ticket batch, M3's Reproduction
epic, ... none of which regenerated these fixtures." That's the proximate cause, but investigation
found the real *structural* reason drift went completely undetected:

1. `test_grade_regression.py`'s anchor-comparison tests
   (`test_grade_within_anchor_band`/`test_grade_within_anchor_band_long_run`) load
   `data/calibration/<run_key>/quality_report.json` via `_load_calibration_report()` — **not** a
   live engine re-run. If that file is absent, the test `pytest.skip()`s (never fails).
2. `data/calibration/` is gitignored — confirmed via `git check-ignore -v data/calibration/` — and
   `git ls-files data/calibration/` returns zero tracked files. It is purely a developer-machine-
   local artifact.
3. `.github/workflows/test.yml` never runs any calibration step — confirmed via
   `grep -n "simq\|evaluate_simq\|calibrat" .github/workflows/test.yml`, the only match is the
   unrelated `simq-corpus-diversity-slow-isolated` slow-tier job.
4. **Confirmed directly, empirically**: running `pytest tests/simulation_quality/test_grade_regression.py -m "not slow"`
   in a clean environment (no `data/calibration/` present, matching real CI exactly) produces
   **64 SKIPPED, 7 PASSED, 0 FAILED**. Every single one of the 61 `FAST_ANCHOR_KEYS` anchor checks
   (plus 2 more named tests and the file-validity test) silently skips. The 7 that pass are pure-
   logic tests needing no calibration data at all (grade-order constants, tolerance-override table
   shape, etc.) — genuinely zero anchor-vs-current-behavior comparisons ever execute in CI.
5. `test_grade_regression.py`'s own module docstring instructs `make calibrate` to regenerate
   anchors — **that Makefile target does not exist** (`grep -n "^calibrate" Makefile` — no match;
   confirmed via `.PHONY` target list too). A second, independent documentation-drift bug, fixed in
   this ticket alongside the real gate (see Files Changed) since it's directly in the same doc block
   and would otherwise mislead the next person who tries to follow the recipe.

**This means "no process to prevent recurrence" (the ticket's own title) is precisely accurate**:
the mechanism that looks like a regression gate (a parametrized pytest suite with real tolerance-
band logic) has never executed a single real comparison in this repo's CI history, for any of the
79 anchors it nominally covers.

## The real fix already exists — it just was never wired into CI
`tools/evaluate_simq.py` (confirmed via direct read) is exactly the tool needed: diffs
`data/calibration/` against `grade_anchors.json`, with a real engine re-run mode (no `--dry-run`)
that populates fresh calibration data for fast-tier (<=500t) scenarios by default, `--include-slow`
for 1000t/2000t. Real documented exit codes: 0=all within band, 1=REGRESS detected, 2=setup error.
`make simq-full-audit-full` already chains: (1) engine re-run + anchor diff via `evaluate_simq.py`,
(2) `test_grade_regression.py -m "not slow"` (now exercising real data, not skipping), (3)
`tools/simq_audit_gaps.py` (read-only anchor-coverage + parity-ledger-candidate scan, always exits
0). **None of these three Makefile targets required any code changes** — this ticket's fix is pure
CI wiring plus the docstring correction, reusing fully-built tooling.

## Why the new CI job must be informational, not blocking
61/81 anchors are *already* known-drifted (confirmed by this ticket's own real
`tools/evaluate_simq.py` run — see Test Summary for the fresh, direct confirmation, not the
2-day-old sweep numbers the ticket text cites). If the new job hard-failed the build, every single
push to `main` would fail immediately over already-known, already-accepted-for-now drift — a
strictly worse outcome than today's silent skip, and one the user's own chosen fix direction
("flagging gate only... doesn't resolve the 61 already-drifted anchors") explicitly rules out.
Mirrored this repo's own existing "Type check (informational)" job pattern (`continue-on-error:
true`) instead of inventing a new mechanism.

## Why push-to-main-only, not every PR
`evaluate_simq.py`'s default engine re-run mode re-simulates all fast-tier (<=500t) scenarios for
real — genuinely CPU/wall-clock work, not a cheap check. Mirrored the "Slow regression" job's own
already-established trigger condition (`github.ref == 'refs/heads/main' || schedule ||
workflow_dispatch`) exactly, per `TCK-20260818-STANDARD-SLOW-REGRESSION-OFF-PR-PATH`'s own
precedent for keeping expensive re-simulation off the PR-blocking fast path.

## Why a new job, not adding this to the existing "Simulation quality" PR-gating job
`tests/simulation_quality/test_grade_regression.py`'s own parametrized anchor tests already run
inside the existing PR-gating "Simulation quality" job today (`pytest tests/simulation_quality -m
"not slow and not extra_slow"`) — they just silently skip there. Wiring a real engine re-run into
*that* job would make it start genuinely comparing against known-drifted anchors on every PR,
immediately blocking all PRs on pre-existing drift this ticket deliberately does not resolve. A
separate, informational, push-to-main-only job avoids that entirely while still making drift
visible.

## Machine-contention check (same discipline as this session's earlier profile-sweep ticket)
Checked `uptime`/`ps aux` before running the real `tools/evaluate_simq.py` engine re-run locally
(needed regardless of gate design, to satisfy this ticket's own AC #1 — "all 81 run_keys confirmed
either stale or current"): load average 0.04/0.16/0.21 on 6 cores, all other Claude sessions'
processes at <4% CPU — genuinely idle, unlike the earlier profile-sweep ticket's contended machine.
Ran the real fast-tier comparison for real (not deferred), then `--include-slow` for the remaining
18 slow-tier keys once fast-tier completed.

## Confirmed fresh AC #1 breakdown (supersedes the ticket's own 2-day-old sweep numbers)
First pass, `tools/evaluate_simq.py` alone: only 3/630 pillar REGRESS — but this tool only checks
the letter-grade band tolerance (`_within_band`), confirmed via direct source read
(`grep -n "_within_band\|_within_score_tolerance" tools/evaluate_simq.py` — only the former
appears). It is missing the score-magnitude tolerance check `test_grade_regression.py`'s own
pytest suite documents as a second, independent regression class ("catches within-band magnitude
regressions the letter-only check cannot see"). This silently undercounts real drift — e.g. an
A→S grade transition is within the ±1 band (passes `evaluate_simq.py`) even if the underlying
score more than doubled (fails the score-tolerance check), exactly the kind of case the ticket's
own causal-isolation test found (SOCIAL: A/1.8 → S/3.97).

Re-ran the *complete* check via the real pytest suite against the now-populated `data/calibration/`
(`pytest tests/simulation_quality/test_grade_regression.py -v`, both fast + slow):
**64 failed, 25 passed**. Breakdown of the 64 failures: 44/61 `FAST_ANCHOR_KEYS`, 18/18
`SLOW_ANCHOR_KEYS` (100% of the slow tier has drifted), plus both named isolated tests
(`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`..._execution_isolated_grade_anchor`). Total: 64/81 real anchor comparisons confirmed drifted,
17/81 confirmed current, 2 probe keys confirmed out of scope (unchanged from the ticket's own
finding — not covered by any parametrize list). This is fresh, real, live evidence — not an
estimate — and closely matches (grew slightly from) the ticket's own 61/81 figure from 2 days
earlier, confirming the drift is a live, ongoing pattern rather than a one-time historical event.

## Files that will change
- `.github/workflows/test.yml` — new `simq-grade-drift` job (informational, push-to-main-only).
- `tests/simulation_quality/test_grade_regression.py` — module docstring: fixed the broken
  `make calibrate` reference (target doesn't exist) and added a CI note pointing at the new job.
- No production code changes; no `grade_anchors.json` mutation (explicitly deferred per the user's
  chosen fix direction).
