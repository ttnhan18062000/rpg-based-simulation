---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE
artifact_type: plan
tags: [data-quality, process-improvement]
---

# Plan — TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE

1. **Scope 1.** Run `runtime_probe.py` over all 21 corpus worlds; rewrite the 7 `verified` blocks
   to `corpus_run`/`observed`/`2026-09-30` with evidence in the note; regenerate every view through
   its generator (verification, priority, registry, rollup, html, capabilities tiers).
2. **Scope 2 (mechanism chosen).** New validator invariant 12 in `tools/mechanism_registry/
   registry.py`: `verdict == contradicted` with a static instrument is an error. Keyed on
   verdict + instrument, matching the registry header's own stated semantics; no new field. No
   grandfathering (Scope 1 fixes all 7 first).
3. **Scope 3.** One new Mandatory Scan item in `.claude/agents/ticket-scoper.md` (the registry-
   verdict premise rule). Not restated in create-tickets.js or any doc.
4. **Scope 4.** Cite rpg-feature-planning's STALE-PREMISE closure `791e6bf6b` in the ticket; do
   not annotate those tickets.
5. Tests: validator unit tests + real-registry guard, scoper-rule once-only test.
6. Update the make target description; close per the hand-orchestration checklist.

Out: RPG fixes, `premise-staleness-check` scope, re-verifying `observed` verdicts (no pattern
found, see investigation.md).
