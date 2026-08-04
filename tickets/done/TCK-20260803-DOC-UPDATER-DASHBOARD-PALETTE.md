---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE
phase: done
date: 2026-08-03
tags: [dashboard, observability]
---

# TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE

## Title
doc-updater Document-Update phase — dashboard-frontend phase-palette registration

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Third of three child tickets under `TCK-20260803-DOC-UPDATER-EPIC` (scope-only epic, tracking).
Implements exactly sub-item 3 of the design doc's (`docs/architecture/doc_updater_agent.md`)
"## Consequences" → "Monitoring/retro/dashboard registration" bullet: registers the new
`Document-Update` phase in `dashboard-frontend/src/lib/phasePalette.ts` (the `WorkflowPhase`
union, `PHASE_FAMILY`, and `PHASE_PALETTE` maps) and updates its completeness test,
`dashboard-frontend/src/test/phasePalette.test.ts`. Sub-items 1, 2, and 4 (`vocabulary.py`,
`glossary_registry.jsonl`, the vocabulary-count test) are `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`'s
job; the agent/phase definition and `implement-ticket.js` wiring are
`TCK-20260803-DOC-UPDATER-CORE-WIRING`'s job. Neither sibling is duplicated here.

This ticket's change is purely additive TypeScript data (a union member, two map entries, one
hex color) with **no runtime effect and no visual change** until `Document-Update` phase events
actually start flowing (i.e. until `CORE-WIRING` lands and the phase is live). Confirmed by
direct read of `phasePalette.ts`: unlike `VOCAB-REGISTRATION`'s target (`vocabulary.py`, which
has an active write-time drift check against a canonical set), this file has **no automated
validation coupling** to `vocabulary.py` at all — only a hand-maintained header comment noting
the sync is manual. So landing this ticket before `CORE-WIRING` produces zero runtime error and
zero drift warning; it just adds an unused (but harmless) mapping entry. This is the opposite
graceful-degradation profile from the vocab-registration sibling and is priced into this
ticket's `P3` (cosmetic/non-blocking) priority.

## Scope
- `dashboard-frontend/src/lib/phasePalette.ts`:
  1. Add `'Document-Update'` as the 22nd member of the `WorkflowPhase` union type (currently 21
     members, lines 46-50).
  2. Add `'Document-Update': 'build'` to the `PHASE_FAMILY` map (lines 56-66) — the `build`
     family, alongside `Implement` and `'Sync Docs'` (direct precedent: both are
     implement-ticket's/simq-audit's doc-update-adjacent build-stage phases).
  3. Add a `PHASE_PALETTE['Document-Update']` hex value (lines 71-80) stepped within the `build`
     family's existing OKLCH-lightness band. `build` is the one family documented (header
     comment, lines 68-70) as stepping **up** in lightness from its base (`Implement: '#008300'`
     → `'Sync Docs': '#289724'`), the opposite of the other 7 families — the new hex continues
     that same direction/step size, not a new hue.
  4. Re-validate via the dataviz skill's `scripts/validate_palette.js`, using the same
     methodology the file's header comment documents (lines 16-40) and the original
     `TCK-20260720-ECHARTS-PHASE-PALETTE` ticket ran: (a) categorical check on the 8 unchanged
     family base hues (regression re-run, expected unaffected), (b) `--ordinal` check on the
     `build` family specifically, now with 3 members instead of 2, (c) direct WCAG contrast
     check on the new hex alone against `--color-bg-tertiary: #242835`. Invoke the actual
     `dataviz` skill to do this, per this ticket's own instructions — do not hand-derive the
     numbers.
  5. Update the header comment (member count, and the WARN-band list at lines 37-40 if the new
     hex's contrast ratio lands below 3:1) to stay accurate, matching the file's own established
     convention of documenting validator results inline.
- `dashboard-frontend/src/test/phasePalette.test.ts`:
  1. Add `'Document-Update'` to the literal `ALL_WORKFLOW_PHASES` array (lines 8-13).
  2. Update the completeness test's description/count (line 45: "exactly equal to the 21
     distinct WORKFLOW_PHASES strings") from 21 to 22.
  3. If the new hex's contrast ratio against `#242835` is below 3.0, add `'Document-Update'` to
     `KNOWN_CONTRAST_WARN` (lines 20-23); otherwise leave it to the default ≥3.0 assertion path.
- `docs/parity_ledger/infrastructure.yaml`: update the `INFRA-302` entry's `v2_evidence` (member
  count and line-number citations currently describe 21 members) to reflect the new 22-member
  state, per CLAUDE.md's Authoritative Mechanics Rule ("if logic changes, update the
  corresponding... parity ledger entry... in the same session"). `status` stays `verified`;
  this is an evidence refresh, not a status change.
- Run the full scoped regression: `cd dashboard-frontend && npm run test -- --run`, `npx tsc -b
  --noEmit`, `npm run build`.

## Out of Scope
- Creating `.claude/agents/doc-updater.md` or wiring the `Document-Update` phase into
  `.claude/workflows/implement-ticket.js` — `TCK-20260803-DOC-UPDATER-CORE-WIRING`'s job.
- Any change to `tools/agent-monitoring/vocabulary.py` or `registries/glossary_registry.jsonl`
  (`WORKFLOW_PHASES`, `WORKFLOW_AGENTS`, or the new glossary `phase` entry) —
  `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`'s job.
- Any change to the 8-family `PhaseFamily` taxonomy itself, or to any other phase's existing
  `PHASE_FAMILY`/`PHASE_PALETTE` entry or hex value — additive-only for `Document-Update`.
- Any rendering/UI/chart-component integration work consuming `phasePalette.ts` (e.g.
  `ProgressTimelineView.tsx`) — this ticket only extends the data module, not any consumer.
- Adding a new automated cross-language sync guard between `phasePalette.ts` and
  `vocabulary.py` — the manual-sync convention established by `TCK-20260720-ECHARTS-PHASE-PALETTE`
  stays; this ticket is that manual sync step for `Document-Update` specifically, not a
  mechanism change.
- Any change to `chartPalette.ts`, the app's `--color-accent-*` tokens, or the dark chart
  surface constant (`#242835`).
- `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced` or
  any Python-side vocabulary-count test — `VOCAB-REGISTRATION`'s job.

## Acceptance Criteria
- [x] `dashboard-frontend/src/lib/phasePalette.ts`'s `WorkflowPhase` union type has exactly 22
      members, including `'Document-Update'`.
- [x] `PHASE_FAMILY['Document-Update']` equals `'build'`.
- [x] `PHASE_PALETTE['Document-Update']` is a valid 6-digit hex string, distinct from every other
      hex in the map (including the other two `build`-family hexes, `'#008300'`/`'#289724'`),
      produced and validated via the dataviz skill's `scripts/validate_palette.js` run the 3 ways
      described in Scope — validator invocations and output cited in Implementation Notes.
- [x] `phasePalette.ts`'s header comment is updated to state 22 total members and reflects any
      new WARN-band contrast entry accurately.
- [x] `dashboard-frontend/src/test/phasePalette.test.ts`'s `ALL_WORKFLOW_PHASES` literal array
      contains exactly 22 entries including `'Document-Update'`, and the completeness assertion's
      description references 22, not 21.
- [x] If `'Document-Update'`'s measured contrast ratio against `#242835` is below 3.0, it is added
      to `KNOWN_CONTRAST_WARN`; otherwise it passes the default ≥3.0 floor assertion — one or the
      other is true and test-enforced, not left ambiguous.
- [x] `cd dashboard-frontend && npm run test -- --run` passes with zero regressions in any
      existing test file, plus all `phasePalette.test.ts` assertions green.
- [x] `cd dashboard-frontend && npx tsc -b --noEmit` and `npm run build` both complete cleanly.
- [x] Diff review confirms no other phase's existing `PHASE_FAMILY`/`PHASE_PALETTE` entry and no
      member of the `PhaseFamily` union was altered — additive-only plus the header-comment/test
      count bump.
- [x] `docs/parity_ledger/infrastructure.yaml`'s `INFRA-302` entry `v2_evidence` is updated to
      cite the 22-member state and current line numbers; `status` remains `verified`.
- [x] Zero runtime error and zero unintended visual change in the dashboard from this ticket's
      addition (confirmed by the full existing test suite passing). Scoping-time framing assumed
      this ticket might land *before* `TCK-20260803-DOC-UPDATER-CORE-WIRING`; in the actual
      implementation order both `TCK-20260803-DOC-UPDATER-CORE-WIRING` and
      `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION` landed first, so `'Document-Update'` was
      already referenced elsewhere (`implement-ticket.js`, `vocabulary.py`,
      `agent-orchestration/workflows/implement-ticket.yaml`) by the time this ticket ran — the
      underlying graceful-degradation property (no coupling, no runtime error either direction)
      is confirmed by the same passing test suite, just not via the literal "lands first" ordering
      originally anticipated.

## Related Tickets
- TCK-20260803-DOC-UPDATER-EPIC (parent, scope-only epic tracking all three child tickets).
- TCK-20260803-DOC-UPDATER-CORE-WIRING (sibling, in progress) — creates `.claude/agents/doc-updater.md`
  and wires the `Document-Update` phase into `implement-ticket.js`; this ticket's addition is
  inert until that sibling lands.
- TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION (sibling, in progress) — Python-side
  `vocabulary.py`/`glossary_registry.jsonl` registration; not touched here.
- TCK-20260720-ECHARTS-PHASE-PALETTE (done) — original ticket that created `phasePalette.ts` and
  `phasePalette.test.ts`, established the 8-family/OKLCH-stepping convention and the
  hand-sync-only relationship to `vocabulary.py` this ticket extends.
- TCK-20260720-PROGRESS-TIMELINE-VIEW / TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX (done) —
  consumers of `phasePalette.ts` for chart rendering; not touched by this ticket (Out of Scope).

## Related Docs
- `docs/architecture/doc_updater_agent.md` — authoritative design doc; "## Consequences" →
  "Monitoring/retro/dashboard registration" bullet, sub-item 3, is exactly what this ticket
  implements.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-302` entry documents `phasePalette.ts`'s
  current (21-member) structure and line numbers; requires an evidence-only update as part of
  this ticket (see Scope).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260720-ECHARTS-PHASE-PALETTE/` (`investigation.md`, `plan.md`,
  `test_plan.md`) — original design rationale for the 8-family/OKLCH-lightness-stepping scheme,
  the `build`-family lightness-direction exception, and the WARN-band contrast handling this
  ticket must follow exactly.

## Related Code Areas
- `dashboard-frontend/src/lib/phasePalette.ts`
- `dashboard-frontend/src/test/phasePalette.test.ts`
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-302` entry)

## Assumptions / Open Questions
- Assumes the exact hex value for `'Document-Update'` is not pre-determined by the design doc —
  it must be derived at implementation time via the dataviz skill's `validate_palette.js` against
  the `build` family's existing two hexes (`#008300` base, `#289724` first step), continuing the
  same upward-lightness-step direction and ≥0.06 OKLCH L gap convention.
- `layer: observability` chosen to match both `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`
  (sibling) and `TCK-20260720-ECHARTS-PHASE-PALETTE` (the ticket that originally built this exact
  file) — dashboard-frontend visualization tooling, not a gameplay/simulation layer. No new
  `dashboard`-specific layer value exists in `registries/layer_registry.jsonl`; `observability` is
  the established fit for this file.
- Confirmed by direct read of `phasePalette.ts` (no import from, or validator run against,
  `vocabulary.py`) that this ticket degrades gracefully if it lands before `CORE-WIRING`: an
  unused union member/map entry causes no TypeScript compile error (all three maps stay fully
  keyed), no test failure, and no drift warning, unlike the `VOCAB-REGISTRATION` sibling's target
  which does have an active write-time drift check.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-302` entry was found during the mandatory
  parity-ledger scan to directly describe `phasePalette.ts`'s exact member count and line
  numbers — a real overlap, despite this ticket's originating request expecting none (dashboard
  tooling, not simulation mechanics). Treated as in-scope per CLAUDE.md's Authoritative Mechanics
  Rule (parity ledger entries must be kept current when the described behavior/file changes), not
  a new or separate parity concern requiring escalation.
- Assumes `TCK-20260803-DOC-UPDATER-CORE-WIRING` has not necessarily landed by the time this
  ticket is implemented — no ordering dependency is enforced between the two sibling tickets;
  this ticket's acceptance criteria hold regardless of landing order.

## Implementation Notes

Followed plan.md's 7 steps exactly, in order.

**Steps 1-2**: Added `'Document-Update'` as the 22nd `WorkflowPhase` union member (appended after
`'Report'`, `phasePalette.ts:56`) and `'Document-Update': 'build'` to `PHASE_FAMILY`
(`phasePalette.ts:66`), on the same line as `Implement`/`'Sync Docs'`.

**Step 3 — hex derivation and real validator invocation** (the critical step):

Derivation: recomputed OKLCH L/C/H for `#008300` and `#289724` using the exact same matrix
constants as `validate_palette.js`'s `oklabFromLin()` (a scratch Node script, not committed):
`Implement` L=0.5285 C=0.1798 H=142.50°, `Sync Docs` L=0.5929 C=0.1796 H=142.50° (ΔL=0.0644,
matching investigation.md). Continued the same +0.0644 ΔL step from `Sync Docs`, holding hue and
chroma constant (standard Ottosson OKLab→linear-sRGB inverse matrices), landing at target
L≈0.6573 → candidate hex `#41ab3b`. Round-trip check confirmed L=0.6563, C=0.1793, H=142.40°
(hue/chroma preserved within floating-point rounding).

Real `dataviz`-skill invocation (Skill tool, `skill: "dataviz"`, base dir
`/tmp/claude-1000/bundled-skills/2.1.220/591ab39d55e0b6efea7b8be10bff9186/dataviz`), then
`node scripts/validate_palette.js` run three ways exactly as Scope item 4 specifies:

1. **Categorical regression, 8 unchanged family base hues** (exact hex order taken from
   `stored_artifacts/TCK-20260720-ECHARTS-PHASE-PALETTE/plan.md:292`, the original validated
   order — NOT `Document-Update` or any non-base hue):
   ```
   node scripts/validate_palette.js "#3987e5,#d95926,#199e70,#c98500,#d55181,#008300,#9085e9,#e66767" --mode dark --surface "#242835"
   ```
   Output: `[PASS] Lightness band`, `[PASS] Chroma floor`, `[PASS] CVD separation` (worst adjacent
   `#c98500`↔`#199e70` ΔE 8.4 protan / 8.7 tritan), `[PASS] Normal-vision floor` (worst adjacent
   `#d55181`↔`#c98500` ΔE 19.3), `[WARN] Contrast vs surface` (`#008300` at 2.97:1, pre-existing) —
   `→ ALL CHECKS PASS`. Identical to the originally-documented result; confirms zero regression.

2. **`--ordinal` check, `build` family, now 3 members, darkest→lightest**:
   ```
   node scripts/validate_palette.js "#008300,#289724,#41ab3b" --ordinal --mode dark --surface "#242835"
   ```
   Output: `[PASS] Lightness monotone`, `[PASS] Adjacent ΔL` (all gaps >=0.06), `[PASS] Light-end
   contrast` (`#008300` at 2.97:1), `[PASS] Single hue` (hue spread 0°) — `→ ALL CHECKS PASS`.

3. **Direct WCAG contrast check on the candidate hex alone**:
   ```
   node scripts/validate_palette.js "#41ab3b" --mode dark --surface "#242835"
   ```
   Output: `[PASS] Lightness band`, `[PASS] Chroma floor`, `[PASS] Contrast vs surface` (all 1 >=
   3:1) — `→ ALL CHECKS PASS`. Exact numeric ratio computed via the script's own exported
   `contrast()` function: `contrast('#41ab3b', '#242835') = 4.974`.

All three checks passed cleanly at the PASS level (no adjustment/re-run needed — the candidate's
first derivation already satisfied every check). `PHASE_PALETTE['Document-Update']` set to
`'#41ab3b'` (`phasePalette.ts:81`).

**Step 4**: Header comment updated — "21 WORKFLOW_PHASES strings"/"21 phases"/"21 values" → 22
throughout (lines 1, 3, 10, 19, 34), added a sentence under check 2 documenting `build`'s new
3-member ordinal PASS result, and a sentence under check 3 noting `Document-Update` clears the
floor at 4.97:1 and is NOT added to the WARN-band list (since 4.974 >= 3.0).

**Step 5**: `phasePalette.test.ts` — added `'Document-Update'` to `ALL_WORKFLOW_PHASES` (line 13),
updated the completeness test's description string 21→22 (line 46). `KNOWN_CONTRAST_WARN` left
unchanged (no `Document-Update` entry added) because the real measured ratio (4.974) is >= 3.0 —
the default branch in the existing per-phase contrast-test loop already covers it correctly once
`ALL_WORKFLOW_PHASES` includes it.

**Step 6**: `docs/parity_ledger/infrastructure.yaml`'s `INFRA-302.v2_evidence` field updated:
member count 21→22, line-number citations refreshed to the post-header-comment-growth state
(union now `:51-56` not `:46-50`, `PhaseFamily` `:58-60`, `PHASE_FAMILY` `:62-72`, `PHASE_PALETTE`
`:77-86`, `getPhaseColor()` `:89-91`), added a note on the `build` family's now-3-member ordinal
PASS citing the real validator result, updated "8 of 21" → "8 of 22" WARN-band count (unchanged
count — `Document-Update` did not join it), and updated the `phasePalette.test.ts` line citations
(`:45-49`, `:51-60`, `:62-65`, `:67-69` — all shifted by +1 line from the new
`ALL_WORKFLOW_PHASES` array entry). `status: verified`, `priority: P2`, `proof_type`, `test_path`,
`divergence_note`, `support_boundary`, and `text` all left untouched, per plan.

**Step 7**: Full regression — see Test Summary. Filtered `git diff` confirmed only
`Document-Update`-bearing lines and the header-comment count/WARN-band updates were touched; no
other phase's `PHASE_FAMILY`/`PHASE_PALETTE` entry or the `PhaseFamily` union was altered.

No deviations from plan.md — all 7 steps executed exactly as specified, including the derive-then-
validate-then-adjust-if-needed loop (no adjustment was needed; the first derived candidate passed
all three checks cleanly).

## Test Summary

- `cd dashboard-frontend && npm run test -- --run`: 15 test files, 141 tests, all passed. (Canvas
  `getContext()` "Not implemented" warnings are pre-existing jsdom noise from unrelated chart
  components, not related to this change.)
- `cd dashboard-frontend && npx tsc -b --noEmit`: exit 0, clean.
- `cd dashboard-frontend && npm run build`: exit 0, clean (`tsc -b && vite build` succeeded; the
  850KB chunk-size warning is pre-existing and unrelated to this additive change).
- `git diff -- dashboard-frontend/src/lib/phasePalette.ts | grep '^[+-]' | grep -v 'Document-Update'`:
  only header-comment count/WARN-band updates and the two `-`-side lines that got
  `Document-Update` appended (their pre-edit form necessarily lacks the string) — no other phase's
  entry touched.
- Real `dataviz`-skill `validate_palette.js` invocations (3): all ALL CHECKS PASS, cited verbatim
  above in Implementation Notes.

## Files Changed

- `dashboard-frontend/src/lib/phasePalette.ts` — added `'Document-Update'` union member,
  `PHASE_FAMILY['Document-Update'] = 'build'`, `PHASE_PALETTE['Document-Update'] = '#41ab3b'`,
  updated header comment (22-member count, build's 3-member ordinal result, WARN-band note).
- `dashboard-frontend/src/test/phasePalette.test.ts` — added `'Document-Update'` to
  `ALL_WORKFLOW_PHASES`, updated completeness test description 21→22.
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-302.v2_evidence` refreshed to the 22-member
  state (line citations, member counts, build-family 3-member ordinal note, WARN-band count);
  `status`/`priority`/`proof_type`/`test_path`/`divergence_note`/`support_boundary`/`text`
  unchanged.

## Completion Summary

Registered the 22nd `WorkflowPhase`, `'Document-Update'`, into `dashboard-frontend/src/lib/phasePalette.ts`
as a purely additive change: a new union member, a `PHASE_FAMILY` entry joining the existing
`build` family, and a `PHASE_PALETTE` hex (`#41ab3b`) continuing `build`'s established upward-
OKLCH-lightness step from `Sync Docs`. The hex was derived (continuing the +0.0644 ΔL step,
hue/chroma held constant) and then validated by three real invocations of the `dataviz` skill's
`scripts/validate_palette.js` — categorical regression on the 8 family base hues (ALL PASS, matches
original), `--ordinal` check on `build`'s now-3 members (ALL PASS), and direct WCAG contrast on the
new hex (PASS, 4.974:1, above the 3.0 floor — not WARN-listed). Header comment, test fixtures, and
`INFRA-302.v2_evidence` were updated to match. Full regression (141 vitest tests, `tsc -b
--noEmit`, `vite build`) passed clean, and a filtered `git diff` confirmed no other phase's
existing `PHASE_FAMILY`/`PHASE_PALETTE` entry was altered. All acceptance criteria met; ticket
ready to move to `tickets/done/`.

