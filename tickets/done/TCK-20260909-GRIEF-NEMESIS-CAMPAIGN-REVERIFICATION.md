---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION
phase: done
date: 2026-09-09
tags: [cognition, social, observability]
---

# TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION

## Title
Re-verify grief/nemesis event reachability in a real, populated campaign_life_arc episode — DONE: `nemesis_relation_formed`/grief's episode-boundary path BLOCKED by a new real bug (survivor position collision, split out); grief's mid-episode path INCONCLUSIVE (real deaths occurred, but no entity ever accumulated real ally trust to trigger it)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260824-GRIEF-NEMESIS-REACHABILITY` closed with a "reachable" claim that, per a 2026-09-08
addendum (added during `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own root-cause
determination, not reopening that ticket), rests on two different kinds of evidence: (1)
`CampaignOrchestrator.run_episode()` being reachable from a real production entrypoint — genuinely
verified, unaffected by anything below; and (2) `grief_urgency_triggered`/`nemesis_relation_formed`
`SimulationEvent`s "are emitted from... paths" — verified only via a **synthetic** event envelope
fed directly into `SocialScorer` (`tests/simulation_quality/test_social_scorer.py`'s
`TestGriefNemesis` class), never via a real campaign episode.

That gap existed because `campaign_life_arc` has, until `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`
lands, run with **zero entities** for its entire episode — no entity has ever died in one, so no
grief/nemesis trigger could possibly have fired in a real run regardless of whether the underlying
emission code is correct. This ticket exists specifically so that gap doesn't depend on someone
remembering to re-check it once entities exist — user decision, 2026-09-09 (via peer review
`rpg-feature-planning`, confirmed directly).

## Scope
Explicitly blocked on `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` landing first; does not
start until that ticket closes with entities genuinely spawning in `campaign_life_arc`.

- Once `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` lands: run a real `campaign_life_arc`
  episode (or a real scenario with the same shape) for real, long enough for at least one entity
  death to plausibly occur (combat, passive decay, or any other real death path).
- Confirm, via real observed `SimulationEvent`s from that run (not synthetic construction), whether
  `grief_urgency_triggered`/`nemesis_relation_formed` events actually fire when a real entity dies
  in a real campaign episode.
- If they fire correctly: record this as the first genuine confirmation, update
  `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own addendum to reflect the closed gap (a further
  addendum, not silently editing the original text).
- If they do NOT fire (a real bug in the emission wiring itself, previously masked by the
  zero-entity gap): this is a real, newly-discovered bug — do not silently patch it as an aside;
  treat it with the same rigor as any other confirmed bug in this batch (real test evidence,
  peer-routed fix decision if the fix isn't trivial).

## Out of Scope
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING`'s own entity-spawn correctness — this ticket
  assumes that ticket's own work is already verified and closed; not re-litigated here.
- Any other Campaign-mode subsystem's own reachability (war/siege/calamity, already covered by
  `TCK-20260908-CAMPAIGN-MODE-ACTIVATED-SUBSYSTEM-BASELINE-DRIFT`'s own addendum and
  `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION`'s own remaining AC item) — this ticket
  is scoped to grief/nemesis specifically.

## Acceptance Criteria
- [x] A real `campaign_life_arc` (or equivalent, now-populated) episode run produces at least one
      real entity death. — Confirmed: a real single-episode 500-tick run produced 4 real
      `lifecycle.active` True→False transitions (real deaths), observed directly via `Kernel
      ._event_listeners`, not inferred.
- [x] Real observed evidence (not synthetic) confirms whether `grief_urgency_triggered`/
      `nemesis_relation_formed` events fire from that real death, through both the mid-episode and
      episode-boundary trigger paths named in the original ticket. — **Mixed real result, not a
      clean pass**: `nemesis_relation_formed` and grief's episode-boundary path are **BLOCKED** by
      a newly-discovered real bug (survivor-reconstruction position collision — see Completion
      Summary), confirmed with real multi-episode evidence, not assumed. Grief's mid-episode path
      is **INCONCLUSIVE**: real deaths occurred, zero `grief_urgency_triggered` fired, and the
      cause was root-caused directly (every entity's `trust_history` was empty for the entire run
      — the trigger's own precondition, not the trigger mechanism, was never satisfied).
- [x] `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own 2026-09-08 addendum is updated with the real
      result (confirmed working, or confirmed a real bug with its own follow-up). — Updated with a
      further, dated addendum (not silently editing the original text) recording this mixed
      blocked/inconclusive result and both follow-ups.

## Related Tickets
- `TCK-20260824-GRIEF-NEMESIS-REACHABILITY` (the ticket whose claim this re-verifies)
- `TCK-20260909-CAMPAIGN-CATALOG-ENTITY-SPAWN-WIRING` (hard blocker — landed, unblocking this
  ticket)
- `TCK-20260908-CAMPAIGN-LIFE-ARC-EPISODE-STALL-TRUNCATION` (origin of the zero-entity finding that
  created this gap)
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (new — the real bug found
  during this investigation that blocks `nemesis_relation_formed`/grief's episode-boundary path)
- `TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION` (new, filed after
  further peer-review tracing — the deeper open question behind grief's own inconclusive
  mid-episode result: why `trust_history` never accumulates despite a complete-looking pipeline)

## Related Docs
None yet.

## Related Stored Artifacts
`stored_artifacts/TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION/` — investigation.md,
plan.md, test_plan.md

## Related Code Areas
- `src/domains/campaigns/orchestrator.py`
- Grief/nemesis emission paths named in the original ticket (`GriefUrgencyImporter`,
  `NemesisRelationImporter`, the mid-episode `entity_death` → `GriefUrgencyImporter.build_strategic_update()`
  route through `Kernel._phase_resolution` → `AuthoritativeApplyPipeline.refine()` → `ApplyPath`)

## Assumptions / Open Questions
- ~~None — scope is a straightforward re-verification once unblocked.~~ A real, previously
  unexercisable bug (survivor-reconstruction position collision) was found mid-investigation and
  blocks 2 of the 3 legs. Not this ticket's own scope to fix (see Out of Scope) — filed separately.
- Whether `entity.social.trust_history` populating (or not) from real `cooperation_event`
  interactions within a single episode's timeframe is itself working correctly is an open,
  unconfirmed question — genuinely out of this ticket's own scope (it investigates grief/nemesis
  event *emission*, not trust-building mechanics), and deliberately not filed as its own ticket
  given the thin evidence (one seed, one composition, one run). Recorded here as the evidence
  trail rather than filed prematurely.

## Implementation Notes
Full investigation, plan, and test plan in
`stored_artifacts/TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION/`. No production code
changed by this ticket — it is a determination, same as
`TCK-20260909-CAMPAIGN-EVENT-RECORDER-SCENARIO-EVENTS-ONLY`'s own "no" result earlier in this
batch, and the "say the negative/mixed result plainly" instruction applies equally here.

1. Traced both real trigger paths for each event type before running anything (see
   investigation.md) — confirmed `nemesis_relation_formed` has no mid-episode path at all
   (structurally requires 2+ real episodes), unlike `grief_urgency_triggered`, which has both.
2. Ran a real 3-episode campaign to test the multi-episode-dependent legs. Episode 0 completed
   cleanly; episodes 1-2 both stalled almost immediately on a real `LAW-SPAWN-OCCUPANCY`
   violation. Traced to its real cause (all 13 of 16 episode-0 survivors reconstructing at the
   identical `(0.0, 0.0)` position) rather than assumed — confirmed at scale, not a synthetic
   2-entity case. Filed `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` rather
   than working around it (explicitly declined, per peer review, to hand-construct carry-forwards
   with distinct positions — doing so would reproduce the exact synthetic-verification flaw this
   ticket exists to correct).
3. Ran a real single-episode 500-tick run to test grief's mid-episode path independently (doesn't
   depend on the survivor-reconstruction bug). Corrected a real mistake in my own first probe
   mid-investigation: initially filtered for a literal `event_type == "entity_death"`, which never
   matches any real SimulationEvent name (the real ones are `"entity_killed"`/`"combat_kill"`,
   neither of which fires for hazard/old-age deaths either) — caught before it produced a false
   "zero deaths occurred" conclusion, by switching to directly observing real `lifecycle.active`
   transitions via `Kernel._event_listeners` instead of trusting an assumed event-type string.
4. Found 4 real deaths, zero `grief_urgency_triggered`. Did not stop at "it didn't fire" — checked
   every alive entity's real `trust_history` toward each of the 4 dead entities directly, at the
   real point of death, and found it uniformly empty across the entire run despite 2470 real
   `cooperation_event`s. This distinguishes "the detection mechanism is broken" from "its own
   precondition was never met" with direct evidence, per the same standard this whole batch has
   applied to every other finding.
5. Updated `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own addendum with a further, dated
   addendum recording this real mixed result.

## Test Summary
See `stored_artifacts/TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION/test_plan.md` for the
full real-run evidence trail (3-episode multi-episode run, 500-tick single-episode run, direct
`trust_history` root-cause check). No automated regression suite applies — no production code was
changed by this ticket.

## Files Changed
- `tickets/done/TCK-20260824-GRIEF-NEMESIS-REACHABILITY.md` — further dated addendum
- `stored_artifacts/TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION/` — investigation.md,
  plan.md, test_plan.md
- `tickets/todos/TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION.md` — new ticket
  (filed and committed separately, before this ticket's own closure)

## Completion Summary
**Closed with real, mixed evidence — not a clean confirmation, and not silently patched or
quietly downgraded to "investigated, nothing to do."** The original ticket's own central risk (was
`grief_urgency_triggered`/`nemesis_relation_formed` reachability ever verified through a real run,
or only synthetically) is answered honestly for all three legs it covers:

- **`nemesis_relation_formed`** and **grief's episode-boundary path**: genuinely **BLOCKED**, with
  real multi-episode evidence, by a new bug found during this same investigation
  (`TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`) — every episode-1+ survivor
  reconstructs at an identical default position, tripping a real hard-law violation that derails
  the episode before either mechanism gets a genuine chance. This bug was itself never
  exercisable until this same follow-up batch gave Campaign mode real entities and therefore real
  survivors for the first time — the same "documented known limitation, no real consequence until
  real data flowed" pattern that has defined this entire batch.
- **Grief's mid-episode path**: **INCONCLUSIVE**, not negative. Real deaths genuinely occurred; the
  detection mechanism was given a genuine chance but its own precondition (a real ally-trust
  relationship) was never satisfied by anything that happened in this run — root-caused directly,
  not assumed.

No fix was attempted for anything found broken or blocked, matching this ticket's own explicit
scope. Both real findings are filed or recorded precisely, not folded into a vague "revisit later"
note: the survivor-position bug has its own standard-tier ticket with real reproduction evidence.

**Addendum (2026-09-11):** the trust-history question, initially left as a deliberately-unfiled
observation (this ticket's own thin, single-run evidence), was pursued further per peer review
(`rpg-feature-planning`), which traced the real trust-delta computation/application chain
(`cooperation/services.py` → `cooperation/phase.py` → `relationships.py`) and confirmed it looks
complete end to end — unlike prior "unwired path" findings in this arc, nothing in the chain is
obviously dead or stubbed. That distinction (a complete-looking pipeline producing zero real
output, vs. a demonstrably unwired one) is exactly what raised this from "thin, don't file" to a
real, scoped investigation question. Filed as
`TCK-20260911-COOPERATION-TRUST-HISTORY-ZERO-ACCUMULATION-INVESTIGATION`.
