---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP
artifact_type: plan
tags: [ai, documentation]
---

# Plan — TCK-20260819-STANDARD-PARITY-LEDGER-HYGIENE-SWEEP

**Planning/scoping only — no implementation.** A separate agent implements each step.

## Step 1 — Fix the 2 malformed entries
In `docs/parity_ledger/town_resource.yaml`, replace `TOWN-040`/`TOWN-041`'s degenerate text and
empty fields with either:
- a real requirement description + evidence, if the underlying `test_rng`/`test_entity` behavior
  is findable and still relevant, or
- removal, if these were a pure import artifact with no corresponding real requirement (check
  `git blame`/`git log -p` on these two lines to find how they were introduced before deciding).

Re-run `tools/parity_index.py build` afterward; confirm the "fully bare entries" SQL scan (see
investigation.md) returns zero rows.

## Step 2 — Triage `absent_file` findings, once the domain-nesting ticket is done
Wait for `TCK-20260819-STANDARD-DOMAIN-TEST-DIR-NESTING` to land (it's actively moving 61 test
files as of this investigation — triaging against a moving target wastes effort). Then:
1. Rebuild the index (`tools/parity_index.py build`), re-pull `absent_file` findings.
2. For each hit under `dashboard-frontend/`-shaped paths (`.tsx`/`.ts` extensions cited as bare
   `src/...`): either fix the ledger's citation to include the `dashboard-frontend/` prefix, or —
   preferably, since this is a systemic checker gap affecting an unknown number of future entries
   too — fix `tools/parity_index.py`'s `_populate_entry_health()` to try both repo root and
   `dashboard-frontend/` when resolving a `.tsx`/`.ts`/`.jsx`/`.js` path.
3. For each remaining `code_refs`/`constraint_refs` hit: check whether the citation is a live
   evidence pointer or a narrative mention of an intentionally-deleted file (like the `INFRA-211`
   sample in investigation.md) — only the former needs a ledger fix (update the citation to the
   real current location, or mark the entry `divergent`/`missing` if the behavior genuinely
   regressed). The latter needs no ledger change but is worth flagging to `_populate_entry_health`
   as a known source of noise for a future refinement (not required in this ticket).
4. For each remaining `test_refs` hit: this is the highest-confidence-real bucket (120 entries
   pre-domain-nesting-fix) — update each ledger entry's `test_path` to the real current location,
   or investigate further if the cited test genuinely no longer exists (possible real coverage
   regression, not just a path rename).

## Step 3 — Archive the orphaned checklist system
1. Confirm (a fresh, quick re-check, not assumed from this investigation) that nothing besides the
   comment in `src/engine/rpg_depth.py` and historical `tickets/done/`/`stored_artifacts/`
   references depends on `docs/logic_checklist_exhaustive.md` or its 5 support scripts.
2. Move `docs/logic_checklist_exhaustive.md` to `docs/archive/` (matching the convention already
   used for `docs/archive/specs/2026-05-03-checklist-governance-design.md`, its own predecessor
   design doc).
3. Move the 5 orphaned scripts (`scripts/validate_checklist.py`, `scripts/ledger_validator.py`,
   `scripts/remediate_checklist.py`, `scripts/report_coverage.py`, `scripts/apply_traceability.py`)
   to `scripts/archive/` or delete outright if truly dead — implementer's judgment, informed by
   whether any of the 5 have logic worth preserving as reference vs. being pure duplicates of what
   `tools/parity_ledger_scan.py`/`tools/parity_ledger_writer.py`/`tools/parity_index.py` now do.
4. Fix (or remove) the dangling `logic_checklist_exhaustive_v2.md` reference in
   `src/engine/rpg_depth.py`'s docstring — either point it at the real archived path or delete the
   stale cross-reference if it's no longer useful context.
5. Add a one-line note to `docs/parity_ledger/schema.json`'s directory or a nearby README-style
   doc stating it is the sole authoritative parity-tracking mechanism, so a future agent doesn't
   reintroduce a parallel checklist.

## Explicitly out of scope (see investigation.md)
- Retrofitting the 1,552 `legacy_unstructured` entries with structured references.
- Any change to `docs/parity_ledger/schema.json` itself.
