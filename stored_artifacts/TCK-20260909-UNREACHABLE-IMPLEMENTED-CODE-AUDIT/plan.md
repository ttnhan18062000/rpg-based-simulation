# Plan — TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT

## Approach
Build a single, committed, re-runnable AST-based audit tool rather than a one-time ad-hoc scan, per
this ticket's own Scope and per peer review's explicit deliverable-shape mandate. The tool must
avoid the specific failure mode that made this repo's prior dead-code audit (`D11_dead_code.md`)
untrustworthy: grep-based, directory-level import counting missed every lazy/deferred
(function-body-level) import, producing a confirmed 100% false-positive rate on its own
"Post-Audit Correction" pass.

1. **Collect definitions** — AST-walk `src/` for every top-level `FunctionDef`/`AsyncFunctionDef`/
   `ClassDef` and nested class method, recording file/line/decorators. AST rather than regex so a
   definition is never missed or double-counted by formatting quirks.
2. **Build a whole-corpus occurrence index** — single-pass identifier tokenization
   (`IDENT_RE.findall`) across every file in `src/`, `tests/`, `tools/`, catching every occurrence
   of an identifier regardless of where in a file it appears (import, call, decorator, string
   reference) — deliberately not scoped to "does another file import this," which is exactly what
   made D11 miss deferred imports.
3. **Classify each definition**:
   - `src_total` = occurrences in `src/` minus the definition's own line(s), counting same-file
     usage (a sibling function in the same module calling a private helper) as alive.
   - `is_candidate` = `src_total <= 0` — zero live call sites anywhere in `src/`, own definition
     excluded.
   - `has_test_coverage` = a separate boolean, occurrences in `tests/`+`tools/` > 0 — tracked, not
     folded into the reachability verdict, since this ticket's own definition of dead code is
     "no live call site outside their own definition and their own tests."
4. **Auto-exclude framework-invoked hooks** — FastAPI route/websocket decorators and Pydantic
   validator decorators are called by the framework, not by any visible call site; flag and exclude
   these separately, with the exclusion mechanism visible in the output, not silently dropped.
5. **Verify the tool against known ground truth before trusting its output** — the original 7-8
   known instances are the acceptance test for the tool itself. Any known instance the tool fails
   to surface, or any obviously-wrong flag on live code, is a methodology bug, not a limitation, and
   must be fixed before the inventory is treated as real.
6. **Organize the raw inventory by mechanism vs. surface** (peer-mandated axis, replacing a
   zero-anywhere/test-only split) — write deep manual-verification writeups only for clusters that
   look like real shared roots, not per-instance triage of all 362 real candidates.
7. **File cluster-level tickets, not instance-level ones** — name the shared root where one exists,
   matching the `spawn_calamity()`/`BiologicalSystem.update()` pair's own precedent.

## Scope Guards
- The audit produces the inventory, the clusters, and the tickets. It does not fix anything, and it
  does not individually triage all 362 real candidates — enforced by design (writeups are
  cluster-level only; the rest stay in the structured CSV/JSON for a future pass).
- Do not pre-judge a cluster's disposition (e.g. "wire it in") before determining whether a live
  equivalent already exists — apply this discipline to every cluster ticket filed, not just the
  ones peer review flagged directly.
- Stop and report a credible negative result rather than shipping an inventory that can't be
  trusted, if the false-positive rate had turned out too high to be checkable. (Did not happen —
  the real false-positive rate is ~15%, low and mechanistically explained.)

## Rollback
No production code changes. If the tool or inventory is later found unreliable, the fix is to
correct `tools/audit_unreachable_code.py` and regenerate the inventory files — no revert of
runtime behavior is needed.
