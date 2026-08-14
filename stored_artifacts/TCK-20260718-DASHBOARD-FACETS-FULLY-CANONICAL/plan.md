---
status: active
layer: observability
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL
date: 2026-07-18
tags: [observability]
---

# Implementation Plan — TCK-20260718-DASHBOARD-FACETS-FULLY-CANONICAL

## Summary

Make `facets["tiers"]`/`facets["layers"]`/`facets["priorities"]` fixed
canonical lists in `ingest.py`, mirroring `facets["statuses"]`. Investigate
and resolve `FilterSelect`'s now-likely-dead synthetic-option code. Update
the parity ledger, including fixing 2 stale claims found while extending
it. Verify live against a real, freshly-built server.

## Steps

### Step 1 — `ingest.py` facets change

Import `TIER_VALUES`/`LAYER_VALUES`/`PRIORITY_VALUES` from
`tools/ticket_field_values.py` alongside the existing
`WORKFLOW_STATUS_VALUES` import. Change the 3 facet computations to
`sorted(...)` over each canonical set.

### Step 2 — Update backend tests

Update the existing pinned facets test in place. Add 2 new tests: canonical
set with zero corpus matches, and filter-independence.

### Step 3 — Frontend dead-code investigation

Write a test proving `FilterSelect`'s synthetic-option fallback is
unreachable for its 4 real call sites given the new canonical facets.
Decide keep-vs-remove based on the result; if kept, re-document why.

### Step 4 — Parity ledger

Extend `INFRA-275` in place, including correcting the 2 stale claims found
during investigation, not just appending new text alongside them.

### Step 5 — Live verification

Kill any stale `dashboard-serve` process, confirm port free, rebuild fresh,
`curl` a zero/low-match filter combination, confirm all 3 newly-canonical
facets return full lists. Confirm the same visually via headless browser.

## Scope Guards

- Do not touch `facets["tags"]` — genuinely corpus-derived, correct as-is.
- Do not touch `TCK-20260718-LAYER-REGISTRY-CONVERSION`'s own registry
  mechanism — only consume `LAYER_VALUES` from it.
- Do not remove `FilterSelect`'s fallback without a test proving it's
  unreachable first.

## Dependency Map

Step 1 → Step 2, Step 3 (both need the facets change) → Step 5
(verification, needs everything landed). Step 4 can run any time after
Step 1's file paths are known.

## Acceptance Criteria Map

- AC "curl confirms full canonical lists regardless of filter combo" →
  Step 1 + Step 5.
- AC "headless-browser confirms no dropdown reverts" → Step 5.
- AC "new/updated unit tests" → Step 2.
- AC "parity ledger updated same session" → Step 4.
- AC "full test suites green, independently re-run" → Steps 2-3 + final
  re-run.

## Anti-Drift Notes

Sort explicitly when converting a frozenset to a list — do not rely on
iteration order.
