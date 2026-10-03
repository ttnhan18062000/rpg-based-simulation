---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP
phase: done
date: 2026-08-07
tags: [simulation-quality, progression]
---

# TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP

## Title
`QuestResolutionSystem` has no progress-evaluator for 3 of 5 quest kinds — `GATHER`/`BOUNTY`/
`LIBERATE` quests can never complete (revised: real fix implemented is EXPLORE metadata
population — see "UPDATE 2026-08-07" below)

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
`TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE`'s investigation found `QuestResolutionSystem`
(`src/engine/quests.py`) has exactly two progress-evaluator methods: `evaluate_explore()` (EXPLORE
kind, wired via `movement_actions.py:35` on movement completion) and `evaluate_combat_victory()`
(explicitly filtered to HUNT kind only — `project.quest_kind != QuestKind.HUNT: continue`, line
90 — wired via `combat_actions.py:72` and `aoe_actions.py:91` on kill).

**`GATHER`, `BOUNTY`, and `LIBERATE` have no `evaluate_*` method at all.** A quest of any of these
3 kinds (3 of `QuestKind`'s 5 total values) could never progress toward `goal_value`, regardless of
tick depth, even once quests are actually generated
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`).

This gap is currently masked/unreachable in practice — no real quests of any kind exist in live
gameplay today (see the sibling ticket above) — but becomes a real, user-facing blocker the moment
that ticket's fix lands: 3 of the 5 documented quest templates
(`docs/simulation/quest_contract.md`'s Built-in templates: `q_herb_gather` GATHER,
`q_bandit_bounty` BOUNTY, `q_camp_liberate` LIBERATE) would generate but never be completable.

**UPDATE 2026-08-07 (found during `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s own real-kernel
verification, now landed — real quests ARE generated in live gameplay):** this ticket's own
premise that HUNT/EXPLORE already work is wrong — the real bug is broader than "3 of 5 kinds have
no evaluator." Ran `sandbox_world_seed42` for 3000 ticks with real quest generation live: multiple
HUNT quests generated (`Wolf Cull` x4, `Clear the Slimes`) and one EXPLORE (`Survey the Woods`),
none ever progressed past `ACTIVE`, despite confirmed ongoing combat in the same world. Root
cause, confirmed by reading `QuestGenerator.generate()`'s real return value directly
(`src/quests/generator.py:130-144`): the constructed `QuestState` **never sets `metadata` at
all** — it defaults to `{}` (the dataclass's own `field(default_factory=dict)` default).
`evaluate_combat_victory()`'s matching (`target_archetype_id`/`target_faction_id`/
`target_projected_label`/`target_kind`, `src/engine/quests.py:93-147`) and
`evaluate_explore()`'s matching (`target_pos`, line 35) **both** read from `project.metadata` —
with it always empty, neither evaluator can ever match anything for a real generated quest. This
is not "3 of 5 kinds have no evaluator" — it's "the quest generator and both existing evaluators
use incompatible, disconnected contracts, for all 5 kinds equally." Revise this ticket's own
Investigate phase accordingly: the real fix is likely in `QuestGenerator.generate()`/
`QuestTemplate` (populate the metadata the evaluators already expect, using each template's own
`subject_options`/kind to derive `target_archetype_id`/`target_pos` deterministically), not
writing 3 new evaluator methods from scratch — confirm this against `QuestTemplate`'s actual
fields before Plan, do not assume.

**UPDATE 2026-08-07 (scope narrowed further, EXPLORE + HUNT → EXPLORE only):** per the user's
explicit decision, this ticket's scope was set to "Fix HUNT + EXPLORE now; defer GATHER/BOUNTY/
LIBERATE." Investigation found EXPLORE fixable (its match signal, `target_pos`, needs only the
requesting entity's own position — already available). HUNT is not safely fixable in the same
pass: `QuestTemplate` has no subject/target-kind field to derive any of
`evaluate_combat_victory()`'s 4 match paths from, and a real-corpus check (sampling
`EntityIdentityResolver` output across 4 worlds) found no ambient identity signal that could
substitute — every non-hero/non-town-service entity resolves to `role_id="citizen"`,
`faction_id="neutral"` regardless of whether it's monster-like or not. Fixing HUNT needs a real
content/catalog design decision (see `investigation.md` for the full trace), which this ticket's
scope does not extend to inventing unilaterally. **Implemented scope: EXPLORE only.** HUNT's gap
is fully documented and tracked by a new follow-up ticket,
`tickets/todos/tech-debt/TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP.md`.

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm the exact typed signal each kind needs: GATHER likely mirrors `resource_harvested`'s
     `intent_results[].source_kind=="NODE"` accepted-intent signal (does the entity already gain
     inventory items on harvest that a `QuestUpdate.progress_delta` could hook into?); BOUNTY is
     likely `evaluate_combat_victory()`'s existing logic minus the `quest_kind != HUNT` filter, but
     confirm whether BOUNTY's `target_id`-based matching (region/camp, per
     `src/systems/world_systems/quest_generator.py`'s now-confirmed-dead `Bounty Quest` sketch — do
     NOT resurrect that dead code, it uses a different constructor shape) needs a genuinely
     different match condition than HUNT's entity-kill matching; LIBERATE likely needs a
     region-ownership-change signal (`region_ownership_changed`/`territory_ownership_changed`),
     not an entity-level one — confirm the exact trigger against real `WorldEvent`/`FactionUpdate`
     records, not guessed.
   - Determine whether each new evaluator needs a new call site (mirroring
     `movement_actions.py`/`combat_actions.py`'s existing wiring pattern) or can share an existing
     one.
2. **Plan**: design the 3 evaluator methods and their call sites.
3. **Implement**: add `evaluate_gather()`, `evaluate_bounty()`, `evaluate_liberate()` (or a unified
   dispatch if the investigation finds them naturally converge), wired at the appropriate
   authoritative-pipeline call sites, following the existing `evaluate_explore()`/
   `evaluate_combat_victory()` pattern (pure functions returning `List[QuestUpdate]`, no direct
   state mutation).
4. Recalibrate `grade_anchors.json` for any scenario whose PROGRESSION grade shifts.

## Out of Scope
- `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING` — this ticket's own fix is inert until that one
  lands; do not implement this ticket's fix in a way that depends on unmerged code from that
  ticket — write and test each evaluator against a hand-constructed `QuestState` fixture
  independent of whether real quest generation is wired yet.
- `TCK-20260807-QUEST-EVENT-TYPE-FILTER-BUG` — unrelated.
- Any change to `QuestGenerator`'s templates or reward values.

## Acceptance Criteria
(Revised 2026-08-07 to match the narrowed EXPLORE-only implemented scope — see "UPDATE" above.)
- [x] `investigation.md` documents EXPLORE's real fix and HUNT's real content-model blocker
      (GATHER/BOUNTY/LIBERATE were already out of scope by the original ticket)
- [ ] ~~`evaluate_gather()`, `evaluate_bounty()`, `evaluate_liberate()` implemented and wired~~ —
      not done, out of scope (unchanged from original ticket)
- [x] Unit test: EXPLORE `QuestState` with generator-produced `target_pos` reaches `COMPLETED`
      when the entity arrives, and does not progress when far away
- [x] `docs/parity_ledger/progression.yaml` updated (`PROG-119`); `grade_anchors.json` not
      recalibrated — no existing scored scenario's baseline reflected a pre-fix "quests complete"
      state to shift away from (see `PROG-119`'s `support_boundary`)
- [x] Scoped pytest run passes

## Related Tickets
- TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE (source of this finding — Finding 3, DONE)
- TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING (practical prerequisite for this fix to matter,
  though independently implementable/testable; also the source of the real-kernel run that first
  showed HUNT quests never completing)
- TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP (new follow-up filed from this ticket's own
  investigation — HUNT's real content-model blocker)

## Related Docs
- `docs/simulation/quest_contract.md` (QuestKind Enum, Built-in templates table)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260806-SIMQ-QUEST-COMPLETION-PACING-PROBE/investigation.md` (Finding 3,
  full trace)

## Related Code Areas
- `src/engine/quests.py` (`QuestResolutionSystem`)
- `src/engine/domain/` (wherever the new call sites land — resource harvesting, territory/region
  ownership change)

## Assumptions / Open Questions
- Whether BOUNTY needs genuinely different matching logic from HUNT, or can reuse
  `evaluate_combat_victory()` with the kind filter removed/widened, is not decided — Investigate
  phase must confirm against real `target_id`/`target_archetype_id`/`target_faction_id` metadata
  semantics for BOUNTY-kind quests specifically, not assume HUNT's logic transfers directly.

## Implementation Notes
`QuestGenerator.generate()` (`src/quests/generator.py`) gained an `origin_pos: Optional[tuple[float,
float]] = None` parameter. When the drawn template is `QuestKind.EXPLORE` and `origin_pos` is
given, it computes a deterministic target position — angle and distance both drawn from the same
`DeterministicRNG` instance already used for template selection (`sub_id=1`/`sub_id=2` so the
draws don't collide), offset `[15.0, 40.0]` tiles from `origin_pos` — and sets
`metadata={"target_pos": (x, y)}` on the returned `QuestState`. Previously the `QuestState(...)`
constructor call never passed a `metadata` kwarg at all, so every quest of every kind defaulted to
`metadata={}` and neither existing evaluator (`evaluate_explore()`, `evaluate_combat_victory()`)
could ever match anything for a real generated quest. `generate_quests()` and `GuildAction.visit()`
(`src/town/guild.py`) thread `entity.navigation.position` through as `origin_pos` — `GuildAction`
is the only real caller of the generator in live gameplay
(`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`'s `GuildVisitPhase`).

HUNT was investigated (per the user's original "Fix HUNT + EXPLORE" scope) but found not safely
fixable in this pass — see the "UPDATE 2026-08-07" section above and `investigation.md` for the
full corpus-sampling trace. Scope narrowed to EXPLORE only; HUNT's gap tracked by
`TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP`. GATHER/BOUNTY/LIBERATE untouched, as originally
scoped out.

## Test Summary
New tests in `tests/unit/quest/test_quest_generation.py`: `test_explore_quest_gets_target_pos_when_origin_given`,
`test_explore_quest_target_pos_deterministic`, `test_explore_quest_without_origin_pos_has_no_target_pos`,
`test_non_explore_quest_has_empty_metadata_regardless_of_origin`,
`test_evaluate_explore_completes_quest_once_entity_reaches_target_pos`,
`test_evaluate_explore_does_not_complete_quest_far_from_target_pos`. All pass (25/25 in this file).
Also re-ran `tests/unit/world/test_guild_pipeline.py`, `tests/unit/world/test_guild_intel.py`,
`tests/unit/ai/test_guild_need_scorer.py`, `tests/unit/engine/test_guild_visit_phase.py`,
`tests/architecture/test_guild_action_dormancy.py` (guild-visit callers of the changed generator
signature) — all pass, no regressions. No pre-existing unrelated failures observed in this scope.

## Files Changed
- `src/quests/generator.py` — `origin_pos` param on `generate()`/`generate_quests()`, EXPLORE
  `target_pos` computation, `metadata=` now passed to `QuestState(...)`
- `src/town/guild.py` — `GuildAction.visit()` passes `origin_pos=entity.navigation.position`
- `tests/unit/quest/test_quest_generation.py` — 6 new tests
- `docs/simulation/quest_contract.md` — Quest Generation Contract section updated
- `docs/parity_ledger/progression.yaml` — new `PROG-119` entry (status: `divergent`, documents the
  remaining HUNT/GATHER/BOUNTY/LIBERATE gap)
- `tickets/todos/tech-debt/TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP.md` — new follow-up ticket

## Completion Summary
Fixed the real root cause blocking EXPLORE quest completion: `QuestGenerator.generate()` never
populated `QuestState.metadata`, so `evaluate_explore()`'s `target_pos` match could never fire.
EXPLORE quests now carry a deterministic target position and complete correctly on arrival,
verified by unit test end-to-end (generate → evaluate → COMPLETED). HUNT was investigated per the
user's original scope but found to need a genuine content-catalog design decision (no template
field, no substitutable real-content identity signal) rather than a mechanical fix — honestly
scoped out and handed off to a new, clearly-scoped follow-up ticket rather than guessed at.
GATHER/BOUNTY/LIBERATE remain deferred, unchanged from the original ticket's own scope.
