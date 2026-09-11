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

Scope covers both line-keyed dicts (investigation.md §1, corrected in §6): 2 + 13 pinned entries. All
changes are in one test file plus both pinned-entry sections of `docs/audits/D14_coupling_depth.md`.

## Step 1 — Rekey both dicts by content, with an expected count

Convert `_DOMAINS_OBSERVABILITY_PINNED` and `_SYSTEMS_ENGINE_PINNED` from
`{(rel_path, lineno): (module, names)}` to `{(rel_path, module, names): expected_count}`.

The count is needed, not optional: `intelligence.py:832` and `:904` are identical imports
(investigation.md §4), so a plain set would collapse them and let a third copy through. That key
gets `2`; every other key gets `1`.

Match by membership, following the in-file precedent `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` — **except keep
`rel_path` in the key**. The precedent can omit it only because its loop covers three fixed files; these
loops cover whole packages (investigation.md §2).

Entries convert mechanically, since each value already holds `(module, names)`:
`("src/domains/campaigns/orchestrator.py", 487): ("src.observability.events", ("SimulationEvent",))`
becomes `("src/domains/campaigns/orchestrator.py", "src.observability.events", ("SimulationEvent",))`.

## Step 2 — Replace the per-line assertions with an exact count comparison

Walk the package, count every boundary-crossing import (non-`TYPE_CHECKING`) by
`(rel_path, module, names)`, and assert the resulting counts equal the pinned mapping exactly:

- a key not in the mapping → fails as a new, unpinned import;
- a key seen more times than pinned → fails (a new duplicate of a pinned import);
- a key seen fewer times than pinned → fails as a stale pin, so removed imports get un-pinned rather
  than staying as silent permissions.

A changed import target is simply a different key. Keep the failure message pointing at this test and
at D14.

## Step 3 — Preserve existing behavior

- Keep the `_type_checking_lines()` skip.
- Keep the "new unpinned import fails" negative path.
- **Multiplicity:** handled by the count in Step 1. Add a one-line comment at the `2` entry naming the
  two sites, so a reader doesn't "fix" it to `1`.

## Step 4 — Convert every D14 pinned-entry citation to content references

Both pinned-entry sections of `docs/audits/D14_coupling_depth.md`:

- **domains → observability** (2 rows): replace `narrative_ledger.py:71` and `orchestrator.py:418` with
  file + imported symbol + enclosing function (`emit_chronicle_event`, `_emit_domain_event`). This also
  fixes `:418`, which has been stale since the import moved to 487.
- **systems → engine** (the 5-row table covering 13 imports): replace the `Lines` column with the
  imported names per file, e.g. `intelligence.py` → `GovernorPolicy`, `SpatialQueryService`,
  `SystemCadence`/`should_run` (×4 sites, one of them `SystemCadence as DefaultCadence` ×2),
  `SimulationDomainLogic` (×2), `AppraisalSystem`. Keep the "13 imports across 5 files" totals — they
  should equal the sum of the pinned counts.
- In **both** sections, replace the sentence describing a "`(file, lineno)`-exact grandfather list"
  with one describing a content-keyed list with exact counts, and cite this ticket.

D14 line citations outside these two sections are unaffected and out of scope.

## Step 5 — Retire the re-pin history comments

The comment block above `_DOMAINS_OBSERVABILITY_PINNED` records each line re-pin (437→440, 447→487). Once
line numbers are gone that history no longer describes anything in the code. Replace it with one sentence
naming this ticket as the reason keys are content-based, so the next reader does not reintroduce lines.

## Out of scope

- D14 line citations outside the two pinned-entry sections.
- The boundary rules themselves — which imports are allowed does not change.
- `_OBS_DOMAINS_SYSTEMS_PINNED_IMPORTS` — already content-keyed.

## Risk

Low. Single test file, no production code. The main risk is a pin conversion typo silently unpinning an
entry — covered by test_plan.md's check that every existing pinned import still passes.

## Deviations (Implement, 2026-09-11)

- **`_SYSTEMS_ENGINE_PINNED` has 11 unique keys, not 12.** The implementation dispatch (and, before
  it, every prior pass over this dict — investigation.md, the ticket, and Review round 2) stated
  "12 unique keys, one with count 2," covering only the `intelligence.py:832`/`:904`
  `SystemCadence as DefaultCadence, should_run` duplicate. Direct re-read of `intelligence.py` at
  implementation time found a second, equally real duplicate: lines 84 and 828 are both
  `from src.engine.domain_logic import SimulationDomainLogic` — identical `(rel_path, module,
  names)`. Collapsing them to a single key at `expected_count: 1` (as "12 unique keys" implies)
  would have made the converted test fail immediately against unmodified `src/` (2 real
  occurrences vs. an expected count of 1 reads as a new duplicate) — i.e. it would have broken the
  "every currently-pinned import still passes after conversion" requirement on day one.
  `_SYSTEMS_ENGINE_PINNED` therefore ships with 11 unique keys, two of them at `expected_count: 2`
  (the `832`/`904` cadence pair and the `84`/`828` domain_logic pair). The sum of all counts is
  still 13, matching every other reference to "13 pinned exceptions" / "13 imports across 5 files"
  in the test comments, the ticket, and D14 — only the unique-key count differs from what was
  dispatched. Verified independently by reading `intelligence.py` lines 82-86 and 826-830 before
  writing the dict, and by `pytest tests/architecture/ -q` passing (109/109) against unmodified
  `src/` after the conversion.
