---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION
phase: done
date: 2026-09-20
tags: [world]
---

# TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION

## Title
`CampState` is real, wired, and correctly implements monster spawning/raids/clearing rewards — but
no compiled or procedurally-generated world today seeds any `state.camps`, so it is a permanent
no-op in every real run

## Status
DONE

## Disposition
STALE-PREMISE

## Disposition Rationale
This ticket's premise — "no compiled or procedurally-generated corpus world today ever populates
`state.camps`" — was already false when the ticket was filed on 2026-09-20, and had been since
2026-09-08. Closed without implementation in `791e6bf6b`; zero `src/` files changed.

Evidence: `data/content/world_modules/goblin_camp_conflict.yaml:29` and
`data/content/world_modules/wolf_den_near_forest.yaml:66` each declare `creature_kind` on a
`CAMP`/`NEST`-kind `PlaceSpec` — the opt-in field `WorldCompiler`'s `CampState` construction path
reads. Both modules are composed into `frontier_living_world`. A real
`WorldAssemblyResolver.assemble()` → `WorldCompiler.compile(seed=42)` yields **2 fully-constructed
`CampState` entries** (`goblin_camp_place`, `wolf_den_nest`). The `creature_kind` declarations
landed in commit `cb0b23b07` (2026-09-08) — 8 days before the `registries/mechanisms.yaml` verdict
this ticket quoted (dated 2026-09-16) and 12 days before the ticket itself.

Verified independently twice, from two worktrees, by two sessions.

AC-1, AC-2 and AC-3 are **void rather than met**: each presupposed a real gap to explain, fix or
document. AC-3 in particular asked for
`docs/plans/world_composition_precondition_gap_finding.md` to record `camp` as a confirmed
instance of its pattern; that document was retired on 2026-09-30 (`f70f58706`) and `camp` was never
an instance of it.

Note this closure is unaffected by
`TCK-20260930-WORLD-ID-HAS-TWO-DIVERGENT-DEFINITIONS`: both cited modules are present in **both**
definitions of `frontier_living_world`, so the 2-`CampState` result holds under either loader.

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
_(none — disposition-only closure; nothing under `src/` changed)_

## Completion Summary
Closed 2026-09-30 as **STALE-PREMISE**; no code change. The premise that no compiled or procgen world
seeds `state.camps` is false. `goblin_camp_conflict.yaml:29` and `wolf_den_near_forest.yaml:66` declare
`creature_kind` on a CAMP/NEST `PlaceSpec` (content shipped `cb0b23b07`, 2026-09-08, 12 days before this
ticket was filed). Both are composed into `frontier_living_world` (`frontier_living_world.yaml:8-9`), and a
real compile yields 2 `CampState` (`goblin_camp_place`, `wolf_den_nest`). Verified independently twice.

**AC-1 and AC-2 are void** (there is no gap to explain or fix). **AC-3 is void, not met:**
`docs/plans/world_composition_precondition_gap_finding.md` is retired (`f70f58706`) and camp was never a
real instance of that pattern.

The stale claim in `docs/world/raid_boss_camp_contract.md` was corrected in `f70f58706`. The
`registries/mechanisms.yaml` `camp` verdict correction is owned by
`TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE`, not this closure.
