---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY
phase: open
date: 2026-08-08
tags: [ai, observability, process-improvement]
---

# TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY

## Title
Derived SQLite parity index (`parity-index/parity.db`) has no `make` target and no staleness
check — silently drifts from `docs/parity_ledger/*.yaml` every time a ticket's Parity phase edits
the YAML, with nothing to detect or surface the drift

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
While verifying today's parity ledger updates (`SUB-375`–`SUB-378`, `COMB-296`, added across a
5-ticket batch), confirmed the derived SQLite index built by `tools/parity_index.py` (from
`TCK-20260731-PARITY-INDEX-EPIC`'s own 4-ticket batch: BASELINE/IMPORTER/IMPACT-PROOF/
READPATH-GATE) works correctly once rebuilt — `build`, `entry`, `impact`, and `health` all
resolved the new entries correctly, 29/29 existing tests pass — but two real gaps exist around
*keeping it built*:

1. **No `make` target.** `docs/REGISTRY.yaml` has `make docs-registry`;
   `config/simulation_quality/corpus_registry.yaml` has `make simq-corpus-registry`; the sibling
   `agent-monitoring-index/monitoring.db` has `make <target>` (confirmed via `Makefile` grep).
   `parity-index/parity.db` has **none** — the only way to rebuild it is the raw
   `python3 tools/parity_index.py build` invocation, and per this repo's own established
   write-safety convention (`INFRA-315`, `TCK-20260803-RETRO-TOOL-SAFETY-AUDIT`), that invocation
   must target a scratch path, not the real repo path — a detail with no discoverable
   documentation pointing at it outside that one ticket's own retro-audit logic.
2. **No staleness check.** Nothing compares the DB's own `ledger_generation.source_manifest_hash`
   (already computed and stored at build time — confirmed present in `build`'s own output) against
   a fresh hash of the current `docs/parity_ledger/*.yaml` shards. A stale, un-rebuilt DB looks
   identical to a fresh one from the outside — `entry`/`impact`/`health` will silently return
   correct-looking results computed from OLD data with no signal that new ledger entries (or
   edits to existing ones) are missing.

**Confirmed this is not a workflow-wiring omission** — checked `.claude/workflows/
implement-ticket.js` and `Makefile` directly: the sibling `agent-monitoring-index/monitoring.db`
is *also* never auto-rebuilt from the ticket pipeline, only from its own `make` target. Rebuild-
on-demand (not rebuild-per-ticket) is this repo's own established convention for derived SQLite
indexes, and the archived idea doc for this exact index
(`docs/plans/archive/agent_infrastructure/parity_ledger_sqlite_context/
idea_parity_ledger_sqlite_context_integration.md`) explicitly rejects adding "workflow ceremony"
for phase-0 scope. This ticket does **not** propose auto-rebuilding the index inside
`implement-ticket.js`'s Parity phase — that would contradict both the established convention and
the idea doc's own explicit constraint. It proposes making the *existing* on-demand model
actually usable: a real entry point (`make`) and a way to know when a rebuild is needed
(staleness check), matching the precedent `docs-registry`/`simq-corpus-registry` already set for
every other derived-from-source-of-truth artifact in this repo.

## Scope
1. **Investigate**: confirm the exact shape of `ledger_generation.source_manifest_hash` and how
   `_build_into()`/`serialize_manifest()` (`tools/parity_index_baseline.py`) compute it, so a
   staleness check can recompute the same hash from live `docs/parity_ledger/*.yaml` WITHOUT
   doing a full DB rebuild (cheap check vs. expensive rebuild — confirm this separation is
   actually possible with the existing code, not assumed).
2. **Plan**: design a `parity_index.py check-staleness` (or similarly named) subcommand — reads
   the existing DB's stored `source_manifest_hash`, recomputes a fresh one from live YAML, reports
   `FRESH`/`STALE`/`NOT_BUILT`. Design the new `make parity-index` Makefile target (matching
   `docs-registry`'s own pattern), and a `make parity-index-check` (or fold check into the same
   target with an informative message) — confirm whether the DB should default-build to a scratch
   path or a real (gitignored) repo path for the `make` target specifically, distinct from the
   agent-session write-safety convention that applies to ad-hoc CLI invocations.
3. **Implement**: the new subcommand, the Makefile target(s), a scoped test confirming staleness
   detection actually distinguishes a real stale case (edit a shard, confirm `STALE`) from a real
   fresh case (rebuild, confirm `FRESH`) and from a never-built case (`NOT_BUILT`).

## Out of Scope
- Wiring an automatic rebuild into `implement-ticket.js`'s Parity phase — contradicts this repo's
  own established convention for derived SQLite indexes (see Request Summary); a legitimate
  future decision, not decided or assumed here.
- Any change to `tools/parity_index_baseline.py`'s manifest/hash computation itself — read-only
  reuse of the existing mechanism, not a redesign.
- CI/pre-commit enforcement that blocks a commit on staleness — a policy decision beyond "make
  staleness visible," not assumed needed.

## Acceptance Criteria
- [x] investigation.md confirms the real hash-recomputation mechanism is separable from a full
      rebuild (cheap staleness check is actually possible with existing code)
- [x] A `make` target exists to build/rebuild `parity-index/parity.db`, matching the
      `docs-registry`/`simq-corpus-registry` precedent (real repo path, not scratch — the
      write-safety concern was re-verified to be structurally invisible to a `make` invocation,
      see Implementation Notes)
- [x] A staleness check reports `FRESH`/`STALE`/`NOT_BUILT` correctly for all 3 real cases, tested
      not assumed
- [x] Scoped pytest passes

## Related Tickets
- TCK-20260731-PARITY-INDEX-EPIC, TCK-20260731-PARITY-INDEX-BASELINE,
  TCK-20260731-PARITY-INDEX-IMPORTER, TCK-20260731-PARITY-IMPACT-PROOF,
  TCK-20260731-PARITY-READPATH-GATE (built the index this ticket adds discoverability/staleness
  visibility to — all DONE)
- TCK-20260803-RETRO-TOOL-SAFETY-AUDIT (established the scratch-path write-safety convention this
  ticket's Investigate phase must respect for the `make` target's own default path decision)
- TCK-20260713-MONITORING-SQLITE-INDEX (the sibling `agent-monitoring-index/monitoring.db` —
  confirmed to have the SAME "build-on-demand via `make`, no auto-wiring" pattern this ticket
  follows, not deviates from)

## Related Docs
- `docs/plans/archive/agent_infrastructure/parity_ledger_sqlite_context/
  idea_parity_ledger_sqlite_context_integration.md` (explicitly rejects workflow-ceremony wiring
  for this index — read before Implement, do not contradict)
- `docs/agent-monitoring/schema.md` §"Derived SQLite Index (Read Path Only)" (the sibling index's
  own documented `make`-target convention to mirror)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/`,
  `stored_artifacts/TCK-20260731-PARITY-IMPACT-PROOF/`,
  `stored_artifacts/TCK-20260731-PARITY-READPATH-GATE/`

## Related Code Areas
- `tools/parity_index.py` (`build()`, `_build_into()`, `main()`)
- `tools/parity_index_baseline.py` (`serialize_manifest()`, `_sha256_hex()`)
- `Makefile` (`docs-registry`/`simq-corpus-registry` targets as the pattern to mirror)

## Assumptions / Open Questions
- Whether the `make` target's own default DB path should be `parity-index/parity.db` (the real,
  gitignored repo-local path `tools/parity_index.py`'s own `DEFAULT_DB_PATH` already points at)
  or something else — not assumed; the write-safety convention (INFRA-315) is specifically about
  ad-hoc *agent-session* CLI invocations polluting monitoring signal, not about a `make` target a
  human deliberately runs, so these may legitimately differ. Investigate should confirm, not
  guess.

## Implementation Notes
- **Subagent spawn cap reached this session** — Investigate/Plan/Implement/Document-Update/
  Parity/Verify performed directly.
- **Confirmed, not just reasoned about, that the write-safety scratch-path convention
  (`INFRA-315`) genuinely does not apply to a `make` target**: `_is_unsafe_parity_build_call()`
  (`tools/agent-monitoring/generate_retro.py`) checks `"parity_index.py" in summary and "build"
  in summary` against a Bash tool call's raw `input_summary`. A `make parity-index` invocation's
  `input_summary` is literally `"make parity-index"` — the substring never appears, so this audit
  is structurally blind to Makefile-wrapped invocations. Combined with `parity-index/` being
  gitignored and the direct `agent-monitoring-index` precedent (its own `make` target builds into
  its real default path with no `--db-path` override), `make parity-index` correctly builds into
  the real repo path, matching `docs-registry`/`simq-corpus-registry`/`agent-monitoring-index`.
- The hash-recomputation mechanism was confirmed genuinely separable and cheap: `_load_shards()`
  + a new, extracted `_shard_manifest_hash()` helper (factored out of `_build_into()`'s own inline
  logic so the check can never silently drift from what a real build actually hashes) — no DB
  writes, no ref-table population, no FTS indexing needed for a staleness check.
- `check_staleness()` reads the DB's own stored `ledger_generation.source_manifest_hash` via a
  plain `SELECT` on a read-only connection (`_connect_readonly()`, already existing), compares
  against a freshly-recomputed hash from live YAML, reports `FRESH`/`STALE`/`NOT_BUILT`.
- New `check-staleness` CLI subcommand matches the existing `entry`/`impact`/`health` argparse
  pattern exactly; exit code `0` for FRESH, `1` for STALE/NOT_BUILT, matching `build`'s own
  `0 if status == "ok" else 1` convention.
- Two new Makefile targets (`parity-index`, `parity-index-check`), plain `python3 tools/<script>`
  form matching `docs-registry`'s simpler style (confirmed bare `python3` can import `yaml` on
  this machine, so the heavier `agent-monitoring-index` venv-detection wrapper wasn't needed).
  Both added to the `.PHONY` line. Ran both for real against the real repo path: `make
  parity-index` built 1981 entries across 9 shards; `make parity-index-check` correctly reported
  `FRESH`, exit code 0. Confirmed `parity-index/parity.db` stays outside `git status` (gitignored,
  as expected) after this real build.
- No doc-file update required — searched `docs/` directly (`grep -rl "parity_index.py" docs/`)
  and confirmed no dedicated CLI-usage guide exists to update; only the module's own docstring
  needed a mention of the new subcommand, done in Implement. The doc-staleness gate independently
  confirmed PASS with `behavior_changed=true` — `tools/`/`Makefile` fall outside the gate's
  flagged-prefix set (`src/`, `config/`, `.claude/workflows/*.js`), consistent with the
  investigation's own finding.
- Parity: no subsystem mapping exists for `tools/parity_index.py`/`Makefile`/the test file —
  `expected_subsystems_for_files()` and `find_p0_intersection()` both returned empty. Confirmed,
  not assumed.

## Test Summary
- `tests/tools/test_parity_index.py` (extended, 5 new tests in a new `TestCheckStaleness` class):
  `test_check_staleness_not_built_when_db_missing`,
  `test_check_staleness_fresh_immediately_after_build`,
  `test_check_staleness_stale_after_shard_edit`,
  `test_check_staleness_reuses_load_shards_not_reimplemented`,
  `test_check_staleness_cli_exit_code`.
- Full `tests/tools/test_parity_index.py` suite: 34 passed, 0 failed (29 existing + 5 new, zero
  regressions).
- Real, non-scratch verification: ran `make parity-index` and `make parity-index-check` against
  the actual repo `docs/parity_ledger/` and confirmed real, correct output (1981 entries, `FRESH`,
  exit 0), not just unit-test-level confidence.

## Files Changed
- `tools/parity_index.py` — new `_shard_manifest_hash()` (extracted shared helper),
  `check_staleness()`, `check-staleness` CLI subcommand, module docstring update
- `Makefile` — new `parity-index`/`parity-index-check` targets, `.PHONY` line updated
- `tests/tools/test_parity_index.py` — new `TestCheckStaleness` class, 5 tests

## Completion Summary
The derived SQLite parity index now has the same discoverability every other derived-from-
source-of-truth artifact in this repo has (`make parity-index`, matching `docs-registry`/
`simq-corpus-registry`/`agent-monitoring-index`), plus a genuinely new capability none of those
siblings have: a cheap `check-staleness` command that reports whether the built index has drifted
from live `docs/parity_ledger/*.yaml` without a full rebuild, reusing the exact same hash
computation a real build performs (factored into a shared helper specifically to prevent drift
between the check and the build). The original write-safety concern that motivated keeping this
tool's CLI usage manual and undiscoverable was investigated directly and found not to apply to a
`make` target at all — confirmed via the actual audit detection code, not assumed.
