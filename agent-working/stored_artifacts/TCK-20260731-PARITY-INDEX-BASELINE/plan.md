---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-BASELINE
artifact_type: plan
tags: [ai, documentation, process-improvement, testing]
---

# Implementation Plan — TCK-20260731-PARITY-INDEX-BASELINE

## Summary

This ticket produces three kinds of new, read-only-of-source artifacts and nothing else: (1) a
deterministic baseline-manifest generator script that dynamically enumerates all nine
`docs/parity_ledger/*.yaml` shards and emits a versioned JSON snapshot (hashes, counts, status/priority
breakdowns, schema-coverage-as-parsed, and the 1,936-vs-1,945 drift note); (2) versioned fixture captures
of the legacy 8-file tools' (`parity_ledger_scan.py`, `parity_updater_static.py`) exact behavior for
faction/unmapped/multi-shard/malformed-YAML cases; and (3) a v1 decision record document that resolves
every open architecture question the idea doc left unsettled (ownership, discovery/IDs, schema shape, FTS
fallback, atomic lifecycle, path-only links, output convention, and CLI/module ownership), explicitly
recording that `parity-record` (mutation) stays deferred. No index, database, `.gitignore`/Make target,
YAML edit, or legacy-tool edit is created. All four Investigation open questions are decided in this plan
(see the per-step rationale and the Anti-Drift Notes) — none require escalation to human review.

## Steps

### Step 1 — Baseline manifest generator script
**Files:** `tools/parity_index_baseline.py` (new)
**Change:** New, standalone, flat module (no new package directory — see CLI/module ownership decision
below) that:
- Discovers shard files via `sorted(Path("docs/parity_ledger").glob("*.yaml"))` — dynamic glob, never a
  hardcoded file list, so `faction.yaml` is included by construction (this is the manifest's own
  enumeration, deliberately independent of `CANONICAL_LEDGER_FILES`).
- For each shard: computes SHA-256 of the raw file bytes, parses via `yaml.safe_load`, counts entries
  (top-level list length), collects `id` values, and tallies `status`/`priority` per entry.
- Computes corpus totals: total entry count (expected 1,945 today), duplicate-ID count across all shards
  (expected 0 today — recorded as an *observed fact*, not asserted as an enforced invariant; the v1
  decision doc in Step 4 is where the invariant itself gets declared).
- Records `entry_count_current` = live count and `entry_count_historical_reference` = 1936, plus an
  explicit `drift` object (`{"delta": entry_count_current - 1936, "source": "idea doc dated 2026-07-31",
  "note": "..."}`). **Decision (resolves Investigation open question 1):** adopt the investigator's
  recommendation verbatim — record both numbers, never coerce one into the other. 1,945 is the
  current/authoritative count; 1,936 is a dated historical comparison figure from the idea doc. This
  satisfies AC #2 by making the drift legible, not by reproducing 1,936.
- Records `excluded_from_legacy_scan: ["faction.yaml"]` by importing `CANONICAL_LEDGER_FILES` from
  `tools.parity_ledger_scan` (import only — never redefine the tuple) and diffing it against the manifest's
  own 9-file glob result.
- Records a `schema_coverage` field describing `docs/parity_ledger/schema.json` **as it actually parses**
  today (only the `divergent`→`divergence_note` rule survives the duplicate top-level `"if"` key; the
  `verified`/`divergent`→`v2_evidence`+`test_path` rule is silently discarded by `json.loads`). **Decision
  (resolves Investigation open question 3):** note-only. The script documents this as a known fact, does
  not attempt to fix, reformat, or reinterpret `schema.json`. Record it as a candidate future ticket in the
  v1 decision doc (Step 4), not as work this ticket performs.
- Records `missing_evidence_health` counts: how many `verified`/`divergent` entries lack `test_path` and/or
  `v2_evidence` (expected 1,347 lacking `test_path` per investigation.md). This is a count/classification
  only — the script must never fabricate, backfill, or drop these entries.
- Serializes to JSON with `sort_keys=True`, fixed `indent`, `ensure_ascii=True`, trailing newline — the
  exact canonical serialization needed for byte-identical reruns.
- Writes output to `staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json` (this
  ticket's own staging directory; migrates to `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/` at
  ticket close per the standard workflow's "After Work" step — no `docs/` location for the manifest itself,
  since it is a point-in-time evidence snapshot, not living cross-ticket guidance).
- Opens every `docs/parity_ledger/*.yaml` file **read-only** (`open(..., "r")` / `Path.read_bytes()` only)
  — never writes to any path under `docs/parity_ledger/`.
**Do NOT touch:** `docs/parity_ledger/*.yaml` (read-only), `tools/parity_ledger_scan.py` (import only, do
not modify), `docs/parity_ledger/schema.json` (do not modify, only describe).
**Verify:** `test_baseline_manifest_covers_all_nine_shards`,
`test_baseline_manifest_source_hashes_match_live_files`,
`test_manifest_records_both_historical_and_current_entry_counts`,
`test_manifest_records_legacy_eight_shard_faction_gap` (Step 2).

### Step 2 — Manifest determinism and coverage tests
**Files:** `tests/tools/test_parity_index_baseline.py` (new)
**Change:** Add the manifest-facing tests from test_plan.md items 1–5:
- `test_baseline_manifest_is_byte_identical_on_rerun` — run the Step 1 script twice against the live
  `docs/parity_ledger/` tree (no fixture substitution needed here since source is unchanged between runs)
  and assert byte-identical output.
- `test_baseline_manifest_covers_all_nine_shards` — assert the manifest's shard list has exactly 9 entries
  including `faction.yaml`.
- `test_baseline_manifest_source_hashes_match_live_files` — recompute SHA-256 of each live shard file
  independently in the test and assert equality with the manifest's recorded hashes.
- `test_manifest_records_both_historical_and_current_entry_counts` — assert `entry_count_current == 1945`
  (or whatever the live count is at test time — read it directly from a fresh glob/count rather than
  hardcoding, so the test doesn't silently rot if the corpus grows again) and
  `entry_count_historical_reference == 1936` are both present and distinct fields.
- `test_manifest_records_legacy_eight_shard_faction_gap` — assert
  `excluded_from_legacy_scan == ["faction.yaml"]` is present.
Also add the two anti-drift guards from test_plan.md's "Anti-Drift Test Guards" section:
- `test_baseline_script_never_writes_to_docs_parity_ledger` — static inspection (source-text scan or
  monkeypatched `open`/`write_text`) proving the Step 1 script never opens a `docs/parity_ledger/` path in
  write mode.
- `test_baseline_manifest_does_not_coerce_missing_test_path` — assert the manifest's
  `missing_evidence_health` count for `test_path` equals 1,347 (or the live equivalent, computed
  independently in the test) and that no entry's `test_path` is fabricated/backfilled by the script.
**Do NOT touch:** `tests/tools/test_parity_ledger_scan.py`, `tests/tools/test_parity_updater_static.py` —
existing 13 tests must remain unmodified and green.
**Verify:** `pytest tests/tools/test_parity_index_baseline.py -v` (new tests, all passing);
`pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -v` (13/13,
unchanged, regression guard).

### Step 3 — Legacy-tool fixture captures
**Files:** `tests/tools/fixtures/parity_index_baseline/` (new directory: synthetic ledger YAML fixtures for
faction-only, unmapped-path, multi-shard, and malformed-YAML cases), `tests/tools/test_parity_index_baseline.py`
(append fixture-comparison tests)
**Change:** Following the existing `_write_ledger`/`tmp_path` fixture pattern already used in
`tests/tools/test_parity_updater_static.py`, create versioned fixture inputs (small synthetic YAML shard
files, not copies of the live ledger) for each of the four legacy-tool behaviors already covered by
existing tests, and capture their exact expected outputs as fixture data (JSON or inline expected literals):
- **Faction case:** a changed-path whose only `v2_evidence` citation lives in a `faction.yaml`-shaped
  fixture shard. Call `find_p0_intersection` (from `tools.parity_ledger_scan`, imported not reimplemented)
  against a ledger dir containing only this fixture; assert result is `[]`, matching
  `test_only_scans_canonical_eight_not_faction`'s existing live-tool behavior.
- **Unmapped case:** a changed-path with no `v2_evidence` citation anywhere in the fixture ledger; assert
  `expected_subsystems_for_files` (from `tools.gate_checks.parity_updater_static`) returns `NA`/`None` for
  it, matching existing behavior.
- **Multi-shard case:** a fixture path cited in 2+ fixture shard files' `v2_evidence`; assert
  `derive_mapping`/`expected_subsystems_for_files` returns the full multi-file candidate set.
- **Malformed-YAML case:** one fixture shard file containing invalid YAML; assert `derive_mapping` skips it
  silently (no exception raised), matching `test_derive_mapping_skips_malformed_yaml_file`'s existing
  behavior.
Add corresponding tests: `test_faction_fixture_matches_live_legacy_scan_output`,
`test_unmapped_path_fixture_matches_live_legacy_scan_output`,
`test_multi_shard_fixture_matches_live_legacy_scan_output`,
`test_malformed_yaml_fixture_matches_live_legacy_scan_output`. Also add
`test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` — a single test
asserting both halves of the ticket's central tension simultaneously: the Step 1 manifest's shard
enumeration includes `faction.yaml` (9 shards) while these fixture captures still reproduce the legacy
8-file exclusion faithfully.
**Do NOT touch:** the fixtures must be synthetic, not copies/subsets of the live `docs/parity_ledger/*.yaml`
content verbatim (avoids the fixture silently going stale if live entries change) — call the legacy
functions (`find_p0_intersection`, `derive_mapping`, `expected_subsystems_for_files`) against fixture data,
never against the live ledger, in these specific tests (live-ledger-facing assertions belong to Step 2).
Do not modify `tools/parity_ledger_scan.py` or `tools/gate_checks/parity_updater_static.py` to make them
"easier to test" — call them exactly as they exist today.
**Verify:** `pytest tests/tools/test_parity_index_baseline.py -v` (fixture-comparison tests, all passing).

### Step 4 — V1 decision record document
**Files:** `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md` (new)
**Change:** A decision document, placed alongside the idea doc it resolves (so `IMPORTER`/epic tickets find
it via the same directory the idea doc already lives in), with one section per Scope boundary named in the
ticket. Required section headings (checked mechanically in Step 5):
- **Ownership** — `parity-index/parity.db` (Phase 1+) is local, gitignored, derived-only from YAML; no
  agent or tool edits it directly. This ticket does not create the db or the `.gitignore` entry — that is
  explicitly Phase 1/IMPORTER's job.
- **Discovery / IDs** — shard discovery must be dynamic (glob `docs/parity_ledger/*.yaml`), never a
  hardcoded file list (contrast with the legacy 8-file `CANONICAL_LEDGER_FILES`, which stays frozen as a
  compatibility fixture, not a pattern to inherit). **Decision (resolves Investigation open question 5,
  "is cross-shard ID uniqueness a law or an observed fact"):** declare cross-shard `id` uniqueness a v1
  **enforced invariant** going forward — Phase 1/IMPORTER's importer must reject (not silently tolerate) a
  duplicate ID across shards at import time. Rationale: today's data already satisfies it (0 duplicates,
  verified), the schema's per-entry ID pattern implies uniqueness was always the intent, and leaving it as
  a mere "observed fact" would let Phase 1 defer a check that is cheap to add now and expensive to retrofit
  after the index has consumers.
- **Normalized schema** — adopt the idea doc's table shape as-is (`ledger_generation`, `entries`,
  `code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`, `entry_fts`, `entry_health` view,
  `impact_candidates` view/query). This ticket does not redesign the shape, only confirms it as the Phase
  1/2 target so IMPORTER does not re-litigate it.
- **FTS fallback** — Phase 1/IMPORTER must probe SQLite's FTS5 compile flag at build time and fall back to
  an exact-ID/path match (no full-text) if unavailable. This ticket records the requirement; it does not
  probe or implement it (no FTS5 code is added by this ticket).
- **Atomic lifecycle** — Phase 1/IMPORTER must build into a sibling temporary DB, validate
  integrity/schema/row counts, close/fsync, then atomically replace the previous DB; a failed build must
  leave the last-good DB and YAML untouched. Explicitly do **not** inherit
  `tools/agent-monitoring/build_index.py`'s delete-then-rebuild pattern (cited as a precedent to avoid, not
  follow, per this ticket's own Implementation Notes).
- **Path-only links** — v1 resolves structured references (`code_refs`, etc.) to path-level only; no
  Graphify symbol resolution in v1.
- **Output convention** — the Step 1 baseline manifest's JSON shape (sorted keys, fixed serialization) is
  the reference convention Phase 1's own build-report/manifest output should follow for determinism.
- **CLI/module ownership** — **Decision (resolves Investigation open question 2):** flat files under
  `tools/`, not a new `tools/parity_ledger/` package. Phase 1 builds `tools/parity_index.py`; the deferred
  Phase 3 mutation tool (if approved) would be `tools/parity_record.py`. Rationale: (a) the existing
  sibling tool `tools/parity_ledger_scan.py` is already a flat top-level module with no package wrapper —
  matching it avoids introducing a second convention for the same tool family; (b) `tools/gate_checks/`'s
  own precedent (`parity_updater_static.py`) is a flat module even though it lives inside an
  already-established subdirectory — it did not spin up a package for one file; (c) only two files
  (`parity_index.py`, deferred `parity_record.py`) are currently planned, which does not justify a new
  package's `__init__.py`/namespace overhead; (d) this decision is reversible later — nothing in Phase 0
  creates the files themselves, only records the intended location, so a future ticket could still
  restructure into a package if the tool family grows materially (e.g. FTS query commands, health-report
  subcommands) without this ticket having locked in anything irreversible.
- **`parity-record` deferral** — explicitly stated as deferred pending a separate Phase-3 go/no-go
  decision; this document must not describe a working implementation or authorize building it now (checked
  by the Step 6 anti-scope-creep guard).
- **Known gaps recorded, not fixed** — (1) `docs/parity_ledger/schema.json`'s duplicate-top-level-`"if"`
  parsing defect (candidate for a future dedicated ticket, e.g. rewriting as `allOf`); (2) the
  `idea_parity_ledger_sqlite_context_integration_review_claude.md` companion doc referenced by the ticket
  prompt does not exist anywhere in the repo or git history — recorded as a gap, not treated as a blocker.
**Do NOT touch:** the idea doc itself
(`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`)
— this is a new companion file, not an edit to the existing one.
**Verify:** `test_v1_decision_artifact_covers_all_scope_boundaries` (Step 5).

### Step 5 — Decision-doc completeness check
**Files:** `tests/tools/test_parity_index_baseline.py` (append)
**Change:** **Decision (resolves Investigation open question 4):** scripted check, not a manual checklist —
consistent with the project's preference for objective, deterministic verification wherever a check can be
made mechanical (the `done_checker_static.py` precedent test_plan.md cites). Add
`test_v1_decision_artifact_covers_all_scope_boundaries`: read
`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md` and assert each
required section heading from Step 4 is present (Ownership, Discovery / IDs, Normalized schema, FTS
fallback, Atomic lifecycle, Path-only links, Output convention, CLI/module ownership, `parity-record`
deferral, Known gaps). A simple presence/heading-string check, not semantic evaluation of the prose.
**Do NOT touch:** do not build a new `tools/gate_checks/` module for this — it is a one-time Phase-0
document-completeness check, not an ongoing CI gate; keep it as a plain pytest test alongside the other new
tests in `tests/tools/test_parity_index_baseline.py`.
**Verify:** the test itself (`pytest tests/tools/test_parity_index_baseline.py::test_v1_decision_artifact_covers_all_scope_boundaries -v`).

### Step 6 — Anti-scope-creep guards
**Files:** `tests/tools/test_parity_index_baseline.py` (append)
**Change:** Add the two remaining test_plan.md guard tests:
- `test_no_database_or_gitignore_or_make_target_created` — assert no `.db`/`.sqlite` file exists anywhere
  this ticket's script can write to (`staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/`), that
  `.gitignore` has no new `parity-index/`-style entry, and that `Makefile` has no new parity-index target,
  by diffing against a known-good git baseline or asserting absence directly.
- `test_v1_decision_artifact_does_not_authorize_mutation_cli` — text-presence/absence check on
  `v1_decisions_phase0.md` confirming it states `parity-record` "stays deferred" and does not include
  implementation-level detail (e.g. no CLI argument spec, no code block implementing a mutation command)
  that would read as authorization to build it now.
**Do NOT touch:** `.gitignore`, `Makefile` — this step only tests that they remain untouched; it must not
modify either file itself.
**Verify:** both tests passing; full new-suite run
`pytest tests/tools/test_parity_index_baseline.py -v`.

## Scope Guards

Reiterating the ticket's Out of Scope section, made concrete per file:

- **`docs/parity_ledger/*.yaml`** (all 9 shards) — read-only inputs. No script in this ticket writes to any
  path under `docs/parity_ledger/`. Enforced by `test_baseline_script_never_writes_to_docs_parity_ledger`.
- **`docs/parity_ledger/schema.json`** — do not modify. The duplicate-`"if"` bug is documented in the
  manifest's `schema_coverage` field and flagged in the v1 decision doc as a future-ticket candidate; it is
  never edited, reformatted, or "fixed" by this ticket.
- **`tools/parity_ledger_scan.py`** — do not modify. `CANONICAL_LEDGER_FILES` is imported by identity only,
  never redefined, copied, or extended to 9 files.
- **`tools/gate_checks/parity_updater_static.py`** — do not modify. Called as-is in fixture-comparison
  tests (Step 3).
- **`tests/tools/test_parity_ledger_scan.py`** and **`tests/tools/test_parity_updater_static.py`** — do not
  modify. Must remain green and unmodified (13/13) throughout.
- **`.gitignore`** — do not modify. No `parity-index/` or `.db` ignore entry is added (that is Phase
  1/IMPORTER's job).
- **`Makefile`** — do not modify. No new parity-index target.
- **No `.db`/`.sqlite` file is created anywhere** by this ticket's script or tests.
- **No mutation CLI (`parity-record`) is implemented** — only its deferral is recorded in prose.
- **`.claude/workflows/implement-ticket.js`, `.claude/agents/parity-updater.md`**, or any workflow/context-
  assembly file — not touched. No workflow/config/context integration.
- **`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`**
  — read-only reference; not edited. The 1,936 figure inside it is left as-is; the drift is recorded in the
  new manifest/decision doc, not by rewriting the idea doc's prose.
- **No entry in any `docs/parity_ledger/*.yaml` file has its `status`, `test_path`, or `v2_evidence`
  coerced, backfilled, or repaired.** The 1,347-entries-missing-`test_path` gap is counted, never fixed.

## Dependency Map

- Step 1 → Step 2 (tests import/exercise the Step 1 script; must exist first).
- Step 1 → Step 6's `test_no_database_or_gitignore_or_make_target_created` (needs the script's known output
  location to assert against).
- Step 3 is independent of Steps 1–2 (exercises legacy tools directly against synthetic fixtures) but
  shares the same test file, so sequence after Step 2 to avoid merge friction, not for a logical dependency.
- Step 4 is independent of Steps 1–3 (a prose decision document); can be authored in parallel with them.
- Step 4 → Step 5 (completeness check needs the document to exist).
- Step 4 → Step 6's `test_v1_decision_artifact_does_not_authorize_mutation_cli` (needs the document to
  exist).
- Steps 2, 3, 5, 6 all append to the same file (`tests/tools/test_parity_index_baseline.py`); implement in
  the listed order to keep each addition independently verifiable via `pytest -k <test_name>` before moving
  on.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — Unchanged source inputs yield byte-identical baseline output; all nine shards represented; source hashes unchanged | Step 1, Step 2 | `test_baseline_manifest_is_byte_identical_on_rerun`, `test_baseline_manifest_covers_all_nine_shards`, `test_baseline_manifest_source_hashes_match_live_files` |
| AC #2 — Manifest records the historical 1,936-entry snapshot and the legacy eight-shard/faction comparison gap | Step 1, Step 2 | `test_manifest_records_both_historical_and_current_entry_counts`, `test_manifest_records_legacy_eight_shard_faction_gap` |
| AC #3 — Fixture inputs and expected legacy outputs versioned for faction, unmapped, and multi-shard cases | Step 3 | `test_faction_fixture_matches_live_legacy_scan_output`, `test_unmapped_path_fixture_matches_live_legacy_scan_output`, `test_multi_shard_fixture_matches_live_legacy_scan_output`, `test_malformed_yaml_fixture_matches_live_legacy_scan_output` |
| AC #4 — A v1 decision artifact resolves each Scope boundary including CLI ownership and FTS-independent fallback | Step 4, Step 5 | `test_v1_decision_artifact_covers_all_scope_boundaries` |
| AC #5 — No DB, workflow/config/context integration, source rewrite, or mutation command is introduced | Step 6 (guarded throughout Steps 1, 4) | `test_no_database_or_gitignore_or_make_target_created`, `test_v1_decision_artifact_does_not_authorize_mutation_cli`, `test_baseline_script_never_writes_to_docs_parity_ledger` |

## Anti-Drift Notes

- **1,936 vs. 1,945:** never make the manifest's live count equal 1,936. The manifest must show both
  numbers with the drift explicit and dated (idea doc, 2026-07-31). Silently reconciling to either number
  misrepresents either the live corpus or the ticket's own AC #2 wording.
- **`schema.json`'s duplicate-`"if"` bug** is a real correctness defect but is explicitly out of this
  ticket's editing scope — document what it *actually enforces after parsing* (only the
  `divergent`→`divergence_note` rule), not what the source text visually appears to specify.
- **Do not extend `CANONICAL_LEDGER_FILES` to 9 files** or otherwise touch the legacy tools to "fix" the
  faction exclusion. The gap is the artifact this ticket exists to expose (via fixture capture), not
  correct.
- **`test_reuses_canonical_ledger_files_constant`** (existing) asserts `is`-identity between
  `parity_ledger_scan.CANONICAL_LEDGER_FILES` and `parity_updater_static.CANONICAL_LEDGER_FILES`. Any new
  code in this ticket that needs the 8-file list for comparison must `import` it from one of these modules,
  never redefine or duplicate the literal tuple.
- **Duplicate-ID invariant:** this ticket's manifest reports 0 duplicate IDs as an *observed fact* today;
  the v1 decision doc separately *declares* cross-shard uniqueness as an enforced invariant for Phase
  1/IMPORTER to implement. Do not conflate the two — Phase 0 does not add an enforcement mechanism itself,
  only states that one is required going forward.
- **Missing companion doc** (`idea_parity_ledger_sqlite_context_integration_review_claude.md`) does not
  exist in the repo or git history. Record this as a gap in the v1 decision doc; do not fabricate its
  content or treat its absence as a blocker.
- **After Work workflow applies normally:** since `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`
  is a new file under `docs/`, `make knowledge-index-update` must run at ticket close. Staging artifacts
  (`baseline_manifest.json`, fixture data if staged there) migrate to
  `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/` per standard convention.
