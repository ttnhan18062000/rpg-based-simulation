---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK
phase: open
date: 2026-08-10
tags: [simulation-quality, calibration, performance]
---

# TCK-20260810-SIMQ-EVALUATE-SLOW-TIER-SCOPE-LEAK

## Title
`make simq-full-audit-full` chronically times out because `tools/evaluate_simq.py`'s default
(no `--scenario`) engine re-run mode ignores tier scoping and re-runs every key in
`grade_anchors.json`, including the expensive SLOW tier — contradicting the Makefile target's
own documented "fast (<=500t) scenarios only" behavior

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Two separate sessions today confirmed `make simq-full-audit-full` timing out at 590s (once
during the precursor `simq-audit` run `SIMQ-AUDIT-20260810T032558Z`, a real instance of a
chronic condition disclosed but never investigated). Root cause traced: `tools/evaluate_simq.py`
(`tools/evaluate_simq.py:197-200`) — when `--scenario` is not passed and `--dry-run` is not set —
sets `scenarios = anchor_keys`, i.e. **every** key in `grade_anchors.json` (81 total), not just
the `FAST_ANCHOR_KEYS`-equivalent (<=500t) subset (60 keys). `docs/simulation_quality/
audit_workflow.md:103` and the Makefile's own comment (`Makefile:354`, "re-runs the engine for
all fast (<=500t) scenarios first") both document fast-only behavior; the actual code does not
honor that scoping.

Measured real per-scenario cost directly: a 200t scenario takes ~4.6s, a 500t scenario ~14.6s, a
2000t (SLOW-tier) scenario ~39s. With 60 fast keys (48×200t + 12×500t ≈ 396s) plus 18 SLOW keys
(1000t/2000t, ~20-39s each, ≈ 450s+) plus 3 extra keys not in either tier tuple, the real total
comfortably exceeds the 590s timeout — confirming the SLOW-tier inclusion is the dominant driver,
not a general engine performance problem.

## Scope
- Scope `tools/evaluate_simq.py`'s default (non-`--scenario`, non-`--dry-run`) scenario list to
  fast-tier only (ticks <= 500, parsed via the existing `_parse_run_key()`), matching the
  Makefile target's own documented behavior.
- Preserve `--dry-run` behavior unchanged (it reads already-computed reports, cheap regardless of
  tier — no reason to scope it).
- Preserve explicit `--scenario <key>` behavior unchanged (already scenario-specific).
- Add a `--include-slow` opt-in flag (or equivalent) so a user who genuinely wants the old
  all-keys engine re-run behavior can still get it explicitly, rather than silently losing SLOW
  tier re-run capability entirely.

## Out of Scope
- `make simq-full-audit-slow` (pytest-only, no engine re-run) — unaffected, not touched.
- The D06 F6 wall-clock watchdog non-determinism mechanism itself — a separate, already
  investigated and accepted engine behavior (`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`
  already confirmed SLOW-tier stability under it); this ticket does not touch `kernel.py`.
- Bulk cleanup of stale monitoring duration records (separate queued task).

## Acceptance Criteria
- [x] `tools/evaluate_simq.py`'s default engine-re-run scenario list is scoped to <=500t keys
- [x] `--include-slow` (or equivalent) opt-in preserves the old full-corpus behavior on request
- [x] `make simq-full-audit-full` completes well within a reasonable timeout on a real re-run
- [x] Existing `--dry-run` and `--scenario` behavior unchanged (regression-tested)

## Related Tickets
- TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION (DONE, same session — surfaced this
  timeout as a side-effect of its own precursor `simq-audit` run)
- TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY (DONE — established SLOW-tier watchdog stability,
  a related but distinct mechanism from this ticket's own scope-leak finding)
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (new follow-up filed from this ticket's
  own verification-run side effects — real corpus recalibration + newly-found FAST-tier
  non-determinism, both disclosed and out of scope here)

## Related Docs
- `docs/simulation_quality/audit_workflow.md` (documents the fast-only intent this ticket
  restores)
- `docs/audits/D06_longrun_health.md` F6 (the related, distinct watchdog mechanism)

## Related Stored Artifacts
None (hotfix, no staging artifacts).

## Related Code Areas
- `tools/evaluate_simq.py` (`_parse_run_key`, `main()` scenario-selection logic)
- `Makefile` (`simq-full-audit-full` target, if the fix needs a flag passed through)

## Assumptions / Open Questions
None — root cause directly confirmed via real timing measurements and direct code read.

## Implementation Notes
Added a `--include-slow` flag to `tools/evaluate_simq.py`. Extracted the scenario-selection logic
into a new, directly-testable `_select_scenarios(anchor_keys, scenario, dry_run, include_slow)`
helper (previously inlined in `main()`) so the fix could be unit-tested without invoking a real
engine run. Default (no `--scenario`, no `--dry-run`, no `--include-slow`) now filters
`anchor_keys` to `ticks <= 500` via `_parse_run_key()`, matching the Makefile target's documented
"fast (<=500t) scenarios" behavior. Keys that fail to parse (defensive) are treated as fast
(included) rather than silently dropped, since a parse failure is already surfaced elsewhere by
the per-scenario loop — filtering must not be the first place an unparseable key silently
disappears. `--include-slow` restores the prior all-keys behavior for a user who explicitly wants
a full corpus re-run and is willing to budget for it. `--dry-run` is never tier-filtered (cheap
regardless of tier, reads already-computed reports). `--scenario <key>` always wins over the
default filter. No `Makefile` change was needed — `simq-full-audit-full` already invokes
`evaluate_simq.py` with no args, so it inherits the new fast-tier-only default automatically.

## Test Summary
Added `tests/tools/test_evaluate_simq_scenario_scope.py` (8 new tests, not 3 as originally
planned -- broadened coverage while writing): default (no flags) scenario list excludes
`_1000t`/`_2000t`/other >500t keys (including a 500t/501t boundary-inclusivity check);
`--include-slow` restores the full key list; `--dry-run` is never tier-filtered even without
`--include-slow`; `--scenario` always wins regardless of other flags; an unparseable key is kept,
not silently dropped. All 8 confirmed to fail against the pre-fix code via git-stash bisection
(collection-level `ImportError` on the extracted `_select_scenarios` helper, which did not exist
pre-fix). `pytest tests/tools/test_evaluate_simq_scenario_scope.py -v` -- 8 passed.

Real timing verification: `timeout 550 python3 tools/evaluate_simq.py` (no `--scenario`, no
`--include-slow` -- the fixed default, fast-tier-only path) completed in **370s** (`real
6m10.221s`), well within the old 590s timeout that previously killed an unscoped (fast+slow) run
before it could finish at all. `--dry-run` and `--scenario <key>` end-to-end invocations
manually re-verified unaffected (still process the full 81-key anchor file / the single
requested key respectively).

**Disclosed, not fixed by this ticket** (real corpus findings, out of scope -- this ticket is a
pure tooling/scoping fix): the fast-tier-only re-run above exited 1 with 12 real REGRESS pillars
across `crowded_frontier`, `frontier_marches`, `generated_frontier_3_42`, `quest_dense_frontier`,
`simq_scale_stress`, and `lifecycle_full_coverage_world` -- keys with stale or entirely-missing
`quality_report.json` data that had never been re-run since
`TCK-20260808-MONSTER-ROLE-MISTAGGING-INVESTIGATION` (SUB-384). Most match the already-confirmed
COMBAT C->A / PROGRESSION C->A cascade pattern exactly. Separately, re-running
`simq_routing_test_seed42_500t` (already recalibrated by
`TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION`) 3 more times just now showed real
run-to-run variance in PROGRESSION (event_count 10/11/11, score -0.272/-0.300/-0.249) and
COGNITION (event_count 194/196/194) beyond score tolerance -- directly opposite the bit-identical
reproducibility confirmed earlier today for `urban_political_seed42_500t`'s SOCIAL score. This is
a genuinely new finding: FAST-tier (<=500t) non-determinism, previously only confirmed absent for
one SLOW-tier reliability sample (`TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`) and one FAST-tier
spot-check (this session's own `urban_political_seed42_500t`) -- neither of which generalizes to
`simq_routing_test`. Both findings handed to a new follow-up ticket rather than fixed here or
silently absorbed.

## Files Changed
- `tools/evaluate_simq.py` (extracted `_select_scenarios()` helper, scenario-scoping fix,
  `--include-slow` flag, updated module docstring/usage)
- `tests/tools/test_evaluate_simq_scenario_scope.py` (new, 8 tests)
- `docs/simulation_quality/audit_workflow.md` (documents the new `--include-slow` flag)

## Completion Summary
Confirmed and fixed the chronic `make simq-full-audit-full` timeout: `tools/evaluate_simq.py`'s
default engine-re-run mode was silently re-running the expensive SLOW tier (1000t/2000t) on every
invocation despite the target's own documented "fast-only" contract, adding ~450s+ of
unnecessary, undocumented engine compute. Fixed by scoping the default scenario list to <=500t,
with an explicit `--include-slow` opt-in preserving the old full-corpus behavior for anyone who
wants it. No behavior change to `--dry-run` or `--scenario`-scoped invocations. Real timing
verification: 370s vs. the prior unbounded run's 590s timeout (which never even finished).
Directly resolves the timeout two separate sessions hit today, closing a real,
previously-disclosed-but-uninvestigated chronic condition (queued task #129).

Verifying the fix (a real fast-tier-only engine re-run) had a genuine, disclosed side effect: it
regenerated calibration data for scenarios that had never been re-run since SUB-384, surfacing 12
real REGRESS pillars (the same already-understood cascade pattern on previously-unverified keys)
plus a new, distinct finding of real run-to-run non-determinism on `simq_routing_test_seed42_500t`
specifically (FAST-tier, not previously covered by any multi-trial reliability check). Both are
out of this ticket's own scope (a pure tooling fix, no anchor data touched) and handed to
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` rather than fixed or silently absorbed
here.
