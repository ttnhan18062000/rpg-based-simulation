---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN

## Approach

1. Enumerate mechanisms with a real `implemented_by` but no `verified` block: 20, confirmed against
   peer's own count exactly.
2. For each, read its own already-present plain-comment evidence (most were bound in earlier
   tickets this epic and already carry real caller citations as YAML comments, just never
   formalized into a `verified:` block).
3. Independently re-confirm the caller evidence via direct grep before formalizing — never trust
   a comment's own prose without re-checking, same discipline as every prior batch.
4. Record a real `verified` block: `instrument: code_trace`, the actual verdict (not assumed
   `observed`), a note citing the re-confirmed evidence.
5. Regenerate consumer artifacts only if a verdict implies a state correction (none did this batch).

## Scope guards
- No new bindings, no code fixes, no state changes unless verification itself demands one.
- A `contradicted` verdict is reported as such, not massaged into `observed`.
