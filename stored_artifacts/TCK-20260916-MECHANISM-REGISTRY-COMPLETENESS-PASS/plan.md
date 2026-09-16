---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS
artifact_type: plan
tags: [architecture, schema, simulation-quality]
---

# Plan — TCK-20260916-MECHANISM-REGISTRY-COMPLETENESS-PASS

## Steps

1. Enumerate `src/domains/*` and `src/systems/*`, classify each as: already-cited /
   infrastructure / genuine gap. (See investigation.md for method and per-item disposition.)
2. For each genuine gap, determine real `state` via direct caller/flag-default check, and append a
   new entry to `docs/brainstorm/mechanisms.yaml` with an inline evidence comment citing the exact
   file/line/flag.
3. Validate the registry after each batch of additions (`python3 -m tools.mechanism_registry` /
   direct script run) to confirm schema validity and get a running mechanism count.
4. Update `tests/unit/tools/test_mechanism_atlas_regenerate.py`'s
   `test_mapping_covers_exactly_73_of_75_mechanisms` (rename + expand its expected `unmapped` set)
   — the atlas-card-coverage count (73) itself does not change, since none of the new mechanisms
   have an atlas card.
5. Regenerate `docs/brainstorm/mechanism_verification_view.md` and
   `docs/brainstorm/mechanism_priority_view.md` for the final mechanism count.
6. Run the scoped test suite with `graphify-out/` genuinely moved aside, confirm pass, restore it —
   standing epic discipline, not skippable for this ticket.
7. Reconcile the ticket file's own record with the actual final state (do not leave a
   decision-pending / partially-resolved section stale relative to completed work).
8. Write staging artifacts, run done-checker precheck, move ticket to `tickets/done/`, migrate
   staging to `stored_artifacts/`, record hand-orchestrated closure, regenerate
   `docs/REGISTRY.yaml`.
9. Commit and push; report to peer.

## Scope guard

Out of scope for this ticket (see ticket's own Out of Scope section): the combined all-mechanism
view (`TCK-20260916-MECHANISM-COMPLETE-REGISTRY-VIEW`, sequenced after), full `depends_on`
edge-population for the newly-registered mechanisms beyond what's directly cited during this pass,
and auditing `src/engine/`/`src/core/`/`src/ai/` for further missed mechanisms.

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1. Every subdirectory of `src/domains/`/`src/systems/` has an explicit recorded decision | investigation.md's three classification lists (registered / infrastructure / already-covered) |
| 2. Every newly-registered mechanism has a real, checked state cited to code | the 11-row evidence table in the ticket's Implementation Notes |
| 3. `cooperation` and `chest` explicitly re-verified | investigation.md Finding 2 |
| 4. Honest statement of what was NOT fully resolved | Completion Summary — nothing from the originally-scoped enumeration was left unresolved; only the explicitly out-of-scope items (edges, combined view, other directories) remain, and those are named, not silent |
