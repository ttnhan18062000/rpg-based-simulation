---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION
artifact_type: investigation
tags: [architecture, schema, simulation-quality]
---

# Investigation — TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION

## Trigger

Claims-as-tests phase 1, scoped per peer review as **state-versus-caller-count mismatch
detection**, not presence/absence: every one of the four real registry state errors found by hand
this epic (`camp`, `motivation_doctrine`, `causal_spatial_memory`, `commitment_betrayal`'s
mis-binding) was a wrong state, never a missing entry, and `orphan`/`gated` are opposite
conclusions a reader could act on backwards.

## Headline finding: the false-positive rate, not the defect count

First real run against the committed registry (20 of 89 mechanisms checkable via `implemented_by`)
produced **4 raw findings**. Investigating each one directly (never trusted at face value) found:

**2 of 4 were real bugs in the detector itself, both fixed before this ticket closed:**

1. **`diplomacy` (state_with_zero_callers)** — false positive. Root cause: the detector's first
   draft only extracted class names (`^class \w+`) as "the symbol to count callers for."
   `diplomacy`'s own implementing module, `src/domains/faction/diplomatic_state_machine.py`, is
   pure free functions (`compute_transitions`, `events_from_transitions`,
   `compute_common_enemy_pairs`) — no class at all. A class-only extractor found nothing to check,
   silently reported zero callers, and flagged a mechanism that is genuinely live (`compute_
   transitions` is called directly from `engine/pipeline.py:260`). **Fix**: extract module-level
   functions too, not just classes (`_symbol_names()`).
2. **`strategic_redirection` (orphan_with_callers)** — false positive. Root cause: the detector's
   first draft searched whole-file text for the class name, with no distinction between a real
   code reference and a comment. `strategic_redirection`'s only repo-wide mention outside its own
   file is a comment in `intelligence.py:611` ("Hoisted logic from StrategicRedirectionSystem") —
   confirming, not contradicting, its registered `orphan` state. **Fix**: strip line comments and
   docstring bodies before matching (`_real_callers()`'s per-line `_strip_line_comment()`).

**1 of 4 is a confirmed, real heuristic failure, kept in the report but flagged low-confidence:**

3. **`temporal_pressure` (skeleton_not_stub)** — false positive, heuristic miscalibration.
   `skeleton` in this registry's own taxonomy means "an early, minimal implementation," not
   "an empty stub" — a 46-line file with real logic can legitimately be a skeleton relative to
   what full behavior would need. The check's own "8+ substantive lines = not a stub" threshold
   conflates "has more than a few lines of code" with "is functionally complete," which is not the
   same claim `skeleton` vs. `done`/`partial` actually makes. **Disposition**: kept in the tool as
   a `low` confidence check (per Scope item 4's own instruction that this check pays less),
   explicitly documented here as demonstrably unreliable on its very first real test. Not disabled
   outright since a low-confidence, explicitly-labeled signal is more honest than silently removing
   the attempt — but any future ticket touching this check should treat this finding as evidence it
   needs a materially different heuristic, not incremental tuning.

**1 of 4 is a genuine taxonomy edge case, not a detector defect:**

4. **`demographic_cohort_cycle` (orphan_with_callers)** — real signal, understood and accepted, not
   a registry error. `DemographicCycleService.process_demographics` genuinely has one real,
   non-comment caller (`engine/world_dynamics.py:178-179`). It is registered `orphan` anyway
   because that caller is guarded by a condition (`if not region.population_cohorts`) that never
   fires in the real corpus — the code is invoked every tick and immediately no-ops. This is a
   broader use of `orphan` than "zero callers": it also covers "invoked but the invocation never
   has a real effect," which is closer to what a data-precondition-gated mechanism would need a
   `gated`-shaped state for, except `gated` in this registry specifically means "guarded by a
   feature flag," not "guarded by a data precondition." **This is a real, structural ambiguity in
   the state taxonomy itself** (a data-starved-but-invoked mechanism doesn't cleanly fit `orphan`
   OR `gated` as currently defined) surfaced by the detector, not resolved by it — recorded here
   for peer/taxonomy-owner attention, not silently reclassified by this ticket.

**Net result after fixing the two real detector bugs: 2 of 20 checkable mechanisms flagged (10%),
one confirmed-unreliable heuristic and one confirmed-real taxonomy ambiguity — zero confirmed new
registry defects from this pass.** Small-sample statistic (N=20); the rate will become more
meaningful as `implemented_by` coverage grows. The four real state errors found by hand this epic
remain the baseline this tool is measured against, not a target it needs to beat on day one.

## A structural limitation found but not fully solved: multi-symbol aggregation

`demographic_cohort_cycle`'s own investigation surfaced a second, more general limitation:
`src/domains/demographics/cohort.py` defines a data class (`PopulationCohort`, genuinely used
widely elsewhere as a plain data type) alongside the actual service class
(`DemographicCycleService`) the registry entry's claim is really about. The detector currently
aggregates caller counts across every symbol in an `implemented_by` file, which conflates "this
unrelated data type is used elsewhere" with "the mechanism's own real entry point is invoked."
This did not change the mechanism's actual finding here (both symbols happen to have real callers),
but it is a real methodology gap: `implemented_by` records a file, not a specific symbol, so the
detector cannot currently distinguish "the whole file is dead" from "one specific class in a
multi-symbol file is dead." Not fixed in this ticket (would need a schema change — `implemented_by`
entries as `path:Symbol` pairs, or a separate primary-symbol field) — recorded as a known
limitation for whoever scopes phase 2/3, or a future `implemented_by` schema refinement.

## Design decisions

- **Reuses `implemented_by`, not a new lookup mechanism** — the detector can only check mechanisms
  with a real binding (20 of 89 today); every other mechanism is a counted, honest `unchecked`,
  never a silent gap.
- **Report-only** — never fails the build, matching every other detector in this corpus.
- **Four checks, ordered by peer's own stated cost/payoff**: orphan-with-callers (highest value,
  `causal_spatial_memory`'s exact shape) → done/partial-with-zero-callers
  (`motivation_doctrine`'s shape, though its own historical instance is unrepresentable here since
  the code was deleted entirely, not merely uncalled) → gated-without-flag-context (weaker) →
  skeleton-not-stub (weakest, confirmed unreliable this pass).
