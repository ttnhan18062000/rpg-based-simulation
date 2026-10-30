---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED
artifact_type: plan
date: 2026-10-30
tags: [determinism]
---

# Plan (held until rpg-planner OKs the audit; no code is written before that)

Order, smallest risk first. Every sort uses the id string or an enum `.value` as the key, never `str(obj)`.

1. `tactical.py:704-722`: sort key `(-power, skill.id)`; keep the stable sort otherwise. Test: an entity with HEAVY_STRIKE and fireball ready picks `HEAVY_STRIKE` (id order) under two `PYTHONHASHSEED` values in subprocesses; positive control = the same test against the unfixed code fails at some seed (or, if it happens not to, record which seeds were tried and why the fixture forces the tie).
2. `learning.py:45`: `sorted(set(...))`. Test: observed skills in non-sorted order give a sorted tuple; more than 10 skills keep the first 10 sorted.
3. `leveling.py:137`: no code change proposed (single addend). Test pins that only `swift_reflexes` contributes, so a future second passive forces a deliberate sort.
4. `updates.py:269-281, 882-883`, `evolution.py:120`: `sorted(set(...))`, hygiene only. Test: merged lists are sorted.
5. `apply_plan.py:153`: `sorted(set(...))` for `active_modifiers`. Test: result is sorted and equals the old set.
6. Per rpg-planner's answer: `intelligence.py:928` (dedupe concerns by id, stable order), `intelligence.py:558/940/1811`, `capacity_enforcement.py:157-162` (hygiene), `generator.py:220` (world generation).
7. Cross-process test (AC4): a short run in subprocesses at two `PYTHONHASHSEED` values; the final canonical hash must be identical. Needs a heavy-slot ask through rpg-planner-ubuntu; not run before the OK.
8. Docs after the OK: Bible `02_combat_laws.md` skill-selection wording, COMB-264/265 ledger entries through `parity_ledger_writer.py`, a divergence entry (class Bug Fix) from the ubuntu block 2.144-2.149, then 2.160+.
9. Ticket must state (AC7): cached paired-run arms from before this fix stay valid only for branches still based before it.

Files named by this plan: `src/engine/tactical.py`, `src/domains/combat_engagement/learning.py`, `src/core/updates.py`, `src/engine/evolution.py`, `src/engine/apply_plan.py`, `src/systems/strategic_systems/intelligence.py`, `src/engine/pipeline_phases/capacity_enforcement.py`, `src/worldgeneration/generator.py`. None is `state.py`. Before editing any of them, re-check u24's open branches #788 and #789 (and #781, held) and route any overlap through rpg-planner-ubuntu.

M7 goldens: sorting state lists does not change emitted event order after ticket A; any change to an event in M7's goldens is reported to rpg-planner, not re-pinned.
