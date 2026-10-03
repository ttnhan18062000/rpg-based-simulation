---
status: active
layer: engine
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND
phase: open
date: 2026-10-01
tags: [bug, lifecycle, engine, determinism]
---

# Plan — TCK-20261001-HAZARD-OVERWRITES-SAME-TICK-COMBAT-OUTCOME-KIND

Stacked behind the death batch on the same branch, by user decision 2026-10-01: **nothing merges while
the zombie route is live** (investigation Finding 3). Read `investigation.md` first — it discharges AC4's
joint-planning requirement and rules out both obvious fixes.

## AC4 — joint planning against the sovereignty consolidation: DONE

**Shared premise, to be recorded in both tickets:** *this fix is order-independent and does not move
`world_dynamics`; any later sovereignty consolidation may move the ownership sweep without disturbing
it.* Reordering the pipeline was **ruled out** because AC3 demands a byte-identical state hash for
non-collision runs and a reorder changes hazard timing for every hazard-affected entity, not just
colliding ones. `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION` keeps all three of its
recorded outcomes and is **not** pre-empted here.

## AC6 escalation — satisfied, and the escalation changed the plan

C1's AC6 requires planner escalation before implementation because this touches write-precedence between
world dynamics and lifecycle. Done: the escalation produced the no-reorder ruling above, the two
findings below that invalidate the obvious fixes, and the Q1 referral. **This plan is the escalation
record.**

## BLOCKED ITEM — Q1, awaiting a rule ruling

**Q1: which cause does a collision record?** No law exists (`05_world_evolution.md` and
`02_combat_laws.md` both silent; C1 recorded that no declared rule exists), so a rule must be
**declared**. Referred to `world-rule-catalog-design` 2026-10-01.

**My recommendation, pending its ruling: the combat kill wins — `death_reason='COMBAT'`** (rationale in
`investigation.md`; AC1 already specifies this, so the referral is about recording *why* and about
whether omitting the hazard contribution breaches anything). **Do not implement S4's reason value from
my recommendation alone.** Everything else in this plan is unblocked.

## Steps

### S1 — Carry hazard application independently of `outcome_kind` (Finding 1)
**This must land before or with S2**, or S2 silently destroys the hazard observability path.

Add a dedicated hazard signal to `CombatUpdate` — preferred shape `hazard_damage: int = 0`, because it
carries magnitude, accumulates naturally in `merge` (same pattern as `hp_delta`), and is strictly more
informative than a bool. Requirements:
- Include it in `CombatUpdate.is_noop()` (`updates.py:127-128`) and in `merge` (`:138-145`) as an
  accumulating field, mirroring `hp_delta`'s `self.x + other.x` treatment.
- `world_dynamics.py:39` sets it on every hazard application, **unconditionally** — this is the part
  that must not become conditional, since it is what preserves observability for colliders.
- Repoint `event_extractor.py:778`'s `hazard_drain_applied` emission at the new field instead of
  `outcome_kind == "HAZARD"`. **Verify the event still fires identically for hazard-only drains** — that
  is the AC2 regression surface, and it is the single most likely thing to break silently.

### S2 — Stop clobbering a terminal combat outcome (`world_dynamics.py:39`)
Set `outcome_kind="HAZARD"` **only if** the slot does not already hold a terminal outcome. Terminal set:
`("KILL", "PERMADEATH", "DEFEAT", "REBIRTH")`. Define it as a named module constant, not an inline
literal, and state its relationship to `_DEFEATED_OUTCOME_KINDS`
(`learning_outcome.py:33`, identical membership today) — if the two are meant to stay identical, derive
one from the other rather than letting them drift.

**Keep `"HAZARD"` as the value when the slot is empty.** This is what preserves
`_NON_COMBAT_OUTCOME_KINDS` (`event_extractor.py:29`, `phase.py:95`), `_real_combat_update`, and the
`event_extractor.py:471-477` "HAZARD-preceded" logic for hazard-only drains — i.e. AC2's discriminant
requirement. A fix that stops setting `"HAZARD"` at all would make hazard deaths look like combat kills
to the extractor, which AC2 names as "a regression, not a fix"
(`TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`'s subject).

### S3 — Guard `alive_set` against hazard resurrection (Finding 2)
`world_dynamics.py:39` writes `alive_set=(new_hp > 0)` unconditionally, and `CombatPatch.apply`
(`patches.py:322`) honours `alive_set` over the HP-derived value. **Hazard must never flip `alive_set`
from `False` to `True`.** Latent today rather than observed — implement as a guard and say so in the
comment, do not claim a fixed defect.

### S4 — Record the hazard death in `resolve_lifecycle` (Finding 3; reason value BLOCKED on Q1)
Add a branch keyed on the **persisted** `outcome_kind == "HAZARD"` recording a real death, so the 8
permanent zombies R1 exposes are deactivated by the sole declared authority. Same shape as the existing
`KILL`/`PERMADEATH` branch and the sibling's `DEFEAT` branch — **not** the HP/alive branch the ticket's
Out of Scope excludes (that remains the sibling's).

- Share the sibling batch's **R6 idempotency guard** — never classify an entity that already carries
  `death_reason` or `is_permadeath`. One implementation across all three branches, not three.
- This is only *possible* because S2 preserves the discriminant: before S2, the branch cannot distinguish
  a hazard death from a hazard-overwritten non-lethal outcome. That is exactly why the earlier attempt
  (recorded in `stored_artifacts/TCK-20260928-PASSIVE-BIOLOGICAL-DEATH-DETECTION-GAP/`) was reverted.
- **Ticket amendment required:** AC2's "hazard-only drain deaths keep their current observable behaviour"
  is unachievable post-R1 (their current behaviour is "deactivated late and silently", which R1 removes)
  and must be rewritten to the intended contract — recorded, classified, deactivated by
  `resolve_lifecycle`. The Out of Scope exclusion of a `death_reason` branch must be narrowed to the
  HP/alive branch it was actually aimed at.

### S5 — Verify Q3 (`hp_delta` double-counting)
`new_hp` at `:38` reads `entity.combat.hp + c_upd.hp_delta - hazard_dmg`, which appears correct, but `hp`
floors at 0 so the arithmetic is only "not provably wrong". Now that a collision is a tested path, assert
the arithmetic explicitly rather than leaving it inferred.

### S6 — Docs, law and parity
- Declare the Q1 precedence rule in the Mechanics Bible (chapter per the owner's ruling) **plus** an
  `docs/guidelines/intentional_divergences.md` entry, since no prior law existed — required by Q1's own
  terms regardless of which way it rules.
- Record the new hazard death cause and the S2 terminal-outcome precedence in
  `docs/simulation/lifecycle_systems_contract.md`.
- **AC7: run `make semantic-control-plane-drift-check` afterwards and SHOW its output.** It is
  report-only (always exit 0), so a clean run must be *demonstrated*, not asserted — SCP rows
  `LIFE-01`/`LIFE-02` cite `combat_resolution` and this changes who decides alive/dead.
- Parity: `combat_movement.yaml` and `world_dynamics.yaml` entries get `status` + `v2_evidence`
  refreshed (AC7 of the ticket). Note `world_dynamics.yaml`'s `WORLD-107` is the sovereignty
  consolidation's entry, not this one — do not edit it here.

## Scope guards

- **Do not reorder the pipeline.** Ruled out; AC3 is the reason.
- **Do not touch the ownership sweep** (`world_dynamics.py:44+`) or `WORLD-107` — that is
  `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`, still open and un-pre-empted.
- Do not change hazard damage magnitude, `calculate_hazard_drain`, or faction hazard immunities.
- Do not add an HP/alive-keyed death branch — the sibling owns that.
- Do not stop setting `outcome_kind="HAZARD"` for hazard-only drains (AC2).
- Do not implement Q1's reason value before the rule ruling lands.

## Acceptance-criteria map

| AC | Steps | Verified by |
|---|---|---|
| 1 — collision records a combat death matching the control arm | S2, S4 | H1, H2 |
| 2 — hazard-only behaviour + `"HAZARD"` discriminant preserved | S1, S2 | H3, H4, H5 |
| 3 — determinism, byte-identical hash with no collision | no reorder; S1–S3 | H6 |
| 4 — AC6 escalation + joint sequencing | this plan, investigation | plan record |
| 5 — AC7 SCP drift check output shown | S6 | S6 output pasted in ticket |
| 6 — defect-asserting tests rewritten, not deleted | S4 | H7 |
| 7 — parity ledger refreshed | S6 | S6 diff |
| — zombie route closed (R1 consequence) | S4 | H8 |
