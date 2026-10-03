---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260804-EXPANSION-RATE-WIRING
artifact_type: test_plan
tags: [agent-monitoring, observability]
---

# Test Plan — TCK-20260804-EXPANSION-RATE-WIRING

Written for the plumbing-only direction investigation.md recommends (Option A): add optional,
never-fabricated `expansion_reason`/`expansion_count` pass-through parameters to the 3
`wrap_*()` functions in `tools/retrieval_events.py`, with no new escalation/retry logic anywhere.
If Plan instead chooses Option B (a minimal real trigger for one producer), this test plan's
first three classes still apply verbatim (the pass-through mechanism is identical either way);
only the additional producer-specific trigger tests would need Plan-phase elaboration not
written here, since investigation.md's evidence argues strongly against Option B.

## New Tests Required

Extend the existing per-wrapper test classes in `tests/tools/test_retrieval_events.py`
(`TestWrapHybridRetrieval`, `TestWrapRetrievalCacheCheck`, `TestWrapContextPacketAssembly`) —
do not create new top-level classes, to keep the 1-class-per-wrapper convention already
established.

| Test | Type | Assertion | Covers |
|---|---|---|---|
| `test_wrapper_omits_expansion_fields_when_not_supplied` (one per wrapper class, 3 total) | unit | Calling the wrapper with no `expansion_reason`/`expansion_count` kwargs produces an emitted record with `"expansion_reason" not in written` and `"expansion_count" not in written` (never a silent `None`/`0` — the field must be genuinely absent, matching `emit_retrieval_event`'s existing pattern of only including keys the caller actually passed via `**retrieval_fields`) | AC5 (never fabricated) |
| `test_wrapper_forwards_expansion_fields_when_supplied` (one per wrapper class, 3 total) | unit | Calling the wrapper with `expansion_reason="manual_widen"`, `expansion_count=1` produces an emitted record with those exact values, verbatim, unmodified | AC1 (plumbing works) |
| `test_expansion_rate_reads_zero_percent_on_real_corpus_absent_any_real_trigger` | integration | Run `compute_retrieval_metrics()` (already-existing function, unchanged) against the real `agent-monitoring/events.jsonl` retrieval-event cohort and assert `expansion_rate == 0.0` — an explicit, disclosed assertion that this is the *honest current state*, not a bug, and a regression guard against a future accidental fabrication making this silently non-zero without a real producer change | AC3 (no fabricated number) |
| `test_wrap_functions_never_fabricate_expansion_reason_internally` (one test, checks all 3) | unit/static | For each of the 3 wrapper functions, call with a full realistic kwargs set but no `expansion_reason`/`expansion_count`, across multiple varied inputs (e.g. a cache MISS, a `noisy` adequacy_verdict, a nonzero `exclusion_reason_counts`) — none of these conditions should cause the wrapper to auto-populate `expansion_reason`/`expansion_count` on its own. Guards against a future edit accidentally wiring `adequacy_verdict == "noisy"` or similar into an auto-expansion signal, which investigation.md's Anti-Drift Hazards explicitly forbids | AC5 |

## Existing Tests Requiring No Change

- `test_wrapper_emits_exactly_one_retrieval_event` and all other existing `TestWrapHybridRetrieval`/
  `TestWrapRetrievalCacheCheck`/`TestWrapContextPacketAssembly` tests — none assert on the absence
  of `expansion_reason`/`expansion_count` keys explicitly today, so adding an optional parameter
  with no default population does not change any existing assertion's truth value. Verify this by
  re-running the full `tests/tools/test_retrieval_events.py` suite after the change — zero existing
  tests should need modification (distinct from the sibling ticket
  TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC, which DID require one existing test's exact-key-set
  assertion to change — that pattern does not repeat here since `emit_retrieval_event`'s underlying
  record shape is dict-based and additive, not enumerated by a fixed key-set test at this layer).
- `tests/tools/test_generate_retro.py`'s existing `expansion_rate`-adjacent tests (if any — check for
  `test_compute_retrieval_metrics_expansion_rate*` during Plan/Implement) should already pass
  unchanged, since `compute_retrieval_metrics()`'s formula itself is untouched.

## Regression Coverage

Run scoped: `pytest tests/tools/test_retrieval_events.py tests/tools/test_generate_retro.py -v`
after implementation — must show 0 failures and 0 skips, with the new tests included in the pass
count.

## What This Test Plan Deliberately Does Not Cover

Per investigation.md's central finding, this ticket should not implement any real expansion
trigger — so there is no test here asserting a specific escalation condition (e.g. "a noisy
adequacy_verdict causes an automatic expansion"), because no such behavior should exist. If Plan
overrides this recommendation and chooses Option B, Plan must expand this test_plan.md itself with
producer-specific trigger tests before Implement proceeds — this document does not pre-authorize
that path.
