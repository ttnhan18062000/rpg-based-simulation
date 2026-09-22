---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP
artifact_type: investigation
---

# Investigation — TCK-20260921-NESTED-EPIC-FOLDER-REGISTRY-VISIBILITY-GAP

## Verified the gap still reproduces (repo state may have moved on — checked first)

```
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC --tier epic --part finalize
# migration_complete: FAIL, ticket_finalized: FAIL, registry_entry_regenerated: FAIL (pre-fix)
```
Both named precedents still reproduce, unchanged. No unrelated in-flight ticket had touched either
tool.

## Open question answered: does `tickets/todos/{folder}/` already recurse?

Yes — `generate_registry.py::collect_tickets()`'s `todos_dir.rglob("*.md")` already walks
arbitrarily deep under `tickets/todos/` (excluding `SEQUENCE.md`), added by
`TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE`. Only `tickets/done/` was left
`glob("*.md")` (flat only). This directly answers the ticket's own open question and gives a
precedent to mirror rather than invent a new pattern.

## Real folder-shape census (before choosing one-level-deep vs. fully recursive)

All 84 `tickets/done/*/` subdirectories checked directly: every one holds `SEQUENCE.md` plus at
most one non-`SEQUENCE.md` `.md` file, at exactly one level deep, never nested further (child
tickets already moved to the flat `tickets/done/` root as they closed, per CLAUDE.md's own rule —
only the epic ticket + `SEQUENCE.md` remain in the folder once it moves). Some folders (e.g.
`tickets/done/m1-quick-wins/`) hold `SEQUENCE.md` only, no epic ticket file at all — a fully
completed epic tracked purely via child tickets, with no separate top-level epic ticket file ever
created. `glob("*/*.md")` (one level deep, matching the ticket's own explicit framing) correctly
handles both shapes: it adds the epic file where one exists, adds nothing where it doesn't.

## `migration_complete`'s FAIL is a separate, pre-existing gap, not itself about folder nesting

Checked whether a **flat** (non-folder-nested) epic ticket has its own `stored_artifacts/`:
`stored_artifacts/TCK-20260613-DOC-HARDENING-EPIC/` does not exist. No epic ticket checked, flat or
folder-nested, has ever had one — `check_migration_complete()` has no epic-tier `NA` branch
(only hotfix), so it FAILs uniformly for every epic, independent of where the ticket file lives.
CLAUDE.md's own Tier Routing table already establishes why: epic tier is "Scope only — tracks
child tickets; no direct implementation" — the epic's own investigation/plan/test_plan work is its
children's, not its own. Decision: add an epic-tier `NA` branch, same shape as the existing
hotfix branch. This corrects the AC's stated requirement (`migration_complete` must PASS) without
conflating it with the folder-visibility fix proper — recorded explicitly so a future reader
doesn't read this as a folder-nesting bug when it is not.

## `registry_entry_regenerated` needed no direct code change

Its own check (`entry.get("path", "").startswith("tickets/done/")`) already accepts any path under
`tickets/done/`, including a folder-nested one — once `collect_tickets()` emits an entry for the
folder-nested epic, this condition passes automatically. Confirmed by re-running the fixed checker
against both precedents (see Completion Summary) rather than assumed.

## Fix implemented

1. `tools/generate_registry.py::collect_tickets()` — added a second, one-level-deep walk
   (`done_dir.glob("*/*.md")`, excluding `SEQUENCE.md`) alongside the existing flat `done_dir.glob("*.md")`.
2. `tools/gate_checks/done_checker_static.py::check_ticket_finalized()` — checks the flat path
   first, then `tickets/done/*/{ticket_id}.md` (one level deep) if the flat path doesn't exist.
3. `tools/gate_checks/done_checker_static.py::check_migration_complete()` — added an epic-tier
   `NA` branch, same shape as the existing hotfix branch, with reasoning recorded in the code
   comment (see above).

## Real acceptance check (per the ticket's own AC, not a synthetic fixture)

```
python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC --tier epic --part finalize
# RESULT: PASS (migration_complete: NA, ticket_finalized: PASS, registry_entry_regenerated: PASS)

python3 tools/gate_checks/done_checker_static.py --ticket-id TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC --tier epic --part finalize
# RESULT: PASS (same three conditions)
```
Both epics confirmed present in the regenerated `docs/REGISTRY.yaml` (`grep -c` on both ticket IDs
returns 4 — ticket_id + path field per entry, 2 entries).

## Related
- `TCK-20260709-REGISTRY-REGEN-ON-CLOSE` — the "regenerate unconditionally at close" convention
  this gap quietly undermined for folder-closed epics.
- `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE` — origin of the `todos/`
  recursive-walk precedent this ticket mirrors for `done/`.
