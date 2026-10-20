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

# Plan: TCK-20261020-RPG-GATE-ROWS-COME-FROM-DECLARED-DOMAINS

1. Declare the row domains: groups from the compiled world (tick-0 kinds plus declared spawn-source kinds), causes from DeathCause, sources from TRANSFER_SOURCES (guarded by a unit test over src literals).
2. Emit every declared row on every seed with true zeros; strays raise GateDataMissingError (except groups explained by an unsourced add, which V8 fails).
3. O1 share = two count rows (starved, at_risk = individuals ever alive) plus a pooled share row (null, empty_denominator).
4. Unit and real-kernel tests; dry chain through the candidate step; fold hash.
