---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-DRIFT-REPAIR
artifact_type: investigation
tags: [data-quality, agent-monitoring, observability]
---

# Investigation — TCK-20260718-STATUS-DRIFT-REPAIR

This extends the Scope-phase `ticket-scoper`'s investigation.md (preserved above the line in spirit —
all of its findings were independently re-verified below and confirmed correct; nothing it found was
discarded). New material added by this pass: the exact 71-file list inlined, raw JSONL line evidence
for the write-safety design, an exemption-mechanism recommendation, and one drift-format finding the
scoping pass did not surface (see Risks and Open Questions).

## Current Behavior

**Part A — `tickets/done/*.md` body `## Status` drift.**

Independently re-ran the scan (same regex the scoper used, `^## Status\s*\n+\s*(\S+)`, multiline) on
2026-07-18 against the live `tickets/done/` tree:

```
python3 -c "
import re
from pathlib import Path
for f in sorted(Path('tickets/done').glob('*.md')):
    text = f.read_text(errors='ignore')
    m = re.search(r'^## Status\s*\n+\s*(\S+)', text, re.MULTILINE)
    if m and m.group(1).upper() != 'DONE':
        print(f.name, m.group(1))
"
```

Result: **83 total**, split exactly as the scoper reported:
- 7 epic-tier (`EPIC_SCOPED`/`SCOPED`) — correct terminal value, not drift.
- 5 pre-TCK-naming legacy `resource_v2_*.md` files — out of scope per project precedent.
- **71 genuine drift files** — confirmed by independent re-derivation, count and file set match the
  scoper's list byte-for-byte. Full authoritative list (alphabetical, as scanned 2026-07-18):

```
TCK-20260331-RUNTIME-INTEGRITY.md                              INPROGRESS
TCK-20260406-PHASE0.md                                         INPROGRESS
TCK-20260407-PHASE0-CONTINUE.md                                INPROGRESS
TCK-20260408-PH3-PASS2-SPAWN-ANCHOR.md                         INPROGRESS
TCK-20260409-PH4-STG2-SUCCESSION-LOGIC.md                      INPROGRESS
TCK-20260410-PH6-ENGINE-INTEGRATION.md                         INPROGRESS
TCK-20260410-PHASE-2-ALIGNMENT.md                               INPROGRESS
TCK-20260415-WS-CLEANUP.md                                     OPEN
TCK-20260419-MB-TASK1-FREEZE-LAW.md                             INPROGRESS
TCK-20260419-MB-TASK2-REAL-SIGNALS.md                            OPEN
TCK-20260419-MB-TASK3-GOVERNOR-HARDENING.md                     OPEN
TCK-20260419-MB-TASK4-ADAPTIVE-POOL.md                           OPEN
TCK-20260419-MD-TASK1-FREEZE-CONCURRENCY-CONTRACT.md            INPROGRESS
TCK-20260419-MD-TASK2-HARDEN-PROTOCOL-AND-COMMIT-LAW.md         INPROGRESS
TCK-20260419-MD-TASK3-HARDEN-FALLBACK-AND-BOUNDS.md              OPEN
TCK-20260419-V2-CONSOLIDATION-FINAL-HARDENING.md                INPROGRESS
TCK-20260420-CORE-MOVEMENT-SLICE.md                              OPEN
TCK-20260420-INTERACT-LOOT.md                                    OPEN
TCK-20260420-INTERACT-PRESS.md                                  INPROGRESS
TCK-20260420-PERF-FOUNDATION.md                                 INPROGRESS
TCK-20260420-TOWN-LOOP.md                                       INPROGRESS
TCK-20260421-STRATEGIC-INTEL.md                                 INPROGRESS
TCK-20260422-PH6-M7-M8-HARDENING.md                              INPROGRESS
TCK-20260422-PH7-M2-SUBSTRATE-CLOSURE.md                         OPEN
TCK-20260422-PH7-M3-KERNEL-STABILITY.md                          OPEN
TCK-20260422-PH7-M4-SNAPSHOT-INTEGRITY.md                        OPEN
TCK-20260422-PH7-M5-DETERMINISTIC-WORLD-GEN.md                   OPEN
TCK-20260422-PH7-M6-EXIT-PACKAGE.md                               OPEN
TCK-20260422-RESOURCE-PH7-M2-T2-ACTION-PROPOSAL-MODEL.md         INPROGRESS
TCK-20260424-PH10-M6-RATIFICATION.md                             INPROGRESS
TCK-20260424-PH11-M2-PRESERVED-PROOF.md                           OPEN
TCK-20260424-PH11-M3-NON-PRESERVED-RATIFICATION.md                OPEN
TCK-20260424-PH11-M5-FINAL-VERDICT.md                             OPEN
TCK-20260424-PH11-M6-EXIT-PACKAGE.md                              OPEN
TCK-20260424-PH2-M1-RPG-RECOVERY.md                               OPEN
TCK-20260424-PH2-M2-COGNITIVE-HARDENING.md                        OPEN
TCK-20260424-PH2-M3-REGIONAL-SOVEREIGNTY.md                       OPEN
TCK-20260424-PH2-M4-SOCIAL-CONTINUITY.md                          OPEN
TCK-20260425-PH4-TACTICAL-AI.md                                  INPROGRESS
TCK-20260426-ARENA-QUESTS.md                                     INPROGRESS
TCK-20260429-PH0-PROTOCOL-VALIDATOR.md                           INPROGRESS
TCK-20260501-E5.0-CHECKLIST-CLOSURE.md                            OPEN
TCK-20260501-PH8-DURABILITY-CRAFTING.md                          INPROGRESS
TCK-20260501-RPG-CORE-MIGRATION.md                               INPROGRESS
TCK-20260503-HARDEN-DOMAIN5.md                                   INPROGRESS
TCK-20260503-INFRA-LEDGER-VALIDATOR.md                           INPROGRESS
TCK-20260503-SOCIAL-COORDINATION.md                               OPEN
TCK-20260506-INVENTORY-TEST-STABILIZATION.md                     INPROGRESS
TCK-20260510-REFACTOR-PIPELINE-DECOMPOSITION-DETAILED.md         INPROGRESS
TCK-20260510-REFACTOR-SUBSYSTEM-TEST-MIGRATION.md                INPROGRESS
TCK-20260510-REFACTOR-TEST-STRUCTURE-INIT.md                     INPROGRESS
TCK-20260512-PERF-STAGGERED-SCHEDULER.md                          OPEN
TCK-20260513-PERF-CADENCE-CORE.md                                 OPEN
TCK-20260513-PERF-CADENCE-INTEGRATION.md                          OPEN
TCK-20260514-DOCS-REORG.md                                       INPROGRESS
TCK-20260514-PERF-PROFILING.md                                   INPROGRESS
TCK-20260521-SIM-OBS-M42.md                                      INPROGRESS
TCK-20260528-COG-PHASE3-DECISION.md                               INPROGRESS
TCK-20260528-PHASE10-OPTIMIZATION.md                             INPROGRESS
TCK-20260529-OBS-PHASE23-BEHAVIOR-TIMELINE-EPISODES.md           INPROGRESS
TCK-20260529-OBS-PHASE24-BEHAVIOR-METRICS.md                     INPROGRESS
TCK-20260529-OBS-PHASE25-BEHAVIOR-PATTERNS-INSIGHTS.md           INPROGRESS
TCK-20260610-ENUM-MIGRATION-REPORT.md                             OPEN
TCK-20260610-MOTIVATION-PRESSURE-RESOLVER.md                      OPEN
TCK-20260610-SCENARIO-CATALOG-MATRIX.md                           OPEN
TCK-20260610-SCENARIO-WORLD-VALIDATION.md                         OPEN
TCK-20260614-WORLDDAT-COMPOSE.md                                 INPROGRESS
TCK-20260619-E21-RESOURCE-ECOLOGY.md                              OPEN
TCK-20260619-E22-DECISION-EXPLAIN.md                              OPEN
TCK-20260619-E23-QUEST-GENERATION.md                              OPEN
TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST.md          OPEN
```
(71 lines — verified via `wc -l` on the script's output.)

The 12 excluded files (verified by re-matching against the same 83-file result set):
- 7 epic-tier: `TCK-20260619-E13-CONTENT-FOUNDATION.md` (`EPIC_SCOPED`), `TCK-20260619-E53A-FACTION-AGENT.md`
  (`EPIC_SCOPED`), `TCK-20260619-E53B-DIPLOMACY.md` (`EPIC_SCOPED`), `TCK-20260619-E53C-WAR.md`
  (`EPIC_SCOPED`), `TCK-20260619-E53D-HISTORY.md` (`EPIC_SCOPED`), `TCK-20260619-E61-PROGRESSION.md`
  (`EPIC_SCOPED`), `TCK-20260628-E-RESOURCE-ECOLOGY.md` (`SCOPED`).
- 5 legacy-naming: `resource_v2_flanking_geometry_e5_9.md`, `resource_v2_governor_reactivity_e6_0.md`,
  `resource_v2_phantom_leader_e5_7.md`, `resource_v2_strategic_phase_order_e6_1.md`,
  `resource_v2_terrain_weight_e5_8.md` (all currently read `OPEN`; frontmatter `ticket_id` for these is
  the filename stem itself, e.g. `resource_v2_flanking_geometry_e5_9`, not `TCK-`-prefixed — confirmed
  by direct read, not just filename inference).

Confirmed one epic file's structure directly (`TCK-20260619-E13-CONTENT-FOUNDATION.md`): YAML
frontmatter has `phase: epic_scoped`; body `## Tier` section reads `epic`; body `## Status` reads
`EPIC_SCOPED`. All three signals agree — any of them could drive an exemption rule (see Part C design
below).

Root cause: predates `implement-ticket.js`'s current Finalize phase, which now explicitly sets
`## Status` to `DONE` on every close. Most recent stale file: `TCK-20260711-SIMQ-TRACEABILITY-PATH-
INTEGRATION-TEST.md` (2026-07-11), consistent with the Finalize fix landing shortly after.

**Part B — `agent-monitoring/runs.jsonl` lowercase `final_status`.**

Independently re-scanned all 641 lines of `agent-monitoring/runs.jsonl`, parsing each as JSON and
checking `final_status != final_status.upper()`. Found exactly 7 matches, identical run_ids and
line offsets to the scoper's report:

| run_id | current value | 0-indexed line # |
|---|---|---|
| `TCK-20260610-WORKER-SINGLETON-GUARD` | `"done"` | 73 |
| `run-e51d-renderer-20260622` | `"success"` | 247 |
| `run-e51e-rest-api-20260622` | `"success"` | 248 |
| `TCK-20260619-E52A-COHORT-MODEL-run1` | `"success"` | 249 |
| `TCK-20260619-E52B-MIGRATION-run1` | `"success"` | 250 |
| `TCK-20260619-E52C-AGE-ADVANCEMENT-001` | `"success"` | 251 |
| `TCK-20260619-E52D-DENSITY-SIGNAL-001` | `"success"` | 252 |

Spot-checked 3 of the 7 against their corresponding `tickets/done/*.md` `## Status` section directly
(not trusting the scoper's cross-check claim):

```
TCK-20260610-WORKER-SINGLETON-GUARD.md  -> ## Status\nDONE
TCK-20260619-E52A-COHORT-MODEL.md       -> ## Status\nDONE
TCK-20260619-E51D-RENDERER.md           -> ## Status\nDONE
```

All 3 confirm `DONE` — consistent with the scoper's claim that `DONE` is the correct target for all 7
(the other 4 were not independently re-checked in this pass but there is no structural reason to expect
a different result; the ticket's own AC requires a JSON-parsing scan post-fix regardless, which will
catch any surprise).

Raw line content for the 7 records (`repr()` of exact bytes, compact JSON, no spaces — matches
`record_run.py`'s `json.dumps(record, separators=(",", ":"))` serialization convention):

```
73:  {"run_id":"TCK-20260610-WORKER-SINGLETON-GUARD",...,"final_status":"done",...}
247: {"run_id":"run-e51d-renderer-20260622",...,"final_status":"success",...}
248: {"run_id":"run-e51e-rest-api-20260622",...,"final_status":"success",...}
249: {"run_id":"TCK-20260619-E52A-COHORT-MODEL-run1",...,"final_status":"success",...}
250: {"run_id":"TCK-20260619-E52B-MIGRATION-run1",...,"final_status":"success",...}
251: {"run_id":"TCK-20260619-E52C-AGE-ADVANCEMENT-001",...,"final_status":"success",...}
252: {"run_id":"TCK-20260619-E52D-DENSITY-SIGNAL-001",...,"final_status":"success",...}
```

Each line has exactly one occurrence of the substring `"final_status":"done"` or
`"final_status":"success"` — confirmed by direct grep-equivalent inspection, not assumed. This makes a
**line-scoped string substitution** (not a full `json.loads`/`json.dumps` round trip) the safest write
approach: it trivially preserves key order, spacing, and every other field's byte content, and sidesteps
the open question about whether any downstream tool depends on JSON key order (moot if the line's bytes
are otherwise untouched). Recommended implementation: read all lines; for each of the 7 target 0-indexed
line numbers, apply `line.replace('"final_status":"done"', '"final_status":"DONE"')` (or the `success`
variant) exactly once; write all lines back via a temp-file-plus-atomic-rename to avoid partial-write
corruption; assert the replaced substring count was exactly 1 per target line (fail loudly if 0 or >1,
which would indicate the byte layout assumption above no longer holds — e.g. a future record_run.py
change adds spaces to serialization).

Consumer of this data — `dashboard-frontend/src/components/GanttBar.tsx` lines 4-16:

```ts
export function classifyFinalStatus(status: string): StatusBucket {
  if (status === 'DONE') {
    return 'done'
  }
  if (status.endsWith('_BLOCKED') || status.endsWith('_FAILED') || status === 'CONFLICTS_DETECTED') {
    return 'failed'
  }
  return 'neutral'
}
```

Confirmed: exact-match on the literal `'DONE'` (line 9), no case-folding, no `LEGACY_TERMINAL_STATUS_
VALUES`-style tolerance. `'done'`/`'success'` both fall through to `'neutral'` (line 15) → gray bucket.
`dashboard-frontend/src/test/GanttBar.test.tsx` only ever constructs fixtures with `final_status:
'DONE'` (lines 18, 95) — there is no existing test that exercises the lowercase-input bug, so nothing
in the frontend suite currently guards against this class of drift recurring on the frontend side; the
regression check belongs entirely in the Python/data layer (Part C), not the frontend.

## Existing Tooling Surveyed

Independently listed and grep'd all 12 `.py` files in `tools/agent-monitoring/` (`cost_proxy.py`,
`epic_scope_orphan_check.py`, `epic_staleness_check.py`, `generate_retro.py`, `post_tool_hook.py`,
`pre_tool_hook.py`, `query.py`, `record_events.py`, `record_run.py`, `retro_nudge_hook.py`,
`scope_ticket_relocate.py`, `validate.py`, `vocabulary.py` — 13 total, scoper said 12; the extra one is
`retro_nudge_hook.py`, immaterial to the count's conclusion). Confirmed: `record_run.py`'s only file-
write is `with open(RUNS_FILE, "a") as f: f.write(...)` (append-only, line 65-66) — no rewrite/seek/
truncate anywhere in the directory. `vocabulary.py` has zero references to `final_status` or
`LEGACY_TERMINAL_STATUS_VALUES` (that constant lives solely in `validate.py`, lines 37-41). **No
existing safe rewrite-in-place helper for `runs.jsonl` exists anywhere in this directory — scoper's
claim independently confirmed.**

`tools/agent-monitoring/validate.py` structure (full file read, 258 lines): `_record_is_complete()`
(line 44) checks `LEGACY_TERMINAL_STATUS_VALUES` membership for *completeness* (has the run terminated,
regardless of casing) — this is deliberately case-sensitive-tolerant parser leniency, unrelated to and
unaffected by this ticket's casing-normalization fix. `compute_drift_report()` (line 61) and
`compute_tool_count_drift_report()` (line 124) are the two existing "read-only report, never gates"
functions — closest in shape to what Part C's new check needs, but neither currently scans
`tickets/done/*.md` at all (that's out of `validate.py`'s current concern entirely — it only reads
`runs.jsonl`/`events.jsonl`/`tools.jsonl`/`working_log.csv`).

`tools/gate_checks/` — confirmed 8 files. Read `doc_staleness_check.py` (65 lines) and
`workflow_meta_conformance.py` (full) in detail. Both follow an identical shape: a docstring citing the
originating ticket and the retro/audit finding that motivated it, one aggregate `check_*()` function
returning `List[dict]` (each dict: `{"status": "PASS"|"FAIL", "evidence": "..."}`), a `MARKER:` +
`json.dumps(result)` stdout contract in `__main__`, and an explicit statement that the check ships
unwired (a future ticket decides where/whether to call it from a workflow or Makefile target). This is
the closest, most directly reusable pattern for Part C.

## Mechanics / Engine Constraints

Not applicable. This is agent-tooling/process data hygiene (ticket lifecycle metadata and monitoring
telemetry), not simulation mechanics. No `docs/mechanics/` chapter or `docs/engine/` contract governs
`## Status` body text or `runs.jsonl` field casing.

## Parity Ledger Overlap

None. Searched all `docs/parity_ledger/*.yaml` for `final_status`, `## Status`, `runs.jsonl`, "ticket
status" — the only hit is `docs/parity_ledger/infrastructure.yaml` around line 4486-4494, a `verified`
P2 entry about the agent-ops dashboard's ticket-to-run join logic reusing `validate.py`'s tolerant
`load_jsonl` + legacy allowlists. It documents *join* behavior (all matching `runs.jsonl` rows per
`ticket_id`), not `final_status` value casing — no overlap with this ticket's scope, confirmed by direct
read of the surrounding YAML block. No parity entry needs updating as a result of this ticket. No new
entry needs adding: this ticket does not change any simulation-facing behavior, only historical data
values and adds a new tooling check.

## Prior Work

- `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` (done, standard, P2) — precedent for a `--check` mode added
  *to an existing generator script* (`tools/generate_registry.py --check`), diffing live-regenerated
  output against on-disk state, wired into a CI job. This is a different structural pattern than
  `gate_checks/*.py`'s standalone-script-with-MARKER-JSON-output pattern — it extends a script that
  already has a primary (non-check) responsibility. Not the best-fit precedent for Part C, since there
  is no single existing "generator" this check would naturally extend (unlike REGISTRY.yaml's
  generate-then-diff shape, `## Status`/`final_status` drift has no generation step to diff against —
  it is a pure corpus scan).
- `TCK-20260708-TAG-SKILL-MAPPING-DRIFT-CHECK` (done, standard, P1) — precedent for "automated
  consistency check for hand-duplicated/drift-prone data" (4 hand-maintained copies of a tag→skill
  mapping table). Read this ticket's header; did not need to read its full stored artifacts since the
  header alone confirms the shape match (standard tier, P2-adjacent priority, chore type, drift-check
  scope) the current ticket's scoper already cited correctly.
- `tools/gate_checks/doc_staleness_check.py` and `workflow_meta_conformance.py` — both read in full;
  both are the strongest structural precedent for Part C specifically (see Existing Tooling Surveyed
  above). Both ship deliberately unwired from any workflow/Makefile — a pattern this ticket's Part C
  should also default to unless the implementer has a strong reason to wire it (the ticket's own scope
  language treats Makefile wiring as optional/"following existing precedent," consistent with this).

## Risks and Open Questions

- **New finding, not in the scoper's investigation**: a third `## Status` body format exists in the
  very old ticket corpus — same-line, colon-suffixed (`## Status: DONE` / `## Status: INPROGRESS` on
  one line, no following newline before the value), distinct from both the two-line format the 83/71/12
  baseline scan targets and the `resource_v2_*` legacy format. Found via a broader regex sweep
  (`^## Status\b(.*)$`) during this investigation pass: 12 files use this same-line format, of which 6
  currently read a non-`DONE` value (`TCK-20260322-BWS_PROTO.md`, `TCK-20260401-FINAL-CONVERGENCE.md`,
  `TCK-20260401-FINAL-NON-PARTIAL-TASKS.md`, `TCK-20260403-FINAL-CONVERGENCE.md`,
  `TCK-20260405-SKILL-SCALING.md`, `TCK-20260407-PH0-FIX.md` — all `INPROGRESS`) and 6 already read
  `DONE` (not drift). **None of these 6 drift files are among the 83/71/12 baseline** — the scan
  script's regex `^## Status\s*\n+\s*(\S+)` requires the value on a line *after* `## Status`, so a
  same-line `: INPROGRESS` never matches and the file is silently skipped by the exact same logic that
  produced the approved 71-file scope. This is not a bug in the ticket's scoping — the 71-file figure is
  internally consistent and correctly derived — but it is a **hazard for Part C**: if the new regression
  check's status-extraction regex is written more permissively than the baseline scan (e.g. to also
  catch same-line colon values, which would be a reasonable-looking improvement), it will newly flag
  these 6 files as drift. That would make the check fail against the "clean" post-fix corpus (violating
  the AC "regression check exits 0 against the post-fix `tickets/done/` + `runs.jsonl` corpus"), since
  fixing them is explicitly out of this ticket's approved scope (not listed in Scope item 1's 71-file
  set, not in Out of Scope's exception list either — they are simply unaddressed). **Decision needed
  from planner/implementer**: Part C's checker must use the *exact same* extraction regex as the
  baseline scan (`^## Status\s*\n+\s*(\S+)`, multiline) to stay scope-consistent, deliberately leaving
  same-line-format files undetected — this should be documented in the checker's docstring as an
  intentional limitation (candidate for a future ticket), not silently reproduced as an accident.
- Confirmed assumption: `"DONE"` is correct for all 7 `runs.jsonl` records (3 of 7 independently
  re-verified against source `tickets/done/*.md` files in this pass; all 3 confirm). Low residual risk
  on the remaining 4 (`run-e51e-rest-api-20260622`, `TCK-20260619-E52B-MIGRATION-run1`,
  `TCK-20260619-E52C-AGE-ADVANCEMENT-001`, `TCK-20260619-E52D-DENSITY-SIGNAL-001`) — implementer should
  still do the full 7-of-7 cross-check the AC already requires (not just trust this sample) before
  writing.
- Open question carried over from scoping, still unresolved: does any downstream tool depend on
  `runs.jsonl` JSON key order within a line? Not found either way. Resolved in practice by the
  line-scoped string-substitution write approach recommended above, which never touches key order —
  this sidesteps the question rather than answering it, which is an acceptable resolution since it
  removes the risk entirely rather than requiring a definitive answer.
- Part C design choice (new script vs. extending `validate.py`) is still open — see recommendation in
  Anti-Drift Hazards / Prior Work: a new `tools/gate_checks/status_drift_check.py` fits the existing
  `gate_checks/*.py` MARKER-JSON pattern more closely than extending `validate.py`'s
  WARNING/ERROR-prints-plus-exit-code contract, and keeps `validate.py`'s existing runs/events/tools/
  working_log-only concern from growing a third, structurally different scan (ticket body text) bolted
  on. This is a recommendation, not a mandate — flagged for planner/implementer judgment as the ticket
  itself invites.
- The duplicated `## Tier\n## Tier` heading glitch (Scope item 4, opportunistic-only) was not
  independently re-verified in this pass (out of the explicit read list); no new information to add
  beyond the ticket's own note.

## Anti-Drift Hazards

- **Regex parity hazard** (see Risks above): Part C's ticket-status scan must reuse
  `^## Status\s*\n+\s*(\S+)` verbatim, not a "cleaner" or more general pattern — a seemingly-correct
  improvement here silently expands scope and breaks the clean-corpus AC.
- **Do not let the exemption list rot into two sources of truth.** If Part C hardcodes the 7 epic-tier
  filenames + 5 legacy filenames as literal string lists (mirroring how this ticket's own Scope/Out-of-
  Scope sections enumerate them), every future epic closure or legacy backfill requires updating the
  checker too, or it starts producing false positives. Prefer a **structural** exemption: value-based
  for epic tier (`## Status` value in `{"EPIC_SCOPED", "SCOPED"}` — durable, self-maintaining, and
  already how `TCK-20260619-E13-CONTENT-FOUNDATION.md` distinguishes itself via 3 agreeing signals:
  frontmatter `phase: epic_scoped`, body `## Tier` = `epic`, body `## Status` = `EPIC_SCOPED`) and
  naming-pattern-based for legacy files (filename does not start with `TCK-` — matches all 5
  `resource_v2_*.md` files structurally, and their frontmatter `ticket_id` field independently confirms
  the same non-`TCK-` prefix, so either the filename or the frontmatter field works as the signal).
  This is more durable than a literal allowlist and was the scoper's own stated preference in plan.md
  Step 4 — confirmed here as the right call.
- **Do not touch `LEGACY_TERMINAL_STATUS_VALUES` in `validate.py`.** It is deliberately tolerant of
  lowercase/legacy values for *completeness* checking (has this run finished), which is an orthogonal
  concern to Part C's *canonical-casing* checking (is this run's status spelled correctly). Narrowing or
  removing it to "align" with the new stricter check would break `_record_is_complete()`'s handling of
  the ~98 legacy-shaped `status`/`started_at` records entirely out of this ticket's scope.
- **Do not let the Part A single-line-value replace touch adjacent whitespace.** Several files in the
  71-file list have a blank line between `## Status` and the value (e.g. `TCK-20260415-WS-CLEANUP.md`:
  `## Status\n\nOPEN\n`); others may not. The replace must substitute only the captured value token
  (`\S+`), not restructure the surrounding blank-line convention per file, or the "1 changed line" AC
  will fail for files whose blank-line layout differs from the implementer's assumption.
- **Do not run a whole-file JSON round-trip on `runs.jsonl`.** Confirmed line-scoped string substitution
  is both simpler and strictly safer than `json.loads`/`json.dumps` per line (which risks reordering
  keys, changing float/int formatting, or altering separator spacing on lines the ticket explicitly
  requires to stay byte-identical).
