---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION
phase: open
date: 2026-09-20
tags: [world]
---

# TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION

## Title
`CampState` is real, wired, and correctly implements monster spawning/raids/clearing rewards — but
no compiled or procedurally-generated world today seeds any `state.camps`, so it is a permanent
no-op in every real run

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found and confirmed while resolving `camp`'s own unbound-claims entry
(`TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION`, batch 2 of the
mechanism-registry unbound-claims program). `registries/mechanisms.yaml`'s own `camp` entry has
carried this finding since 2026-09-16 (`verdict: contradicted`) but was never given its own tracking
ticket — only cross-referenced against the shared
`docs/plans/world_composition_precondition_gap_finding.md` document, alongside two siblings
(`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
NEVER-FIRES`) that each already had one.

`CampState` (`src/core/state.py`) is a real, complete state model — spawns monsters, triggers raids,
runs a real clearing-reward loop — and is correctly wired into the apply path. But no compiled or
procedurally-generated corpus world today ever populates `state.camps` with a single real camp
instance, so the entire mechanic is a structural no-op regardless of how correct its own code is.
Same shape as the two siblings above: not dead code, not a wiring gap, but a mechanic whose
precondition (a `camp`-kind world object actually existing in a world's own composition) is never
satisfied by anything in the current world-generation pipeline.

## Scope
- Confirm directly why no compiled/procgen world ever seeds `state.camps` — check whether `camp`
  world-object placement exists anywhere in `WorldCompiler`'s own content-resolution logic at all,
  or whether it was never wired into world composition in the first place (as opposed to being
  wired but never triggered, the shape the two sibling tickets found).
- Check whether any content schema (`data/content/world/`) even declares a `camp`-kind template
  that composition could place, or whether the content side itself is the gap.
- Propose a real fix (content-authoring: add camp placement to one or more world modules;
  world-gen: add a camp-placement rule to `WorldCompiler`; or something else) — bring findings and
  options to peer/user review before implementing, same investment-cap discipline the two sibling
  tickets already established for this pattern family.

## Out of Scope
- Any change to `CampState`'s own apply-path logic — already confirmed correct and wired.
- The two sibling instances (`lair`, `calamity_intensity`) — each already has its own ticket.

## Acceptance Criteria
- [ ] A real, evidence-backed explanation for why no corpus world seeds `state.camps`.
- [ ] A proposed fix, reviewed with peer/user before any implementation.
- [ ] `docs/plans/world_composition_precondition_gap_finding.md` updated with this as its own
      confirmed instance (already partially done — see Implementation Notes).

## Related Tickets
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`, `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-
  NEVER-FIRES` — same pattern family, each already tracked; this ticket gives `camp` the same
  standing.
- `TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION` — where this gap
  in tracking (a real, contradicted finding with no dedicated ticket) was noticed.

## Related Docs
- `docs/plans/world_composition_precondition_gap_finding.md` — the shared pattern document; this
  ticket adds `camp` as a named instance.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/core/state.py` (`CampState`)
- `src/worldbuilding/compiler.py` (`WorldCompiler`, where camp placement would need to be added if
  missing)
- `data/content/world/` (camp-kind content templates, if any exist)

## Assumptions / Open Questions
Whether the gap is purely content-authoring (no world module places a camp) or a deeper world-gen
gap (no placement RULE exists at all, even for authors who wanted to place one) is the central open
question — not yet distinguished.

## Implementation Notes
**2026-09-30 — verdict recorded via `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED` (epic `T02`,
`TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`): `STALE-PREMISE` (AC-7 fifth outcome, same
label and shape as `demographic_cohort_cycle`'s own verdict this pass, not forced into `CONDITION`
or `MISLABEL`).**

This ticket's own premise — "no compiled or procedurally-generated world today seeds any
`state.camps`" — is **false as of today**, contradicted by executing (not reading)
`WorldCompiler.compile()` against the same real, in-corpus composition used for the cohort check
(`data/content/world_compositions/frontier_living_world.yaml`). Result: **`state.camps` had 2 real
entries** — `goblin_camp_place` (`kind='goblin'`) and `wolf_den_nest` (`kind='wolf'`) — both fully
constructed `CampState` instances with real positions, not placeholders.

**Root cause, verified directly:** two of this composition's constituent world modules
(`data/content/world_modules/goblin_camp_conflict.yaml`, `wolf_den_near_forest.yaml`) already
declare `creature_kind` on a `CAMP`/`NEST`-kind `PlaceSpec` — the exact opt-in field
`WorldCompiler.compile()`'s `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` construction path
(`compiler.py`'s camp-construction block, cited in `docs/world/raid_boss_camp_contract.md` §"World-gen
construction") reads to build a companion `CampState`. `git log --follow` on both content files
shows the `creature_kind` declarations landed in commit `cb0b23b07` (2026-09-08) — **8 days before**
`registries/mechanisms.yaml`'s own `camp` verdict (`verdict: contradicted`, dated 2026-09-16) and
**12 days before** this ticket's own filing (2026-09-20).

**`docs/world/raid_boss_camp_contract.md` (Certified/authoritative, `last_verified: 2026-09-04`) is
itself stale on this exact point** — its own §"World-gen construction" text still reads "No content
on disk sets it today (including `hero_guild_routing`'s `goblin_camp_place`), so `state.camps`
remains `{}` for every currently-compiled world," which was true as of its 2026-09-04 verification
date but has been false since the 2026-09-08 content commit. Flagging for whoever owns that doc's
next update — not corrected here, per this epic's own out-of-scope guard against fixing anything.

**Ticket-provenance finding (not a mechanism verdict, same shape as `demographic_cohort_cycle`'s):**
both the registry verdict (2026-09-16) and this ticket (2026-09-20) were authored after real content
already produced non-empty `state.camps` in a world composition already part of this repo's own test
corpus. Routed to `agent-working-design` as a second instance of the same registry/ticket-filing-
staleness class, per this pass's earlier `demographic_cohort_cycle` finding.

Full experiment output: `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED`'s own Implementation Notes
(this ticket's classifying parent).

## Test Summary
_(not started — classification-only pass; no repo test authored or run beyond an ad hoc
verification script, see the classifying parent ticket)_

## Files Changed
_(none — read-only verification; `registries/mechanisms.yaml` confirmed byte-for-byte unchanged
against `origin/main`)_

## Completion Summary
Filed 2026-09-20 to close a real tracking gap found while resolving `camp`'s own unbound-claims
entry — a confirmed, contradicted finding that had lived in the registry and a shared pattern doc
for 4 days with no dedicated ticket of its own, unlike its two siblings. **Verdict as of
2026-09-30: `STALE-PREMISE`** — the premise this ticket exists to track no longer holds against real
content, and has not held since 2026-09-08. Still `OPEN` pending whoever owns the
`registries/mechanisms.yaml` `camp` entry correction, `docs/world/raid_boss_camp_contract.md`'s
stale construction-note update, and this ticket's own closure — out of scope for the classifying
pass itself (no registry edits, no doc fixes, per the epic's scope guard).
