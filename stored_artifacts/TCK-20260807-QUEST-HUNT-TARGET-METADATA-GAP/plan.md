---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP
artifact_type: plan
tags: [simulation-quality, progression]
---

# Plan: TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP

Per the user's chosen approach and investigation.md's findings: add `target_kind` to
`QuestTemplate`, set it to `"wolf"` for `q_wolf_hunt`, leave `q_slime_cull` unset (no real
content).

## Steps

1. `src/quests/generator.py`: add `target_kind: Optional[str] = None` field to `QuestTemplate`.
   Set `target_kind="wolf"` on `q_wolf_hunt`'s `TEMPLATES` entry; document why `q_slime_cull`
   deliberately has none.
2. `generate()`: when `template.kind == QuestKind.HUNT and template.target_kind`, set
   `quest_metadata["target_kind"] = template.target_kind`.
3. Tests (`tests/unit/quest/test_quest_generation.py`):
   - `q_wolf_hunt` gets `metadata["target_kind"] == "wolf"`.
   - `q_slime_cull` never gets a `target_kind` key.
   - `evaluate_combat_victory()` completes a wolf-hunt quest on a matching "wolf" kill.
   - `evaluate_combat_victory()` does NOT progress on an unrelated "goblin" kill.
   - End-to-end: real `generate()` → real `evaluate_combat_victory()` → real
     `QuestService.add_progress()` reaches `QuestStatus.COMPLETED` after repeated real kills.
4. Docs: `docs/simulation/quest_contract.md`'s Metadata population section — document the
   `target_kind` field and its per-template disposition.
5. Parity: `docs/parity_ledger/progression.yaml` — new `PROG-120` entry; `update_2026_08_07` note
   on `PROG-119` pointing to it (since `PROG-119`'s own text said HUNT "remain[s] permanently
   uncompletable," now stale for `q_wolf_hunt` specifically).
6. Run scoped tests, doc-staleness check, parity cross-reference, Verify static precheck,
   Finalize.

## Acceptance criteria map

| Original AC | Disposition |
|---|---|
| investigation.md documents chosen vocabulary approach and why | Done — `target_kind` field, `"wolf"` for `q_wolf_hunt`, none for `q_slime_cull` (no real content) |
| HUNT quests carry metadata `evaluate_combat_victory()` can match | Done for `q_wolf_hunt`; `q_slime_cull` remains a disclosed content gap, not fixed |
| Unit test: hand-constructed HUNT QuestState completes on matching kill, not on unrelated one | Done |
| Real-kernel verification: a live run shows a HUNT quest reaching COMPLETED | Done — full real generate→evaluate→add_progress lifecycle through 9 real kills |
| progression.yaml updated; grade_anchors.json recalibrated if needed | Done — new PROG-120; not recalibrated (HUNT quests were never completable in any scored scenario before this fix) |
| Scoped pytest passes | Done |
