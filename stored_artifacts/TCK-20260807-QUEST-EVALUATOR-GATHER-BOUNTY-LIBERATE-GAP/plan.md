---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP
artifact_type: plan
tags: [simulation-quality, progression]
---

# Plan: TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP

Scope, per investigation.md's findings and the user's explicit decision: **fix EXPLORE only**;
document HUNT's real content-model blocker and file a follow-up ticket; leave GATHER/BOUNTY/
LIBERATE deferred (already out of scope per the original ticket).

## Steps

1. `src/quests/generator.py`:
   - Add `_EXPLORE_TARGET_MIN_DIST = 15.0` / `_EXPLORE_TARGET_MAX_DIST = 40.0` class constants on
     `QuestGenerator`.
   - Add `origin_pos: Optional[tuple[float, float]] = None` parameter to `generate()`.
   - When `template.kind == QuestKind.EXPLORE and origin_pos is not None`: compute a deterministic
     offset (angle via `DeterministicRNG.get_float(Domain.QUEST, tick, level, sub_id=1)`, distance
     via `sub_id=2`, both reusing the same `rng` instance already seeded for template selection so
     ordering stays deterministic) and set `metadata={"target_pos": (x, y)}`. Otherwise
     `metadata={}` — unchanged behavior for non-EXPLORE quests or callers not passing `origin_pos`.
   - Pass `metadata=quest_metadata` into the `QuestState(...)` constructor call (previously
     missing the kwarg entirely).
   - Add matching `origin_pos` parameter to `generate_quests()`, threaded through to its internal
     `generate()` call.
2. `src/town/guild.py`: `GuildAction.visit()`'s `QuestGenerator.generate_quests(...)` call passes
   `origin_pos=entity.navigation.position`.
3. Tests (`tests/unit/quest/test_quest_generation.py`):
   - EXPLORE quest with `origin_pos` gets a `target_pos` within `[15.0, 40.0]` tiles.
   - Deterministic: same `(seed, level, tick, origin_pos)` → same `target_pos`.
   - No `origin_pos` → no `target_pos` in metadata (same as before this fix).
   - Non-EXPLORE quest → `metadata == {}` regardless of `origin_pos`.
   - `QuestResolutionSystem.evaluate_explore()` actually completes a quest once the entity's
     position matches the generated `target_pos`, and does not complete it when far away.
4. Docs: `docs/simulation/quest_contract.md`'s "Quest Generation Contract" section — update the
   `generate()` signature and note the metadata population; its existing "Live Entry Point: Guild
   Visit" section (added by the sibling ticket) already covers the `GuildAction.visit()` caller,
   no change needed there beyond the signature note.
5. Parity: `docs/parity_ledger/progression.yaml` — quest generation/completion is a progression
   concern (XP/reward delivery gated on completion); add or update the relevant entry noting
   EXPLORE quests are now completable in live gameplay, HUNT/GATHER/BOUNTY/LIBERATE remain
   incomplete-by-design pending their own follow-up work.
6. File `tickets/todos/tech-debt/TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP.md` — HUNT's own
   content-model blocker (`QuestTemplate` has no subject/kind field; no real entity-identity
   signal distinguishes monsters from other neutral NPCs in any sampled world), scoped as a
   standard-tier ticket since it needs a genuine content/catalog design decision, not a
   mechanical fix.
7. Update this ticket's own body: Status, Scope (narrowed), Acceptance Criteria (revised to match
   EXPLORE-only), Implementation Notes, Test Summary, Files Changed, Completion Summary.
8. Run scoped tests, doc-staleness check, architecture check (informal — no dedicated durable
   state introduced; `metadata` is an existing `Dict[str, Any]` field on an already-durable
   `QuestState`), Parity cross-reference, Verify static precheck, Finalize.

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md documents exact trigger signal for GATHER/BOUNTY/LIBERATE | Superseded — these remain out of scope per user decision; investigation.md instead documents EXPLORE's real fix and HUNT's real blocker |
| evaluate_gather/bounty/liberate implemented | Not done — out of scope, unchanged from original ticket |
| Unit test per new evaluator | N/A — no new evaluators in this pass |
| parity_ledger updated | Done — progression.yaml entry for EXPLORE completion fix |
| Scoped pytest passes | Done |
