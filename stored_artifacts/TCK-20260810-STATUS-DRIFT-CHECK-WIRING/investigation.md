---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-STATUS-DRIFT-CHECK-WIRING
artifact_type: investigation
tags: [ai, agent-monitoring, process-improvement, data-quality]
---

# Investigation — TCK-20260810-STATUS-DRIFT-CHECK-WIRING

## Current Behavior

**`tools/gate_checks/status_drift_check.py`** (154 lines total):
- `check_ticket_status_drift(done_dir=Path("tickets/done"))` (L68-107): globs `tickets/done/*.md`,
  extracts `## Status` via `parse_body_section(_strip_frontmatter(text), "Status")` (imported from
  `tools/generate_registry.py`, L55), flags any non-empty value that isn't `DONE` (case-insensitive)
  or in `EPIC_TIER_VALUES = {"EPIC_SCOPED"}` (L65), skipping files whose name doesn't start with
  `TCK-` and files where `parse_body_section` returns `""` (no heading, or same-line
  colon-suffixed `## Status: X` — documented known limitation, L28-34 of the module docstring).
- `check_runs_jsonl_final_status_drift(runs_path=Path("agent-monitoring/runs.jsonl"))` (L110-137):
  flags any `runs.jsonl` record with a `final_status` key whose value isn't already its own
  uppercase form.
- `check_status_drift()` (L140-144): aggregates both.
- `__main__` (L147-154): `MARKER:` + `json.dumps(result)` stdout, `sys.exit(1)` on any FAIL.
- **Confirmed still exactly what its own docstring says (L38-40): zero call sites.** Grepped
  `.claude/workflows/*.js`, `Makefile`, and every `tools/*.py`/`tools/gate_checks/*.py` — the only
  hits are prose references in `tools/ticket_field_values.py`'s docstring, never an import or
  subprocess call.

**`tools/generate_registry.py::parse_body_section(body, section)`** (L69-81): regex
`r"^## " + re.escape(section) + r"\s*\n(.*?)(?=^## |\Z)"` with `re.MULTILINE | re.DOTALL` — captures
the entire section body up to the next `## ` heading or EOF, not just the first token. This is the
exact function `src/api/agent_ops_dashboard/ingest.py:137` uses to populate the dashboard's
`workflow_status` field, so `status_drift_check.py` importing it directly (rather than a bespoke
regex) means a file only passes the checker if the dashboard would also render it as clean `DONE`.

**`tools/gate_checks/done_checker_static.py::run_static_precheck`** (L466-483): aggregates 7 Part A
conditions as a fixed-order list of `{"condition", "status", "evidence"}` dicts, called from the
Verify-phase agent prompt in `implement-ticket.js`. `check_ticket_field_values_valid` (L291-305) is
the literal template for extending this file: a thin adapter unwrapping
`tools/ticket_field_values.py::check_ticket_field_values(ticket_path)`'s single-item list into the
`(status, evidence)` tuple shape, called with **only the ticket currently being closed** — it never
scans `tickets/done/` as a whole. This is the key architectural detail for Plan: `ticket_field_values.py`'s
precedent (the thing option (a) is asked to "mirror") validates one ticket at close time, not the
corpus.

**`tools/ticket_field_values.py`**: defines `TIER_VALUES`, `PRIORITY_VALUES`,
`WORKFLOW_STATUS_VALUES = {"OPEN","INPROGRESS","BLOCKED","DONE","EPIC_SCOPED"}` (L46-48, re-exported
for `ingest.py`/`status_drift_check.py`'s shared use, per L14-16), and `LAYER_VALUES` (re-exported
from `validate_frontmatter.py`). `check_ticket_field_values` (L67-86) validates only `## Tier`/
`## Priority` for one ticket file — explicitly, by its own docstring (L24-27), "does NOT re-validate
`## Status` — that remains `status_drift_check.py`'s job." This module is wired into
`run_static_precheck` as a blocking 6th condition (`ticket_field_values_valid`).

**`docs/guidelines/tag_taxonomy.md`** Enforcement section (L201-218): the forward-only-enforcement
precedent is date-gated by the `TCK-YYYYMMDD` embedded in the ticket ID, applied only to
`validate_frontmatter.py`'s tag/registry checks, cutoff `2026-07-04`. No date-exemption mechanism
exists anywhere in `status_drift_check.py` or `ticket_field_values.py` today.

**`tests/tools/test_status_drift_check.py`** (265 lines, 16 tests): solid coverage of both check
functions, the aggregate, read-only-ness, the CLI `MARKER:` contract and exit code, and all 3
documented extraction-edge-case fixes (stray trailing line, bold-block bleed, colon-format
exemption). No test currently exercises a *wired* call site (there is none to exercise) or a
date-exemption path (none exists).

## Mechanics / Engine Constraints

None. This ticket is agent-workflow/developer-tooling only (ticket-body text repair + gate wiring
decision) — no `docs/mechanics/` or `docs/engine/` law governs ticket-status bookkeeping or dashboard
tooling. Confirmed via `search_docs`/`graphify` (Step 0c) and by the ticket's own `layer: ai`
classification: no mechanics/engine doc paths were returned as relevant.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: INFRA-277 (the entry covering `status_drift_check.py`) currently states "Ships unwired... a future ticket decides where/whether to gate on it" and cites a live-corpus check result of `[]` (clean) as of its last update — both are now stale once this ticket (a) wires the checker into a real path and (b) the live corpus is confirmed to have 9 non-empty FAIL findings today, not 0. `status`/`v2_evidence` must be updated per CLAUDE.md's Authoritative Mechanics Rule parity requirement, regardless of which wiring option Plan selects.

## Parity Ledger Overlap

- **INFRA-277** (`docs/parity_ledger/infrastructure.yaml`, `status: verified`, `priority: P2`) — the
  entry that documents `status_drift_check.py` itself, built for TCK-20260718-STATUS-DRIFT-REPAIR.
  Its `test_path` (16 tests in `tests/tools/test_status_drift_check.py`) all currently exist and
  pass. Not a P0 entry, so no test_path is strictly mandatory to keep green, but its `text` describes
  the exact "ships unwired" state this ticket changes — needs a `v2_evidence` update regardless of
  which wiring option is chosen (see Docs Requiring Update).
- **INFRA-278** (adjacent entry, `tools/ticket_field_values.py`) — the precedent entry for the
  blocking-gate wiring option (a). Not touched by this ticket unless option (a) is chosen and the
  new condition is added to `run_static_precheck`'s checks tuple, in which case its own `text`
  describing "6 blocking Part A conditions" would need a count update (would become 7).
- No other parity ledger file (`combat_movement.yaml`, `faction.yaml`, `progression.yaml`,
  `social_narrative.yaml`, `strategic_cognition.yaml`, `substrate.yaml`, `town_resource.yaml`,
  `world_dynamics.yaml`) references `status_drift_check`, `ticket_field_values`, or
  `done_checker_static` — confirmed via corpus-wide grep.

## Prior Work

- **TCK-20260718-STATUS-DRIFT-REPAIR** (DONE): built `status_drift_check.py`, did the original
  71-file body-text repair, explicitly scoped out the 6 same-line colon-suffixed `## Status: X`
  files ("Colon-Suffixed Files Decision" in its plan.md) — this ticket's Out of Scope correctly does
  not reopen that.
- **TCK-20260718-STATUS-MULTILINE-FIX** (DONE): replaced the original first-token-only regex with
  the current `parse_body_section` reuse, closing a "checker says clean, dashboard shows garbage"
  gap for 2 real drift shapes (stray trailing line, bold-block bleed).
- **TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM** (DONE): built `ticket_field_values.py` and wired
  `check_ticket_field_values_valid` into `run_static_precheck` as a blocking 6th Part A condition —
  this IS the literal precedent option (a) would extend, and its scope is per-closing-ticket-only,
  not corpus-wide (see Current Behavior above — important for Plan's design decision).
- **TCK-20260718-STATUS-FACET-CANONICAL** (DONE): tightened `EPIC_TIER_VALUES` from
  `{"EPIC_SCOPED","SCOPED"}` to `{"EPIC_SCOPED"}` to match the dashboard's real canonical set.
- **TCK-20260720-TAG-CORPUS-REPAIR-SWEEP** (DONE): the report-only, separately-ticketed sweep
  precedent this ticket's Out of Scope cites for NOT doing a blanket legacy sweep here.
- **TCK-20260720-GATE-CHECK-WIRING-DECISIONS**: precedent for explicitly deciding/documenting
  wiring vs. deferral for a batch of previously-unwired gate checks (`doc_staleness_check.py` wired;
  others explicitly deferred with reasons) — the same shape of decision this ticket needs to make
  for `status_drift_check.py`.
- **`docs/parity_ledger/infrastructure.yaml` INFRA-277**: see Parity Ledger Overlap.

## Risks and Open Questions

1. **The corpus has moved significantly beyond the ticket's cited 3 real-drift cases — now 7.**
   Live run today (`python3 tools/gate_checks/status_drift_check.py`):
   ```
   FAIL: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER.md: ## Status reads 'OPEN', expected DONE
   FAIL: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md: ## Status reads 'OPEN', expected DONE
   FAIL: TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION.md: ## Status reads 'OPEN', expected DONE
   FAIL: TCK-20260806-PUSH-SHADOW-VALIDATION-PERF.md: [same false-positive trailing-prose shape as before]
   FAIL: TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT.md: [same false-positive trailing-prose shape as before]
   FAIL: TCK-20260806-SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC.md: ## Status reads 'OPEN', expected DONE
   FAIL: TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS.md: ## Status reads 'INPROGRESS', expected DONE
   FAIL: TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION.md: ## Status reads 'INPROGRESS', expected DONE
   FAIL: TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md: ## Status reads 'INPROGRESS', expected DONE
   PASS: no lowercase final_status drift in agent-monitoring/runs.jsonl
   ```
   The original 3 cited real-drift cases **still hold** (still FAIL, identical evidence). The 2 cited
   false positives **still hold** (identical trailing-prose shape, still real completion text, not
   drift). But there are **4 additional real drift instances** not cited in the ticket:
   `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (same `OPEN`-body shape as the original 3 —
   it is the 5th and final child of the same `SIMQ-OBSERVABILITY-PUSH-MIGRATION-EPIC` closed the same
   day), and 3 tickets from this very session's cognition/combat batch
   (`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`, `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`,
   `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, all `INPROGRESS`-body). I independently
   confirmed all 7 are genuinely completed work with real `working_log.csv` DONE rows and
   `stored_artifacts/` references (not misplaced in-progress tickets) — one working_log entry
   (`TCK-20260810-D22-DORMANT-WIRING-AUDIT`) even explicitly self-disclosed
   "C2 [`PROJECT-SWITCH-BYPASS-GENERALIZATION`] own body Status field is stale (INPROGRESS) despite
   being DONE" as a known, undischarged hygiene gap. **This is squarely within this ticket's AC
   wording** ("investigation.md re-confirms the 3 real drift cases... or documents if the corpus has
   moved") — the corpus has moved, and Plan/Implement must decide whether to fix all 7 now-confirmed
   instances or hold to the originally-cited 3 (the fix mechanism — set `## Status` body text to
   `DONE` — is identical for all 7, so this is a scope-size decision, not a new mechanism). None of
   this session's own 4 closed tickets cited in the task brief
   (`TCK-20260810-HOTFIX-PATH-SEARCH-BEFORE-GREP-GAP`, `TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL`,
   `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`, `TCK-20260810-SKILL-USAGE-RETRO-TRACKING`)
   show drift — evidence Finalize's own `## Status` body-setting is reliable for tickets closed very
   recently in this session; all 7 confirmed drift cases predate this session's own runs.

2. **The ticket's "frontmatter already correctly showing they're closed" premise is inaccurate for
   the 3 originally-cited tickets** (not just the new 4). All 7 real-drift tickets — including the
   original 3 — have frontmatter `status: active` / `phase: open`, not `status: historical` /
   `phase: done`. Corpus-wide, 173/~1450 `tickets/done/*.md` files show `status: active` and
   191 show `phase: open` in frontmatter — a materially larger, separate drift class
   (frontmatter status/phase, not just body `## Status`) that this ticket's scope explicitly does
   not cover (`status_drift_check.py` only checks the body section; `check_frontmatter_valid` in
   `done_checker_static.py` validates frontmatter *shape/tags/layer*, not `status:`/`phase:` value
   correctness against the closed/open state). Flagging as an open question, not fixing: does not
   block this ticket's scoped body-text repair, but Plan should note it explicitly as a distinct,
   larger, separately-scoped future gap rather than silently absorbing it.

3. **The ticket's cited "real, non-cosmetic consequence" (`GanttBar.tsx`'s `classifyFinalStatus()`)
   is dead — the file was deleted 11 days before this ticket was authored.**
   `git log --diff-filter=D -- "**/GanttBar.tsx"` shows commit `1c6b6a83`
   (`TCK-20260720-PROGRESS-TIMELINE-VIEW`, 2026-07-30) deleted `GanttBar.tsx`, `TimeAxis.tsx`,
   `Legend.tsx`, and `RecentActivityGantt.tsx`, replacing them with `ProgressTimelineView.tsx` +
   `dashboard-frontend/src/lib/toChartOption.ts`. `classifyFinalStatus()` does not exist anywhere in
   the current codebase — the only surviving reference is a comment in
   `dashboard-frontend/src/views/ReplayTimelineView.tsx:9-10` ("...than GanttBar's
   `RunSummary.final_status` buckets... rather than a generalization of GanttBar's
   `classifyFinalStatus`"), which is itself now a dangling reference to deleted code. In the current
   `toChartOption.ts`, segment color comes from `getPhaseSegmentColor(phase)` (L178, L220), never
   from a `final_status` bucket classification — the specific green/gray-miscoloring bug this ticket
   cites as its motivating consequence chain no longer has a live code path to occur in.
   **The real, live current-day consumer of the ticket-body `## Status` field (via `parse_body_section`,
   not `runs.jsonl`'s `final_status`) is `src/api/agent_ops_dashboard/ingest.py:137,150,388,586`'s
   `workflow_status`, rendered and filterable in `dashboard-frontend/src/views/TicketsView.tsx:46,355-356`.**
   A drifted body `## Status` means: (a) the Tickets dashboard tab displays the wrong status text for
   that row, and (b) `ingest.py:586`'s `r["workflow_status"] != status` filter comparison means a
   dashboard user filtering by `status=DONE` will silently NOT see a genuinely-completed ticket with
   a drifted body. This is a real, still-live consequence — just a different one than the ticket's
   `GanttBar.tsx` citation, which should be corrected in `plan.md`/`Implementation Notes` rather than
   propagated as-is. `GanttBar.tsx` should also be flagged as a stale "Related Code Areas" file path
   per the investigator's file-existence check (it does not exist; the reference-only listing in this
   ticket's Related Code Areas is factually wrong).

4. **Design Question 1 (blocking gate vs. recurring report) — evidence for Plan, not decided here:**
   - *For a per-ticket blocking gate mirroring `ticket_field_values.py` literally* (validating only
     the ticket currently at Verify/Finalize, matching `check_ticket_field_values_valid`'s exact
     shape): closes the gap going forward — a newly-closing ticket could never again leave `## Status`
     non-canonical. Cheap (one file read, not a corpus scan). Because it only ever inspects the
     *current* ticket_id (which is always today's date), it has **no legacy/forward-only date-exemption
     need at all** — this reframes Design Question 2 (see below).
     - **Caveat:** it would NOT have caught any of the 7 real drift cases found today, since none of
       those files are being re-closed — a per-ticket gate only prevents new drift, it does not
       detect/report existing corpus drift (which is what actually found this ticket's own motivating
       evidence).
   - *For a recurring, corpus-wide report* (Makefile target or `generate_retro.py`-driven, reusing
     `check_ticket_status_drift(done_dir)`'s existing whole-corpus-scan design as-is, no code change
     needed beyond a call site): matches exactly how this ticket's own audit found the drift — a
     periodic sweep over `tickets/done/`. Lower blast radius (report-only, never blocks a ticket
     close). Would need re-running deliberately (cadence decision) rather than being automatically
     enforced at every close.
   - Both are legitimate for different reasons — they are not mutually exclusive (option (a) prevents
     new drift; option (b) audits for drift in the existing/legacy corpus, including from any future
     out-of-band edit to an already-closed ticket file). Plan should decide with this framing rather
     than treating them as strictly either/or.

5. **Design Question 2 (forward-only-enforcement exemption) — real numbers:** Of the 9 total FAIL
   findings in the live corpus-wide scan today, **0 are pre-2026-07-04** (all 9 are dated
   2026-07-21 or later, per the `TCK-YYYYMMDD` embedded date). If wired as a *per-ticket-only*
   blocking gate (4's first bullet), no date-exemption is needed at all, structurally — a closing
   ticket's own ID always postdates any historical cutoff. If wired as a *corpus-wide* blocking gate
   (re-scanning all of `tickets/done/` on every close), a forward-only exemption would in principle
   be needed to avoid blocking on legacy drift, but **today's real evidence shows zero legacy
   (pre-2026-07-04) tickets would trip it** — so the exemption is not urgently needed by current
   corpus state, though it remains a live risk if a pre-cutoff ticket with lingering body drift is
   ever discovered later (the `status_drift_check.py` corpus scan has apparently never been run
   comprehensively against the full historical corpus before this ticket — no ledger evidence of a
   full-corpus pass beyond the routine test suite's small fixtures).

## Anti-Drift Hazards

- **Do not "fix" the 2 known false positives** (`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`,
  `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`) by editing their real, accurate completion prose to
  satisfy the checker's exact-match limitation — reconfirmed still real completion text, not drift,
  in this investigation's live run.
- **Do not silently expand scope to the frontmatter `status:`/`phase:` drift class** (173/191 files
  corpus-wide) found in Risk #2 — it is a materially larger, differently-shaped problem (frontmatter
  field correctness, not body-section text) that this ticket's checker does not detect and was never
  scoped to fix.
- **Do not silently expand scope to a corpus-wide legacy sweep** — Out of Scope explicitly excludes
  this, matching `TCK-20260720-TAG-CORPUS-REPAIR-SWEEP`'s report-only-and-separately-ticketed
  precedent. If Plan decides to fix all 7 now-confirmed instances (not just the originally-cited 3),
  that is still a bounded, evidence-driven decision about *today's* real corpus state — not a
  "sweep everything, including anything not yet found" expansion.
- **Do not reuse the stale `GanttBar.tsx` citation uncorrected** in `plan.md` or the eventual
  `## Implementation Notes` — cite `TicketsView.tsx`/`ingest.py`'s `workflow_status` as the real,
  live consequence chain instead (see Risk #3).
- **If option (a) (blocking gate) is chosen, do not accidentally build a corpus-wide-scanning
  blocking gate** — that would fail-closed on any future unrelated ticket close the moment a new
  drift instance appears anywhere in `tickets/done/`, a materially different (and more fragile)
  design than the literal `ticket_field_values.py` precedent it's meant to mirror (single-ticket
  scope only). This distinction is easy to get wrong by reusing `check_ticket_status_drift(done_dir)`
  as-is inside `run_static_precheck` instead of writing a narrower single-file variant.
- **The checker's documented exclusions (same-line colon-suffixed `## Status: X`, `EPIC_TIER_VALUES`,
  non-`TCK-`-prefixed files) are explicitly out of scope to revisit** per this ticket's Out of Scope —
  do not touch `check_ticket_status_drift`'s existing exemption logic while wiring it.
