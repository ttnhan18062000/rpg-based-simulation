---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260718-STATUS-SUFFIX-TRIM
artifact_type: investigation
tags: [data-quality, observability]
---

# Investigation — TCK-20260718-STATUS-SUFFIX-TRIM

## Current Behavior

**Root mechanism confirmed by direct execution**, not just re-reading the ticket's claim. Two
extraction paths exist over the same `## Status` body section, and they disagree on how much text
they return:

- `tools/gate_checks/status_drift_check.py:42` — `TICKET_STATUS_RE = re.compile(r"^## Status\s*\n+\s*(\S+)", re.MULTILINE)` — captures only the first whitespace-delimited token. Running it live against all 10 files (via `TICKET_STATUS_RE.search(text).group(1)`) returns `'DONE'` for every one of them — the trailing prose after `DONE` is invisible to this regex because `\S+` stops at the first space.
- `tools/generate_registry.py:54-66` — `parse_body_section(body, "Status")` — captures everything from `## Status\n` up to the next `## ` heading (or EOF), `re.DOTALL`. Running it live against all 10 files returns the full fragmented values verbatim:

```
TCK-20260408-PH3-STG1-HOUSEHOLD.md          -> 'DONE (SUPERSEDED by TCK-20260408-PH3-PASS1-LIVED-MODELS)'
TCK-20260619-E12-BALANCE-BASELINE.md        -> 'DONE (EPIC_SCOPED)'
TCK-20260619-E62-CULTURE-DRIFT.md           -> 'DONE (EPIC_SCOPED)'
TCK-20260619-E63-FEATURE-PACKS.md           -> 'DONE (EPIC_SCOPED)'
TCK-20260628-E-NARRATIVE-CONSEQUENCE.md     -> 'DONE — all 3 child tickets complete: E43F (grief urgency), E43G (nemesis relation), E43H (observability surface)'
TCK-20260628-E-PARTY-LOOP.md                -> 'DONE (all child tickets complete: E41F, E41G, E41H)'
TCK-20260628-E-PERSONALITY-CALIBRATION.md   -> 'DONE (E11B audit + E11C weight-tuning + E11D abandonment-rate all complete)'
TCK-20260628-E-WORLD-EVOLUTION.md           -> 'DONE — E52E (seasonal propagation), E52F (trauma motivation), E52G (sovereignty events)'
TCK-20260701-SIMQ-EMIT-CAMP.md              -> 'DONE — CLOSED, WRONG PREMISE'
TCK-20260701-SIMQ-KERNEL-WIRE.md            -> 'DONE — DUPLICATE / CREATED IN ERROR'
```

`src/api/agent_ops_dashboard/ingest.py::parse_ticket_file` (per
`docs/observability/agent_ops_dashboard_contract.md`'s "Ingest / cache" section) reuses
`parse_body_section` for `TicketSummary.workflow_status`, so these 10 distinct strings are exactly
what the dashboard's Tickets-view Status filter dropdown lists as 10 separate selectable options
alongside plain `DONE` — confirmed mechanism, not inference. `get_tickets`'s `facets.statuses` is
computed over the full filtered corpus (contract doc, "get_tickets computes total_count and facets
... over the full filtered result"), so every distinct `workflow_status` string becomes its own
facet value.

**Exact current text of each of the 10 files' `## Status` and `## Completion Summary` sections**
(read verbatim from source, line numbers as of this investigation):

1. **`tickets/done/TCK-20260408-PH3-STG1-HOUSEHOLD.md`** (lines 44-45, last content in file — no
   `## Completion Summary` or any other post-Status section exists; body ends immediately after
   `## Status`):
   ```
   ## Status
   DONE (SUPERSEDED by TCK-20260408-PH3-PASS1-LIVED-MODELS)
   ```
   This is a pre-12-section legacy-format ticket (frontmatter `layer: misc`, no `## Related
   Tickets`/`## Related Docs`/etc. sections at all — only `Tier`/`Type`/`Priority`/`Request
   Summary`/`Scope`/`Out of Scope`/`Acceptance Criteria`/`Status`).

2. **`tickets/done/TCK-20260619-E12-BALANCE-BASELINE.md`** (lines 17-18 Status; line 94-95
   Completion Summary):
   ```
   ## Status
   DONE (EPIC_SCOPED)
   ```
   ```
   ## Completion Summary
   _Epic completes when E12A + E12B + E12C are all DONE._
   ```

3. **`tickets/done/TCK-20260619-E62-CULTURE-DRIFT.md`** (lines 17-18 Status; lines 105-111
   Completion Summary):
   ```
   ## Status
   DONE (EPIC_SCOPED)
   ```
   ```
   ## Completion Summary
   EPIC_SCOPED on 2026-06-22. Four child tickets created in tickets/todos/:
   E62A-CULTURE-MODEL, E62B-CULTURE-DERIVER, E62C-MOTIVATION-OVERLAY, E62D-PARITY-VERIFY.
   Linear dependency chain: E62A → E62B → E62C → E62D.
   Prerequisites: E51 (Chronicle Compiler) done; E53 (Faction Diplomacy) scoped.
   All three staging artifacts (investigation.md, plan.md, test_plan.md) migrated to
   stored_artifacts/TCK-20260619-E62-CULTURE-DRIFT/.
   ```

4. **`tickets/done/TCK-20260619-E63-FEATURE-PACKS.md`** (lines 17-18 Status; lines 88-94
   Completion Summary):
   ```
   ## Status
   DONE (EPIC_SCOPED)
   ```
   ```
   ## Completion Summary
   All 4 child tickets DONE (2026-06-23):
   - E63A: Gate verified SATISFIED — 7+ extension patterns in E53/E61/E62; architecture doc created.
   - E63B: FeaturePackManifest (Pydantic, frozen, YAML round-trip) + RuntimeProfile + CompatibilityResolver (Kahn's BFS); wired into SimulationScenarioDefinition.
   - E63C: FeatureRegistry[T] (dict-based, canonical enum + pack entries) + FeaturePackLoader (discovers manifests, filters by profile, imports classes); demo_escort_pack registers ESCORT_DIGNITARY from content/packs/ without touching src/.
   - E63D: BalanceExperimentSpec + pure BalanceExperimentRunner (dot-path metric snapshot); integration tests confirm no src/ modifications; docs finalized; knowledge index updated.
   45 tests pass across all child tickets.
   ```

5. **`tickets/done/TCK-20260628-E-NARRATIVE-CONSEQUENCE.md`** (lines 17-18 Status; lines 121-122
   Completion Summary):
   ```
   ## Status
   DONE — all 3 child tickets complete: E43F (grief urgency), E43G (nemesis relation), E43H (observability surface)
   ```
   ```
   ## Completion Summary
   All acceptance criteria met: ally death → grief urgency concern → episode decay; 2+ antagonist episodes → nemesis relation → FORM_PARTY block; grief + nemesis visible in EntityInspectionSnapshot.narrative_modifiers. Parity ledger entries SOC-231 and SOC-232 added.
   ```

6. **`tickets/done/TCK-20260628-E-PARTY-LOOP.md`** (lines 17-18 Status; line 119 Completion
   Summary — EMPTY, header only):
   ```
   ## Status
   DONE (all child tickets complete: E41F, E41G, E41H)
   ```
   ```
   ## Completion Summary
   ```
   (nothing follows the header — file ends here)

7. **`tickets/done/TCK-20260628-E-PERSONALITY-CALIBRATION.md`** (lines 17-18 Status; line 130
   Completion Summary — EMPTY, header only):
   ```
   ## Status
   DONE (E11B audit + E11C weight-tuning + E11D abandonment-rate all complete)
   ```
   ```
   ## Completion Summary
   ```
   (nothing follows the header — file ends here)

8. **`tickets/done/TCK-20260628-E-WORLD-EVOLUTION.md`** (lines 17-18 Status; lines 122-123
   Completion Summary):
   ```
   ## Status
   DONE — E52E (seasonal propagation), E52F (trauma motivation), E52G (sovereignty events)
   ```
   ```
   ## Completion Summary
   All 3 acceptance criteria met: seasonal calamity propagation (E52E), direct trauma→DANGER concern in <1 tick (E52F), sovereignty shift WorldEvents observable in recent_world_events (E52G). Parity ledger entries WORLD-105, WORLD-106, WORLD-107 added.
   ```

9. **`tickets/done/TCK-20260701-SIMQ-EMIT-CAMP.md`** (lines 17-18 Status; lines 92-108
   Completion Summary):
   ```
   ## Status
   DONE — CLOSED, WRONG PREMISE
   ```
   ```
   ## Completion Summary
   **Closed — premise incorrect, no viable engine path.**

   Investigation (2026-07-01) found:
   - `StateUpdate` has no `camps_add` field — only `camp_updates: Dict[str, CampUpdate]`
   - `CampUpdate` only supports: `maturity_delta`, `active_set`, `last_raid_tick_set` — no construction
   - `CampService.process_camps()` only evolves existing camps (maturity, monster spawns, raids)
   - Camps are pre-placed at world generation; no dynamic camp construction occurs during simulation ticks

   The ticket assumed "CampService has no event recorder" but the real issue is deeper: there is
   no camp construction mechanic in the simulation at all. Adding an event recorder to CampService
   would not fix this — the code path that creates new camps does not exist.

   Implementing `camp_constructed` requires first adding a camp placement mechanic (new entity
   action, world event, or pipeline phase that creates `CampState` entries dynamically). That is a
   gameplay feature, not a SimQ wiring task. Closing this ticket; if camp placement is added in the
   future, create a new SimQ emit ticket at that time.
   ```

10. **`tickets/done/TCK-20260701-SIMQ-KERNEL-WIRE.md`** (lines 17-18 Status; lines 114-119
    Completion Summary):
    ```
    ## Status
    DONE — DUPLICATE / CREATED IN ERROR
    ```
    ```
    ## Completion Summary
    **Ticket created in error.** All three gaps (G1/G2/G3) were already resolved on 2026-06-30:
    - G1 + G3: `TCK-20260630-SIMQ-WIRE-KERNEL` — `quality_fn=hub.on_envelope` wired into `QueueDrainWorker`; `InProcessQualityFeed` refactored to not create a competing consumer
    - G2: `TCK-20260630-SIMQ-WIRE-SERVER` — `set_quality_hub()` called in server lifespan

    The D20 audit was written before those fixes and was not updated when the fixes landed. This ticket was created against stale audit text. No implementation required. Closing as duplicate.
    ```

**Gap identified:** file #1 (`TCK-20260408-PH3-STG1-HOUSEHOLD.md`) has no `## Completion Summary`
section (or any of the other 7 standard-format trailing sections) to reword into — confirmed by
direct read of the full file (46 lines, ends at `## Status`). This matches the ticket's own
Assumptions note and is not a new finding, but is re-confirmed here by direct read rather than
trusted from the ticket text.

**`status_drift_check.py` current pass/fail state for these 10 files, confirmed by direct
execution** (not assumed): all 10 already report `'DONE'` under `TICKET_STATUS_RE`, so
`check_ticket_status_drift()` does **not** flag any of them today, and will not flag them after this
ticket's fix either (the fix only changes the *tail* text after the already-matching first token).
This confirms the ticket's AC "`status_drift_check.py` continues to report PASS ... no regression"
is trivially satisfiable by the data change alone, independent of the go/defer decision on
extending the checker.

## Mechanics / Engine Constraints

Not applicable. This is ticket-corpus data hygiene (ticket body text normalization for a
dashboard's derived filter facet), not simulation mechanics. No `docs/mechanics/` chapter or
`docs/engine/` contract governs `## Status`/`## Completion Summary` body text — same conclusion the
predecessor's investigation.md reached for the equivalent question, reconfirmed here for this
ticket's narrower scope.

## Parity Ledger Overlap

- **`INFRA-277`** (`docs/parity_ledger/infrastructure.yaml:4630-4654`) — `status: verified`,
  `priority: P2`. Documents `status_drift_check.py`'s current two-check scope
  (`check_ticket_status_drift` / `check_runs_jsonl_final_status_drift`) and explicitly states the
  checker's `TICKET_STATUS_RE` is a first-`\S+`-token capture — it does **not** claim to validate
  the full tail text is clean of trailing prose. This ticket's 10-file data fix does not falsify
  anything currently asserted in INFRA-277's `text`/`v2_evidence` (the checker's behavior is
  unchanged either way), so **no update to INFRA-277 is required if the go/defer decision is
  "defer."** If the go/defer decision is "extend now" (adding a new check function or widening
  `check_ticket_status_drift` to also flag first-token-DONE-but-trailing-prose cases), INFRA-277
  must be updated (or a new entry added) to describe the widened scope and its new `v2_evidence`
  line range, per this ticket's own AC and CLAUDE.md's Authoritative Mechanics Rule ("If logic
  changes, update the corresponding doc AND the parity ledger entry in the same session").
  `test_path` implied by INFRA-277's `v2_evidence` is `tests/tools/test_status_drift_check.py` —
  confirmed to exist and currently pass (11 tests, read in full).
- No other parity ledger entry overlaps. Searched `docs/parity_ledger/*.yaml` (via the predecessor's
  own confirmed search plus a fresh grep for `## Status`, `workflow_status`, `Completion Summary`)
  — no other hit. This ticket changes no simulation-facing behavior.

## Prior Work

- **`TCK-20260718-STATUS-DRIFT-REPAIR`** (done, standard, P1, same defect family) — the direct
  predecessor and only relevant prior work. Fixed 71 `tickets/done/*.md` files whose `## Status`
  first token was genuinely wrong (`OPEN`/`INPROGRESS` stale), normalized 7 `runs.jsonl`
  `final_status` casing records, and built `tools/gate_checks/status_drift_check.py` (ships
  unwired, no Makefile/workflow call site — still true today, unchanged by this ticket regardless
  of go/defer). Its **"Colon-Suffixed Files Decision"** (`stored_artifacts/TCK-20260718-STATUS-DRIFT-REPAIR/plan.md`,
  lines 31-63) is the direct structural precedent for this ticket's own go/defer scoping call on
  extending the checker: that ticket found 6 files using a different, newly-discovered `## Status`
  drift shape (same-line colon-suffixed) mid-investigation and explicitly declined to fold them
  into its already-approved scope, citing (1) the approved AC's fixed 71/12/83 count baked into the
  count-based ACs, (2) CLAUDE.md's "never plan more work than the ticket scope... note adjacent
  problems as future tickets" rule, (3) risk of an inconsistent diff shape mixing two substitution
  patterns, and (4) keeping the checker's regex internally consistent with the approved fix scope
  rather than newly flagging out-of-scope files. That reasoning transfers near-exactly to this
  ticket's own extension question: the 10-file "trailing-prose-after-DONE" class was likewise
  discovered as a byproduct of the *previous* pass's `\S+`-token regex behavior (the same regex that
  intentionally captures only the first token), and the same four reasoning threads apply almost
  verbatim (see Risks and Open Questions below for the reasoned but non-final recommendation).
  Confirmed disjoint file sets between the two tickets' targets — verified independently in this
  investigation by checking each of this ticket's 10 filenames against the predecessor's 71-file and
  6-colon-suffixed lists: zero overlap.
- No other stored artifact or done ticket addresses ticket-body `## Status`/`## Completion Summary`
  reformatting. `docs/REGISTRY.yaml` exists; a targeted check for `related_code_areas` overlapping
  `tickets/done/` or tags intersecting `{data-quality, observability}` surfaces only the predecessor
  and generic dashboard-build tickets (`TCK-20260716-AGENTOPS-*`, `TCK-20260717-AGENTOPS-*`), none of
  which touch ticket-body content — they build/extend the dashboard's read side, not the ticket-data
  corpus.

## Risks and Open Questions

- **`status_drift_check.py` extend-vs-defer — recommend but do not finalize, per ticket
  instruction.** Recommendation: **defer**, for reasoning that mirrors the predecessor's
  Colon-Suffixed Files Decision almost exactly:
  1. This ticket's own ACs are anchored to a fixed 10-file list frozen at ticket-creation time, not
     to "however many files a widened regex newly finds" — extending the checker inside this same
     ticket risks the checker surfacing a different (larger or smaller) live count than 10 if any
     other `tickets/done/*.md` file happens to share this trailing-prose shape but wasn't part of
     the frozen list (not verified in this investigation — out of scope per the ticket's own
     "re-verify against the frozen list only, do not re-scan and expand scope" instruction).
  2. `test_regex_matches_baseline_scan_pattern()` (`tests/tools/test_status_drift_check.py:213-215`)
     currently asserts `TICKET_STATUS_RE.pattern == r"^## Status\s*\n+\s*(\S+)"` byte-for-byte —
     changing `check_ticket_status_drift`'s matching logic to also inspect the tail text past the
     first token means either changing this assertion (which the predecessor's own Anti-Drift Notes
     called "load-bearing... must not be weakened or removed" for the *existing* colon-suffix
     concern) or adding an entirely separate regex/check function that coexists with it. Either path
     is a real, non-trivial design decision, not a small tweak — consistent with the ticket's own
     framing that this is a "go/defer" call, not an assumed "go."
   3. The two identified defect classes (colon-suffixed same-line drift, and now trailing-prose-
      after-DONE) are structurally distinct enough that a future ticket scoping *both* remaining
      checker gaps together (rather than this ticket bolting on one of the two in isolation) may
      produce a cleaner design — e.g. a single `EXTRA_PROSE_RE` or a documented tri-state
      classification (`clean` / `colon-suffix-drift` / `trailing-prose`) rather than two
      independently-added special cases in two separate tickets.
   4. If deferred, this ticket's own 10-file data fix is fully self-contained and independently
      valuable (fixes the dashboard facet fragmentation today) — it does not need the checker
      extension to close cleanly, matching the predecessor's own "the plan does not create that
      ticket; it only flags the recommendation" precedent.
   This is a recommendation only, per the task instructions — the actual go/defer call and its
   reasoning belongs in this ticket's own `## Implementation Notes` once decided, not pre-decided
   here.
- **`TCK-20260408-PH3-STG1-HOUSEHOLD.md` legacy handling** — confirmed by direct read: body
  genuinely ends at `## Status`, no other post-Status section exists anywhere in the file. The
  ticket's own recommended default (append a minimal `## Completion Summary` containing only the
  reworded superseded-by note) is reasonable and consistent with this project's "legacy data scope"
  precedent (don't force full 12-section restructuring onto old-format files), but is explicitly
  left as a recommendation for Implement phase to confirm, not a final decision — this investigation
  does not override that.
- **Rewording risk for the two empty-Completion-Summary files** (`E-PARTY-LOOP`,
  `E-PERSONALITY-CALIBRATION`) — both are `BLOCKED`/deferred epics (frontmatter `layer: simulation`,
  tags include `blocked`, `deferred`) whose bodies describe unresolved gate conditions (HERO role
  population status "UNCLEAR", D05-style audit "NOT YET DONE") elsewhere in the file (`## Request
  Summary`, `## Status: BLOCKED pending...` prose inside the body, `## Implementation Notes`). The
  reworded Completion Summary sentence must reflect only the trimmed Status tail's literal content
  ("all child tickets complete: E41F, E41G, E41H" / "E11B audit + E11C weight-tuning + E11D
  abandonment-rate all complete") — it must not silently imply the epic's original BLOCKED gate
  conditions were resolved with different content than what's already stated elsewhere in the file,
  since this ticket's scope is trimming/relocating existing text, not re-litigating epic completion
  status. Flagging so Implement phase does not accidentally invent new completion narrative beyond
  what the trimmed Status tail already says.
- **No blocking open question found for the 9 standard-format files** — each has an unambiguous
  trimmed tail and either an empty or mergeable existing Completion Summary; the rewording is
  mechanical, not a judgment call, except for the legacy-file handling and the go/defer call above.

## Anti-Drift Hazards

- **Regex/AC precision**: the AC's exact-match pattern `^## Status\s*\n+\s*DONE\s*\n` requires the
  next line after `DONE` to immediately hit the next `## ` heading or EOF — i.e., no trailing
  whitespace-only line, no re-inserted parenthetical anywhere in the section, not even reformatted.
  Do not leave a stray blank line with leftover punctuation, and do not "clean up" surrounding
  blank-line conventions differently per file (mirrors the predecessor's own "do not restructure
  blank-line layout" hazard) — only change the value token's trailing content.
- **Verbatim-paste hazard**: Scope explicitly forbids pasting the raw parenthetical/clause into
  Completion Summary — it must be reworded into a natural sentence. A word-for-word copy (even
  moved to a different section) would fail the ticket's own intent even though the AC's regex check
  would not literally catch it — this is a human/architecture-review-catchable violation, not a
  script-checkable one.
- **Frontmatter and unrelated-file guard**: AC explicitly requires `git diff --stat tickets/done/`
  to show exactly these 10 files and no frontmatter field changed on any of them. Confirmed current
  frontmatter `layer` values vary across the 10 files (`misc`, `simulation` ×3, `world` ×2,
  `architecture`, `observability` ×2) — do not "fix" or homogenize these as a drive-by; that is
  explicitly out of scope.
- **Do not re-derive or expand the 10-file list.** Out of Scope explicitly warns against re-scanning
  `tickets/done/` and pulling in additional files that superficially resemble this defect class —
  this investigation did not do so and Implement should not either; the frozen 10-file list from the
  ticket's Related Code Areas is authoritative.
- **`TCK-20260628-E-PARTY-LOOP.md` / `TCK-20260628-E-PERSONALITY-CALIBRATION.md`**: both bodies
  contain a `**Status: BLOCKED pending ...**` sentence *inside* the `## Request Summary`/prose text
  (not the `## Status` body section itself — confirmed by direct read, these are two structurally
  distinct occurrences of the word "Status" in the same file). Do not confuse this in-prose sentence
  with the `## Status` body section being trimmed — only the latter is in scope, and the in-prose
  BLOCKED sentence is not touched by this ticket (Out of Scope: "any `tickets/done/*.md` file not in
  this ticket's frozen 10-file list" does not apply here since these ARE in the list, but the
  specific *section* being edited is `## Status` and `## Completion Summary` only — not `## Request
  Summary`).
- **`## Tier\n## Tier` duplicate-heading glitch** (`E-NARRATIVE-CONSEQUENCE.md` /
  `E-WORLD-EVOLUTION.md`, per predecessor's plan.md) — confirmed by direct read: **not present** in
  either file's current content read during this investigation (both show a single `## Tier` /
  `standard` or `epic` line, no duplication observed at the lines read). If this glitch was already
  fixed by some other change since the predecessor's note, or if the predecessor's note referred to
  different files than currently exist, do not go looking for it — Out of Scope explicitly excludes
  pursuing it, matching the ticket's own instruction.
