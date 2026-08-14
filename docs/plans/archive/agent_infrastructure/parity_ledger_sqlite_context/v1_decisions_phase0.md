---
status: historical
layer: ai
authority: P2
audience: agent
maturity: shipped
date: 2026-08-02
archived: 2026-08-04
tags: [ai, documentation, process-improvement]
---

# Parity Ledger SQLite Index — V1 Phase 0 Decisions

Companion decision record to
`idea_parity_ledger_sqlite_context_integration.md`, produced by
`TCK-20260731-PARITY-INDEX-BASELINE`. It resolves every "Open decisions
before tickets are created" item the idea doc left unsettled that falls
within this ticket's Scope, and every Scope boundary named in the ticket
body. It decides; it does not build. No database, `.gitignore`/Makefile
entry, index code, or mutation CLI is created by this ticket or by this
document — those remain Phase 1/IMPORTER and later phases' work.

## Ownership

`parity-index/parity.db` (Phase 1+) is a local, gitignored, derived-only
artifact rebuilt from the reviewed `docs/parity_ledger/*.yaml` shards. No
agent or tool edits it directly — the YAML shards remain the sole
reviewable, version-controlled source of truth. This ticket (Phase 0) does
not create the database file or the `.gitignore` entry that would ignore
it; that is explicitly Phase 1/IMPORTER's job.

## Discovery / IDs

Shard discovery for the index (and for this ticket's own baseline
manifest, `tools/parity_index_baseline.py`) must be **dynamic**: glob
`docs/parity_ledger/*.yaml`, never a hardcoded file list. This is a
deliberate contrast with the legacy `tools/parity_ledger_scan.py`'s
`CANONICAL_LEDGER_FILES` 8-file tuple, which stays frozen as a
compatibility fixture for the existing Parity-phase skip check — it is not
a pattern for the index to inherit.

**Decision (resolves idea doc Open decision area "shard/ID rules"):**
cross-shard `id` uniqueness is a v1 **enforced invariant** going forward.
Phase 1/IMPORTER's importer must reject (not silently tolerate) a
duplicate `id` across shards at import time. Rationale: today's corpus
already satisfies it (0 duplicate IDs across all 1,945 entries in 9
shards, verified by this ticket's baseline manifest), the schema's
per-entry `id` pattern (`^[A-Z]+-[0-9]{3}$`) implies uniqueness was always
the intent, and leaving it as a mere "observed fact" would let Phase 1
defer a check that is cheap to add now and expensive to retrofit once the
index has consumers.

## Normalized schema

Adopt the idea doc's table shape as-is: `ledger_generation`, `entries`,
`code_refs`, `test_refs`, `constraint_refs`, `ticket_refs`, `entry_fts`
(FTS5 discovery projection), `entry_health` view, `impact_candidates`
view/query (see idea doc "Target data model" section). This ticket does
not redesign the shape — it confirms it as the Phase 1/2 target so
IMPORTER does not re-litigate the table design.

## FTS fallback

Phase 1/IMPORTER must probe SQLite's FTS5 compile flag at build time and
fall back to an exact-ID/path match (no full-text search) if FTS5 is
unavailable in the runtime SQLite build. This document records the
requirement; it does not probe or implement it — no FTS5 code, no
`PRAGMA compile_options` check, and no fallback logic is added by this
ticket.

## Atomic lifecycle

Phase 1/IMPORTER must build into a sibling temporary database file,
validate integrity/schema/row counts against the source manifest,
close/fsync as appropriate, then atomically replace the previous database.
A failed build must leave the last-good database and all YAML untouched.

This deliberately does **not** inherit
`tools/agent-monitoring/build_index.py`'s lifecycle pattern
(`if db_path.exists(): db_path.unlink()` followed by unconditional
rebuild) — that precedent is cited here as a pattern to avoid, not follow,
because it has no validated-temporary-file/atomic-replace step and would
leave no last-good database if a rebuild failed partway through.

## Path-only links

V1 resolves structured references (`code_refs`, `test_refs`,
`constraint_refs`, `ticket_refs`) to **path-level only**. No Graphify
symbol resolution is used or depended on in v1, matching the idea doc's
"Structured reference evolution" section verbatim ("V1 resolves the
Graphify decision to path-level links only"). Symbol-level resolution
remains explicitly deferred pending a future reliability/contract review
of Graphify's update/rebuild guarantees.

## Output convention

This ticket's own baseline manifest (`tools/parity_index_baseline.py`,
written to
`staging_artifacts/TCK-20260731-PARITY-INDEX-BASELINE/baseline_manifest.json`,
migrating to `stored_artifacts/` at ticket close) is the reference
serialization convention for Phase 1's own build-report/manifest output:
JSON with `sort_keys=True`, a fixed `indent`, `ensure_ascii=True`, and a
trailing newline, so unchanged source input reliably yields byte-identical
output across reruns. Phase 1's importer build-report should follow this
same convention rather than inventing a new one.

## CLI/module ownership

**Decision (resolves idea doc Open decision #6):** flat files directly
under `tools/`, not a new `tools/parity_ledger/` package. Phase 1 builds
`tools/parity_index.py`; the deferred, not-yet-authorized Phase 3 mutation
tool (if that phase ever approves it) would be `tools/parity_record.py`.

Rationale:
- The existing sibling tool `tools/parity_ledger_scan.py` is already a
  flat top-level module with no package wrapper — matching it avoids
  introducing a second convention for the same tool family.
- `tools/gate_checks/`'s own precedent (`parity_updater_static.py`) is a
  flat module even though it lives inside an already-established
  subdirectory — it did not spin up a package for one file.
- Only two files (`parity_index.py`, deferred `parity_record.py`) are
  currently planned, which does not justify a new package's
  `__init__.py`/namespace overhead.
- This decision is reversible later — nothing in Phase 0 creates the
  files themselves, only records the intended location, so a future
  ticket could still restructure into a package if the tool family grows
  materially (for example FTS query subcommands or a health-report
  subcommand) without this ticket having locked in anything irreversible.

## `parity-record` deferral

`parity-record` (the record-oriented YAML mutation tool sketched in the
idea doc's "Write and management path" section) **stays deferred**,
pending a separate Phase-3 go/no-go decision that has not happened yet.
This document does not describe a working implementation of it and does
not authorize building it now. Phase 3 must first compare `parity-record`
against the lighter static lineage-preservation guard alternative (per
the idea doc) before either is implemented; this Phase 0 document takes no
position on which of those two Phase 3 will select.

## Known gaps

Recorded here as facts for later phases to account for, not fixed by this
ticket:

1. **`docs/parity_ledger/schema.json`'s duplicate top-level `"if"` key.**
   The source JSON declares two `if`/`then` conditional pairs inside the
   same `items` object (`verified`/`divergent` requiring `v2_evidence` and
   `test_path`; `divergent` requiring `divergence_note`). Duplicate JSON
   object keys mean any standard parser, including `json.loads`, silently
   keeps only the second pair — the `v2_evidence`/`test_path` requirement
   for `verified`/`divergent` entries is not actually enforced by the
   schema as it parses today. This ticket's baseline manifest
   (`tools/parity_index_baseline.py`'s `schema_coverage` field) records
   this as an observed parsing fact. It is a candidate for a future,
   dedicated ticket to fix (for example rewriting the two conditionals as
   a single `allOf` composition, the standard JSON Schema pattern for
   multiple conditional branches) — not something Phase 0, Phase 1, or
   this document addresses.
2. **Missing companion document.** The ticket's originating context
   referenced a `idea_parity_ledger_sqlite_context_integration_review_claude.md`
   companion file. This investigation searched the full repository tree
   and `git log --all` for any file matching that name — zero matches, no
   file, no git history. Recorded here as a gap, not treated as a blocker,
   since nothing in this ticket's Scope or Acceptance Criteria depends on
   that specific file existing.
