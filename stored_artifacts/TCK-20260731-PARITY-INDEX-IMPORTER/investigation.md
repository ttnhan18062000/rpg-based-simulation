---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-IMPORTER
artifact_type: investigation
tags: [ai, observability, process-improvement, testing]
---

# Investigation — TCK-20260731-PARITY-INDEX-IMPORTER

## Current Behavior

### `docs/parity_ledger/` — 9 live shard files, 1,945 entries today

Confirmed by reading `stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json` directly
(not recomputed independently, since this ticket depends on that Phase-0 evidence, not a re-derivation of
it): `shard_count: 9`, `entry_count_current: 1945`, `duplicate_ids.count: 0`,
`excluded_from_legacy_scan: ["faction.yaml"]`, `missing_evidence_health.missing_test_path_count: 1347`,
`missing_v2_evidence_count: 0`. Shard list: `combat_movement.yaml`, `faction.yaml`, `infrastructure.yaml`,
`progression.yaml`, `social_narrative.yaml`, `strategic_cognition.yaml`, `substrate.yaml`,
`town_resource.yaml`, `world_dynamics.yaml`. Per-shard SHA-256 hashes are in the manifest's `shards[].sha256`
field — this ticket's importer must re-hash the live files at build time and compare, not trust the
Phase-0 manifest's hashes as still current (source could have changed since Phase-0 closed).

### `tools/parity_index_baseline.py` (read in full, 189 lines) — reusable evidence-capture logic

Functions directly reusable by this ticket's importer, per the ticket's own hint ("likely reuses its
shard-enumeration/hashing logic rather than reimplementing it"):
- `_sha256_hex(path)` (line 38-39) — `hashlib.sha256(path.read_bytes()).hexdigest()`. Trivial, but the exact
  hashing convention (`read_bytes()`, not `read_text()`) must match for `ledger_generation`'s
  `source_manifest_hash` to be meaningfully comparable to Phase 0's baseline.
- `_scan_shard(path)` (line 42-59) — `yaml.safe_load`, per-entry `status`/`priority` tallies, `ids` list.
  This is the raw per-shard parse the importer's `entries` table population should build on, though the
  importer needs additional per-entry fields (`text`, `v2_evidence`, `test_path`, etc.) that
  `_scan_shard` does not extract into its own return dict (it keeps the full `entries` list under
  `shard["entries"]`, so those fields are still reachable, just not projected as this function's own
  return keys).
- `build_manifest(ledger_dir)` (line 110-170) — dynamic glob `sorted(ledger_path.glob("*.yaml"))` (line 112),
  duplicate-ID detection across all shards (line 115-117, using the `eid in seen or seen.add(eid)` idiom),
  `excluded_from_legacy_scan` diff against `CANONICAL_LEDGER_FILES` (imported by identity, line 26, never
  redefined). The importer's own duplicate-ID check should reuse this exact detection logic (or import it)
  rather than reimplementing — Phase 0's v1 decision doc requires the importer to *reject*, not just
  observe, a duplicate; the observation logic itself is proven here.
- `serialize_manifest(manifest)` (line 173-174) — `json.dumps(manifest, sort_keys=True, indent=2,
  ensure_ascii=True) + "\n"`. The v1 decision doc's "Output convention" section requires the importer's own
  build-report to follow this exact serialization, so this ticket's build-report writer should call this
  function (or an identically-parameterized one) rather than inventing a new `json.dumps` call.
- **Not reusable as-is:** `_schema_coverage_as_parsed()` and `_missing_evidence_health()` are Phase-0-specific
  evidence fields (they describe the corpus as a point-in-time snapshot for the baseline manifest); the
  importer's `entry_health` view computes overlapping but differently-shaped health facts (per-entry rows,
  not corpus-wide counts) and should not literally call these two functions, though the underlying logic
  (parse `schema.json`'s surviving `if`/`then` pair; flag `verified`/`divergent` entries missing
  `test_path`/`v2_evidence`) is the right reference behavior to reproduce at the entry-row granularity.

### `tools/agent-monitoring/build_index.py` (read in full, 211 lines) — anti-pattern confirmed by direct read

Line 179-183, inside `build()`:
```python
db_path.parent.mkdir(parents=True, exist_ok=True)
if db_path.exists():
    db_path.unlink()

conn = sqlite3.connect(str(db_path))
_create_schema(conn)
```
This is the literal delete-then-build lifecycle the ticket's Implementation Notes and the v1 decision doc's
"Atomic lifecycle" section both flag as NOT to be copied. There is no temporary-file build, no
integrity/schema/row-count validation step, and no atomic replace — a crash between `unlink()` and
`conn.commit()` leaves zero usable database (previously the old one, now nothing). Confirmed directly, not
assumed. This ticket's importer must instead: build into a sibling temp file (e.g.
`parity-index/.parity.db.tmp` or `tempfile.NamedTemporaryFile` in the same directory as the target, so
`os.replace` is same-filesystem-atomic), validate row/schema counts against the source manifest, then
`os.replace(tmp_path, final_path)`.

Also confirmed by direct read: `build_index.py` has **no FTS5 usage at all** (grep for "fts" in the file:
zero matches) — it is not a precedent for the FTS5 probe/fallback this ticket must implement; that is
new work with no in-repo precedent to reuse.

### `tools/parity_ledger_scan.py` and `tools/gate_checks/parity_updater_static.py` (read in full) — protected, read-only reference

`CANONICAL_LEDGER_FILES` (parity_ledger_scan.py line 24-33) is an 8-file tuple excluding `faction.yaml`.
`parity_updater_static.py` imports this tuple by identity (line 34; `test_reuses_canonical_ledger_files_constant`
enforces `is`, not `==`). Both modules are explicitly Out of Scope for this ticket ("Do NOT modify the legacy
scanner/static gate or treating their eight-shard list as importer input" — ticket Out of Scope). This
ticket's importer must use its **own** dynamic 9-shard glob (following `parity_index_baseline.py`'s
precedent), never import or extend `CANONICAL_LEDGER_FILES` as its shard-discovery source. The two modules
are read-only reference for this investigation only; no code from this ticket touches them.

### `tests/tools/test_build_index.py` (read in full, 390 lines) — precedent test structure

Seven test-class groups: happy-path+schema, read-only guarantee (source-byte-identity), normalization
parity, legacy-shape regression guards, rerun row-count stability, Makefile+`.gitignore` wiring, and
architecture guards (anti-drift via source-text scanning, e.g. `test_no_incremental_build_flag_exists`,
`test_build_index_never_touches_write_path_modules`). Directly reusable pattern shapes for this ticket's
`tests/tools/test_parity_index.py`:
- `_load_module()` via `importlib.util.spec_from_file_location` (line 31-35) — load-by-path pattern this
  ticket's test file should mirror for `tools/parity_index.py`.
- `_make_corpus(tmp_path, ...)` (line 97-112) — isolated `tmp_path` fixture-corpus builder; this ticket's
  equivalent should build a `tmp_path`-scoped fake `docs/parity_ledger/`-shaped directory with small
  synthetic YAML shards, never touch the live ledger directory in these tests (per the ticket's Scope:
  "isolated `tmp_path` tests").
  Architecture-guard idiom (`test_build_index_never_touches_write_path_modules`, line 378-382: static
  source-text `assert name not in source` scanning) is the direct precedent for this ticket's own guard that
  `tools/parity_index.py`'s source never contains a raw `docs/parity_ledger/` write-mode `open()` call.
- **Important gap found during this investigation, unrelated to this ticket's own scope:** running
  `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py
  tests/tools/test_parity_index_baseline.py tests/tools/test_build_index.py -q` today yields
  **1 pre-existing failure**: `TestMakeTarget.test_makefile_dry_run_agent_monitoring_index` fails because
  `make --dry-run agent-monitoring-index` prints `"make: 'agent-monitoring-index' is up to date."` instead
  of a command line containing `build_index.py` — a phony-target/timestamp quirk in the existing Makefile
  target, not something this ticket's Scope touches or is asked to fix. All other 44 tests in that combined
  run pass. This must be recorded as a known pre-existing regression-surface gap, not attributed to this
  ticket's work.

### `tests/tools/test_parity_updater_static.py` and `tests/tools/test_parity_ledger_scan.py` — confirmed 13/13 green

Re-ran in isolation: `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py
-q` → 13 passed, matching the Phase-0 investigation's own finding. Neither suite is touched by this ticket.

### FTS5 availability — verified directly, not assumed

```
python3 -c "import sqlite3; c=sqlite3.connect(':memory:'); c.execute('CREATE VIRTUAL TABLE t USING fts5(x)'); print('FTS5 OK')"
```
Output: **`FTS5 OK`**. FTS5 is compiled into this environment's Python `sqlite3` module. This means the
"FTS5-present" branch of AC #3 ("FTS5-present and forced-unavailable tests both pass") can be exercised
directly against the real environment, but the "forced-unavailable" branch **cannot** be exercised by
simply relying on environment absence — the importer's implementation and its test suite must include an
explicit code path to force-disable FTS5 (e.g. an injectable flag/monkeypatched probe function, not a
literal `PRAGMA compile_options` check with no override), since this environment will never naturally lack
FTS5. This is a concrete implementation requirement for Plan to size, not an open question — the "forced
unavailable" test must monkeypatch or parameterize the FTS5-availability probe, not rely on running in a
FTS5-less environment.

### Target data model — table/view list cross-check

`idea_parity_ledger_sqlite_context_integration.md`'s "Target data model" section (line 148-158) names 9
table/views: `ledger_generation`, `entries`, `code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`,
`entry_fts`, `entry_health` (view), `impact_candidates` (view/query). Cross-referencing against this
ticket's own Scope text: Scope says "populate normalized generation, entries, code/test/constraint/ticket
reference, and ordered health data" — this maps to `ledger_generation`, `entries`, `code_refs`, `test_refs`,
`constraint_refs`, `ticket_refs`, and `entry_health` (7 of 9). The Scope text does **not** explicitly name
`entry_fts` (though "FTS5 is optional discovery only" language implies it) or `impact_candidates`. Per the
idea doc's own Delivery Sequence, `impact_candidates` (the `impact` query) is explicitly **Phase 2** scope
("Phase 2 — Deterministic impact API and legacy-equivalence proof... Implement exact `impact`, `entry`, and
`health` APIs/CLI output"), not Phase 1/IMPORTER — so its absence from this ticket's Scope text is
consistent with the idea doc's own phase split, not silent scope-narrowing. `entry_fts` **is** Phase 1 scope
per the idea doc ("first schema must use ordinary SQLite and FTS5 only... verify FTS5 availability and
retain an exact-ID/path fallback") and per this ticket's own Scope line ("FTS5 is optional discovery only:
probe it and provide exact ID/path lookup when unavailable") — the table itself is implied but not named
by field-name in Scope. This is a real (if narrow) drift risk: see Risks/Open Questions below.

## Mechanics / Engine Constraints

None. Consistent with the Phase-0 investigation's own finding: this is agent-infrastructure/tooling work
(`tools/`, a local derived index) — no `docs/mechanics/` chapter or `docs/engine/` contract governs
parity-ledger tooling. The only binding "law" in scope is `docs/parity_ledger/schema.json` as it actually
parses (see the confirmed duplicate-`"if"`-key gap below) and this ticket's own explicit constraint to
follow every decision recorded in `v1_decisions_phase0.md` without reopening it.

`docs/parity_ledger/schema.json` was re-read directly in this investigation and the duplicate-`"if"`-key
defect Phase 0 documented is confirmed unchanged: two top-level `"if"`/`"then"` pairs exist inside the same
`items` object (lines ~34-45 of the raw JSON) — the first (`verified`/`divergent` → `v2_evidence`+`test_path`)
is silently discarded by `json.loads`, only the second (`divergent` → `divergence_note`) survives parsing.
The importer's `entry_health` classification logic must therefore compute "missing evidence/test" health
findings against the schema's *documented intent* (both fields required for `verified`/`divergent`), not
against what `json.loads(schema.json)` would mechanically enforce if used as a JSON-Schema validator — this
ticket does not fix `schema.json`, but its health classification is expected to encode the *intended* rule
(matching `parity_index_baseline.py`'s own `_missing_evidence_health()` scope comment: "verified and
divergent entries only (schema's intended v2_evidence+test_path rule)").

## Parity Ledger Overlap

This ticket implements/changes no `src/` simulation behavior — it is meta/tooling work about the ledger,
not a behavior the ledger tracks. Consistent with the Phase-0 investigation's finding, no parity-ledger
entry's `status`/`v2_evidence` needs to change as a result of this ticket, and no new entry is required.

Informational-only entries describing the closest prior-art precedent (confirmed present, unmodified,
re-read directly in this investigation):
- `INFRA-289` (`docs/parity_ledger/infrastructure.yaml` line 5710) — documents
  `tools/agent-monitoring/query.py`'s migration to the derived SQLite index (`TCK-20260713-MONITORING-QUERY-
  INDEX-MIGRATE`).
- `INFRA-290` (line 5779) — documents `validate.py`'s equivalent migration
  (`TCK-20260713-MONITORING-VALIDATE-INDEX-MIGRATE`).
- `INFRA-291` (line 5859) — documents `generate_retro.py`'s equivalent migration.

None require edits. No `INFRA-*` entry documents `tools/parity_ledger_scan.py`,
`tools/gate_checks/parity_updater_static.py`, or `tools/parity_index_baseline.py` themselves — consistent
with those tickets' own precedent of shipping workflow-determinism/evidence-capture tooling without a
parity-ledger entry. No P0 entries are at risk from this ticket (no `src/` change, no `v2_evidence` touched).

## Prior Work

- **`stored_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/`** (read in full — `investigation.md`, `plan.md`,
  `test_plan.md`, `baseline_manifest.json`) — the direct Phase-0 predecessor. Its `investigation.md`
  documents the 1,945-entry live corpus, the 1,936-vs-1,945 historical drift (never to be silently
  reconciled), the `schema.json` duplicate-`"if"`-key parsing gap, and the CLI/module ownership decision
  rationale. Its `plan.md` records the exact decisions this ticket inherits as settled (see
  `v1_decisions_phase0.md` below, which is the canonical output of that plan's Step 4). This ticket must
  build directly on `baseline_manifest.json`'s captured hashes/counts as comparison evidence, not
  re-derive the Phase-0 evidence from scratch.
- **`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`** (read in full)
  — binding architecture decisions this ticket must follow without reopening: dynamic glob discovery,
  cross-shard ID uniqueness as an **enforced invariant** (reject, don't tolerate, a duplicate at import
  time), the 9-table/view normalized schema shape confirmed as-is, FTS5 probe-and-fallback requirement,
  atomic sibling-temp-file-then-replace lifecycle (explicitly rejecting `build_index.py`'s delete-then-build
  pattern), path-level-only structured references (no Graphify symbol resolution), the
  `parity_index_baseline.py` JSON serialization convention as the build-report reference format, and flat
  `tools/parity_index.py` (not a `tools/parity_ledger/` package) as the CLI/module location.
- **`stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/`** (`plan.md`'s Deviations section, read in
  full) — lifecycle precedent, not a lifecycle template (per this ticket's own Related Tickets annotation).
  The load-bearing lesson: a **literal Step 5 spec** (`record.get(...) is not None` value-non-nullness
  check) diverged from its own **stated intent** ("filter on presence/type of `run_id`/`seq`/`tool`, not on
  matching specific known record contents") because `dict.get()` cannot distinguish "key absent" from "key
  present with explicit JSON `null`." This was only caught by verification against the live 67,726-line
  corpus, and would have silently dropped ~30,372 legitimate records if shipped as literally specified.
  Direct relevance to this ticket: any "missing reference" or "unparseable reference" health classification
  in the importer's `entry_health` logic must be built and checked against a realistic corpus sample (or the
  live ledger itself, read-only) before trusting a literal field-presence check, not assumed correct from
  the spec text alone.
- **`tests/tools/test_build_index.py`** (read in full) — precedent test-file structure (grouped test
  classes, `tmp_path`-isolated fixture corpus, source-text architecture guards). Directly informs this
  ticket's `tests/tools/test_parity_index.py` shape (see Current Behavior above).
- **`docs/REGISTRY.yaml`** query (`related_code_areas` overlap with `tools/parity_ledger_scan.py`,
  `tools/gate_checks/parity_updater_static.py`, `docs/parity_ledger/`, `tools/agent-monitoring/build_index.py`,
  or tags intersecting `sqlite`/`index`/`parity`) surfaced 37 candidate tickets beyond the ones the ticket
  prompt already names explicitly. All 37 were reviewed by title/related_code_areas; none are architectural
  precedent for a SQLite-import/atomic-lifecycle tool — they are either simulation-domain parity-ledger
  *entries* (faction/progression/social calibration tickets citing a `docs/parity_ledger/*.yaml` file as
  their own behavior-change evidence target) or unrelated gate-check/doc tickets that cite
  `parity_updater_static.py` only incidentally as one of several files a conformance/staleness scan reads.
  None require this investigation's findings to change.

## Risks and Open Questions

1. **`entry_fts` table naming is implied, not explicit, in this ticket's own Scope text.** The Scope line
   "FTS5 is optional discovery only: probe it and provide exact ID/path lookup when unavailable" clearly
   requires FTS5 wiring, but does not spell out the `entry_fts` table name the idea doc's Target Data Model
   assigns it. This is a low-risk gap (the idea doc and v1 decision doc both confirm the 9-table/view shape
   "as-is" and Plan is instructed to build against that shape) — flagging so Plan explicitly names
   `entry_fts` in its own scope rather than only implying an FTS5 mechanism without the table it should live
   in.
2. **`impact_candidates` is correctly out of this ticket's Scope** (confirmed Phase-2 per the idea doc's
   Delivery Sequence), but this ticket's Scope text says "populate normalized... and ordered health data
   needed by **later exact path-level queries**" — this phrasing gestures at `impact_candidates` without
   naming it. No contradiction found: Phase 1's job is to leave the underlying tables in a state Phase 2's
   `impact` query can be built against, not to build the view/query itself. Recording this as confirmed-
   consistent, not as an open question requiring escalation.
3. **Testing the "FTS5 forced-unavailable" branch requires an explicit code seam.** Since this environment's
   `sqlite3` genuinely has FTS5 compiled in (verified above), the importer's FTS5-probe function must be
   structured so a test can force the fallback path (e.g. accept an injectable `fts5_available: bool | None`
   parameter, or expose the probe as a separately-mockable function) — Plan must decide this seam's exact
   shape; Investigation flags it as a concrete design requirement, not a vague risk, since AC #3 is
   unsatisfiable without it in this environment.
4. **No pre-existing `tools/parity_index.py` or `tests/tools/test_parity_index.py` file exists yet**
   (confirmed via direct `ls`) — this is a pure-greenfield build, consistent with the ticket's Scope and
   the v1 decision doc's CLI/module ownership decision. No conflicting partial implementation to reconcile.
5. **Pre-existing unrelated test failure**: `tests/tools/test_build_index.py::TestMakeTarget::
   test_makefile_dry_run_agent_monitoring_index` fails today (see Current Behavior) due to a `make
   --dry-run` phony-target quirk unrelated to this ticket's Scope. Not a blocker — must not be "fixed" by
   this ticket's implementer as a drive-by, since `Makefile`/`build_index.py` are outside this ticket's
   Related Code Areas and Scope.
6. **Cross-shard ID uniqueness enforcement mechanics are not fully specified by the v1 decision doc.** The
   decision doc states the importer "must reject (not silently tolerate) a duplicate id across shards at
   import time" but does not specify whether "reject" means abort the whole build (leaving prior-good DB in
   place, per the atomic-lifecycle rule) or complete the build while recording the duplicate as a build-
   failure classification. Given the atomic-lifecycle decision's own language ("A failed build must leave
   the last-good database and all YAML untouched"), the more consistent reading is: a duplicate ID is a
   build-time validation failure that aborts before the atomic replace, same as any other integrity-check
   failure — not a "classify and continue" case (that "classify, never invent" language is reserved for
   *health* findings like missing test paths, not the cross-shard-uniqueness *invariant*). Flagging as a
   Plan-phase decision to confirm explicitly rather than assume silently, since the ticket's own AC #4
   ("An injected parse/validation/failure leaves a prior good DB byte-identical") reads consistently with
   this interpretation but doesn't literally enumerate "duplicate ID" as one of the injected-failure classes
   tested.

## Anti-Drift Hazards

- **Do not import shard discovery from `CANONICAL_LEDGER_FILES`.** The importer's own dynamic glob
  (`docs/parity_ledger/*.yaml`) must be independent of the legacy 8-file list, per the v1 decision doc's
  "Discovery / IDs" section — mirror `parity_index_baseline.py`'s pattern, not `parity_ledger_scan.py`'s.
- **Do not copy `build_index.py`'s `if db_path.exists(): db_path.unlink()` lifecycle.** Confirmed present
  in that file (line 180-181) and explicitly flagged by both this ticket's Implementation Notes and the v1
  decision doc as the anti-pattern to avoid — build to a sibling temp file, validate, then atomically
  replace.
- **Do not modify `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
  `docs/parity_ledger/*.yaml`, or `docs/parity_ledger/schema.json`.** All explicitly Out of Scope; the
  schema's duplicate-`"if"` defect is a known, documented gap to work around in health-classification logic,
  never a file to "fix" as part of this ticket.
- **Do not build the mutation CLI (`parity-record`), context/retrieval/workflow integration, or any
  Graphify-dependent symbol resolution.** All explicitly Out of Scope and explicitly deferred by both the
  idea doc's Phase gating and the v1 decision doc's "`parity-record` deferral" and "Path-only links"
  sections.
- **Do not silently narrow the 9-table/view target schema without documenting why.** Per the ticket
  prompt's own instruction: if Plan's schema covers fewer than the 9 named tables/views (`ledger_generation`,
  `entries`, `code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`, `entry_fts`, `entry_health`,
  `impact_candidates`), it must state explicitly which are deferred and why (e.g. `impact_candidates` is
  correctly Phase-2-deferred per the idea doc) rather than quietly shipping a subset.
- **Do not treat FTS5 as always available.** Even though this environment's `sqlite3` has FTS5 compiled in
  (confirmed), the importer code and its tests must exercise the forced-unavailable fallback path via an
  injectable seam, not skip that branch because the local environment happens to support FTS5.
- **Do not treat the `entry_health` classification as an opportunity to "fix" or backfill legacy data.**
  Per the v1 decision doc and the Phase-0 precedent's own "never coerce" pattern, entries missing
  `test_path`/`v2_evidence` or citing unparseable references are classified findings in the health table,
  never silently repaired, dropped, or fabricated.
- **Do not extend `CANONICAL_LEDGER_FILES` to 9 entries or otherwise touch the legacy 8-file compatibility
  fixture.** The all-9-shard behavior is this ticket's own importer's property, not a change to the
  frozen legacy tools; `tests/tools/test_parity_ledger_scan.py` and `tests/tools/test_parity_updater_static.py`
  (13 tests) must remain green and untouched.
