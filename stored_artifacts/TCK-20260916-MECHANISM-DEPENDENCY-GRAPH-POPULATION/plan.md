---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-DEPENDENCY-GRAPH-POPULATION

## Step 1 — Add cited edges (done)
12 edges added to `docs/brainstorm/mechanisms.yaml`, each backed by a direct source-code citation
(see investigation.md). `movement` (the proof case) gains 2 direct dependents
(`combat_resolution`, `party_formation`) and rises to 14 transitive dependents / priority 70 — from
priority 0, off any ranked view, to #1 (tied).

## Step 2 — Corroborate with graphify (done)
`tools/mechanism_registry_graphify_check.py` run against the full updated edge set. 6 of 13 new
edges independently supported by the tool's own 3-hop BFS; 3 flagged suspicious (kept, with direct
primary-source citations stronger than the tool's own heuristic, reasoning recorded); 4 landed in
the tool's own non-defect `no_match` bucket.

## Step 3 — Decide the remaining 14 isolated mechanisms (done)
Each gets a recorded reason (see investigation.md's own table) — mostly explained by genuinely
inactive/gated/gap/orphan/skeleton state, or a directly-checked absence of any plausible consumer.
`social_contracts` is flagged as the one shallower check, honestly recorded as such rather than
overclaiming exhaustive certainty.

## Step 4 — Top-25 truncation (decided)
Kept as-is; the truncation question is properly the newer, separately-sequenced complete-view
ticket's own concern, not this one's — recorded, not left unexamined.

## Step 5 — Regenerate, test, close
`make mechanism-registry-validate`, `make mechanism-priority-view`, full scoped suite with
`graphify-out/` genuinely moved aside and restored, standard-tier finalize sequence.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1 (movement has real dependents) | Step 1 — 2 direct, 14 transitive, priority 0→70, now #1 |
| 2 (each of 26 isolated gets a decision) | Steps 1+3 — 12 resolved with cited edges, 14 recorded with reasons |
| 3 (ranked view stops omitting foundational systems) | Step 1 — confirmed by regenerating and reading the real output, not assumed |
| 4 (graphify cross-check run on every new edge) | Step 2 |
| 5 (top-25 cut explicitly decided) | Step 4 |
