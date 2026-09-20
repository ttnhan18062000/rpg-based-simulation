---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN

## Title
Batch 3 of the unbound-claims program: static re-confirmation of 20 already-bound mechanisms'
pre-existing caller citations — `code_trace` only, no differential test, and a real selection
effect (**re-languaged 2026-09-20, see Completion Summary addendum** — this ticket originally read
as a broader "instrument run" than what was actually done)

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Batch 3 of the 4-batch unbound-claims program. Unlike batches 1/2 (find or correct a binding),
these 20 mechanisms already carry a real `implemented_by` (most bound in earlier tickets across
this epic, with real caller evidence already recorded as plain YAML comments) but never got a
formal `verified:` block. This batch runs a real instrument (`code_trace`, re-confirming each
binding's own caller evidence directly rather than trusting the comment prose) against all 20 and
records the result.

**Governing constraint, explicit and equally weighted with prior batches**: a `contradicted`
verdict is as good a result as `observed` — this batch reports what the instrument actually found,
it does not repair code to make a claim agree with its binding.

## Scope
Instrument-verify all 20 bound-but-unverified mechanisms: `movement`, `declared_cognition_schema`,
`temporal_pressure`, `adventure_routing`, `committed_intentions`, `diplomacy`, `cultural_drift`,
`cooperation`, `resource_harvesting`, `fame`, `fidelity_drift`, `belief_institution`,
`strategic_learning_bias`, `strategic_redirection`, `concern_intake`, `event_interpretation`,
`narrative_memory`, `group_coordination`, `quest_reward_distribution`,
`commitment_pressure_consequences`.

## Out of Scope
- Adding new bindings (that's batches 1/2's own job, already done).
- Fixing any code found to be dead/uncalled during verification.
- Batch 4 (`contradicted`-verdict triage into scoped tickets) and the `xp_leveling`/`evolution`
  identity investigation — separate pieces of the same program.

## Acceptance Criteria
1. All 20 mechanisms carry a real `verified` block with `instrument: code_trace` (or better) and
   a real, specific note.
2. Every verdict reflects what was actually found, not what would make the claim look better.
3. `registry.py::validate()` clean; consumer artifacts regenerated where state changed (none did
   this batch — verification only, no state corrections needed).

## Related Tickets
- `TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION`,
  `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION` — batches 1/2,
  same program.
- `TCK-20260916-MECHANISM-ORPHAN-STATE-BATCH-VERIFICATION`,
  `TCK-20260916-MECHANISM-IMPLEMENTED-BY-BINDING`, `TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-
  POPULATION` — the earlier tickets that originally bound most of these 20, whose own caller
  evidence (already recorded as YAML comments) this batch formalizes into `verified` blocks.

## Related Docs
None new.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN/`.

## Related Code Areas
- `registries/mechanisms.yaml`
- `tests/unit/tools/test_mechanism_registry.py` (one hardcoded "real, unverified id" example,
  `movement`, swapped for `clan` since `movement` now has a real verified block)

## Assumptions / Open Questions
**Addendum, 2026-09-20, peer review of this batch after it landed**: the original framing above
("instrument runs," "100% observed") read as stronger evidence than what was actually done. See
the Completion Summary addendum for the full correction; the finding itself is not overturned, only
the language describing it.

None otherwise. All 20 verdicts came back `observed` — every one of the 20's own pre-existing
caller citations (already documented as plain comments from earlier tickets) held up under direct
re-confirmation this pass. No `contradicted` verdicts in this batch (that shape showed up in batch
2's own `calamity_intensity`, not here) — see the addendum below for why a 100% rate here is less
surprising than it looks.

## Implementation Notes
For each of the 20, the real caller citation already present as a plain YAML comment (from the
original binding ticket) was independently re-confirmed via direct grep this pass, then formalized
into a `verified: {instrument: code_trace, verdict: observed, date, note}` block. Several bindings
got a small additional confirmation beyond what the original comment stated (e.g. `diplomacy`'s
own `compute_transitions()` reconfirmed at a second real call site, `pipeline.py:260`, not just
the one the original comment cited). No code changes; no state changes.

**What this batch actually was, stated plainly (2026-09-20 addendum)**: a **static re-confirmation
of pre-existing citations**, not a differential test. The check for each mechanism was "does the
caller this earlier ticket already cited still resolve to a real, non-test call site" — never
"does toggling this mechanism's own precondition produce a different, observable outcome." All 20
used `instrument: code_trace`; none used `scenario` or `corpus_run`. This is accurately recorded in
each entry's own `instrument` field — the field itself was never mislabeled — but this ticket's own
prose ("instrument run," "100% observed") did not say so plainly enough for a reader to tell the
difference from a stronger claim.

**The selection effect, named explicitly per peer review**: these 20 were not a random or
adversarial sample of the registry's own bound-but-unverified mechanisms — they were selected
*because* they already carried a real caller citation from an earlier ticket in this epic. A 100%
pass rate on a population pre-filtered for its own prior evidence of passing is close to guaranteed
before any checking happens. See `docs/plans/mechanism_claims_as_tests_initiative.md` §3.3 for the
full write-up of this as its own named failure-adjacent shape, distinct from §3.1's search failures
and §3.2's misattribution.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py`: one existing test's hardcoded example id swapped
(`movement` → `clan`) since `movement` gained a real verified block this pass. Full `tests/unit/
tools/` suite: 260 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5 blocking checks:
clean (no drift, since no `state` value changed this batch).

## Files Changed
- `registries/mechanisms.yaml` — 20 `verified` blocks added, no state/binding changes.
- `tests/unit/tools/test_mechanism_registry.py` — one hardcoded example id swapped.
- `docs/brainstorm/mechanism_verification_view.md`, `mechanism_registry_view.md`,
  `mechanism_system_rollup_view.md`, `mechanism_registry.html` — regenerated (verification-count
  fields moved; no badge/tier changes since no state changed).

## Completion Summary
**Done.** All 20 bound-but-unverified mechanisms now carry a real `verified` block. Every verdict
came back `observed` — each binding's own pre-existing caller citation held up under direct
re-confirmation. No code fixed, no states changed, consistent with this batch's own scope as pure
verification. Batch 4 (`contradicted`-verdict triage, 6 mechanisms) and the `xp_leveling`/
`evolution` identity investigation remain, landing in the same PR per the user's own call.

**Addendum, 2026-09-20, peer review the same PR cycle**: the finding stands — all 20 pre-existing
citations independently re-confirmed accurate, `instrument: code_trace` correctly recorded on
every entry. What was wrong was the *description* of that finding: prose calling it an "instrument
run" with a "100% observed" rate, in a PR that had just corrected 7 of 47 claims in its own
preceding batch, read as stronger, more adversarial verification than a static re-check of
already-cited callers actually is. Re-languaged per direct peer challenge (3 questions: which
instrument, did any meet a differential test, was there a near-miss) rather than by re-verifying or
downgrading any of the 20 — the peer's own explicit instruction was "re-language, don't re-run,"
since the data was never wrong, only the story told about it. Two durable fixes came out of the
same review, not scoped to this ticket alone: `runtime_verified_share` added as a first-class
metric to the system rollup view (`TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY`,
registry-wide and per-system, so this exact gap can't hide in prose again), and the selection effect
recorded in `docs/plans/mechanism_claims_as_tests_initiative.md` §3.3 as its own named shape.
