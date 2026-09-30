---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-REPORT-PARITY-TEST-PATH-PRESENCE
artifact_type: plan
tags: [testing]
---

# Plan

1. `parity_layer` adds a `test_path` block: P0 with and without a `test_path`, other priorities the same, and per-file ids of P0 entries without one. A `test_path` counts as present only if it is a non-empty string other than `null`/`None`.
2. The markdown report shows the counts and the per-file totals; ids are in the JSON.
3. The block states that a `test_path` is a recorded path, not evidence that the test exists or passes; the v0 limits text says so.
4. Test: a P0 entry gaining a `test_path` changes the counts and the list.
