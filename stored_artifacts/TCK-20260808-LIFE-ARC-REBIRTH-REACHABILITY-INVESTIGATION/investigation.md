---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [progression, simulation-quality]
---

# Investigation — TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION

## Real, structural root cause found: not rarity, a missing code path

Traced the real rebirth trigger chain in `src/engine/combat.py`. `CombatRewardClassificationService
.classify_defeated_target()` (`combat_rewards.py:44-51`) correctly marks `rebirth_eligible=True`
specifically when the defender's role is `HERO` — confirming rebirth is HERO-specific by design,
as expected.

**But the REBIRTH/PERMADEATH branching logic itself
(`if classification.rebirth_eligible: ... outcome = "REBIRTH"` / `"PERMADEATH"`,
`combat.py:182-188`) exists in exactly one place: `resolve_attack()`** — confirmed via direct
grep (`rebirth_eligible`/`REBIRTH`/`PERMADEATH`/`generation_delta` appear nowhere else in
`combat.py`). `resolve_skill_usage()`, `resolve_multi_attack()`, and `resolve_aoe_attack()` all
independently call the same `classify_defeated_target()` and correctly use its
`xp_multiplier`/`gold_multiplier` — but **none of them read or act on `rebirth_eligible`** at
all, and none set `generation_delta`/`is_permadeath_set` on their own returned `CombatUpdate`.

**This session's own direct instrumentation (multiple tickets, same real corpus) already
established `resolve_multi_attack` — via `movement.py`'s opportunity-attack path — is the
corpus's real, dominant kill mechanism; `resolve_attack` (the one function with rebirth logic)
fires 0 times in real 2000-tick runs.** This is the exact same class of defect as
`TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE`'s own orphaned-kill-reward
finding: a real, correctly-implemented mechanic that is structurally unreachable because it only
exists in the code path the corpus doesn't actually exercise.

**Real conclusion: rebirth is not "rare" — it is currently unreachable via the corpus's real
combat mechanism, full stop**, independent of HERO population size or kill rate. This directly
explains `life_arc_detector_reachable: null` across every real run this session's own tools have
observed, at every tick length tested (200 through 2000).

## Real fix: port the existing, correct branching logic into `resolve_multi_attack`

Not a new mechanic — `resolve_multi_attack` already computes the exact `classification` object
with the correct `rebirth_eligible` value (`combat.py:391`); the fix ports the same branching
`resolve_attack` already has, reusing the same classification, into the path that's actually
exercised. Mirrors this session's own already-successful, already-reviewed fix pattern for the
orphaned-kill-reward bug.

**Deliberately not ported to `resolve_skill_usage`/`resolve_aoe_attack` in this ticket** — both
have the identical gap, but this session's own direct instrumentation found 0 real calls to
either in the corpus (skill/AOE actions are not currently selected by any real AI-decision path
observed). Disclosed, not silently ignored — flagged as a real, lower-priority residual gap for
whoever next re-examines those 2 paths' own real usage.

## Docs Requiring Update

- `docs/guidelines/intentional_divergences.md`: new entry recording this fix, matching the
  Bug Fix rationale class already used for the sibling opportunity-attack fix (§2.33)

**Checked, not touched**: `docs/mechanics/01_entity_anatomy.md` and `docs/mechanics/
02_combat_laws.md` — neither currently documents the Hero's Journey/rebirth mechanic at all (real,
disclosed gap in the Mechanics Bible itself, pre-existing and independent of this fix — no false
claim to correct, and authoring net-new Bible content for an existing-but-previously-unreachable
mechanic is out of this ticket's own narrower scope).
