---
ticket_id: TCK-20260618-AUDIT-D14-COUPLING
type: plan
date: 2026-06-18
---

# D14 Plan

Scan-based audit: run import graph scanner across all src/ packages, classify violations, score by coupling risk rubric (3×5=15).

Steps:
1. [done] Scan cross-domain imports in src/domains/
2. [done] Scan core→engine/domains upward deps
3. [done] Scan API layer for raw model exposure
4. [done] Map upper-layer→Kernel coupling
5. [todo] Write D14 audit document
6. [todo] Finalize ticket, update index, monitoring
