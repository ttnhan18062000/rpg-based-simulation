---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261013-HEALTH-NEVER-RISES-ABOVE-MAX-HP-AT-THE-PATCH-WRITER
phase: done
date: 2026-10-13
tags: []
---

# Relationship half of D43: evidence for the later ticket (D68)

Urban political, 5000 ticks, trait+relationship build (C) vs hp clamp only (B):
- tick 0, seeds 42-44: 28 of 147 trading-person x functional-building pairs refused, all bandit_company people at hero_guild-owned buildings (probe_serves.py).
- bandit_company deaths identical B and C (8 COMBAT + 3 DEFEAT over seeds 42-44).
- town_council HAZARD deaths 7 -> 14, all seed 42 (2 -> 9, plus 1 STARVATION); seeds 43 and 44 identical (fac.py). Mechanism not found.
- The owner grain (D68): what the town actually knows about the person, not a faction label (serves.py reads the legacy owner bucket).
- probes/trait_only_variant.patch is the change applied in this PR.
