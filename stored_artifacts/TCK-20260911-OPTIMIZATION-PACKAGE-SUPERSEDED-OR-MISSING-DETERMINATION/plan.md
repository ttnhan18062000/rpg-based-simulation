# Plan — TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION

## Disposition (peer-reviewed)
Determination-only, per this ticket's own explicit Scope — no deletions or wiring in this ticket.
All 8 modules investigated manually, module-by-module. Headline: none is cleanly "superseded,
delete" or "missing, wire" — every one is partially superseded with orphaned unique capability, a
genuine refinement of the parent audit's own "superseded, not missing" conclusion (see
investigation.md's Headline section). Follow-up work grouped by decision type into 5 tickets, per
peer review's explicit direction, rather than one ticket per module.

## Steps
1. File Ticket A (clean deletion, hotfix): `diagnostics.py` — whole file, superseded by
   `AlertsManager`/`AlertRouter`, nothing unique.
2. File Ticket B (`memory_limits.py`'s own disposition, hotfix): whole file deletable, but with two
   distinct rationales per half (superseded vs. abandoned-design-nothing-to-track) — kept as its own
   ticket so the reasoning isn't diluted into A's simpler framing.
3. File Ticket C (orphaned-capability determination, standard): one decision session covering all 5
   genuinely-unique behaviors found across `degradation.py`, `cache_strategy.py`,
   `dirty_scheduler.py`, `trace_governor.py` — are they wanted; if not, delete the whole containing
   module including its superseded core; if wanted, rescope to plug into the live mechanism that
   already owns the adjacent superseded half.
4. File Ticket D (`budget_manager.py`, standard): genuinely missing, its own "should we build this"
   question.
5. File Ticket E (`provider_enforcement.py`, standard): genuinely missing, its own "should we build
   this" question — flag the possible overlap with D's own `provider_calls` tracking for that
   ticket's own Investigate phase to check, not resolved here.
6. Close this ticket with the full determination recorded, no code changed.

## Guardrails
- Do not delete or wire anything in this ticket — determination and follow-up tickets only, per
  this ticket's own Scope and Out of Scope.
- Every follow-up ticket's disposition text must be written at method/behavior granularity, not
  file granularity — a reader must not be able to misread any of them as "just delete the file"
  when the file carries real, distinct capability alongside its superseded core.
- Ticket C must not presuppose the implementation shape for any of the 5 capabilities if kept —
  that's real design work for whoever picks it up, informed by which live mechanism already owns
  the adjacent superseded half, not decided here.
