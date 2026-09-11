---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE
artifact_type: plan
tags: [testing, architecture]
---

# Plan — TCK-20260909-ARCHITECTURE-BOUNDARY-LINE-KEYED-PINNING-BRITTLE

Scope covers both line-keyed dicts (investigation.md §1). All changes are in one test file plus two
citations in `docs/audits/D14_coupling_depth.md`.

## Step 1 — Rekey both dicts by content

Convert `_DOMAINS_OBSERVABILITY_PINNED` and `_SYSTEMS_ENGINE_PINNED` from
`{(rel_path, lineno): (module, names)}` to a set of `(rel_path, module, names)`.

Match by membership, following the in-file precedent `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` — **except keep
`rel_path` in the key**. The precedent can omit it only because its loop covers three fixed files; these
loops cover whole packages (investigation.md §2).

Entries convert mechanically, since each value already holds `(module, names)`:
`("src/domains/campaigns/orchestrator.py", 487): ("src.observability.events", ("SimulationEvent",))`
becomes `("src/domains/campaigns/orchestrator.py", "src.observability.events", ("SimulationEvent",))`.

## Step 2 — Collapse the two assertions into one

Today there are two: "is this `(path, line)` pinned?" and "does its import target still match?". With
content keys both reduce to one question — is `(rel_path, module, names)` in the set? A changed import
target is simply a different key and fails as unpinned. Keep the failure message pointing at this test and
at D14.

## Step 3 — Preserve existing behavior

- Keep the `_type_checking_lines()` skip.
- Keep the "new unpinned import fails" negative path.
- **Multiplicity:** a set means two identical imports in one file are both covered by one pin. Accept
  that and say so in a comment — identical duplicate imports would be caught by ordinary lint, and adding
  count-matching buys nothing today.

## Step 4 — Fix the two D14 citations coupled to the pins

In `docs/audits/D14_coupling_depth.md`, replace `domains/campaigns/narrative_ledger.py:71` and
`domains/campaigns/orchestrator.py:418` with content references — file, imported symbol, and enclosing
function (`emit_chronicle_event`, `_emit_domain_event`), matching how the pins now identify them. This also
corrects `orchestrator.py:418`, which has been stale since the import moved to 487.

Scope is only the citations that correspond to pinned entries. D14's other nine line citations are
documentation, not gate keys; note them as a follow-up rather than rewriting the audit.

## Step 5 — Retire the re-pin history comments

The comment block above `_DOMAINS_OBSERVABILITY_PINNED` records each line re-pin (437→440, 447→487). Once
line numbers are gone that history no longer describes anything in the code. Replace it with one sentence
naming this ticket as the reason keys are content-based, so the next reader does not reintroduce lines.

## Out of scope

- D14's nine non-pinned line citations.
- The boundary rules themselves — which imports are allowed does not change.
- `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` — already content-keyed.

## Risk

Low. Single test file, no production code. The main risk is a pin conversion typo silently unpinning an
entry — covered by test_plan.md's check that every existing pinned import still passes.
