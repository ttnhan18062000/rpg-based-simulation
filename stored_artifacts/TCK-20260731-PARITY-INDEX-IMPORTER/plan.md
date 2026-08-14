---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-IMPORTER
artifact_type: plan
tags: [ai, observability, process-improvement, testing]
---

# Implementation Plan — TCK-20260731-PARITY-INDEX-IMPORTER

## Summary

Build a single new flat module, `tools/parity_index.py`, that dynamically globs all nine
`docs/parity_ledger/*.yaml` shards and imports them into a local, gitignored, derived SQLite
database (`parity-index/parity.db`) via a validated build-to-sibling-temp-file-then-atomic-replace
lifecycle — never the delete-then-rebuild pattern in `tools/agent-monitoring/build_index.py`. The
importer populates seven of the nine tables/views named in the idea doc's target data model
(`ledger_generation`, `entries`, `code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`,
`entry_fts`) plus `entry_health` (implemented as a materialized table, not a live SQL view — see
Step 4 rationale), for a total of eight of nine. `impact_candidates` is explicitly Phase-2 scope
(`TCK-20260731-PARITY-IMPACT-PROOF`) and is not built here — this is a documented deferral per the
idea doc's own Delivery Sequence, not a silent omission. Every step reuses
`tools/parity_index_baseline.py`'s hashing/discovery/duplicate-detection/serialization
conventions rather than reinventing them, and every mutation-shaped concept (`parity-record`,
`impact`/`entry`/`health` CLI, Graphify symbol resolution) stays out of scope. The plan resolves
all three open questions Investigation flagged (FTS5 test seam shape, duplicate-ID/malformed-shard
abort semantics, `entry_fts` naming) as concrete decisions below — none require escalation.

## Decisions (resolving Investigation's flagged open questions)

**Decision 1 — `entry_fts` is named explicitly as in-scope.** Per the idea doc's target data model
and the ticket's own "FTS5 is optional discovery only" Scope line, `entry_fts` is built in Step 5.
`impact_candidates` remains the one deliberately deferred table/view (Phase 2 — see Summary).

**Decision 2 — Duplicate-ID and malformed-YAML-shard failures are whole-build-abort classes, not
per-entry health findings.** AC #2's sentence lists "duplicate IDs, malformed sources,
unparseable references, missing local refs/tests, and legacy-unstructured evidence" together as
"deterministic classified findings" — but this describes a shared *property* (always classified,
never a raw crash, never invented data), not a shared *home*. Two of those five land in a
build-abort report (duplicate IDs, malformed sources) because they are corpus/shard-structural
integrity failures that make a complete, joinable import impossible — consistent with AC #1's "all
nine shards" completeness requirement and AC #4's "no usable partial DB." The other three
(unparseable references, missing local refs/tests, legacy-unstructured evidence) land as
non-fatal rows in the `entry_health` table within an otherwise-successful build, because they are
per-entry evidence-quality gaps, not corpus-integrity failures. This directly extends
`v1_decisions_phase0.md`'s "reject, not tolerate" language for cross-shard ID uniqueness (an
enforced invariant) to the structurally analogous case of an unparseable shard file. Both failure
classes are surfaced via a structured, typed exception/build-report (e.g. `DuplicateEntryIdError`,
`ShardParseError`) caught by the CLI entrypoint and reported as JSON — never an unhandled Python
traceback — and both abort **before** the atomic temp-to-final replace step, leaving any prior good
DB byte-identical.

**Decision 3 — FTS5 test seam.** `tools/parity_index.py` exposes a module-level
`_probe_fts5(conn: sqlite3.Connection) -> bool` function (attempts
`CREATE VIRTUAL TABLE _fts5_probe USING fts5(x)` then drops it; returns `False` on
`sqlite3.OperationalError`) as an independently unit-testable/monkeypatchable primitive, **and**
the top-level `build()` function accepts `force_fts5_unavailable: bool = False`. When `True`,
`build()` skips calling `_probe_fts5` and treats FTS5 as unavailable regardless of the real
environment. This gives AC #3's forced-unavailable branch an explicit, stable public seam (the
parameter) that doesn't depend on fragile monkeypatching of an internal function, while keeping
`_probe_fts5` itself directly unit-testable for the present-and-working case.

## Steps

### Step 1 — Module skeleton, atomic build lifecycle, `.gitignore`
**Files:** `tools/parity_index.py` (new), `.gitignore` (edit)
**Change:**
- Create `tools/parity_index.py` with a module docstring describing scope (read-only importer,
  Phase 1 of the parity-ledger SQLite index; no mutation CLI).
- `argparse`-based CLI with a single `build` subcommand (`python3 tools/parity_index.py build
  [--db-path PATH] [--force-fts5-unavailable]`). Default `--db-path` is `parity-index/parity.db`
  (relative to repo root, matching `v1_decisions_phase0.md`'s "Ownership" section).
- Implement the atomic lifecycle as its own function, e.g. `_atomic_replace_db(build_fn, final_path,
  ...)`: create `final_path.parent`, build into a `NamedTemporaryFile`-style sibling path in the
  *same directory* as `final_path` (e.g. `parity-index/.parity.db.tmp-<pid>` or
  `tempfile.mkstemp(dir=final_path.parent)`), run `build_fn(temp_conn)` against it, close/fsync the
  connection, then `os.replace(temp_path, final_path)` only on success. On any exception from
  `build_fn`, delete the temp file and re-raise/report — the target path is never touched.
- Minimal schema for this step: only `ledger_generation` (`schema_version INTEGER, importer_version
  TEXT, built_at TEXT, source_manifest_hash TEXT, shard_manifest_json TEXT, shard_count INTEGER,
  entry_count INTEGER`), populated with a placeholder row (`shard_count=0` is acceptable at this
  step — shard discovery lands in Step 2) so the lifecycle is behaviorally provable end to end now,
  not just statically.
- Add `parity-index/` to the repository root `.gitignore` (new stanza with a one-line comment
  referencing this ticket), covering the DB file and the temp file glob under it.
**Do NOT touch:** `tools/agent-monitoring/build_index.py`, `tools/parity_ledger_scan.py`,
`tools/gate_checks/parity_updater_static.py`, any file under `docs/parity_ledger/`.
**Verify:** `test_build_uses_sibling_temp_file_then_atomic_replace` (both the static-source guard —
confirm `if db_path.exists(): db_path.unlink()` never appears in the file — and the dynamic
behavior: a successful `build()` call leaves a sibling temp path that no longer exists after
completion, and the final path was written only via replace); `test_db_not_tracked_by_git`.

### Step 2 — Dynamic shard discovery, `entries` table, duplicate-ID and malformed-shard abort
**Files:** `tools/parity_index.py`, `tests/tools/test_parity_index.py` (new)
**Change:**
- Import `_sha256_hex` from `tools/parity_index_baseline.py` (or an identically-behaved local copy
  if importing creates an undesirable cross-module coupling — prefer importing, per Investigation's
  reuse finding) for per-shard hashing.
- Shard discovery: `sorted(Path("docs/parity_ledger").glob("*.yaml"))` — own dynamic glob, never
  `CANONICAL_LEDGER_FILES`.
- For each shard, `yaml.safe_load` the file inside a `try/except yaml.YAMLError` — on failure, raise
  a typed `ShardParseError(filename, underlying_message)` that propagates up through `build()` as a
  build-abort (per Decision 2). This is caught only at the CLI boundary, not swallowed mid-import.
- Create `entries` table: `id TEXT PRIMARY KEY, shard TEXT NOT NULL, subsystem TEXT NOT NULL,
  entry_order INTEGER NOT NULL, text TEXT, status TEXT, priority TEXT, legacy_evidence TEXT,
  v2_evidence TEXT, proof_type TEXT, test_path TEXT, divergence_note TEXT, support_boundary TEXT,
  canonical_fragment_hash TEXT NOT NULL`. `subsystem` = shard filename minus `.yaml`. `entry_order`
  = the entry's 0-based position within its own shard file (needed for stable ordering independent
  of SQLite's unordered storage). `canonical_fragment_hash` = `sha256(json.dumps(entry,
  sort_keys=True, ensure_ascii=True).encode()).hexdigest()` — the per-entry fragment hash used for
  future stale-detection (Phase 2+), computed now since it is cheap and part of the "entries" row
  shape.
- Populate `ledger_generation.shard_manifest_json` with the sorted list of
  `{filename, sha256, entry_count}` per shard (JSON string via the Step 6 serialization convention)
  and `source_manifest_hash` as the sha256 of that same JSON string — this is what
  `test_importer_preserves_source_byte_hashes` compares against an independently recomputed hash of
  each fixture file.
- Duplicate cross-shard ID detection: reuse `build_manifest`'s `eid in seen or seen.add(eid)` idiom
  (import the idiom's logic, not `build_manifest` itself, since that function returns Phase-0-shaped
  data this ticket doesn't need). On any duplicate, raise a typed `DuplicateEntryIdError(id,
  filenames)` — build-abort per Decision 2.
- Stable ordering: all table population and all query-facing iteration order by `(shard, id)` ascending
  — enforce via `ORDER BY shard, id` in every SELECT that feeds a build-report or health output, not
  by relying on insertion order.
**Do NOT touch:** `CANONICAL_LEDGER_FILES` in `tools/parity_ledger_scan.py` — import nothing from
that module; this importer's shard list must stay fully independent.
**Verify:** `test_importer_imports_all_nine_shards`, `test_importer_preserves_source_byte_hashes`,
`test_duplicate_cross_shard_id_rejected_at_import`,
`test_malformed_yaml_shard_produces_classified_finding_not_crash`.

### Step 3 — Reference tables: `code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`
**Files:** `tools/parity_index.py`
**Change:**
- Four tables, each `(id INTEGER PRIMARY KEY AUTOINCREMENT, entry_id TEXT NOT NULL REFERENCES
  entries(id), path TEXT NOT NULL, relation TEXT, source_field TEXT NOT NULL)`. `source_field`
  records which raw field the reference was parsed from (`v2_evidence`, `legacy_evidence`,
  `test_path`, `text`) for traceability.
- `test_refs` population: when `entries.test_path` is non-null and matches a conservative pattern
  (`^tests/[\w./:-]+\.py(::[\w_]+)?$` — file path, optionally with a pytest node ID suffix), insert
  one `test_refs` row directly from that field (`relation="declared"`). This is the one field the
  schema already treats as structured, so it does not go through the prose-scanning regex below.
- `code_refs`/`constraint_refs`/`ticket_refs` population: scan `v2_evidence`, `legacy_evidence`, and
  `text` for path-like substrings using one conservative regex requiring a known repo-root prefix
  (`\b(src|tools|tests|docs)/[\w./-]+\.\w+\b`) — never a bare heuristic on arbitrary words. Classify
  each high-confidence match by prefix: `src/` or `tools/` → `code_refs`; `docs/mechanics/`,
  `docs/engine/`, `docs/architecture/`, `docs/guidelines/`, `docs/core/` → `constraint_refs`;
  `tests/` → `test_refs` (dedup against the direct `test_path` row if identical). Separately scan
  the same three fields for a ticket-ID pattern (`\bTCK-\d{8}-[A-Z0-9-]+\b`) → `ticket_refs`.
- Anything in `v2_evidence`/`legacy_evidence`/`text` that is not matched by either regex is **not**
  inserted anywhere in these four tables — no row is fabricated for low-confidence text. This
  "no match" state feeds Step 4's `legacy_unstructured` classification; Step 3 itself only ever adds
  rows for confident matches, never a placeholder/guess row.
**Do NOT touch:** No Graphify import, no symbol-level resolution — path-level string matching only,
per `v1_decisions_phase0.md`'s "Path-only links" section.
**Verify:** `test_entries_table_supports_join_to_code_test_constraint_ticket_refs`,
`test_unparseable_code_ref_never_invents_a_link`.

### Step 4 — `entry_health` (materialized table)
**Files:** `tools/parity_index.py`
**Change:**
- Implement `entry_health` as a real `TABLE` (`entry_id TEXT NOT NULL REFERENCES entries(id),
  finding_type TEXT NOT NULL, detail TEXT`), populated by a Python pass after `entries` and the four
  ref tables are built — **not** a live SQL `VIEW**. Rationale (state this in the module docstring
  too): one required finding class (`absent_file` — a referenced `code_refs`/`test_refs`/
  `constraint_refs` path that does not exist on disk relative to repo root) needs a filesystem
  `Path.exists()` check, which cannot be expressed as portable SQL without a custom SQLite function.
  A materialized table populated at build time satisfies the idea doc's "Derived health
  classification" purpose and the "ordered health data" Scope language identically to a view for
  every read this ticket or Phase 2 needs, without requiring a SQLite UDF registration step. This is
  a documented interpretation of "view," not a scope reduction.
- Finding types populated: `missing_test_path` and `missing_v2_evidence` (only for entries whose
  `status` is `verified` or `divergent` — matching `_missing_evidence_health`'s scope comment and
  the schema's *documented intent*, since the schema.json duplicate-`"if"`-key defect means this
  rule is not mechanically enforced by `json.loads`); `legacy_unstructured` (entries whose
  `v2_evidence`/`legacy_evidence` is non-empty but produced zero rows in all four Step-3 ref tables);
  `absent_file` (any `code_refs`/`test_refs`/`constraint_refs` row whose `path`, resolved from repo
  root, does not exist at build time).
- Never coerce, repair, or fabricate a missing field — every finding is a row describing an
  absence, never a corrected value written back into `entries`.
**Do NOT touch:** `docs/parity_ledger/schema.json` — the duplicate-`"if"`-key defect is read
around, never fixed, per both the ticket's Out of Scope and `v1_decisions_phase0.md`'s "Known
gaps" section.
**Verify:** `test_missing_test_path_produces_entry_health_finding`.

### Step 5 — `entry_fts` (FTS5) with probe-and-fallback
**Files:** `tools/parity_index.py`
**Change:**
- Implement `_probe_fts5(conn)` and the `force_fts5_unavailable` parameter on `build()` exactly as
  specified in Decision 3 above.
- When FTS5 is available (real probe succeeds, and not force-disabled): `CREATE VIRTUAL TABLE
  entry_fts USING fts5(id, text, subsystem, status, v2_evidence)`, populated from `entries` in
  `(shard, id)` order. Standalone FTS5 table (no `content=` linkage) — each row carries its own copy
  of the searchable columns, queryable by `WHERE id = ?` or `MATCH`.
- When FTS5 is unavailable (probe fails or forced): skip creating `entry_fts` entirely; record
  `fts5_available: false` in the build-report (see Step 6) and in `ledger_generation` (add a
  `fts5_available INTEGER` column, `0`/`1`). Exact ID/path lookups always go through `entries`
  directly and never depend on `entry_fts` existing — this must hold identically in both branches.
**Do NOT touch:** No `sqlite-vec` dependency, no Graphify dependency — FTS5 is the only search
mechanism, and it is explicitly "discovery only," never a correctness gate, per the idea doc's Read
path section.
**Verify:** `test_fts5_present_populates_entry_fts_table`,
`test_fts5_forced_unavailable_falls_back_to_exact_lookup`.

### Step 6 — Validation, structured build-report, abort-before-replace wiring
**Files:** `tools/parity_index.py`
**Change:**
- After all tables in Steps 2-5 are populated inside the temp-file build (Step 1's lifecycle), run a
  validation pass before the connection is handed back for `os.replace`: row-count of `entries`
  equals the sum of per-shard entry counts recorded in `shard_manifest_json`; every table from Steps
  1-5 exists with the expected columns (a schema sanity check, cheap `PRAGMA table_info` per table).
  Any validation failure raises a typed `BuildValidationError` — build-abort per Decision 2, same
  path as `DuplicateEntryIdError`/`ShardParseError`.
- `build()`'s top-level `try/except` around the whole temp-build call: on `ShardParseError`,
  `DuplicateEntryIdError`, or `BuildValidationError`, delete the temp file, **never** touch
  `final_path`, and return/raise a structured failure report — `{"status": "failed",
  "failure_class": <one of the three>, "detail": ...}` — serialized via
  `parity_index_baseline.serialize_manifest`'s exact convention (`json.dumps(..., sort_keys=True,
  indent=2, ensure_ascii=True) + "\n"`), printed to stdout by the CLI with a non-zero exit code.
  Never let a raw Python traceback reach the CLI's stdout/exit path for these three failure classes.
- On success, `build()` returns `{"status": "ok", "ledger_generation": {...}, "shard_count": N,
  "entry_count": N, "fts5_available": bool, "health_finding_counts": {...}}` using the same
  serialization convention.
**Do NOT touch:** No write path to any file under `docs/parity_ledger/` anywhere in this function —
grep the finished file for `docs/parity_ledger` occurrences outside of read-mode (`glob`,
`read_bytes`, `read_text`, `Path(...)` construction) as a self-check before calling this step done.
**Verify:** `test_failed_build_preserves_prior_good_db_byte_identical`,
`test_failed_build_never_writes_to_source_yaml`.

### Step 7 — Determinism proof
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add a test that runs `build()` twice against the same unchanged `tmp_path` fixture
corpus (fresh output path each run, or the same path — either is valid since Step 1's atomic
lifecycle is already idempotent) and asserts: identical row counts in every table, identical
`(shard, id)`-ordered `entries`/`entry_health` row sequences, and identical
`ledger_generation.source_manifest_hash` and `shard_manifest_json`. Explicitly **exclude**
`ledger_generation.built_at` from the equality check — that field is expected to legitimately
differ between runs (wall-clock timestamp), and the test must document this exclusion in a comment
so it is never mistaken for a determinism gap.
**Do NOT touch:** No change to `tools/parity_index.py` in this step — pure test addition proving
behavior already built in Steps 1-6.
**Verify:** `test_build_is_deterministic_on_unchanged_source`.

### Step 8 — Anti-drift static guards and legacy regression confirmation
**Files:** `tests/tools/test_parity_index.py`
**Change:** Add the following as source-text/behavior guards, mirroring
`test_build_index.py::test_build_index_never_touches_write_path_modules`'s idiom:
- `test_importer_does_not_implement_impact_or_entry_or_health_cli` — assert `tools/parity_index.py`
  contains no `impact`, `search`, or `entry` argparse subcommand/CLI surface beyond `build` (a
  `--help`-output or source-text check), guarding against Phase 2's CLI surface being absorbed early.
- `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` — assert no `parity-record`-shaped
  entrypoint exists and no `open(..., "w")`/`write_text` call targets any path under
  `docs/parity_ledger/` anywhere in the source text.
- Confirm (do not write a wrapper test per the test plan's own recommendation) that
  `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py -q`
  still exits 0 (13/13) after all prior steps — run as a scoped regression command, report the
  result in the ticket's Test Summary.
**Do NOT touch:** `tests/tools/test_parity_ledger_scan.py`, `tests/tools/test_parity_updater_static.py`
themselves — regression-run only, zero edits.
**Verify:** `test_importer_does_not_implement_impact_or_entry_or_health_cli`,
`test_no_mutation_cli_or_write_path_to_docs_parity_ledger`,
`test_legacy_eight_shard_tests_unmodified_and_green` (satisfied by the scoped pytest command above,
per test_plan.md's own recommendation — no literal wrapper test required).

## Scope Guards

- Do not modify `tools/parity_ledger_scan.py`, `tools/gate_checks/parity_updater_static.py`,
  `docs/parity_ledger/*.yaml`, or `docs/parity_ledger/schema.json`. All read-only reference; zero
  edits anywhere in this ticket.
- Do not modify `tools/agent-monitoring/build_index.py` or its tests
  (`tests/tools/test_build_index.py`) — read-only anti-pattern precedent only. Do not "fix" its
  pre-existing `test_makefile_dry_run_agent_monitoring_index` failure as a drive-by; it is out of
  scope and unrelated to this ticket's Related Code Areas.
- Do not modify `tools/parity_index_baseline.py` or `tests/tools/test_parity_index_baseline.py` —
  reuse by import/pattern-mirroring only, never edit.
- Do not import or extend `CANONICAL_LEDGER_FILES` as this importer's shard-discovery source. The
  importer's glob is fully independent, per `v1_decisions_phase0.md`.
- Do not build `impact`, `entry`, `search`, or `health` CLI subcommands (Phase 2 —
  `TCK-20260731-PARITY-IMPACT-PROOF`). `build` is the only subcommand this ticket authorizes.
- Do not build `parity-record`, any YAML mutation path, or any write-mode `open()`/`write_text()`
  call targeting `docs/parity_ledger/`. Deferred to a separate, not-yet-approved Phase 3.
- Do not depend on Graphify or `sqlite-vec` for any reference resolution. V1 references are
  path-level string matches only.
- Do not add context/retrieval/workflow integration (`tools/context_packet_assembler.py`,
  `.claude/agents/parity-updater.md`, `.claude/workflows/implement-ticket.js`). Those are Phase 4+
  per the idea doc's Delivery Sequence.
- Do not implement `impact_candidates` (table, view, or query). Explicitly Phase-2-deferred per the
  idea doc's Delivery Sequence — this is a documented deferral, not a silent omission.
- Do not run `pytest tests/` repo-wide. Scoped commands only, per test_plan.md's Scoped Pytest
  Commands section.
- Do not "fix" `docs/parity_ledger/schema.json`'s duplicate-`"if"`-key defect. Work around it in
  `entry_health` logic per Step 4; leave the file itself untouched.

## Dependency Map

- Step 1 (module skeleton, atomic lifecycle, `.gitignore`) — no dependencies. Foundation for all
  later steps.
- Step 2 (shard discovery, `entries`, duplicate/malformed abort) — depends on Step 1's lifecycle
  scaffolding.
- Step 3 (reference tables) — depends on Step 2's `entries` rows to link against.
- Step 4 (`entry_health`) — depends on Step 2 (`entries`) and Step 3 (all four ref tables, for the
  `absent_file` and `legacy_unstructured` findings).
- Step 5 (`entry_fts`) — depends on Step 2 (`entries` text/status/subsystem columns). Independent of
  Steps 3-4; could be built in parallel with them if desired, but is sequenced after for a single
  linear implementation order.
- Step 6 (validation, build-report, abort wiring) — depends on Steps 1-5 (validates row counts and
  schema across every table those steps create).
- Step 7 (determinism proof) — depends on Steps 1-6 (tests the fully assembled build).
- Step 8 (anti-drift guards, legacy regression) — depends on Steps 1-7 (final source file must be
  complete for static-text guards to be meaningful).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — Rebuild imports all nine shards, preserves YAML byte hashes, exposes normalized joinable rows, no DB committed to git | Steps 1, 2, 3 | `test_importer_imports_all_nine_shards`, `test_importer_preserves_source_byte_hashes`, `test_entries_table_supports_join_to_code_test_constraint_ticket_refs`, `test_db_not_tracked_by_git` |
| AC #2 — Identical inputs give same logical generation/ordered tables/health findings; duplicate IDs, malformed sources, unparseable refs, missing local refs/tests, legacy-unstructured evidence are deterministic classified findings, never invented links | Steps 2, 3, 4, 7 | `test_build_is_deterministic_on_unchanged_source`, `test_duplicate_cross_shard_id_rejected_at_import`, `test_malformed_yaml_shard_produces_classified_finding_not_crash`, `test_unparseable_code_ref_never_invents_a_link`, `test_missing_test_path_produces_entry_health_finding` |
| AC #3 — FTS5-present and forced-unavailable tests both pass; unavailable FTS reports disabled discovery while exact ID/path lookups remain correct | Step 5 | `test_fts5_present_populates_entry_fts_table`, `test_fts5_forced_unavailable_falls_back_to_exact_lookup` |
| AC #4 — Injected parse/validation/replacement failure leaves prior good DB byte-identical, no usable partial DB, failed input never changes YAML | Steps 1, 2, 6 | `test_failed_build_preserves_prior_good_db_byte_identical`, `test_failed_build_never_writes_to_source_yaml`, `test_build_uses_sibling_temp_file_then_atomic_replace` |
| AC #5 — Old eight-shard legacy functions and their tests retain unchanged behavior | Step 8 (regression-only; zero edits anywhere) | `test_legacy_eight_shard_tests_unmodified_and_green` (scoped pytest command), `test_importer_does_not_implement_impact_or_entry_or_health_cli`, `test_no_mutation_cli_or_write_path_to_docs_parity_ledger` |

## Anti-Drift Notes

- The single most important guard in this plan is Step 1/Step 8's static-text check that
  `if db_path.exists(): db_path.unlink()` never appears in `tools/parity_index.py` — this is the
  exact anti-pattern confirmed present in `build_index.py` lines 179-183 that both the ticket's
  Implementation Notes and `v1_decisions_phase0.md` name as the failure mode to avoid.
- `entry_health` is intentionally a materialized table, not a live SQL `VIEW`, because of the
  `absent_file` finding's filesystem-existence check (Step 4). This is a documented interpretation
  of the idea doc's "view" language, not a scope reduction — implementers must not "simplify" this
  later into a view that silently drops the `absent_file` finding class.
- Never treat FTS5 as always available just because this build environment happens to have it
  compiled in (confirmed `FTS5 OK` in Investigation) — the `force_fts5_unavailable` parameter from
  Decision 3 must actually be exercised by a test (Step 5), not left dead code.
- `docs/parity_ledger/schema.json`'s duplicate-`"if"`-key defect (only the second `if`/`then` pair
  survives `json.loads`) means the schema does not mechanically enforce the `v2_evidence`+
  `test_path` requirement for `verified`/`divergent` entries. Step 4's `entry_health` logic encodes
  the schema's *documented intent* (both pairs), matching `parity_index_baseline.py`'s own
  `_missing_evidence_health` scope comment — never validate against what `json.loads` would
  mechanically accept.
- Reuse, do not reimplement: `_sha256_hex` (hashing convention — `read_bytes()`, not `read_text()`)
  and the `eid in seen or seen.add(eid)` duplicate-ID idiom from `tools/parity_index_baseline.py`,
  and its `serialize_manifest` JSON convention for this importer's own build-report. Divergence from
  these conventions would make the two tools' evidence non-comparable.
- The Phase-0 `TCK-20260713-MONITORING-SQLITE-INDEX` lesson applies directly to Step 4: do not trust
  a literal field-presence check (`record.get(...) is not None`) as correct-by-construction for
  `missing_test_path`/`missing_v2_evidence`/`absent_file` classification without checking it against
  a realistic multi-shard fixture (or the live ledger, read-only) — that lesson was only caught by
  verification against a real corpus, not by the spec text alone.
- `tests/tools/test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index` is
  a known pre-existing failure unrelated to this ticket (Makefile phony-target quirk). It must never
  be included in this ticket's required-green regression set, and must never be "fixed" as a
  drive-by — `Makefile` and `build_index.py` are outside this ticket's Related Code Areas.

## Deviations

**Discovered during Implementation, not resolved by the implementer, reported per project instruction
against silently working around a failing check:** Step 1's required `parity-index/` `.gitignore`
entry (mandatory — also required by the ticket's own Scope and `v1_decisions_phase0.md`'s "Ownership"
section) causes `tests/tools/test_parity_index_baseline.py::
test_no_database_or_gitignore_or_make_target_created` (from `TCK-20260731-PARITY-INDEX-BASELINE`,
commit `1ec93c0d`) to fail, because that test asserts `"parity-index" not in gitignore_text` — a
Phase-0-scoped tripwire proving Phase 0 didn't prematurely create Phase 1 artifacts, not a permanent
invariant, but its assertion has no phase-completion escape hatch. This was not anticipated by this
plan or by investigation.md, both of which assumed (based on a pre-implementation regression run)
that `test_parity_index_baseline.py` would stay green throughout this ticket. It creates a direct,
unavoidable collision between two of this plan's own binding constraints: Step 1's mandatory
`.gitignore` addition, and the Scope Guards' "Do not modify ... `tests/tools/test_parity_index_
baseline.py`" / test_plan.md's "must remain green and untouched." The implementer did not edit the
protected test file (out of authorized scope) and did not obfuscate the `.gitignore` entry to dodge
the test's substring match (would be gaming a gate rather than fixing the substance). See the ticket's
Implementation Notes for full detail.

**Resolved (user decision, 2026-08-02):** `test_no_database_or_gitignore_or_make_target_created` was
narrowed to check `TCK-20260731-PARITY-INDEX-BASELINE`'s own commit diff
(`git diff-tree --no-commit-id --name-only -r 1ec93c0d`) rather than the live `.gitignore`/`Makefile`
contents — the property it actually needed to prove (Phase 0's own commit didn't jump ahead into Phase
1's territory) is a historical fact about one specific commit, not a live-state invariant that Phase 1
was always going to violate by design. Full regression suite (`test_parity_index_baseline.py` +
`test_parity_index.py` + `test_parity_ledger_scan.py` + `test_parity_updater_static.py`) is 44/44 green.
