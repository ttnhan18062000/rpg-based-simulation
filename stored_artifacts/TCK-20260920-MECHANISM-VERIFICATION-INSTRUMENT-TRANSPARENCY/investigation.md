---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY

## The 3 questions, answered directly

1. **Instrument**: all 20 of batch 3's mechanisms are `instrument: code_trace`. Confirmed by direct
   query of the registry. Zero `scenario`, zero `corpus_run`.
2. **Differential requirement**: none met it. Each check was "does a pre-existing caller citation
   still resolve," never "does toggling the mechanism's own precondition change the outcome."
3. **Near-miss**: none. Every one of the 20 was selected because it already had citation evidence
   from an earlier ticket — no case was picked without a prior expectation it would pass.

## The numbers

Registry-wide runtime-verified share: 24 code_trace / 5 scenario / 4 corpus_run (33 total verified,
27.3% runtime) before batch 3 → 73 code_trace / 5 scenario / 4 corpus_run (82 total verified, 11.0%
runtime) after. Confirmed by direct computation against both the pre-batch-1 registry snapshot and
the current one.

## What was fixed and how

Not re-verification. `_rollup_stats()`'s own `runtime_verified`/`static_verified` counts already
existed; only the RATE was missing from what gets rendered. Added `runtime_verified_share`
(denominator `verified`, matching this file's own zero-count convention for existing rates).
Rendered in both consumer views with baseline comparison. Re-languaged the prior ticket's own
Title/Assumptions/Implementation Notes as dated addenda. Recorded the selection effect in
`docs/plans/mechanism_claims_as_tests_initiative.md` §3.3.
