---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260731-PARITY-INDEX-BASELINE
artifact_type: investigation
tags: [ai, documentation, process-improvement, testing]
---

# Investigation — TCK-20260731-PARITY-INDEX-BASELINE

## Current Behavior

### `docs/parity_ledger/` — 9 live shard files, 1,945 entries (not 1,936)

Confirmed via `ls docs/parity_ledger/*.yaml` (9 files) and `grep -c '^\s*- id:'` per file:

| File | Entries |
|---|---|
| `substrate.yaml` | 386 |
| `infrastructure.yaml` | 319 |
| `combat_movement.yaml` | 294 |
| `social_narrative.yaml` | 260 |
| `strategic_cognition.yaml` | 247 |
| `town_resource.yaml` | 189 |
| `world_dynamics.yaml` | 121 |
| `progression.yaml` | 116 |
| `faction.yaml` | 13 |
| **Total** | **1,945** |

Status breakdown (all 9 shards): `verified` 1,704, `legacy_verified` 232, `divergent` 3, `missing` 4,
`unsupported` 2. Priority breakdown: `P0` 1,661, `P1` 218, `P2` 66. Zero duplicate `id` values across
all 9 files (verified programmatically). `faction.yaml` has **0 `priority: P0` entries** (13 total,
confirmed by grep) — this is the fact `tools/parity_ledger_scan.py`'s own docstring cites (line 9) to
justify excluding it, and it independently re-confirms today.

**Drift from the idea doc's cited baseline (1,936):** the live corpus is 9 entries larger than the
"1,936 entries over nine YAML files" figure in
`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`
("Why this is needed" section, line 73-74), written 2026-07-31 (same date as this ticket). The ticket's
own AC #2 says the manifest must "record the historical 1,936-entry snapshot" — read together with the
ticket's Assumptions section and the idea doc's own framing, **1,936 is a historical comparison figure
from the idea doc, not a reproduction target.** The baseline manifest this ticket produces must capture
the CURRENT accurate count (1,945) as the authoritative snapshot, and separately note 1,936 as the
idea-doc-vintage comparison number with the 9-entry drift explicit and dated. Silently overwriting 1,936
with 1,945 without noting the discrepancy would make AC #2 impossible to satisfy honestly; silently
reproducing 1,936 as if it were still accurate would misrepresent the current corpus.

Per-shard SHA-256 hashes captured (baseline manifest must include these, sorted by filename, as the
"source hashes are unchanged" byte-identity check for AC #1):

```
010ff4862f760774db588311341d3851d5ceae08af73fc348c3e77053b819c49  combat_movement.yaml
35f0d18e17d68d14e479c6c6509daf7be18074d535f2d6513d54765318952820  faction.yaml
9b882132df3c98e62463a6d49fa1d1e5d4aaeb29dab57eb9c11c781408da75d1  infrastructure.yaml
e8c8f0e083709b0479784edb85ab0fbc5b33d91e88594656940119813e0920ac  progression.yaml
b58b0d4c8683e79850b12a9c7157ed8bfa3f54a25b40e05ce495059f6ce6a87f  social_narrative.yaml
1063250a862a6501347d38c1ad4c64f19bb27dba489d0ece8b0ed0312aa62a38  strategic_cognition.yaml
2b24e800814b313002dcbf8c0b593a022f7e3816093ea160e3a7926d11d5d66d  substrate.yaml
2eadddc73ff47947dbaedc44c5f561ded7e2572817b855c54a49b4b9a0165d2a  town_resource.yaml
529e45cf82613afa20da00f70e06c07cd94ba961bc8a8629ec4d90baa76501a8  world_dynamics.yaml
```

### `tools/parity_ledger_scan.py` (read in full)

- `CANONICAL_LEDGER_FILES` (line 24-33): hard-coded 8-file tuple — `substrate.yaml`,
  `combat_movement.yaml`, `strategic_cognition.yaml`, `town_resource.yaml`, `progression.yaml`,
  `social_narrative.yaml`, `world_dynamics.yaml`, `infrastructure.yaml`. `faction.yaml` is **not**
  included — confirmed both by reading the tuple literal and by `test_only_scans_canonical_eight_not_faction`
  in `tests/tools/test_parity_ledger_scan.py:39-49`.
- `find_p0_intersection(files_changed, ledger_dir="docs/parity_ledger")` (line 36-59): loads each of the
  8 canonical files via `yaml.safe_load`, filters to `priority == "P0"`, substring-matches each
  `changed_path` against the entry's `v2_evidence` text, returns `(filename, entry_id, changed_path)`
  triples. Silently `continue`s if a canonical file doesn't exist (line 47-48) — no error on missing
  shard.
- This module is built for `TCK-20260705-WORKFLOW-PARITY-SKIP`'s Parity-phase skip-eligibility check in
  `.claude/workflows/implement-ticket.js` — an orchestrator-run, non-agent `bash()` call gating whether
  the full `parity-updater` agent call can be skipped.

### `tools/gate_checks/parity_updater_static.py` (read in full)

- Imports `CANONICAL_LEDGER_FILES` directly from `parity_ledger_scan` (line 34) — `test_reuses_canonical_ledger_files_constant`
  (`test_parity_updater_static.py:98-101`) asserts identity (`is`, not `==`), so the two modules share
  exactly one source of truth for the 8-file list. Any future all-shard change must keep this identity
  assertion true or update both modules and this test together.
- `derive_mapping(ledger_dir)` (line 39-61): regex-extracts `src/[\w\-./]+\.py` substrings from every
  `v2_evidence` field across the 8 canonical files, building `{src_path: {ledger_filename, ...}}` —
  deliberately set-valued because ~16% of paths are cited in 2+ subsystem files (documented finding from
  the prior `TCK-20260705-GATE-DET-PARITY-UPDATER` investigation, re-confirmed structurally by this
  investigation's read of the same function). Skips a missing canonical file silently (line 51-52) and
  skips (via `try/except Exception: continue`, line 53-56) any canonical file that fails YAML parsing —
  legacy-data tolerance, never raises.
- `expected_subsystems_for_files` / `cross_reference_touched`: consumers of `derive_mapping`, used by
  the Parity workflow phase's pre/post `bash()` calls (established in `TCK-20260705-GATE-DET-PARITY-UPDATER`).
  Both are orchestrator-run, not agent-judged.
- **`faction.yaml` exclusion is doubly confirmed**: `test_excludes_faction_yaml` (`test_parity_updater_static.py:86-95`)
  proves a `faction.yaml`-only `v2_evidence` citation never appears in `derive_mapping`'s output.

### `tests/tools/test_parity_ledger_scan.py` (3 tests, read in full)

`test_detects_p0_intersection_via_synthetic_fixture`, `test_no_intersection_for_representative_docs_only_change`,
`test_only_scans_canonical_eight_not_faction`. The second test's own comment (line 20-21) states: "none
of the real ledger's current P0 entries can exercise this branch (investigation.md's empirical finding),
so this uses a synthetic fixture" — i.e. it is already documented (by a prior ticket's investigation.md)
that no real P0 `v2_evidence` today cites a non-`src/`/non-`tests/` path that would trip a false
positive. This investigation re-ran `pytest tests/tools/test_parity_ledger_scan.py
tests/tools/test_parity_updater_static.py -q` — **13/13 passed**, confirming this baseline's starting
regression surface is green before any Phase-0 artifact work begins.

### `tests/tools/test_parity_updater_static.py` (10 tests, read in full)

Covers `derive_mapping` (multi-subsystem accumulation, malformed-YAML tolerance, faction exclusion,
shared-constant identity), `expected_subsystems_for_files` (non-`src/` exclusion), and
`cross_reference_touched` (PASS/FAIL/NA semantics, ANY-of-candidates-touched clearing a multi-mapped
file, unmapped file is `NA` not `FAIL`). All 10 use isolated `tmp_path` fixtures via a shared
`_write_ledger` helper — none read the live ledger except implicitly through the shared
`CANONICAL_LEDGER_FILES` import identity check.

### `docs/parity_ledger/schema.json` — a load-bearing parsing gap found during this investigation

The file's JSON literally contains **two top-level `"if"` keys** inside the same `items` object
(the `verified`/`divergent` → `v2_evidence`+`test_path` requirement, and the `divergent` →
`divergence_note` requirement). JSON object keys must be unique; parsing this file with `json.loads`
(verified directly in this investigation) silently keeps only the **second** `"if"/"then"` pair — the
first pair (requiring `v2_evidence`/`test_path` for `verified`/`divergent` status) is discarded by any
standard JSON parser before enforcement even begins. This is a pre-existing defect in the schema file
itself, not something this ticket is asked to fix (Out of Scope explicitly excludes "Changing YAML
fields, legacy tools... a mutation CLI" and this ticket does not create/modify a schema-validation tool),
but the baseline manifest's "schema coverage" claim must describe what the schema **as parseable today**
actually enforces (only the `divergent`→`divergence_note` rule), not what the human-readable source text
appears to say. Flagging as a documented gap, not fixing it — the fix belongs to a separate ticket if the
project decides to pursue it (e.g. rewriting as an `allOf` composition, the standard JSON Schema fix for
multiple conditional branches).

### `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`
(read in full, 541 lines)

Establishes the v1 architecture this ticket must record decisions against:
- `parity-index/parity.db`: local, gitignored, derived from YAML, never directly edited by agents.
- V1 read-only Phases 0-2 only; mutation tool (`parity-record`) explicitly deferred behind a separate
  Phase-3 go/no-go decision (Open decision #2). This ticket's own scope line ("`parity-record` stays
  deferred") matches the idea doc exactly.
- Table shape (`ledger_generation`, `entries`, `code_refs`, `test_refs`, `constraint_refs`,
  `ticket_refs`, `entry_fts`, `entry_health` view, `impact_candidates` view/query) is Phase 1/2 scope,
  not Phase 0 — this ticket does not build any of these tables, only decides/records the shape they will
  need.
- FTS5: "must use ordinary SQLite and FTS5 only; the implementation must verify FTS5 availability and
  retain an exact-ID/path fallback if unavailable" (Target data model section) — this is exactly the
  "FTS fallback" decision this ticket's Scope requires recording, not implementing.
- V1 link boundary: "V1 resolves the Graphify decision to path-level links only... does not depend on
  Graphify symbol resolution" (Structured reference evolution section) — matches this ticket's Scope
  line "path-level-only link boundary" verbatim.
- Phase 0's own bullet list (Delivery sequence → Phase 0) is the most direct spec for this ticket:
  "Capture an immutable manifest... Decide YAML-to-index source ownership, FTS5 availability/fallback,
  shard/ID rules, output schema, the v1 path-level-only link boundary, and CLI/module ownership
  (`tools/parity_index.py`/`tools/parity_record.py` versus a package under `tools/parity_ledger/`)...
  Record the current schema-versus-historic-data discrepancy explicitly; classify entries rather than
  silently changing statuses... Define the Phase-2 equivalence fixture corpus and success criteria
  before implementation; it must include the currently excluded `faction.yaml` case." This ticket's
  scope is a faithful restatement of this bullet list.
- "Open decisions before tickets are created" (#6) explicitly asks: "What user-facing CLI
  ownership/location best fits existing tooling: `tools/parity_index.py`/`tools/parity_record.py` or a
  package under `tools/parity_ledger/`?" — **this decision is unresolved in the idea doc itself** and is
  this ticket's job to make, not inherit as already-decided.
- Companion doc gap: `idea_parity_ledger_sqlite_context_integration.md`'s own "Related material" list
  does not cite a `_review_claude` companion file. This investigation searched the full repo tree and
  `git log --all` for any file matching `*idea_parity_ledger_sqlite_context_integration_review_claude*`
  — **zero matches, no file, no git history.** The ticket prompt's reference to this companion doc points
  at something that does not exist anywhere in this repository. Recorded as a gap/open question below,
  not treated as a blocker (nothing in the ticket's Scope/AC depends on that specific file existing).

### `tools/agent-monitoring/build_index.py` — precedent lifecycle pattern (for comparison, not reuse)

Line ~181 equivalent (`build()`/`main()` per `stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/plan.md`
Step 2): `if db_path.exists(): db_path.unlink()` — unconditional delete-then-recreate on every rebuild.
This ticket's own Implementation Notes section already states this delete-before-build lifecycle must
**not** be copied by the future Phase 1/IMPORTER ticket, which needs "validated temporary build plus
atomic replacement" instead (confirmed independently: `TCK-20260731-PARITY-INDEX-IMPORTER`'s own scope
text requires "Build in a sibling temporary DB, validate integrity/schema/rows, close/fsync as
appropriate, then atomically replace the old DB. A failed build must preserve the last good DB and
YAML." — a materially stricter contract than `build_index.py`'s delete-then-build). Phase 0 (this
ticket) does not build a database at all; it only needs to **decide and record** the atomic-lifecycle
requirement as a v1 architecture decision so Phase 1/IMPORTER inherits it as settled, not re-litigated.

## Mechanics / Engine Constraints

None. This ticket is agent-infrastructure/tooling work (`tools/`, `docs/parity_ledger/` as a *process*
artifact, not simulation state) — no `docs/mechanics/` chapter or `docs/engine/` contract governs
parity-ledger tooling. The only "law" in scope is the parity-ledger entry schema itself
(`docs/parity_ledger/schema.json`, see the parsing-gap finding above) and this ticket's own explicit
Out-of-Scope guard against creating a database, changing YAML fields, or touching legacy tools/workflow
integration.

## Parity Ledger Overlap

This ticket does not implement or change any `src/` behavior, so it does not require updating any
parity-ledger entry's `status`/`v2_evidence` — it is meta/tooling work about the ledger, not a behavior
change the ledger tracks. No entry ID needs a status change as a result of this ticket.

Relevant existing entries that describe the ledger-tooling surface this ticket documents a baseline for
(informational only, none require edits):
- `INFRA-289`, `INFRA-290`, `INFRA-291` in `docs/parity_ledger/infrastructure.yaml` — document
  `tools/agent-monitoring/build_index.py`'s SQLite index precedent (`agent-monitoring-index/monitoring.db`),
  the closest prior art for "derived SQLite index over JSONL/YAML text source" this repo has shipped.
  Confirmed via grep; not modified by this ticket.
- No existing `INFRA-*` entry documents `tools/parity_ledger_scan.py` or
  `tools/gate_checks/parity_updater_static.py` themselves — both were delivered as workflow-determinism
  tooling (`TCK-20260705-WORKFLOW-PARITY-SKIP`, `TCK-20260705-GATE-DET-PARITY-UPDATER`) without a
  parity-ledger entry, consistent with those tickets' own Completion Summaries stating "no `src/` files
  were touched... no parity-ledger entries required updates."
- No P0 entries are at risk from this ticket (no `src/` change, no `v2_evidence` touched).

## Prior Work

- **`stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/`** — `investigation.md` is the source of the
  "16% of paths cited in 2+ subsystem files" finding and the `CANONICAL_LEDGER_FILES` 8-file precedent;
  `test_plan.md`/`plan.md` establish the `tools/gate_checks/` module convention (plain functions, no
  argparse/CLI, `_write_ledger`/`tmp_path` fixture pattern) this ticket's baseline-tooling decisions
  should be consistent with if/when Phase 1 picks a CLI/module shape.
- **`stored_artifacts/TCK-20260713-MONITORING-SQLITE-INDEX/`** — `plan.md`'s Deviations section is the
  single most relevant lifecycle lesson: a **literal Step 5 spec** (`is not None` value check) diverged
  from its own **stated intent** (key-presence check) and was only caught by live-data verification,
  silently dropping ~30,372 legitimate records before the fix. Direct precedent for this ticket's own
  "record v1 decisions... rather than assume" framing: Phase 0's decisions must be explicit enough that
  Phase 1/IMPORTER cannot repeat this class of literal-vs-intent gap. Also the direct precedent for the
  "delete-then-build is not the pattern to inherit" finding above (Anti-Drift Notes: "`(run_id, seq)` is
  not a safe unique key" — a parallel caution about assuming a derived index's uniqueness/rebuild
  invariants without checking real data first, directly relevant to Phase 0's "shard/ID rules" decision
  given `docs/parity_ledger/`'s own 0-duplicate-ID finding above, which should not be assumed to hold
  forever without a stated invariant).
- **`docs/REGISTRY.yaml`** query (`related_code_areas` overlap with `docs/parity_ledger/*`, or tags
  intersecting `parity`/`ai`) surfaced 94 candidate entries; the two above are the only ones with direct
  code/artifact overlap with this ticket's Related Code Areas. Others (e.g. `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK`,
  `TCK-20260711-DOC-STALENESS-GATE-CHECK`) reference `tools/gate_checks/parity_updater_static.py` only
  incidentally (as one of several files a doc-staleness/conformance check scans), not as a design
  precedent for this ticket's baseline/index-boundary work.

## Risks and Open Questions

1. **1,936 vs. 1,945 entry-count drift is real and dated.** The idea doc and this ticket's own AC #2 cite
   1,936 as "the historical snapshot." The live corpus is 1,945 today. This must be handled by treating
   1,936 as a historical comparison figure (idea-doc-vintage, 2026-07-31) and 1,945 as the current,
   authoritative baseline-manifest number — **not** by trying to reproduce 1,936, which would require
   deleting 9 real entries or misdating the manifest. This is a blocking interpretive question for AC #2
   if read literally ("Manifest records the historical 1,936-entry snapshot") — my read is that AC #2 is
   satisfied by recording *both* numbers with the drift explicit, not by making the manifest's live count
   equal 1,936. Flagging for Plan to confirm this reading rather than assuming it silently.
2. **`docs/parity_ledger/schema.json`'s duplicate-`if` parsing gap** (see Current Behavior) means any
   "schema coverage" claim in the baseline manifest must describe the schema *as it actually parses*, not
   as the source text visually appears to specify two independent conditional rules. This is worth
   recording as an explicit baseline-manifest fact (documented, not fixed) so Phase 1/IMPORTER's schema
   validation doesn't inherit a false assumption about what's enforced.
3. **Missing companion doc** (`idea_parity_ledger_sqlite_context_integration_review_claude.md`) does not
   exist anywhere in the repo or git history. Not a blocker per this ticket's own scope (nothing in
   Scope/AC names it as a required input), but should be recorded as a gap rather than silently ignored,
   in case a future phase's Related Docs list assumes it exists.
4. **CLI/module ownership is explicitly unresolved by the idea doc itself** (Open decision #6:
   `tools/parity_index.py`/`tools/parity_record.py` vs. a `tools/parity_ledger/` package). This is a
   genuine decision this ticket must make, not a pre-answered fact to record. Recommend Plan weigh:
   (a) `tools/gate_checks/parity_updater_static.py` precedent uses a flat `tools/gate_checks/` module,
   not a package; (b) `tools/agent-monitoring/build_index.py` precedent uses a `tools/agent-monitoring/`
   subdirectory rather than a flat top-level file, because the domain already had a subdirectory. Parity
   ledger tooling currently has no subdirectory (`parity_ledger_scan.py` and the schema/YAML files are
   flat under `tools/`/`docs/parity_ledger/` respectively) — a fresh `tools/parity_ledger/` package would
   be a new convention for this specific tool family, while a flat `tools/parity_index.py` following the
   existing `parity_ledger_scan.py` naming pattern requires no new directory. Both are legitimate; this
   is a Plan-phase decision, not something Investigation should assume an answer for.
5. **Duplicate-ID and shard/ID-rule invariants have never been formally declared.** This investigation
   found 0 duplicate IDs across all 9 shards today (empirically verified), and the schema's `id` pattern
   (`^[A-Z]+-[0-9]{3}$`) is enforced only per-entry, never cross-shard. Whether cross-shard uniqueness is
   a *law* (schema-enforced) or merely an *observed fact* (today's data happens to satisfy it) is exactly
   the kind of "shard/ID rules" decision this ticket's Scope calls out as needing to be recorded
   explicitly — Phase 1/IMPORTER's later "duplicate-ID checks" (its own Scope line) depends on Phase 0
   having stated this rule, not inferred it silently.

## Anti-Drift Hazards

- **Do not build any database, `.gitignore` entry, or Make target in this ticket** — explicitly Out of
  Scope; that's Phase 1/IMPORTER's job. The v1-decision artifact records *what* Phase 1 will build, never
  *builds* it.
- **Do not modify `tools/parity_ledger_scan.py` or `tools/gate_checks/parity_updater_static.py`** —
  explicitly Out of Scope ("Changing YAML fields, legacy tools..."). The 8-file `CANONICAL_LEDGER_FILES`
  exclusion of `faction.yaml` must be captured as a documented, versioned fixture (Scope item 2), not
  "fixed" or "corrected" — the legacy tools are deliberately frozen compatibility fixtures per this
  ticket's own Implementation Notes.
- **Do not silently normalize the 1,936-vs-1,945 discrepancy away.** Reproducing 1,936 in the new
  manifest as if unchanged, or updating the idea doc's own "1,936" prose without a separate decision to
  do so, would both violate this ticket's Out-of-Scope guard against source rewrites (the idea doc itself
  is not this ticket's Related Code Area to edit) and misrepresent the baseline's determinism claim.
- **Do not coerce or "repair" any entry missing `test_path`/`v2_evidence`.** 1,347 of the 1,945 entries
  (all `verified`/`divergent` status, which nominally require these fields per the schema's *intended*
  rule) lack a `test_path` — this is the exact "evidence-health gap, not a reason to make the entire
  corpus suddenly fail" the idea doc calls out explicitly. This ticket's job is to classify/count this
  gap in the baseline manifest, never to backfill, delete, or reclassify entries to make the count look
  cleaner.
- **Do not build or assume FTS5 is available** — the Scope requires *recording* the FTS5
  availability/fallback decision, not probing/implementing it. Any Phase-0 test that checks
  `sqlite3`'s FTS5 compile flag is verifying an environment fact for the *decision record*, not building
  index infrastructure.
- **Do not extend `CANONICAL_LEDGER_FILES` to 9 files.** All-shard coverage is Phase 1/IMPORTER's
  explicit acceptance criterion ("imports all nine source shards (including faction)"); Phase 0 only
  needs to capture what the legacy 8-file exclusion currently does (including a versioned `faction.yaml`
  fixture case) as a comparison baseline — not fix or extend it.
- **Do not touch `.claude/workflows/implement-ticket.js`, `.claude/agents/parity-updater.md`, or any
  context-assembly/workflow file** — explicitly Out of Scope ("does not do any workflow/context
  integration").
