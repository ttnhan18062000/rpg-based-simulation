---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE
artifact_type: plan
tags: [dashboard, observability]
---

# Implementation Plan — TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE

## Summary

Register the 22nd `WorkflowPhase`, `'Document-Update'`, into `dashboard-frontend/src/lib/phasePalette.ts`
as an additive-only change: a new union member, a `PHASE_FAMILY` entry in the existing `build`
family, and a `PHASE_PALETTE` hex that continues `build`'s established upward-OKLCH-lightness
step from `'Sync Docs'` (`#289724`). The hex is not hand-derived and frozen up front — it is
derived as a starting candidate, then validated (and adjusted if necessary) by actually invoking
the `dataviz` skill's `validate_palette.js` the three ways the ticket's Scope specifies, with real
output cited in the ticket's Implementation Notes. The header comment, the test file's literal
21→22 fixtures, and `docs/parity_ledger/infrastructure.yaml`'s `INFRA-302.v2_evidence` field are
then updated to match the confirmed final state, and the full frontend regression
(vitest + tsc + build) closes the loop. Every step is additive; no existing phase's family or hex
changes.

## Steps

### Step 1 — Add `'Document-Update'` to the `WorkflowPhase` union
**Files:** `dashboard-frontend/src/lib/phasePalette.ts`
**Change:** In the `WorkflowPhase` union type (lines 46-50), add `'Document-Update'` as the 22nd
member. Append it to the existing multi-line union in whatever position keeps the union's grouping
sensible (grouping by family is not required by the type itself — the file does not currently
group union members by family order — so appending at the end of the union, after `'Report'`, is
acceptable and lowest-risk for diff minimality).
**Do NOT touch:** Any of the other 21 existing union members, their spelling, or their order
relative to each other.
**Verify:** `npx tsc -b --noEmit` will now fail (expected, transiently) because `PHASE_FAMILY` and
`PHASE_PALETTE` are `Record<WorkflowPhase, ...>` and are missing the new key — this failure is the
correct intermediate state until Steps 2-3 land. Final verification is deferred to Step 5's full
compile run.

### Step 2 — Add `PHASE_FAMILY['Document-Update'] = 'build'`
**Files:** `dashboard-frontend/src/lib/phasePalette.ts`
**Change:** In the `PHASE_FAMILY` map (lines 56-66), add `'Document-Update': 'build'` on the same
line as the existing `build`-family entries: `Implement: 'build', 'Sync Docs': 'build', 'Document-Update': 'build',`.
Do not create a 9th `PhaseFamily` value — `'Document-Update'` joins the existing `build` family
exactly as the ticket's Scope item 2 specifies.
**Do NOT touch:** The `PhaseFamily` union type itself (lines 52-54, must stay at exactly 8
members), or any other `PHASE_FAMILY` entry/family assignment.
**Verify:** `phasePalette.test.ts`'s 8-family-cap test (`new Set(Object.values(PHASE_FAMILY)).size === 8`,
lines 66-68) — still passes after this change (Document-Update reuses `'build'`, no new distinct
value added). Full green run happens at Step 5; this step can be sanity-checked standalone via
`npx vitest run src/test/phasePalette.test.ts` (it will still fail on the completeness assertion
until Step 4, and on TS compile until Step 3 — expected until Step 4/5 land).

### Step 3 — Derive and validate the `PHASE_PALETTE['Document-Update']` hex
**Files:** `dashboard-frontend/src/lib/phasePalette.ts`
**Change:**
1. Derive a starting candidate hex by continuing the `build` family's established upward step:
   `Implement` (`#008300`, L≈0.5285) → `Sync Docs` (`#289724`, L≈0.5929, ΔL≈0.0644). Apply the same
   RGB-channel scaling pattern used for the `#008300 → #289724` step to `#289724`, holding hue
   constant, to produce a candidate landing near L≈0.658 (per investigation.md's headroom math —
   this is a *starting point* for validation, not the final answer).
2. Invoke the `dataviz` skill (via the `Skill` tool, `skill: "dataviz"`) and use its bundled
   `scripts/validate_palette.js` to run the three checks the ticket's Scope item 4 and the file's
   own header-comment convention specify, against `--color-bg-tertiary: #242835`:
   - (a) Categorical check on the 8 unchanged family base hues — regression re-run, expected
     unaffected (do NOT include `Document-Update` or any non-base hue in this list).
   - (b) `--ordinal` check on the `build` family specifically, now with 3 members
     (`#008300`, `#289724`, and the candidate hex, darkest-to-lightest order since `build` steps
     up) — confirms monotone lightness, ≥0.06 OKLCH L gap between adjacent members, single hue,
     `CHROMA_FLOOR` respected.
   - (c) Direct WCAG contrast check on the candidate hex alone against `#242835`.
3. If any check fails or WARNs unexpectedly (band ceiling exceeded, ordinal gap too small, hue/
   chroma drift), adjust the candidate hex and re-run until all three checks pass at least at the
   WARN level (a sub-3:1 contrast WARN is acceptable and precedented — e.g. `Implement` itself is
   already WARN-listed at 2.97:1 — but a hard FAIL on lightness band or CVD/hue separation is not
   acceptable and must be corrected).
4. Set `PHASE_PALETTE['Document-Update']` to the final validated hex, on the same line as the
   other `build`-family palette entries: `Implement: '#008300', 'Sync Docs': '#289724', 'Document-Update': '<final-hex>',`.
5. Record the actual validator invocations and their real output (not a paraphrase, not a
   hand-derived number) in this ticket's `## Implementation Notes` section — this is a
   ticket-acceptance-criterion requirement, not optional documentation.
**Do NOT touch:** `Implement`'s or `'Sync Docs'`'s existing hex values, any other family's hexes,
`chartPalette.ts`, the `#242835` surface constant, or any `--color-accent-*` token. Do not re-run
the categorical check across all 22 palette values as one list (per the header comment's explicit
warning at lines 18-21 — this would misfire on same-family adjacent pairs by design).
**Verify:** The three `validate_palette.js` invocations' real console output, cited verbatim (or
faithfully summarized with pass/warn/fail status per check) in Implementation Notes. This is the
authoritative verification for this step — it must not be skipped, faked, or replaced by
hand-derived OKLCH arithmetic.

### Step 4 — Update the header comment
**Files:** `dashboard-frontend/src/lib/phasePalette.ts`
**Change:** Update the header comment (lines 1-44) to reflect the confirmed 22-member state:
- Change "21 WORKFLOW_PHASES strings" / "21 phases" references (lines 1, 10) to 22.
- Add a line documenting `Document-Update`'s validation result under the three-way breakdown
  (lines 22-40) — its categorical/ordinal status, and its measured WCAG contrast ratio against
  `#242835`.
- If `Document-Update`'s measured contrast lands below 3:1, add it to the WARN-band list (lines
  38-40, e.g. `..., Report 2.68:1, Document-Update <ratio>:1.`) with the same mandatory-visible-
  label caveat already stated for the other WARN entries; if it clears 3:1, do not add it there.
**Do NOT touch:** Any other line of the header comment describing the other 8 families' or 21
other phases' already-recorded validator results.
**Verify:** No automated test reads the header comment directly, but the acceptance criterion
("header comment updated to state 22 total members and reflects any new WARN-band contrast entry
accurately") is diff-reviewed at Step 6.

### Step 5 — Update `phasePalette.test.ts`'s fixtures and assertions
**Files:** `dashboard-frontend/src/test/phasePalette.test.ts`
**Change:**
1. Add `'Document-Update'` to the `ALL_WORKFLOW_PHASES` literal array (lines 8-13), in the same
   position convention as the source file (end of array is fine, consistent with Step 1).
2. Update the completeness test's description string (line 45) from
   `'exports a key set exactly equal to the 21 distinct WORKFLOW_PHASES strings'` to
   `'exports a key set exactly equal to the 22 distinct WORKFLOW_PHASES strings'`. The assertion
   body itself (lines 46-47) needs no logic change — it already compares against
   `ALL_WORKFLOW_PHASES`, which Step 5.1 already extended.
3. Based on Step 3's actual measured contrast ratio for `Document-Update` against `#242835`:
   if it is below 3.0, add `'Document-Update'` to `KNOWN_CONTRAST_WARN` (lines 20-23); if it is
   ≥3.0, make no change here — the existing per-phase loop in the contrast test (lines 50-59)
   already covers it via the default ≥3.0 branch once `ALL_WORKFLOW_PHASES` includes it.
**Do NOT touch:** The 8-family-cap test (lines 66-68) or the `getPhaseColor` purity test (lines
61-64) — both are phase-agnostic and require no edit per test_plan.md's explicit "No changes
needed" items 4-5. Do not add `Document-Update` to `KNOWN_CONTRAST_WARN` speculatively — only if
the real measured ratio requires it.
**Verify:** `cd dashboard-frontend && npx vitest run src/test/phasePalette.test.ts` — all 4 tests
green.

### Step 6 — Update `docs/parity_ledger/infrastructure.yaml`'s `INFRA-302.v2_evidence`
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** `INFRA-302` (confirmed at lines 6472+ in the current file) has a distinct `v2_evidence`
field (not just `text`) that currently reads: `"dashboard-frontend/src/lib/phasePalette.ts:46-50
(WorkflowPhase union, 21 members), :52-54 (PhaseFamily union, 8 members), :56-66 (PHASE_FAMILY
mapping), :71-80 (PHASE_PALETTE mapping, 8 unchanged base hexes stepped by lightness within each
family), :83-85 (getPhaseColor(), pure passthrough). Validated via the dataviz skill's
scripts/validate_palette.js ... (1) categorical check ... (2) --ordinal check ... (3) direct
per-hex WCAG contrast check -- 8 of 21 entries sit in the same sub-3:1 ... tests/.../phasePalette.test.ts:45-48
(literal 21-key completeness, not Set-derived) ...".
Update this field to:
- Change `21 members` → `22 members` in the `WorkflowPhase` union citation.
- Re-confirm/update line-number citations for the union, `PHASE_FAMILY`, `PHASE_PALETTE`, and
  `getPhaseColor()` blocks if Steps 1-4's edits shifted any line numbers (they likely will, since
  the header comment grows).
- Add a note that the `build`-family ordinal check now covers 3 members (not just the original
  2-member state implicit in the prior text), citing Step 3's real validator result.
- Update `"8 of 21 entries sit in the same sub-3:1 ... WARN band"` to the correct new count out of
  22 (9 if `Document-Update` joined the WARN band, else still 8 of 22).
- Update the `phasePalette.test.ts` line citation (`:45-48`) if Step 5's edits shifted it.
Leave `status: verified` and `priority: P2` unchanged — this is an evidence-only refresh per the
ticket's explicit instruction, not a status change. Do not touch the `text` field's narrative
prose describing the original `TCK-20260720-ECHARTS-PHASE-PALETTE` ticket's work — that is a
historical record of what that ticket did and remains accurate; only `v2_evidence` (the
currently-true structural description) needs the refresh.
**Do NOT touch:** Any other `INFRA-*` entry in this file, the `status`/`priority`/`proof_type`/
`test_path`/`divergence_note`/`support_boundary` fields of `INFRA-302` itself, or the `text` field.
**Verify:** No automated test reads this YAML file's prose content; verification is manual
diff-review confirming only `v2_evidence` changed and the cited line numbers/counts are accurate
against the actual post-Step-4 file state.

### Step 7 — Full scoped regression
**Files:** none (verification only)
**Change:** Run, in order:
```
cd dashboard-frontend && npm run test -- --run
cd dashboard-frontend && npx tsc -b --noEmit
cd dashboard-frontend && npm run build
```
Also run the anti-drift diff check test_plan.md specifies:
```
git diff -- dashboard-frontend/src/lib/phasePalette.ts | grep '^[+-]' | grep -v 'Document-Update'
```
and confirm the only non-`Document-Update` lines in that filtered output are the header comment's
member-count/WARN-band-list updates (Step 4) — any other line is a scope violation requiring
investigation before proceeding.
**Do NOT touch:** Nothing new here — this step is verification-only, no file edits.
**Verify:** All three commands exit 0 with zero regressions in any existing test file (per
test_plan.md's Regression Surface, this includes `toChartOption.test.ts`, which imports
`PHASE_PALETTE` but does not assert an exact key count). The filtered `git diff` produces no
unexpected lines.

## Scope Guards

- No change to any other phase's existing `PHASE_FAMILY` or `PHASE_PALETTE` entry, or to any hex
  value outside the new `Document-Update` addition.
- No change to the `PhaseFamily` union (must stay exactly 8 members) — `Document-Update` reuses
  `'build'`, it does not justify or require a 9th family.
- No change to `.claude/agents/doc-updater.md`, `.claude/workflows/implement-ticket.js`,
  `tools/agent-monitoring/vocabulary.py`, or `registries/glossary_registry.jsonl` — all are
  sibling tickets' (`CORE-WIRING`, `VOCAB-REGISTRATION`) already-completed territory.
- No change to `chartPalette.ts`, any `--color-accent-*` token, or the `#242835` dark-surface
  constant.
- No change to any consumer of `phasePalette.ts` (e.g. `ProgressTimelineView.tsx`,
  `toChartOption.ts`) — this ticket only extends the data module.
- No new automated cross-language sync mechanism between `phasePalette.ts` and `vocabulary.py` —
  the manual-sync convention stays; this ticket is that manual sync step for `Document-Update`
  only.
- No re-run of the categorical check across all 22 palette values as a single list (would misfire
  on same-family adjacent pairs — see header comment lines 18-21).
- No status change to `INFRA-302` (`status: verified` stays) — evidence-only refresh.
- Do not touch `INFRA-302`'s `text`, `proof_type`, `test_path`, `divergence_note`, or
  `support_boundary` fields — only `v2_evidence`.
- Do not fabricate or hand-derive the final hex's validator output — Step 3 requires an actual
  `dataviz`-skill invocation with real cited output.

## Dependency Map

- Step 1 (union member) has no dependencies; it transiently breaks TS compile until Steps 2-3
  land — expected, not a defect.
- Step 2 (`PHASE_FAMILY` entry) depends on Step 1 (the union member must exist to key the map).
- Step 3 (hex derivation + validation) depends on Step 1 (union member must exist) but is
  independent of Step 2 — can be done in parallel with Step 2 in principle, though sequential
  Step 1→2→3 as ordered above is simplest to implement and review.
- Step 4 (header comment) depends on Step 3's confirmed validator output (needs the real contrast
  ratio and pass/warn status to document accurately).
- Step 5 (test file) depends on Step 1 (union member for `ALL_WORKFLOW_PHASES`) and Step 3 (needs
  the real measured contrast ratio to decide `KNOWN_CONTRAST_WARN` membership).
- Step 6 (parity ledger) depends on Steps 1-5 being finalized (line numbers and counts must
  reflect the final file states).
- Step 7 (regression) depends on all prior steps being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `WorkflowPhase` union has exactly 22 members including `'Document-Update'` | Step 1 | `npx tsc -b --noEmit` (Step 7); `phasePalette.test.ts` completeness test (Step 5) |
| `PHASE_FAMILY['Document-Update']` equals `'build'` | Step 2 | `phasePalette.test.ts` completeness test + 8-family-cap test |
| `PHASE_PALETTE['Document-Update']` valid, distinct hex, validated via `validate_palette.js` 3 ways, cited in Implementation Notes | Step 3 | Real `dataviz` skill invocation output (Step 3); `phasePalette.test.ts` contrast test |
| Header comment states 22 total members and accurate WARN-band entry | Step 4 | Manual diff review (Step 7's filtered `git diff`) |
| `ALL_WORKFLOW_PHASES` has exactly 22 entries incl. `'Document-Update'`; completeness assertion description says 22 | Step 5 | `phasePalette.test.ts` completeness test |
| `Document-Update` correctly placed in/out of `KNOWN_CONTRAST_WARN` per measured ratio | Step 3 (measurement) + Step 5 (test edit) | `phasePalette.test.ts` contrast test |
| `npm run test -- --run` passes, zero regressions | Steps 1-5 | Step 7 full suite run |
| `npx tsc -b --noEmit` and `npm run build` complete cleanly | Steps 1-3 (structural completeness) | Step 7 |
| Diff review: no other phase's `PHASE_FAMILY`/`PHASE_PALETTE` entry or `PhaseFamily` union altered | Steps 1-4 (additive-only discipline) | Step 7's filtered `git diff` |
| `INFRA-302.v2_evidence` updated to 22-member state, `status` remains `verified` | Step 6 | Manual diff review |
| Landing before `CORE-WIRING` produces zero runtime error / visual change | Steps 1-5 (no consumer touched, no import from `vocabulary.py`) | Step 7 full suite passing with no other file referencing `Document-Update` |

## Anti-Drift Notes

- The exact final hex is intentionally not fixed in this plan — Step 3 requires deriving a
  candidate then running the real `dataviz`-skill validator, adjusting if it fails, and citing the
  actual output. Do not treat the investigation's L≈0.658 headroom estimate as a pre-validated
  final answer; it is a starting point only, explicitly flagged in investigation.md as
  requiring the real validator run (hue/chroma drift from naive lightness-only interpolation is a
  named risk the validator — not hand math — must catch).
- Whether `Document-Update` joins `KNOWN_CONTRAST_WARN` is a live, measurement-dependent decision
  (Step 3's output, applied in Step 5) — not foreclosed by this plan. Both the WARN-add and
  no-op-leave-default paths are valid outcomes; pick the one the real number supports.
- `INFRA-302` does have a distinct `v2_evidence` field separate from `text` (confirmed by direct
  read of `docs/parity_ledger/infrastructure.yaml` at Plan time — resolves investigation.md's
  flagged schema-shape uncertainty). Step 6 edits `v2_evidence` only, not `text`.
- The `build` family is the sole family stepping *up* in lightness (all 7 others step down from a
  near-ceiling base) — do not apply the other families' downward-step convention by copy-paste
  habit when deriving the Step 3 candidate.
- The dataviz skill's `validate_palette.js` lives at a per-session bundled-skill path (not a
  stable repo path) — it must be invoked via the `Skill` tool (`skill: "dataviz"`) during this
  session, not referenced as a durable import or hardcoded script path in any committed file.
- `toChartOption.test.ts` must be re-confirmed (per test_plan.md) to have no hidden exact-key-count
  coupling to `PHASE_PALETTE` before Step 7's full run — if it does, that is new information
  requiring escalation back to Plan, not a silent fix.
- The exact final hex is Step 3's derive-then-validate task, not a blocking open question — the
  plan specifies the derivation method, the three required validator invocations, and the
  adjustment loop if validation fails. The `INFRA-302` schema-shape question flagged in
  investigation.md is resolved by Step 6: `v2_evidence` is a distinct field and is the correct
  edit target.
