---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260923-TERR01-STALE-JURISDICTION-CITATION
phase: open
date: 2026-09-23
tags: [world, documentation]
---

# TCK-20260923-TERR01-STALE-JURISDICTION-CITATION

## Title

TERR-01 cites a `TERR-04` Rule ID that was correctly never created

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P1

## Request Summary

`docs/world_rules/places-culture/territory-control.md:30` reads:

> …**jurisdiction** (legal/institutional applicability, see TERR-04), **property**…

No `TERR-04` heading exists anywhere in `docs/world_rules/` — a repo-wide grep returns that single
citation and nothing else. The file's own headings run `TERR-01`, `TERR-02`, `TERR-03`, `TERR-05`.

**This is a citation bug, not a coverage gap.** Jurisdiction *was* investigated for Batch 11A and
admitted as an **Inherited entry** — a direct reuse of Batch 10's `LAW-03` adding no new semantics —
rather than as a new Domain Rule. Under the Catalog's own Rule admission discipline, Inherited
entries never receive a local ID, so a `TERR-04` heading was never going to exist by design. The
same file already cites it correctly at `:324`: "Inherited jurisdiction entry → Law/Enforcement
(LAW-03, Batch 10 — the deferred integration…)", and the Inherited entry itself sits at `:217`
("Jurisdiction's territorial basis is one declared scope among several"), carrying no `TERR-0N` ID.

Line 30 is a leftover from an earlier drafting guess, written before the admission pass concluded
Inherited. Corroborating that "one ID per relation type" was never the pattern: none of TERR-01's
other six relation types carries a self-referential `TERR-0N` pointer either — ownership points
externally to "Batch 08/01," the rest have none.

**Why it matters beyond tidiness.** `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`'s validator
resolves every `rule_id` against a **live scan** of `docs/world_rules/**/*.md` headings
(`tools/semantic_control_plane/rule_catalog.py::scan_rule_ids()`). A stale ID in the Catalog's own
prose is an invitation for a future mapping entry to cite an unresolvable foreign key. The validator
rejecting `TERR-04` is correct behavior; the prose pointing at it is the defect.

## Scope

- Repoint `territory-control.md:30`'s inline jurisdiction citation away from the non-existent
  `TERR-04` and at the real Inherited entry (`LAW-03`, Batch 10), matching how the same file's own
  bottom section at `:324` already phrases it.
- Confirm by grep that no other occurrence of `TERR-04` exists in the repo after the change.

## Out of Scope

- Creating a `TERR-04` Rule. Jurisdiction's admission as Inherited is settled and correct; this
  ticket must not reopen it.
- Renumbering `TERR-05`, or any other Rule ID. The numbering gap is a correct artifact of the
  admission discipline, not an error to close.
- Any change to TERR-01's target semantics, its seven-way relation-type split, or any other Rule's
  prose.
- Any mapping data (that is `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE`).

## Acceptance Criteria

1. `territory-control.md:30`'s jurisdiction citation points at the Inherited `LAW-03` entry, not
   `TERR-04`.
2. `grep -rn "TERR-04" docs/` returns zero hits.
3. `grep -cE "^## TERR-[0-9]+" docs/world_rules/places-culture/territory-control.md` still returns
   4 — no Rule added, removed, or renumbered.
4. TERR-01's seven relation types and its target-semantic prose are otherwise byte-identical; the
   diff touches one line.

## Related Tickets

- `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` — found this while scoping; deliberately kept it
  out of that slice so a frozen-Catalog edit gets its own traceability.
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` — its live-scan `rule_id` resolution is why a stale
  ID in Catalog prose is a real hazard.

## Related Docs

- `docs/world_rules/places-culture/territory-control.md` — `:30` (the defect), `:217` (the Inherited
  entry), `:324` (the correct existing citation)
- `docs/world_rules/README.md` — Rule admission discipline (Inherited vs. new ID)

## Related Stored Artifacts

- None.

## Related Code Areas

- `tools/semantic_control_plane/rule_catalog.py::scan_rule_ids()` — read-only context for why this
  matters; no code change expected.

## Assumptions / Open Questions

- Assumes the exact replacement wording should mirror `:324`'s existing phrasing rather than
  inventing a third form. If a different form reads better inline, that is the implementer's call;
  the requirement is only that it names the real Inherited `LAW-03` target.
- Diagnosis supplied by `world-rule-catalog-design` (the Catalog's author) and independently verified
  against the file at `:217` and `:324` before this ticket was filed.

## Implementation Notes

_To be completed by the implementer._

## Test Summary

_To be completed by the implementer._

Expected shape: no new tests. This is a one-line documentation fix; AC 2 and AC 3 are greps, and the
existing frontmatter validator covers the file's structural integrity.

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
