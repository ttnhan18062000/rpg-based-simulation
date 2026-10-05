---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER
phase: open
date: 2026-10-05
tags: [world, documentation]
---

# TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER

## Title
`allow_overlapping_regions` is declared, set to `false` by all 24 corpus worlds, and read by no
production code — the Mechanics Bible's "strictly disjoint by default, enforced" claim is enforced
nowhere, and `frontier_living_world` resolves with 9 overlapping region pairs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while answering a world-semantics question `rpg-implementer-2` raised when closing
`TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` as stale-premise. It asked whether
overlapping region bounds are intended or should be a rule. The answer turned out to be that the
repo already decided — and then never implemented the decision.

**What the Bible says.** `docs/mechanics/06_worldbuilding_foundation.md:32`:

> **Overlap Policy**: By default, regional bounds are strictly disjoint (no overlapping). This is
> enforced unless `allow_overlapping_regions` is explicitly enabled in the validation spec.

**What the code does.** `allow_overlapping_regions` exists at
`src/worldbuilding/schema.py:245` as `bool = Field(False, ...)` and **nothing reads it.** A sweep of
`src/`, `tools/` and `codebase/` finds exactly two non-test occurrences: that declaration, and
`src/lab/workflows/generate_simulation_setup.py:332` which *writes* it into a generated
`ValidationSpec`. There is no overlap check anywhere in `src/worldbuilding/` or `src/worldassembly/` —
`grep -rniE overlap` over both packages returns only the `Field` description itself. Every other
occurrence in the repo is a test asserting the field's own value, a lab fixture, or
`tests/unit/lab/test_mutation_engine.py` using `validation.allow_overlapping_regions` as a mutation
*target*, which exercises the mutation engine rather than any validation.

**The measured consequence.** All 24 `data/worlds/*/resolved/world.resolved.yaml` set
`allow_overlapping_regions: false`. `rpg-implementer-2` measured the resolved
`frontier_living_world` and found **9 overlapping region pairs** — among them
`bandit_road`/`trading_hometown`, `trading_hometown`/`near_forest`, `near_forest`/`wolf_den`,
`goblin_camp`/`haunted_battlefield`. So a world that declares overlap forbidden assembles with nine
overlaps and nothing notices.

**This is not the region-id defect.** Region *ids* are genuinely safe: `resolver.py:359` and
`schema.py:319` both raise on a duplicate id, and #335's namespace prefixing means
`trading_company_hub` composes as `trading_hometown`, so all 24 compositions assemble with 0
collisions. The ids are distinct; the *geometry* overlaps. Two separate properties, and only the
first one is enforced.

**Why P1 rather than a tidy-up.** A declared validation knob that nothing reads is indistinguishable
from a validation that passes, which is precisely the "executes without effect" shape the owner moved
into foundation scope (`roadmap.md` §8 work-order item 6 addendum). Worse than the three instances
cited there: those mechanisms at least *ran*. This one never runs and its `false` value is read by
nobody, so every world in the corpus carries a false assurance.

## Scope
1. Establish and record whether anything in the simulation depends on a position belonging to **at
   most one** region. `RegionState` lives in `src/core/state.py`; find every place that maps a
   position to a region and record what each does when two regions contain the point — first match,
   last match, or undefined. **This is the question that decides how serious the overlap is**, and it
   is not answered yet. Do this before proposing any fix.
2. Record what the Bible already defines for the overlap case so it is not re-derived:
   `06_worldbuilding_foundation.md:37` gives a paint-order rule — `WorldSpec.regions` is iterated in
   declaration order and each region's terrain write is a plain dict-key overwrite, so a later region
   unconditionally overwrites an earlier one for a shared tile. So overlap is *contemplated* for
   terrain and declaration order is the documented priority mechanism. Whether that rule extends to
   anything other than terrain is open.
3. Reconcile doc and code in whichever direction the owner chooses (see Assumptions — **this ticket
   must not pick the direction unilaterally**). Either implement the enforcement the Bible claims, or
   amend `:32` to state what is actually true and record the change in
   `docs/guidelines/intentional_divergences.md`.
4. Whichever direction is chosen, `allow_overlapping_regions` stops being a dead field: it is either
   read by a real check, or removed from the schema and from the 24 resolved specs with a note saying
   why.
5. Update the parity ledger. `docs/parity_ledger/substrate.yaml` is the subsystem file; add or correct
   the entry covering the overlap policy, since the current state is a documented-but-absent
   behaviour.

## Out of Scope
- Region **id** collisions and the namespace-prefix rule. Settled by #335; the doc gap for it is
  `TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE`.
- Correcting the bounds of any specific corpus world. That is a content change whose blast radius is
  every measurement taken on that world, and it is gated on Scope 3's direction.
- `src/rendering/` and the visual consequence of overlapping terrain. Unowned area; route to the
  planner if it comes up.
- The lab mutation engine's use of the field as a mutation target.

## Acceptance Criteria
- [ ] Scope 1's position-to-region audit is recorded in `investigation.md`, naming every call site and
      its behaviour on an ambiguous point. "Nothing maps a position to a region" is a valid and very
      important answer if true.
- [ ] The chosen direction is the **owner's**, recorded with who decided and when, before any code or
      Bible edit lands.
- [ ] `allow_overlapping_regions` is either read by a real check or gone. It does not survive this
      ticket as a declared-and-unread field.
- [ ] If enforcement is implemented: the 9 `frontier_living_world` pairs are resolved or the world
      explicitly opts in, and **every** corpus world is checked, not just that one — a check that
      aborts assembly on worlds the whole corpus is measured against is a blast radius that must be
      reported before it lands, not discovered by CI.
- [ ] If the Bible is amended instead: `:32` states what the code does, the divergence is recorded in
      `intentional_divergences.md` with a rationale class and a verification path, and `:37`'s
      paint-order rule is checked for consistency with the amended text.
- [ ] `docs/parity_ledger/substrate.yaml` reflects the outcome.
- [ ] `make knowledge-index-update` run, since `docs/` changed.

## Related Tickets
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` — closed stale-premise by #335's
  namespacing; this ticket is the residue its closure surfaced, and is **not** the same defect.
- `TCK-20261005-ASSEMBLY-CONTRACT-OMITS-REGION-ID-COLLISION-RULE` — the sibling doc gap.
- `TCK-20260909-WORLD-COMPOSITION-CONTENT-RECONCILIATION` (#335) — established the namespace rule.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — this is a fifth instance of the
  "declared but has no effect" shape and a candidate validation case for that instrument. Not a child
  of it.

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md:32` (the claim), `:37` (the paint-order rule), `:114`
  (which lists "out-of-bounds spatial overlaps" as an ERROR that aborts compilation — check whether
  that refers to this policy or to something else; the two may already contradict each other)
- `docs/world/assembly_contract.md` — assembly-time collision contract
- `docs/parity_ledger/substrate.yaml`
- `docs/guidelines/intentional_divergences.md`

## Related Stored Artifacts
_(none yet — Scope 1's audit will produce the first)_

## Related Code Areas
- `src/worldbuilding/schema.py:245` — the unread field
- `src/worldbuilding/resolver.py:359`, `src/worldbuilding/schema.py:319` — the id-collision raises,
  for contrast with the absent geometry check
- `src/worldbuilding/compiler.py::WorldCompiler` — where a check would attach
- `src/core/state.py::RegionState` — **contested surface**, and currently held in part by Lane A for
  an unrelated region of that file. Claim before editing.
- `src/lab/workflows/generate_simulation_setup.py:332` — the only non-test writer

## Assumptions / Open Questions
- **The fix direction is the owner's, not this ticket's.** Implementing the enforcement the Bible
  claims would abort assembly on at least `frontier_living_world`, i.e. on a world the corpus is
  measured against — a blast radius that may be larger than the defect. Amending the Bible instead is
  cheap but ratifies overlapping regions as world law.

  **Owner decision, 2026-10-05: audit first, decide after.** Put to the owner by the planner with
  four options (audit first / enforce / amend the Bible / route to the rule catalog). The owner chose
  to see Scope 1's position-to-region audit before picking a direction, on the ground that it is the
  one fact that changes the answer: if nothing in the simulation depends on a position belonging to
  at most one region, overlap is near-harmless and amending `:32` is right; if the kernel resolves
  "which region is this" anywhere, this is a live correctness bug and not a documentation defect.
  **So Scope 1 is the whole of the first pass. Do not propose a direction in the same breath as the
  audit — report the audit, then ask.**
- One concrete consumer to include in Scope 1, which is not obvious from a grep for "region":
  `SocialComponent.regional_reputation` is `Dict[RegionID, float]` (`src/core/models/social.py:48`)
  and is already in both the canonical dict (`src/core/state.py:987`) and the replay fingerprint
  (`src/replay/fingerprint.py:72`). Nothing produces a delta today, so the map is empty and
  contributes nothing — but it is a *region-keyed* durable field on the determinism surface, so if
  narrower reputation scopes are ever built (parked by owner decision 4, 2026-10-05) they will need
  exactly the position-to-region answer this audit produces. Record it as a future consumer, not a
  current one.
- No accepted world-rules catalog Rule governs region-bounds geometry. Checked
  `docs/world_rules/places-culture/` and the `PLACE-*`/`SETT-*` families: nothing addresses extent or
  overlap. So the Bible is the authority here and nothing outranks it — but that also means the
  question has never been put to the catalog, and arguably should be.
- The 9 overlapping pairs are `rpg-implementer-2`'s measurement of the resolved
  `frontier_living_world`. Reproduce it before building on it, and state the commit — the resolved
  specs changed in #335.
- Whether `:114`'s "out-of-bounds spatial overlaps" ERROR is the same policy under a different name is
  unchecked. If it is, the Bible contradicts itself in one chapter and that is its own small finding.

## Implementation Notes
_(not started)_

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
_(not started)_
