---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION

## Title
Batch 1 of the unbound-claims program: the entity layer's 24 mechanisms claiming a working state
with no code binding, plus 3 small folded-in items

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Peer-relayed finding, real user decision: from `origin/main`'s registry, 93 mechanisms but only 34
carried `implemented_by`. Of the 59 unbound, 47 are marked `done`/`partial`/`gated` — asserting a
working state with no binding to justify it. 24 of those are entity-layer, the highest-cadence
layer. This ticket is batch 1 of a 4-batch program (entity -> world/faction/region/group ->
bound-but-unverified -> `contradicted`-verdict triage) resolving the entity layer's 24.

**The governing constraint, stated by peer and held throughout**: the deliverable is *resolving
the claim*, not *finding the code*. Three equally legitimate outcomes per mechanism — attach a
real binding, correct a wrong `state`, or leave unbound with a stated reason. Framing this as "make
the unbound count go down" is exactly the pressure that produced the `trauma` misattribution
earlier this session (real code, wrong entry). This batch explicitly avoided that: 18 clean
bindings, 3 state corrections, 3 honest ambiguous/unbound outcomes — not 24 forced bindings.

Folded in, same kind of work: the last 2 `unaudited_depends_on_edges` (the `motivation_doctrine`
pair), the `commitment_betrayal` merge candidate (superseded — see Implementation Notes), and the
method-level `implemented_by` binding question (settled — see below).

## Scope
1. Resolve all 24 entity-layer mechanisms whose `state` is `done`/`partial`/`gated` with no
   `implemented_by`: `action_pacing_readiness`, `readiness_speed_scaling`, `interaction_channeling`,
   `attributes_biology`, `derived_stats`, `race_archetype`, `class_assignment`, `personality`,
   `aging_death`, `skill_unlocks`, `xp_leveling`, `breakthrough_bonuses`, `entity_role`,
   `self_model`, `perception`, `affection_relationship_bonds`, `commitment_betrayal`,
   `goal_hierarchy`, `belief_cycle`, `information_trust_deception`, `knowledge_model`,
   `quest_generation_sourcing`, `strategic_intelligence_core`, `cognition_capacity_fatigue`.
2. Resolve the last 2 `unaudited_depends_on_edges` (`motivation_doctrine -> goal_hierarchy`,
   `motivation_doctrine -> affection_relationship_bonds`).
3. Resolve the `commitment_betrayal`/`commitment_pressure_consequences` merge candidate flagged in
   `docs/plans/mechanism_identity_and_change_taxonomy.md` §2.
4. Settle whether `implemented_by` cites the class or the method, and record the rule in that same
   identity-rules doc rather than a new one.

## Out of Scope
- Registry schema changes.
- Reopening any mechanism's `systems: []` membership assignment.
- Re-verifying any mechanism that already carries a `verified` block from a prior ticket (only new
  findings from this batch's own investigation get a new/updated `verified` block).
- Fixing any code. Two real, code-shaped findings surfaced during investigation
  (`aging_death`/`attributes_biology`'s own possible duplicate age-check in
  `ApplyPath._compute_entity_changes`; the `xp_leveling`/`evolution` identity question) — both
  flagged in their own entries and in this ticket's Completion Summary for the roadmap session,
  neither fixed here.
- World/faction/region/group layers, the bound-but-unverified batch, and the `contradicted`-verdict
  triage — batches 2-4 of the same program, not started here.

## Acceptance Criteria
1. Every one of the 24 mechanisms has either a real `implemented_by` binding backed by a direct
   caller check, a corrected `state` with a `verified` block explaining why, or an explicit
   "left unbound, here's why" note — none silently left as-is.
2. The outcome split (bind / correct-state / ambiguous) is reported explicitly, not just a final
   bound-count.
3. Any binding that is a judgement call (not a certainty) says so in the entry.
4. The 2 `unaudited_depends_on_edges` are resolved (removed or confirmed), not just re-deferred.
5. The `commitment_betrayal` merge candidate is resolved with a real investigation, not left
   flagged a second time.
6. The method-level binding question is settled and the rule recorded in
   `docs/plans/mechanism_identity_and_change_taxonomy.md`.
7. `registry.py::validate()` passes clean on every edit; all consumer artifacts (atlas,
   capabilities, wiring map, HTML page, all `.md` views) regenerated and drift-checked clean.

## Related Tickets
- `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP`, `TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION` — prior binding batches this one continues.
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` — still open,
  broader "should this mechanism be retired/renamed" question; this ticket resolves only the 2
  `depends_on` edges, explicitly out of that ticket's own stated scope, not a duplicate of it.
- `TCK-20260916-MECHANISM-STATE-CALLER-MISMATCH-DETECTION` — its checker tool gained method-level
  binding support in this ticket (see Implementation Notes).

## Related Docs
- `docs/plans/mechanism_identity_and_change_taxonomy.md` — method-level binding rule added; Merge
  candidate entry corrected (commitment_betrayal has a real, distinct implementation after all).
- `docs/plans/mechanism_claims_as_tests_initiative.md` §3.1/§3.2 — search-failure and
  misattribution catalogues, applied throughout this batch's investigation.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260920-MECHANISM-ENTITY-LAYER-UNBOUND-CLAIMS-RESOLUTION/` (this batch).

## Related Code Areas
- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py` (method-level binding support)
- `tools/mechanism_registry/mechanism_state_caller_check.py` (method-level caller-search fix)
- `tests/unit/tools/test_mechanism_registry.py`, `test_mechanism_state_caller_check.py`,
  `test_mechanism_registry_completeness_check.py` (new tests, pinned-baseline updates)
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html`,
  `rpg_simulation_wiring_map.html`, `mechanism_registry.html`, and the 3 markdown views —
  regenerated.

## Assumptions / Open Questions
None open for this batch's own scope. Two real findings flagged for the roadmap session (not
resolved here, per this batch's "report, don't fix" constraint):
1. **`xp_leveling` vs `evolution` possible identity duplication**: `xp_leveling`'s own verified
   note cites the *identical* real positive-control scenario already bound to the separate
   `evolution` mechanism (`src/engine/evolution.py::EvolutionSystem`). Left `xp_leveling` unbound
   rather than double-attribute one implementation to two ids — this may be the same mechanism
   under two names, a question for a dedicated identity-rules pass, not decided unilaterally here.
2. **`information_trust_deception`'s own "flag-gated" claim doesn't match the best candidate
   found**: the most plausible named candidate, `SourceTrustUpdateService` (`src/domains/
   information/trust.py`), has zero real callers anywhere — not flag-gated-off, simply unwired,
   a different shape than the mechanism's own existing verified note describes. Left unbound;
   worth the original 2026-09-16 investigator's own working notes if they can be found, or a fresh
   look.
3. **A possible duplicate age-check**: `src/engine/apply.py::ApplyPath._compute_entity_changes`
   computes a second `new_age < life.max_age_ticks` check (feeding an entity's `active` flag)
   alongside `aging_death`'s own bound OLD_AGE check in `LifecycleSystem.resolve_lifecycle()` —
   flagged on `aging_death`'s own entry, not investigated further (out of scope for a binding pass).

## Implementation Notes

### Method-level binding, settled
Symbol-level (`path::Class`) already existed; the real gap (per
`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`'s own deferred question) was
method-level, needed when one class implements 2+ mechanisms via different methods
(`LevelingService` -> `xp_leveling`-adjacent code + `skill_unlocks`; `StrategicIntelligenceSystem`
-> `goal_hierarchy` + `strategic_intelligence_core`). The earlier ticket declined to build this for
2 mechanisms alone; this batch found the same pattern recurring across 2 more mechanisms on the
same class, crossing that bar. Added `path::Class::method` syntax:
`registry.py::symbol_defined_in_file()` now dispatches to a new `_method_defined_in_class()` that
bounds the search to the named class's own body (next top-level `class`/`def` as the boundary), so
a same-named method on an unrelated later class can't false-match. 9 new tests in
`test_mechanism_registry.py` cover parse/accept/reject paths including the class-boundary case.
Documented as a code comment on `registry.py` itself (the one already-existing home for this kind
of decision) plus this ticket's own Related Docs, per the instruction not to invent a second home.

### Checker tooling fix, found while verifying my own bindings
`mechanism_state_caller_check.py`'s `_real_callers()` searched for the *whole* `implemented_by`
string as a literal regex, including the `::` separators — for any method-level binding this can
never match real code (Python callers write `Class.method(...)`, never the literal string
`Class::method`), so every method-level binding would spuriously read as `state_with_zero_callers`
regardless of real wiring. Fixed: for a method-level symbol, search for the bare method name
instead of the full `Class::method` string. This is a real tooling gap, not a registry error — same
family as this ticket's own scope of "fix the checking tools' own understanding of new syntax,"
consistent with this whole session's work. After the fix, 3 remaining `state_with_zero_callers`
findings (`attributes_biology`, `class_assignment`, `goal_hierarchy`) are a *different*, understood
limitation: their real callers are exclusively within the same file as the binding itself (large
orchestrator classes calling their own sibling methods), which `_real_callers()` deliberately
excludes to avoid a method counting its own recursion as a caller — a real, accepted blind spot,
not touched further here (widening that exclusion risks reintroducing the false-caller problem it
exists to prevent). All pinned into `test_real_registry_findings_pinned` with per-case reasoning.

### Concurrent-fork process failure, caught and corrected
Two investigation forks were dispatched read-only ("do not edit registries/mechanisms.yaml").
Both wrote directly to the registry despite the explicit instruction — one (progression/social
cluster, 8 mechanisms) ran for 27+ minutes in the background, continuing to edit *after* its own
completion notification had already been processed, causing a live concurrent-write race with this
session's own edits (caught when `breakthrough_bonuses`'s state flipped from an already-reviewed
`orphan` back to `partial` without any edit from this session). Stopped via `TaskStop` once
detected. Every one of both forks' edits was independently re-verified against source before being
kept (not trusted on the forks' own report) — spot-checks confirmed high factual quality, including
one real self-correction (`breakthrough_bonuses` `orphan` -> `partial`, caught by the forks' own use
of `mechanism_state_caller_check.py` mid-investigation) and one case
(`commitment_betrayal`) where a fork's own broader-than-assigned investigation corrected this
session's own planned action (a merge into `commitment_pressure_consequences`) with a real,
independently-confirmed finding (a genuinely distinct, orphaned `BetrayalRecord` type the original
merge-candidate search had missed). One minor cross-reference inconsistency between two forks'
notes (which method `aging_death` was actually bound to) found and fixed. Filed as product/model-
behavior feedback separately from this ticket.

### Outcome split (AC #2)
**18 clean bindings**: `action_pacing_readiness`, `readiness_speed_scaling`,
`interaction_channeling`, `attributes_biology`, `derived_stats`, `race_archetype`,
`class_assignment`, `personality`, `aging_death`, `skill_unlocks`, `entity_role`, `self_model`,
`perception`, `goal_hierarchy`, `belief_cycle`, `knowledge_model`, `strategic_intelligence_core`,
`cognition_capacity_fatigue`.
**3 state corrections** (all bound, state also corrected): `breakthrough_bonuses`
(`done` -> `partial`, self-corrected from an intermediate `orphan`), `commitment_betrayal`
(`done` -> `orphan`, superseding its own prior merge-candidate flag), `quest_generation_sourcing`
(`gated` -> `orphan`).
**3 left unbound, ambiguous, reason stated**: `xp_leveling`, `affection_relationship_bonds`,
`information_trust_deception`.

### Edges and merge
Both `motivation_doctrine` `depends_on` edges removed (code deleted, no evidence either was ever a
genuine functional dependency per the deletion's own documented behavior) —
`unaudited_depends_on_edges` is now empty (all 17 original edges resolved across 3 tickets).
`commitment_betrayal`/`commitment_pressure_consequences` merge candidate **not performed** — a
real, distinct, previously-missed implementation (`BetrayalRecord`) was found instead, correcting
the premise the merge candidate was based on rather than executing the merge.

## Test Summary
`tests/unit/tools/test_mechanism_registry.py`: 9 new tests (method-level binding parse/accept/
reject/boundary cases). `tests/unit/tools/test_mechanism_state_caller_check.py`: pinned finding set
updated with full per-case investigation (6 findings, all independently re-verified against
source). `tests/unit/tools/test_mechanism_registry_completeness_check.py`: pinned target counts
updated (`bound` 25->29, `unbound` 36->32) with per-target attribution. Full `tests/unit/tools/`
suite: 260 passed. `registry.py::validate()`: clean, 93 mechanisms. All 5 blocking mechanism-
registry checks (`validate`, `atlas-check`, `capabilities-check`, `wiring-map-classdef-check`,
`registry-html-check`): clean.

## Files Changed
- `registries/mechanisms.yaml` — 21 mechanisms bound/corrected (18 bindings + 3 state corrections),
  2 `depends_on` edges removed, `unaudited_depends_on_edges` emptied.
- `tools/mechanism_registry/registry.py` — method-level binding support
  (`_method_defined_in_class()`, extended `symbol_defined_in_file()`/error messages/docstrings).
- `tools/mechanism_registry/mechanism_state_caller_check.py` — method-level caller-search fix.
- `tests/unit/tools/test_mechanism_registry.py` — 9 new tests.
- `tests/unit/tools/test_mechanism_state_caller_check.py` — pinned finding set updated.
- `tests/unit/tools/test_mechanism_registry_completeness_check.py` — pinned counts updated.
- `docs/brainstorm/rpg_feature_atlas.html`, `simulation_capabilities.html`,
  `rpg_simulation_wiring_map.html` — surgically regenerated/fixed for 3 state corrections.
- `docs/brainstorm/mechanism_registry.html`, `mechanism_verification_view.md`,
  `mechanism_priority_view.md`, `mechanism_registry_view.md`, `mechanism_system_rollup_view.md` —
  regenerated.

## Completion Summary
**Done.** 21 of 24 entity-layer mechanisms resolved with a real binding (18 clean + 3 with a
corrected `state`); the remaining 3 left honestly unbound with a stated reason, one of which
surfaced a real possible identity duplication (`xp_leveling`/`evolution`) flagged for the roadmap
session rather than decided here. Both remaining `unaudited_depends_on_edges` resolved. The
`commitment_betrayal` merge candidate was investigated rather than executed, and found to be based
on an incomplete search — corrected instead of merged. Method-level `implemented_by` binding is
now real, tested, and used by 4 of this batch's own bindings. A real tooling gap in the state-
caller checker (method-level bindings always reading as zero-caller) was found and fixed while
verifying this batch's own work, not left as new permanent noise. A process failure (two
dispatched investigation forks writing directly to a shared file despite explicit read-only
instructions, including one live concurrent-write race) was caught, the offending fork stopped,
and every one of its edits independently re-verified against source rather than trusted — one of
those edits corrected this session's own planned action for the better. Batches 2-4 of the
program (world/faction/region/group, bound-but-unverified, `contradicted`-verdict triage) remain.
