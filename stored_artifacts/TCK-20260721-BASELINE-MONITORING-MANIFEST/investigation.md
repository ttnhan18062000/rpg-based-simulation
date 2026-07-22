---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-BASELINE-MONITORING-MANIFEST
artifact_type: investigation
tags: [agent-monitoring, data-quality]
---

# Investigation — TCK-20260721-BASELINE-MONITORING-MANIFEST

## Current Behavior

**No manifest tool exists yet.** `tools/agent-monitoring/` has no file named `manifest.py` or
similar, and `tests/fixtures/` has no subdirectory for agent-monitoring legacy shapes (only
`tests/fixtures/agent_replay/` and `tests/fixtures/lab_runs/` exist). This ticket's deliverables
are genuinely new, not a modification of existing code — confirmed via direct listing, not
grep-inferred.

### The three corpus files (measured directly, `ls -la` / `wc -l`, 2026-07-22)

| File | Bytes | Lines |
|---|---|---|
| `agent-monitoring/runs.jsonl` | 172,286 (~168 KiB) | 702 |
| `agent-monitoring/events.jsonl` | 1,017,335 (~994 KiB) | 3,642 |
| `agent-monitoring/tools.jsonl` | 18,069,849 (~17.2 MiB) | 65,023 |

`tools.jsonl` is the file the AC's streaming-read requirement targets.

### `validate.py`'s `load_jsonl` (the function this ticket's AC requires reusing)

`tools/agent-monitoring/validate.py:170-182`:

```python
def load_jsonl(path):
    if not path.exists():
        return []
    records = []
    for i, line in enumerate(path.read_text().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as e:
            print(f"WARNING: {path}:{i}: invalid JSON — {e}", file=sys.stderr)
    return records
```

This is a **full in-memory read** — `path.read_text()` loads the entire file into a single string
before `.splitlines()` ever runs, then every parsed record is kept in a `list` for the process
lifetime. This is the pattern the ticket's AC explicitly says the manifest tool must **not**
replicate for `tools.jsonl` (avoid full in-memory parse of ~18 MB). It is fine to reuse for
`runs.jsonl`/`events.jsonl` (168 KiB / 994 KiB — trivial), and reusing it there literally satisfies
"reuse validate.py's load_jsonl" for those two files. For `tools.jsonl`, a different (streaming)
code path is required — see "No streaming precedent" below, this is a genuine design gap the Plan
phase must close, not something this ticket can copy from elsewhere in the repo.

`load_jsonl` also tolerates malformed JSON lines gracefully (prints a warning, skips the line,
keeps parsing) — this "warn and continue" behavior is what the manifest tool's own "legacy-warning
count" field should likely build on, though the exact counting rule is undefined by the ticket (see
Risks below).

### No streaming/bounded read precedent anywhere in this codebase

Searched every `.jsonl`-touching module under `tools/`. **All four existing "load a corpus JSONL
file" implementations use the identical full-read pattern**, not a streaming one:

- `tools/agent-monitoring/validate.py:174` — `path.read_text().splitlines()`
- `tools/agent-monitoring/query.py:27` — `path.read_text().splitlines()`
- `tools/agent-monitoring/generate_retro.py:47` — `path.read_text().splitlines()`
- `tools/agent-monitoring/record_events.py:59` — `TOOLS_FILE.read_text().splitlines()`

None iterate a file object line-by-line (`for line in open(path)`), and none hash file content in
fixed-size chunks. **The Plan phase has no in-repo precedent to point to for the streaming
requirement — it must design this from stdlib primitives** (e.g. `with open(path, "rb") as f: for
line in f: ...` for line/JSON counting — file-object iteration is lazy per-line in Python, unlike
`.read_text().splitlines()` — and `hashlib.sha256()` updated via bounded `f.read(chunk_size)` calls
for the byte-hash, not `path.read_bytes()`).

### Precedent patterns worth reusing (both confirmed by direct read)

- **Fail-closed fixture validation** — `tools/agent_replay/fixture_envelope.py`'s `load_fixture()`
  (lines 46-86): raises `FixtureValidationError` naming the exact missing field on any missing/null
  required key, no default substitution, no log-and-continue. `docs/ai/replay_fixture_spec.md`'s
  "Fail-closed law" section frames this as a deliberate inversion of the repo's dominant fail-open
  monitoring-write convention — the same framing applies to this ticket's legacy-reader: reading a
  fixture that's supposed to represent a known legacy shape and silently misclassifying it would be
  worse than a loud failure.
- **Pre/post content-hash snapshot, dirty-tree-aware** —
  `tests/agent_replay/test_no_mutation_snapshot.py:37-97`. Two-branch design: if `git status
  --porcelain` is clean before, assert it's clean after; if the tree is already dirty (the common
  case in this actively-developed repo), fall back to a SHA-256 content hash of every watched file
  taken immediately before/after and assert those hashes match. This directly matches AC's
  "verified via hash comparison before and after" requirement and should be reused near-verbatim,
  scoped to `agent-monitoring/*.jsonl` instead of `tickets/` + `agent-monitoring/*.jsonl`.
- **Real-corpus-path guard** — `tests/tools/test_monitoring_writer_lockfile_candidate.py:28-35`'s
  `_assert_not_real_corpus()` helper: resolves a path and asserts `"agent-monitoring"` is not one of
  its relative parts, refusing to let a test write anywhere under the real corpus directory. Useful
  as an anti-drift guard for this ticket's own fixture-corpus tests (fixtures under `tests/fixtures/`
  must never be confused with, or accidentally point at, the real `agent-monitoring/` directory).

## Mechanics / Engine Constraints

N/A. This ticket touches agent-tooling observability infrastructure (`tools/agent-monitoring/`,
`agent-monitoring/*.jsonl`), not simulation mechanics. No chapter of `docs/mechanics/` or contract
in `docs/engine/` governs this area.

## Parity Ledger Overlap

**None.** Searched all `docs/parity_ledger/*.yaml` for `monitoring`/`jsonl`/`manifest` — every hit
is unrelated: `docs/parity_ledger/infrastructure.yaml`'s "Monitoring stack checks do not silently
pass with empty data" entries concern the simulation's own health-monitor/observability subsystem
(`src/observability/`), not `agent-monitoring/` tooling; other `manifest` hits are
`CertificationHarness`'s `manifest_snapshot.json`, `RunManifest.world_id`, `CampaignManifest`, and
replay-manifest atomicity — all simulation-domain artifacts, unrelated to this ticket's scope. No
parity ledger entry needs updating as part of this ticket, and none should be added — the parity
ledger tracks Mechanics Bible/engine-contract semantic parity, not agent-tooling infrastructure.

## Prior Work

Queried `docs/REGISTRY.yaml` for entries whose `tags` include `agent-monitoring` (58 matches
total; the ticket's own `related_code_areas` don't yet exist as files to overlap on, since this is
greenfield tooling). Most relevant:

- **`stored_artifacts/TCK-20260705-MONITORING-RUNID-JOIN/investigation.md`** — the exhaustive audit
  (126 incomplete-run/zero-event records, 107/107 confirmed genuinely completed) that is the
  evidentiary basis for `docs/agent-monitoring/schema.md`'s "Known Limitations" section this ticket
  fixtures against. Cited directly by schema.md as "Full evidence."
- **`TCK-20260705-MONITORING-VALIDATE-SCHEMA-GAP`** — prior work hardening `validate.py`'s
  workflow/`final_status` field-gap handling; same read-side-absorbs-variance philosophy this ticket
  extends into a dedicated fixture corpus.
- **`TCK-20260716-MONITORING-TOOLS-JSONL-WRITE-LOCK`** — added the `fcntl.flock` write-lock to
  `post_tool_hook.py` after an observed unparseable interleaved line; establishes precedent that
  malformed lines in `tools.jsonl` are a real, previously-observed failure mode, not hypothetical.
- **`TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`** — added `compute_drift_report` /
  vocabulary single-sourcing to `validate.py`; `tests/tools/test_validate_agent_monitoring.py`
  (read in full) shows the established test style for this module: plain-dict fixtures, no file
  I/O, pure-function testing — the manifest tool's own unit tests should follow this style where
  they test pure logic (e.g. shape classification), reserving actual file I/O for a small number of
  integration-style tests against real fixture files.
- **`TCK-20260721-CODEX-REPLAY-PROOF`** (done) — sibling ticket in the same epic that established
  the `tests/fixtures/*.yaml` + fail-closed loader pattern (`fixture_envelope.py`) this ticket's
  own `tests/fixtures/` corpus and legacy-reader should mirror stylistically, even though the data
  shape is different (replay envelopes vs. legacy JSONL record shapes).
- **`TCK-20260721-MONITORING-WRITER-DECISION`** (done) — already produced the legacy-shape
  inventory this ticket's fixture corpus must match field-for-field (`docs/ai/monitoring_writer_decision.md`
  Section 1), and is explicit that it "decides and evidences... does not implement" — this ticket is
  the first implementation consumer of that inventory.
- **`docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md`**
  (Phase 0, lines 137-154) — names this exact deliverable ("Create the read-only monitoring
  baseline manifest and legacy-reader fixture corpus covering each known historical schema
  generation... Add tests asserting current Claude records remain readable before and after the
  new reader is introduced") almost verbatim as this ticket's scope, confirming this ticket
  correctly operationalizes that plan line and is not duplicate/orphaned scope.

No stored `plan.md` exists yet for producing a manifest tool specifically — this is the first
ticket to build one.

## Risks and Open Questions

1. **Real historical data has far more than 6 distinct shapes.** A direct classification pass over
   all 702 `runs.jsonl` records (not a sample) found the 6 documented shapes plus **~25 additional,
   undocumented ad hoc key-sets** (e.g. `{ticket_id, phase, seq, status, agent}` with no
   `run_id`-adjacent timestamp field at all; `{gate_result, notes, duration_s}` variants; a raw UUID
   used as `run_id` instead of a ticket ID). The ticket's own AC explicitly scopes the fixture
   corpus to "all 6 documented legacy shapes... as enumerated in `docs/agent-monitoring/schema.md`"
   — this is consistent with the AC as written, but the Plan phase should not be tempted to expand
   fixture coverage to the full undocumented tail; that is out of this ticket's stated scope and
   would need its own audit (like `TCK-20260705-MONITORING-RUNID-JOIN`'s) to do responsibly rather
   than fixturing ad hoc.
2. **Reproducibility (AC2: byte-identical output on re-run) constrains the manifest record schema.**
   If the manifest tool's own output includes any field that varies between runs against unchanged
   input — most obviously a "generated at" wall-clock timestamp, a common inventory-tool convention
   — AC2 cannot hold literally. The Plan phase must either omit any such field from the manifest
   record entirely, or explicitly exclude it from the reproducibility comparison (e.g. compare all
   fields except one named exception) — this is not decided anywhere in the ticket and needs a
   Plan-phase call.
3. **Streaming/bounded read has no in-repo precedent** (see Current Behavior) — this is new design,
   not a reuse. The Plan phase should specify: line/JSON-record counting via lazy file-object
   iteration (`for line in f`), and SHA-256 hashing via bounded `f.read(chunk_size)` calls — both
   stdlib-only, no new dependency, consistent with this repo's existing no-new-dependency norm (see
   `docs/ai/monitoring_writer_decision.md` Section 2's `secrets`/`time`-only precedent).
4. **"Legacy-warning count" is not a field `validate.py` currently computes per-file** — it has a
   global `warnings` list (incomplete-run / no-events / missing-working-log-entry checks), not a
   per-record-shape classification. This ticket's manifest tool needs its own definition of what
   counts as a "legacy warning" for a given record (most naturally: matched one of the 6 documented
   shapes, or failed the current schema's required-field check) — undefined by the ticket, needs a
   Plan-phase decision.
5. **Manifest tool output location is unspecified.** The AC says "one record per JSONL file,
   reproducible on re-run" but never says where the manifest itself is written. Given
   `agent-monitoring/` is append-only historical JSONL data (not a place for a new derived-artifact
   file) and this ticket is explicitly read-only, the natural options are: print to stdout only, or
   write to a path outside `agent-monitoring/` (e.g. `reports/` or a `stored_artifacts/` path). Not
   decided — Plan phase must choose, and the "zero git diff on `agent-monitoring/*.jsonl`" AC
   confirms the manifest itself must never land inside that directory.
6. **Fixture provenance: synthetic vs. copied-from-real.** The ticket doesn't say whether each
   fixture file under `tests/fixtures/` should be a verbatim copy of one real line pulled from
   `agent-monitoring/*.jsonl` (this investigation found and quotes one concrete real example for
   each of the 6 shapes, below) or a hand-authored synthetic record matching the shape. Copying real
   lines verbatim is recommended — it guarantees fidelity to what actually exists in the corpus and
   avoids inventing a 7th, never-observed shape by accident — but this is a Plan-phase call, not
   assumed here.
7. `TCK-20260623-TYPE-CHECKER`'s shape does not satisfy any of `validate.py`'s
   `LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` checks (no `end_ts`, no
   `final_status`, no `status` key at all — uses `"outcome":"success"` instead). It is
   `validate.py`'s one accepted, permanently-documented residual warning (schema.md: "Final residual
   after the fix: exactly 1"). The manifest/legacy-reader must classify it correctly as this named
   exception, not as an error or an unrecognized/`other` bucket.

## Anti-Drift Hazards

- **Do not modify `validate.py`, `record_run.py`, `record_events.py`, or `post_tool_hook.py`.**
  Explicitly Out of Scope. The manifest tool must be a new, separate module that only *reads*
  `agent-monitoring/*.jsonl` (reusing `load_jsonl` for the two small files is fine; writing to any
  of those files, or to any file the production writers touch, is not).
- **Do not "fix" or backfill any legacy record.** `docs/agent-monitoring/schema.md`'s Known
  Limitations section is explicit: "Do not 'fix' any of this by backfilling `runs.jsonl`... the fix
  lives entirely in `validate.py`'s read-side interpretation." This ticket's manifest/legacy-reader
  must follow the same read-side-only philosophy — classify, never rewrite.
- **Do not let the manifest tool's SHA-256/hash proof become a full second in-memory parse of
  `tools.jsonl`** — computing the file hash and counting/validating JSON lines are two different
  operations; both must independently avoid loading the whole ~18 MB file into one Python object.
  It would be easy to accidentally satisfy the "streaming" requirement for parsing while still
  calling `path.read_bytes()` for the hash (or vice versa) — both paths need the bounded-read
  treatment.
- **Do not treat `FOLDER-*`/`EPIC-*` records with `final_status` present as a legacy shape.** This
  investigation found two distinct `FOLDER-*`/`EPIC-*` populations in real data: 65 records already
  matching the *current* schema (`start_ts`/`end_ts`/`workflow`/`final_status`/`agent_count`, just
  with a `FOLDER-`/`EPIC-` `run_id`), and 7 records matching the genuinely legacy "bare `status`
  field" shape (e.g. `{"run_id":"FOLDER-phase40-44-cleanup-authoring","folder":"...","status":"DONE","ts":"...","ticket_count":15,...}`,
  no `final_status`/`start_ts`/`end_ts` at all). Only the second population is "Legacy shape 5" per
  schema.md — the fixture for shape 5 must use the bare-`status` example, not the current-schema one,
  or the fixture would not actually exercise legacy-path handling.
- **Do not conflate `tools.jsonl`'s two distinct null-gap causes.** `run_id`/`seq` both `null` means
  "interactive tool call outside any workflow run" (by design, not legacy) — e.g. the very first
  line of the real file. `phase`/`agent` absent *while* `run_id`/`seq` are present (found at line
  278: `run_id="TCK-20260614-CERT-SAFE-SERIAL"`, `seq=2`, no `phase`/`agent` keys) means "record
  predates `TCK-20260719-LIVE-PHASE-AGENT-LABEL`" — a genuinely different, time-based null-gap
  cause. A legacy-reader test that only fixtures one of these two would silently miss the other.
- **Keep fixture files clearly out-of-band from the real corpus.** Reuse the
  `_assert_not_real_corpus`-style guard so a fixture-corpus test can never accidentally read or
  write `agent-monitoring/*.jsonl` directly instead of its intended `tests/fixtures/` copy.
