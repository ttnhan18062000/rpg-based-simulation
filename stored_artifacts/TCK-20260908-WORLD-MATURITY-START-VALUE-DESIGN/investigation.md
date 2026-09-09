---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN
artifact_type: investigation
tags: [world, architecture]
---

# Investigation — TCK-20260908-WORLD-MATURITY-START-VALUE-DESIGN

The design decision itself was already made by the real user before this ticket was picked up
(accept the `state.maturity >= 50` gate as long-horizon-only; no schema field; no gate
recalibration). This ticket's own remaining work was the blast-radius survey and the disclosure —
see the ticket's own Implementation Notes for the full write-up. Summary of the survey:

`grep -rn "state\.maturity\b" src/` (excluding tests) found 6 reference sites:

| Site | Kind | Reachable? |
|---|---|---|
| `boss.py:92` `check_for_boss_spawn()` | Gate (`>=50` + region.trauma>=20) | Yes, long-horizon-only |
| `boss.py:218` `check_for_lair_spawn()` | Gate (same threshold) | Yes, long-horizon-only |
| `raid.py:40` / `camp.py:125` `spawn_raid()` sizing | Scaler (`3+maturity`) | Yes, always ~3 in practice — separate ticket `RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` |
| `generator.py:254-266` `spawn_stronghold()` | Scaler (HP/DEF) | Yes, real caller (`influence.py:94`), always baseline stats in practice |
| `generator.py:238-251` `spawn_calamity()` | Scaler (HP/ATK/DEF/level) | **No — zero callers anywhere, dead code** |
| `checkpoint.py`, `state_presenter.py`, `fingerprint.py` | Read/serialize | N/A, not a gate |
| `apply.py:308` | Carry-forward assignment | N/A, not a consumer |

Two findings beyond the ticket's own original framing: (1) `check_for_boss_spawn()` shares the
identical gate with `check_for_lair_spawn()` — not previously connected; (2) `spawn_calamity()` is
confirmed dead code, unrelated to the maturity threshold itself.

Also found and corrected, directly adjacent to this investigation:
`docs/world/raid_boss_camp_contract.md`'s own "Boss — Spawn conditions" section read
`camp.maturity >= 50`, inconsistent with the same doc's own correct `state.maturity >= 50`
phrasing two paragraphs later.
