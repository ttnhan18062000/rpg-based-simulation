---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: investigation
tags: [cognition, determinism]
---

# Investigation — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

Full investigation lives in `docs/brainstorm/2026-09-02-core-rpg-knowledge-belief-axis-proposal.md`
§2.2 — not duplicated here. Summary of the finding this ticket acts on:

- `StrategicComponent`'s canonical hash (`src/core/state.py:768-783`) covers only
  `current_project_id` and omits 6 fields: `hypotheses`, `source_trust`, `contracts`, and 3 others
  (full list in the source doc's §2.2 table) — with no comment explaining why.
- `source_trust` (`SourceTrustEntry`) is confirmed **behaviorally live** — it feeds
  `belief_and_detour_contract.md`'s documented `source_trust_bonus` term in real detour selection. Its
  exclusion means a real behavioral divergence between two same-seed runs can go completely undetected
  by the canonical hash — not a hypothetical audit gap, an active one.
- By contrast, `KnowledgeModelComponent.facts` is fully covered by its own `to_canonical_dict()` — this
  gap is specific to `StrategicComponent`.
- Required direction: add the 6 fields, or document each specific exclusion with a real, checkable
  reason.

## Next step for implementation
1. Re-read the source doc's §2.2 table directly against current `src/core/state.py:768-783` (confirm no
   drift since 2026-09-02) before writing code.
2. `source_trust` gets first attention given its confirmed live-behavior status — default expectation is
   it MUST be added unless a specific, recorded reason says otherwise.
3. Confirm with the concurrent M3 implementation session before editing `src/core/state.py` — shared,
   central file.
