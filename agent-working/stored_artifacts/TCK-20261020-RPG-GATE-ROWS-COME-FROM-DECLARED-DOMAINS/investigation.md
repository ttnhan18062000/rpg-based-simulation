---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS
phase: done
date: 2026-10-20
tags: []
---

# Investigation: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

Run 39212800104's documents were sparse: rows existed only when something happened (crowded lacked O4.accepted/meat+plant+prepared on every seed, urban on s42/44/46, frontier 4-9 rows per seed), so the candidate step refused (every seed must report the same rows). Testing ruled the row set is declared, not observed (TCK-20261020-RPG-GATE-RUN-ROW-SET-IS-DECLARED-NOT-OBSERVED). source_kind is a free string with no enum; DeathCause is an enum; the only spawn producers that name a kind are camps (nest spread, flag off) and the calamity world boss (flag off); births and territory spawns copy an existing kind.
