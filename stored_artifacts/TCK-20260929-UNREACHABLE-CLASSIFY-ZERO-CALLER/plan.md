---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER
artifact_type: plan
tags: [investigation, root-cause, corpus, world]
---

# Plan — TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER

Scope-only classification: reuse PR #258's method (execute or re-run a falsifiable check per covered ticket, then
one verdict from the four-value axis or an AC-7 fifth outcome). Steps: (1) read the epic, its SEQUENCE.md and the
three covered tickets; (2) per ticket, re-run the zero-caller claim across `src/`, `tests/`, `tools/`, `data/`
including dynamic/string-keyed access and re-export shims, and date the cited code against the filing date;
(3) for the orphan class, look for a live equivalent before accepting "never wired in"; (4) for the tool ticket,
execute the tool; (5) record each verdict in the covered ticket's own body; (6) confirm `registries/mechanisms.yaml`
is unchanged against `origin/main` (not local `main`, which is stale here).

Explicitly not done: the shared classification doc (-> `T06`); fixing anything; correcting the runtime contract.
