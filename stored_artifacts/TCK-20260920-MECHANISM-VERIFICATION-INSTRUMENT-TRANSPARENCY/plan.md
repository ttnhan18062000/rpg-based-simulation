---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY
phase: done
date: 2026-09-20
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260920-MECHANISM-VERIFICATION-INSTRUMENT-TRANSPARENCY

## Approach

1. Answer peer's 3 direct questions honestly before touching any registry entry: instrument used
   (all `code_trace`), whether any met a differential requirement (none), whether any case came
   close to a contradiction (no — the selection itself explains why).
2. Add `runtime_verified_share` to `_rollup_stats()`, same zero-count convention as existing rates.
3. Render it in both consumer views (markdown, HTML), with baseline comparison, same discipline as
   `bound_rate`/`verified_rate`.
4. Re-language `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` as dated addenda, not a
   silent rewrite.
5. Record the selection effect in the claims-as-tests doc as its own named case.
6. Update PR #229's own body to match.

## Scope guard

Do not touch any of the 20 `verified` entries the prior batch produced — explicit peer instruction,
and unnecessary since the finding itself is not in question, only its framing.
