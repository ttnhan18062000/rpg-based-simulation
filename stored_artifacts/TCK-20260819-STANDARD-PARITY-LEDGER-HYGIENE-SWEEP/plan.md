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
**Default outcome: removal.** A repo-wide grep (`def test_rng(` / `def test_entity(`) found zero
real matching test functions — only unrelated names like `test_rng_reproducibility` — corroborating
the fixture-name-leak theory. Remove `TOWN-040`/`TOWN-041` from `docs/parity_ledger/town_resource.yaml`
unless the implementer finds a genuine underlying requirement backed by a real, currently-passing
test (check `git blame`/`git log -p` on these two lines to find how they were introduced before
deciding) — do not fabricate plausible-looking `v2_evidence`/`test_path` values just to satisfy the
acceptance criterion; that would be gate-gaming the ledger's own meaning fields, forbidden regardless
of which choice is made.

**If kept instead of removed** (only if a genuine requirement is found): both entries are
`priority: P0`. Per `docs/parity_ledger/schema.json`'s `allOf[2]` (mirrored in
`tools/parity_ledger_writer.py::validate_entry()`, lines 82-85), **P0 requires a non-null,
non-empty `test_path` regardless of `status`** — this holds even if `status` stays `missing`
(which only triggers the separate `verified`/`divergent` evidence rule). A fix that adds real
`text`/`v2_evidence` but leaves `test_path: null` is schema-non-compliant.

Re-run `tools/parity_index.py build` afterward; confirm the "fully bare entries" SQL scan (see
investigation.md) returns zero rows. **Note:** `parity_index.py build()` does not itself call
`validate_entry()` or check `schema.json`'s `allOf` rules — passing `build` and the bare-entries
scan does NOT prove schema compliance. See test_plan.md Step 1 verification for the required
explicit check.

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
1. Run an actual `grep -rln "logic_checklist_exhaustive"` sweep across the live tree (do not
   restate this investigation's snapshot as a pre-baked answer — it's already known to be
   incomplete, see below). Expected live references beyond `src/engine/rpg_depth.py` and
   historical `tickets/done/`/`stored_artifacts/` mentions, confirmed during Review:
   - `tools/add_frontmatter_live.py:138` — a hardcoded `LOOSE_FILES["docs/logic_checklist_exhaustive.md"]`
     entry (`status="active", authority="P1", layer="guidelines", audience="developer"`). This
     tool is documented as "re-run if adding a new directory" (`docs/guidelines/frontmatter_schema.md:214`)
     — it's live/maintained, not historical. Update this entry's `status`/`audience` to match the
     new archived frontmatter (see step 4), or remove it if `add_frontmatter_live.py` only tracks
     non-archived loose files (implementer's judgment on which — check the script's own logic).
   - `tests/tools/test_add_frontmatter_live.py::test_loose_logic_checklist` (~line 628) asserts
     against that same `LOOSE_FILES` entry — update in step with whatever `add_frontmatter_live.py`
     change is made, so the test keeps asserting a true statement.
   - `docs/plans/engine_future_epics_roadmap.md:43` — a live (non-archived) roadmap doc mention;
     update its reference to point at the new archived path, or note the file is now archived.
   None of these three break anything at runtime (path-string routing / pure prose, no filesystem
   I/O depends on the old path resolving), but leaving them unfixed is exactly the stale-reference
   hygiene this ticket exists to eliminate.
2. Move `docs/logic_checklist_exhaustive.md` to `docs/archive/` (matching the convention already
   used for `docs/archive/specs/2026-05-03-checklist-governance-design.md` and every other file
   under `docs/archive/`).
3. Move the 5 orphaned scripts (`scripts/validate_checklist.py`, `scripts/ledger_validator.py`,
   `scripts/remediate_checklist.py`, `scripts/report_coverage.py`, `scripts/apply_traceability.py`)
   to `scripts/archive/` or delete outright if truly dead — implementer's judgment, informed by
   whether any of the 5 have logic worth preserving as reference vs. being pure duplicates of what
   `tools/parity_ledger_scan.py`/`tools/parity_ledger_writer.py`/`tools/parity_index.py` now do.
4. Fix the frontmatter of `docs/logic_checklist_exhaustive.md` itself as part of the archive move —
   not just the directory relocation. Per every existing `docs/archive/*.md` file's convention
   (confirmed: `status: archive`, `authority: P2`, `audience: historical`, plus an `original_date`
   field), change the current `status: active` / `authority: P1` / `audience: developer` frontmatter
   to `status: archive` / `authority: P2` / `audience: historical`, keep `layer: guidelines`
   (already a registered layer, no reason to change it), and add `original_date: 2026-05-04` (the
   file's first commit date per `git log --follow`). Without this, `docs/REGISTRY.yaml`
   (auto-regenerated at Finalize) will keep listing the archived file as `status: active`.
5. Fix all 3 dangling `logic_checklist_exhaustive_v2.md` references (that exact filename variant
   exists nowhere in the repo) — more than investigation.md's original count of 1:
   - `src/engine/rpg_depth.py:8` (docstring)
   - `scripts/certification_long_run.py:154`
   - `tests/integration/kernel/test_certification_scenarios.py:112`
   All three feed into `src/core/certification_reporter.py::_analyze_checklist()`, which already
   no-ops gracefully via an `os.path.exists` guard (this filename never resolved, so this is not a
   new regression risk) — but fix all 3 to point at the real archived path
   (`docs/archive/logic_checklist_exhaustive.md`) or remove the stale cross-reference if no longer
   useful context, consistently across all 3 sites.
6. Add a one-line note to `docs/parity_ledger/schema.json`'s directory or a nearby README-style
   doc stating it is the sole authoritative parity-tracking mechanism, so a future agent doesn't
   reintroduce a parallel checklist.

## Explicitly out of scope (see investigation.md)
- Retrofitting the 1,552 `legacy_unstructured` entries with structured references.
- Any change to `docs/parity_ledger/schema.json` itself.

## Deviations (recorded during Implement)

1. **Step 2 — two additional systemic checker bugs found and fixed beyond the plan's
   dashboard-frontend-root scope.** While triaging, found that (a) a declared `test_path` with a
   `::test_function` pytest node-id suffix was checked as a literal filesystem path including the
   `::` suffix, so `_populate_entry_health()` always reported it absent even when the underlying
   `.py` file is real — this explained 117 of the plan's anticipated 120 "highest-confidence real
   drift" `test_refs` findings, meaning most of that bucket was checker imprecision, not real
   drift, contrary to the plan's stated expectation. (b) `legacy_evidence`-sourced `code_refs` were
   checked for existence even though `legacy_evidence` exists specifically to document the
   pre-V2, often since-deleted implementation location — a category error affecting all 3
   `legacy_evidence`-sourced `code_refs` rows repo-wide (SUB-007, SUB-073, STRAT-257). Both fixed
   in `tools/parity_index.py` with new regression tests, following the same "prefer systemic fix
   over one-off citation edits" principle the plan explicitly endorsed for the frontend-root case.

2. **Step 3 — chose "remove" over "point at the real archived path" for the certification-reporter
   call sites.** The plan's step 5 offered either option for all 3 dangling
   `logic_checklist_exhaustive_v2.md` references, but for `scripts/certification_long_run.py:154`
   and `tests/integration/kernel/test_certification_scenarios.py:112` specifically, repointing to
   the real archived path would change observable behavior: both pass the string as a functional
   argument into `CertificationReporter.generate_report()`, whose `_analyze_checklist()` would
   then actually parse `[x] VERIFIED v2` markers from the archived doc and compute a real
   `coverage["percent"]`, which directly feeds the report's `CERTIFIED`/`PROVISIONAL` status —
   silently reactivating the exact checklist-based scoring mechanism this ticket exists to retire.
   Used a deliberately-still-unresolvable sentinel path instead, preserving today's no-op behavior
   byte-for-byte. `src/engine/rpg_depth.py:8` (a pure docstring, no functional path argument) was
   repointed to the real archived path as the plan suggested, since there is no behavior-change
   risk there.

3. **`add_frontmatter_live.py`'s `LOOSE_FILES` entry was removed, not updated to archived
   frontmatter values**, per the plan's own offered alternative — the tool's docstring states it
   "excludes archive," so keeping an entry for a now-archived file would be self-contradictory
   with the tool's stated scope and would only ever produce a stale-path `WARNING` on future runs.

4. **A real functional dependency was found and fixed that the plan's grep-sweep list did not
   anticipate**: `scripts/release_gate.py:93` calls `scripts/ledger_validator.py` via
   `subprocess.check_call`. Updated the call site to `scripts/archive/ledger_validator.py` so
   moving the script didn't create a fresh dangling reference (release_gate.py is itself confirmed
   unwired from Makefile/CI, so this was already unreachable in practice, but leaving it broken
   would contradict the ticket's own purpose).
