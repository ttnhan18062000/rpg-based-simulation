# Investigation — TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT

## Critical prior art checked first: D11's own methodology already failed once

`docs/audits/D11_dead_code.md` (2026-06-18) attempted a superficially similar audit — directory-
level, grep-based import-counting across `src/`'s top-level directories. Its own
"Post-Audit Correction" (2026-06-23, `TCK-20260623-DEAD-CODE-REMOVAL`) found **every single
"orphan" finding was a false positive**: real importers existed for all 9 flagged directories,
missed because the grep-based count didn't catch lazy/deferred imports (imports inside function
bodies — a pattern this codebase uses heavily, confirmed directly throughout this whole session's
own work) and test-only imports.

This is the load-bearing precedent for this audit's own methodology. A naive "grep for `from X
import`" approach is proven unreliable in this specific codebase. This audit uses AST-based
definition collection plus whole-identifier text search across the full corpus (not import-
statement-only matching), specifically to avoid D11's own confirmed failure mode.

## Known-instance list has grown past the ticket's original seven

Per peer review (`rpg-feature-planning`), before starting: the ticket's own Request Summary table
(7 instances) is a starting inventory, not the scope. Confirmed additions since filing:
- `EntitySpawnContext.spawn_region` → `properties["spawn_region"]` write (added as an 8th instance
  directly in this ticket's own body, 2026-09-11, during Batch B).
- Batch C surfaced more candidates worth folding in (per peer review) — checked during this
  investigation's own sweep, not re-derived from scratch.

## Methodology (see plan.md for the full script design)

Two-tier automated candidate generation, followed by manual verification of every surviving
candidate against known false-positive categories (entry points, dynamic dispatch, registry/
plugin lookup by string, framework-invoked hooks, re-exported public API) — per this ticket's own
explicit AC requirement that exclusions be reasoned, not silently filtered.

- **Tier 1**: top-level functions/classes in `src/`, checked for zero identifier occurrences
  anywhere else in the full repo corpus (`src/`, `tests/`, `tools/`), excluding their own
  defining file. Low false-positive risk (exact identifier match, not substring).
- **Tier 2**: class methods, checked similarly but with an explicit confidence downgrade for
  generic/common method names (`apply`, `execute`, `resolve`, etc.) shared across many unrelated
  classes, where a text-match hit doesn't confirm it's actually calling *this* class's method
  (and a miss is a much stronger signal for a distinctive name than a generic one).

Full raw results and manual verification notes below (populated as the sweep runs).
