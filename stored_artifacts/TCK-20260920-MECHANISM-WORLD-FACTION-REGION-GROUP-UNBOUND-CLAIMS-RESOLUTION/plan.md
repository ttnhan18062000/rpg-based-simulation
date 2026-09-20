---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260920-MECHANISM-WORLD-FACTION-REGION-GROUP-UNBOUND-CLAIMS-RESOLUTION

## Approach

1. Enumerate the 23 world/faction/region/group mechanisms with `state in (done, partial, gated)`
   and no `implemented_by`, confirming peer's own per-layer counts exactly (12/5/4/2).
2. For each, check the mechanism's own existing `verified` note first, same citation-trail-first
   discipline as batch 1.
3. Investigate directly (no forks this batch, per the read-only-violation incident in batch 1) —
   real caller checks via grep before every binding, never trusted from a note's own prose alone.
4. Bind, correct state, or leave unbound per the same three-outcome framework as batch 1.
5. Regenerate all consumer artifacts and re-run the full validation/check suite after every
   substantive edit, same as batch 1.
6. Land on the same branch/PR as batch 1 (#229), per the user's own explicit call relayed by peer
   — no new PR.

## Scope guards
- No registry schema changes, no system-membership reassignment.
- No re-verification of already-verified entries UNLESS this batch's own investigation directly
  surfaces contradicting evidence (see `calamity_intensity` in Completion Summary) — in that case,
  the contradiction is reported on the entry, not silently forced into a binding either direction.
- No code fixes, including real defects found (unused `EquipmentService`, dead `Betrayal` directive,
  the `town_services`/`InnAction` discrepancy).
- No Split/Merge execution on a candidate found mid-batch (`betrayal_siege_war`) — flag only, same
  restraint as batch 1's `commitment_betrayal` non-merge.
