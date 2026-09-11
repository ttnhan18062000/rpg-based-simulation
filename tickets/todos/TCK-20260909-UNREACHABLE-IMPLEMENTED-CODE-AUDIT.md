---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT
phase: open
date: 2026-09-09
tags: [architecture, audit]
---

# TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT

## Title
Audit src/ for implemented, tested, but never-called code — seven instances found incidentally in one session

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Over a single session of follow-up work (PR #148 / PR #150 batches), **seven separate instances**
of real, frequently unit-tested production code with **zero live callers** were found — every one
of them incidentally, while investigating something else:

| Mechanism | Location | How it surfaced |
|---|---|---|
| `BeliefCycleSystem.decay_stale_beliefs()` | `src/systems/strategic_systems/belief.py:42` | Diagnosing `combat_risk` belief staleness |
| `BiologicalSystem.update()` | `src/systems/biological_system.py` | Dirty-set consumer investigation |
| `spawn_calamity()` | `src/world/calamity.py` | `state.maturity` consumer survey |
| `CatalogScenarioStateBuilder` chain | `src/scenarios/catalog_state_builder.py` | Campaign zero-entity investigation |
| `invalidate_read_model` | `src/engine/apply_plan.py:20` | Dirty-set consumer investigation |
| Camp raid-reuse discard stub | `src/world/camp.py` | Camp content-authoring follow-up |
| `effective_certainty()` | `src/cognition/knowledge_model.py:137` | Parity-ledger check on STRAT-239 |
| `EntitySpawnContext.spawn_region` → `properties["spawn_region"]` write | `src/entities/archetype_factory.py:24,66-67` | Investigating `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`'s spawn-position approach |

**Eighth instance (2026-09-11), found while designing the fix for
`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`:** `EntitySpawnContext` carries a
`spawn_region: Optional[str] = None` field; when non-`None`, `ArchetypeEntityFactory.build_entity()`
writes it into the built entity's `properties["spawn_region"]`. But the only real caller,
`WorldEntitySpawner.spawn_from_context()` (`entity_spawner.py:57`), hardcodes
`spawn_region=None` on every construction — so the write path never fires in practice — and a
repo-wide grep for any reader of `properties["spawn_region"]` / `properties.get("spawn_region")`
found zero consumers. Genuinely dead on both ends (never written with a real value, and nothing
reads it even if it were). Checked specifically because it looked like it might be the intended
hook for that ticket's own per-entity spatial-placement fix — it is not: it stores a region-name
*string tag* on entity metadata, not spatial coordinates, so it wouldn't have served that purpose
even if wired. That ticket is adding a new, separate `spawn_position` field rather than reusing
this one — recorded here rather than silently fixed, per this audit ticket's own Out of Scope
("Fixing, wiring, or deleting any of the found code... each disposition is its own ticket").

The problem is not any individual entry — most have now been filed for disposition individually.
The problem is the **pattern and the detection gap**: this codebase has a systematic divergence
between "implemented and tested" and "actually reachable at runtime," and nothing surfaces it.
Discovery has been entirely accidental, at a rate of roughly one per investigation.

Two aggravating findings show existing quality mechanisms actively certify the gap rather than
catch it:

1. **A unit test asserted the defect as intended behavior.** `tests/unit/domains/campaigns/
   test_campaign_orchestrator.py` asserted `state.entities == {}` as an intentional invariant —
   codifying the Campaign-mode zero-entity bug as expected. It passed continuously and helped the
   bug survive a full ticket dedicated to Campaign-mode correctness.
2. **A P1 parity-ledger entry is marked `verified` for a mechanism that has never executed.**
   `STRAT-239` (`docs/parity_ledger/strategic_cognition.yaml:2873`) describes lead-staleness
   demotion (APPROXIMATE→VAGUE→EXHAUSTED). Its `v2_evidence` cites
   `belief.py:47 — stale_threshold: int = 50 (default)` — which verifies that *a default parameter
   exists*, not that the behavior occurs. The method has zero callers.

So both the test suite and the parity ledger have certified unreachable behavior as working.

## Scope
- Enumerate implemented-but-unreferenced code across `src/`: modules, classes, and functions with
  no live call site outside their own definition and their own tests.
- Account for legitimate false positives explicitly rather than filtering them silently — entry
  points, dynamic dispatch, registry/plugin lookup by string name, framework-invoked hooks,
  re-exported public API. The output must distinguish "genuinely unreachable" from "reachable by a
  mechanism static analysis cannot see," with the reasoning recorded per entry.
- Triage each genuine finding into exactly one of: **wire** (real intent, never connected),
  **delete** (abandoned), or **document** (deliberately dormant, with the rationale recorded).
- Produce the result as a durable artifact under `docs/audits/`, not only as ticket-body text, so
  it can be re-run and diffed later.
- File follow-up tickets for the individual dispositions rather than executing them here.

## Out of Scope
- Fixing, wiring, or deleting any of the found code. This ticket produces the list and the triage;
  each disposition is its own ticket.
- Building a CI check for unreferenced code. That was considered and deliberately deferred: the
  false-positive rate is unknown until this audit produces real numbers. Revisit with that data.
- The seven already-known instances' own dispositions — each already has, or will have, its own
  ticket (`BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`, `BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`,
  `SPAWN-CALAMITY-DEAD-CODE-DISPOSITION`, `CAMP-RAID-ORIGIN-SPAWN-FIX` (done),
  `CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (done), and the `effective_certainty()` disposition).
  Include them in the audit's inventory for completeness, but do not re-litigate them.
- A full parity-ledger re-verification. See Assumptions below — it is a real adjacent question,
  but it is its own ticket if the audit's findings justify one.

## Acceptance Criteria
- [ ] A complete inventory of implemented-but-unreferenced code in `src/` exists as a durable
      artifact under `docs/audits/`, with each entry triaged wire / delete / document and the
      reasoning recorded.
- [ ] False positives are enumerated with the mechanism that makes each reachable, not silently
      excluded — a reader must be able to check the exclusion reasoning.
- [ ] The seven known instances all appear in the inventory, cross-referenced to their own
      disposition tickets.
- [ ] Follow-up tickets are filed for any newly-found genuine instances; none are fixed here.
- [ ] The audit records its own method and its limitations plainly, including what class of
      unreachable code it cannot detect, so a future re-run knows what it is and isn't covering.

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` — the instance that also exposed STRAT-239.
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`
- `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION`
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (done) — wired the catalog spawn chain, the
  largest instance, and the one that had left Campaign mode running with zero entities.
- `TCK-20260908-CAMP-RAID-ORIGIN-SPAWN-FIX` (done)
- `TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY` — same family one level up: a
  pipeline that runs but delivers almost nothing to its consumer.

## Related Docs
- `docs/audits/` — where the output belongs; see existing D-numbered dimension audits for shape.
- `docs/parity_ledger/schema.json` — for the STRAT-239-class question in Assumptions.
- `docs/guidelines/design_patterns.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up.

## Related Code Areas
All of `src/`. The seven known instances are listed in Request Summary with exact locations.

## Assumptions / Open Questions
- The false-positive rate for static reachability analysis in this codebase is unknown. If it turns
  out high enough that the inventory is untrustworthy, say so and stop rather than shipping a list
  nobody can act on — a credible negative result is a valid outcome.
- **Adjacent, deliberately not scoped here:** STRAT-239 is marked `verified` on evidence that only
  confirms a constant. Whether other parity entries rest on similar evidence — a signature, a
  default value, a definition — rather than on observed behavior is a real question this audit will
  likely produce evidence for. If it does, file it; do not expand into it.
- Whether any of the seven represent one shared root cause (e.g. a refactor that moved call sites,
  or a subsystem built ahead of its integration) rather than seven independent oversights. Worth
  looking for a pattern in their git history; it would change what prevention is worth building.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
