---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP
artifact_type: plan
---

# Plan — TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP

## Steps

1. Verify both named precedents still reproduce the gap (repo state may have moved on) — see
   `investigation.md`.
2. Answer the ticket's own open question: does `tickets/todos/{folder}/` already recurse? Yes —
   mirror that precedent for `tickets/done/{folder}/`, not invent a new pattern.
3. Census all real `tickets/done/*/` folders to confirm one-level-deep is the correct, sufficient
   depth (not arbitrary recursion) before implementing.
4. Fix `generate_registry.py::collect_tickets()` to also walk one level into `tickets/done/`.
5. Fix `done_checker_static.py::check_ticket_finalized()` to check the nested path when the flat
   one doesn't exist.
6. Diagnose why `migration_complete` also FAILs — determine whether it's a folder-nesting
   consequence or a separate pre-existing gap (found: separate — no epic, flat or nested, has ever
   had its own `stored_artifacts/`). Fix with an epic-tier `NA` branch, same shape as hotfix's.
7. Confirm `registry_entry_regenerated` needs no direct change (its own `startswith("tickets/done/")`
   check already covers a nested path once `collect_tickets()` emits the entry).
8. Run the real acceptance check against both named precedents — PASS on all three conditions.
9. Add regression tests for both fixed functions.

## Acceptance criteria map

| Ticket AC | How this plan satisfies it |
|---|---|
| `generate_registry.py` includes an entry for a folder-closed epic ticket | Step 4, confirmed via `grep -c` on the regenerated registry |
| `done_checker_static.py --tier epic --part finalize` PASSes all 3 conditions for a real folder-closed epic | Steps 5-7, confirmed live against both named precedents (step 8) |
| Re-run against both real precedents to confirm generalization | Step 8, both PASS |
| No blocking gate introduced | Unchanged — both tools remain report/advisory-only; no new CI gate added |

## Scope decision (per the ticket's own open question)

- The folder-awareness fix (steps 4-5, and 7's automatic pass) is scoped generically — any ticket
  type that ends up in `tickets/done/{folder}/`, not epic-specific — matching how
  `generate_registry.py`'s own `todos/` precedent already handles all ticket types generically.
- The separate `migration_complete` fix (step 6) is genuinely epic-tier-specific — it has nothing
  to do with folder nesting (a flat epic fails it too) — so it is scoped to `tier == "epic"`
  exactly, mirroring the existing `tier == "hotfix"` branch's own scoping.

## Out of scope (per ticket)
- Changing the CLAUDE.md folder-move rule itself.
- `docs/REGISTRY.yaml`'s schema or `done_checker_static.py`'s non-finalize conditions.
- Recursing more than one level deep — no real folder shape needs it (see `investigation.md`'s
  census).
