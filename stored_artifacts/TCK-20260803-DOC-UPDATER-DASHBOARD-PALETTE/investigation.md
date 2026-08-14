---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE
artifact_type: investigation
tags: [dashboard, observability]
---

# Investigation — TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE

## Current Behavior

**`dashboard-frontend/src/lib/phasePalette.ts`** (confirmed by direct full read, 86 lines):

- `WorkflowPhase` union type (lines 46-50) currently has **21 members** — confirmed still 21, not
  22. Direct grep/diff confirms the sibling `TCK-20260803-DOC-UPDATER-CORE-WIRING` did **not**
  touch this file (its own "Out of Scope" section explicitly excludes it, and its "Related Code
  Areas" list does not include `phasePalette.ts`). `'Document-Update'` is absent from the union.
- `PHASE_FAMILY` map (lines 56-66): the `build` family currently has exactly 2 members —
  `Implement: 'build'` (line 60) and `'Sync Docs': 'build'` (line 60).
- `PHASE_PALETTE` hex values for the `build` family (lines 71-80): `Implement: '#008300'`,
  `'Sync Docs': '#289724'`.
- Header comment (lines 1-44) documents: (1) the file is hand-copied from
  `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES` with **no automated cross-language
  sync guard** (line 2-6); (2) validation methodology used at `TCK-20260720-ECHARTS-PHASE-PALETTE`
  time — three separate `validate_palette.js` invocations: (a) categorical check on the 8 family
  base hues, (b) `--ordinal` check per family (lightest→darkest, except `build` which is
  darkest→lightest), (c) direct WCAG contrast check per individual hex against
  `--color-bg-tertiary: #242835` (lines 16-40); (3) `build` is called out (line 68-70) as the one
  family stepping **up** in lightness from its base, opposite the other 7 families.
- `getPhaseColor()` (line 83-85): pure lookup, `PHASE_PALETTE[phase]`.

**Verified numerically** (recomputed OKLCH L using the exact matrix constants from
`validate_palette.js`'s `oklabFromLin()`, lines 88-97 of that script, not hand-approximated): `L(#008300) = 0.5285`, `L(#289724) = 0.5929` — ΔL ≈ 0.0644, consistent with the original plan's
documented "ΔL ≈ 0.065" step and confirming the *upward* stepping direction the ticket's Scope
item 3 describes. The dark-mode OKLCH lightness band ceiling used by `validate_palette.js` is
`0.67` (`BAND.dark = [0.48, 0.67]`, script line 39). A third `build` member continuing the same
~0.065 step would land at L ≈ 0.658 — inside the band but with only ≈0.012 headroom to the 0.67
ceiling. This is a real constraint, not just a formality (see Risks below).

**`dashboard-frontend/src/test/phasePalette.test.ts`** (confirmed by direct full read, 69 lines):
- `ALL_WORKFLOW_PHASES` literal array (lines 8-13): 21 entries, hardcoded independently of both
  `vocabulary.py` and `phasePalette.ts` itself (comment lines 4-7 explain this is intentional —
  catches local edits that silently change the key set).
- Completeness test (line 45): exact text is
  `'exports a key set exactly equal to the 21 distinct WORKFLOW_PHASES strings'` — the ticket's
  cited count (21) matches; must become 22.
- `KNOWN_CONTRAST_WARN` (lines 20-23): currently 8 entries (`Recalibrate`, `Link`, `Implement`,
  `Architecture-Verify`, `Classify Drift`, `Parity Check`, `Update Anchors`, `Report`) — all sit in
  the sub-3:1 "relief" WARN band, floored at ≥2.0 by the contrast test (lines 50-59). Whether
  `Document-Update` joins this set depends on its actual measured contrast ratio, which cannot be
  known until the final hex is chosen (see Risks).
- WCAG formula (`srgbToLinear`/`relativeLuminance`/`contrastRatio`, lines 29-42) is a local
  reimplementation matching `validate_palette.js`'s `contrast()` (that script's L86) since the
  script lives outside this repo and can't be imported at test time (comment lines 25-28).
- 4th test (line 66-68): asserts `new Set(Object.values(PHASE_FAMILY)).size === 8` — the 8-family
  cap. Adding `Document-Update: 'build'` does not change this count (still 8 distinct families),
  so this test needs no edit.

**`docs/parity_ledger/infrastructure.yaml`** — `INFRA-302` entry (lines 6472-6487): `text` field
currently describes `phasePalette.ts` as "covering all 21 hand-copied WORKFLOW_PHASES strings"
with no explicit line-number citations for the union/`PHASE_FAMILY`/`PHASE_PALETTE` blocks beyond
prose description. `status: verified`. This needs a `v2_evidence`/`text` refresh to the 22-member
state per the ticket's own Scope item 4 (a `v2_evidence` field is not present as a separate key in
this entry — the descriptive `text` field itself is what encodes "evidence" for this particular
entry's schema variant; the refresh target is that `text` field).

**dataviz skill location** (searched both `.agents/skills/` and `.claude/skills/` — neither
contains it; it is a *bundled* skill, not a repo-local one): resolved at
`/tmp/claude-1000/bundled-skills/2.1.220/591ab39d55e0b6efea7b8be10bff9186/dataviz/scripts/validate_palette.js` (also `validate_palette.py`, a mirror implementation). This confirms
`phasePalette.test.ts`'s own comment (lines 25-28) that the script "lives outside this repo and
cannot be imported at test time" — it is a per-session bundled-skill path, not a stable repo path,
so it cannot be referenced by a durable import or CI step, only invoked ad hoc by an agent running
the skill. CLI usage confirmed by header comment (script lines 1-37): `node validate_palette.js
"<hex,hex,...>" --mode dark --surface "#242835"` for the categorical check, add `--ordinal` for
the per-family ordinal check. Exit code 0 unless a hard FAIL; WARN bands (adjacent CVD 6-8 floor,
contrast sub-3:1) still exit 0.

## Mechanics / Engine Constraints

None. `phasePalette.ts` is dashboard-frontend visualization tooling (chart color mapping for the
Agent Ops Dashboard), not simulation logic. No `docs/mechanics/` chapter or `docs/engine/` contract
governs chart color selection or `WorkflowPhase` enumeration — confirmed by `search_docs` and
`graphify query` returning no `docs/mechanics/`/`docs/engine/` hits for this topic, and by the
existing header comment's own citations, which are entirely to the (external, non-mechanics)
dataviz skill's `references/` docs.

## Docs Requiring Update

None.

## Parity Ledger Overlap

- **INFRA-302** (`docs/parity_ledger/infrastructure.yaml`, lines 6472-6487) — `status: verified`,
  not `P0` (this entry has no separate `priority` line visible in the grepped block, but no `P0`
  marker was found; treat as non-blocking evidence refresh). Its `text` field currently states
  "covering all 21 hand-copied WORKFLOW_PHASES strings" — this must change to 22 once
  `Document-Update` is added, per this ticket's own Scope item 4 and CLAUDE.md's Authoritative
  Mechanics Rule ("if logic changes, update... the parity ledger entry... in the same session").
  `status` stays `verified` (this is an evidence refresh, not a status change, per the ticket's
  explicit instruction) — no `test_path` currently associated with this specific evidence claim
  beyond the general dashboard-frontend test suite, so no P0 blocking-test requirement applies.
- No other parity ledger entry across `docs/parity_ledger/*.yaml` references `phasePalette.ts`,
  `PHASE_FAMILY`, `PHASE_PALETTE`, or `WorkflowPhase` (confirmed: `INFRA-303`/`INFRA-304` cover
  `TimelineRangeControl`/adjacent dashboard tickets, not this file; the sibling
  `VOCAB-REGISTRATION` ticket's own `INFRA-316` covers `vocabulary.py`/`glossary_registry.jsonl`
  only, explicitly noting zero `phasePalette.ts` overlap in its own Implementation Notes).

## Prior Work

- **`stored_artifacts/TCK-20260720-ECHARTS-PHASE-PALETTE/`** (`investigation.md`, `plan.md`,
  `test_plan.md`) — the ticket that originally built `phasePalette.ts` and `phasePalette.test.ts`.
  `plan.md`'s "Resolved Decisions #4" (lines 52-64) is the governing precedent this ticket must
  follow: for 7 of 8 families, the pre-validated base hex sits near the dark band's 0.67 ceiling,
  so those families step *darker* by ΔL ≈ 0.065 per member. `build` (green, base L = 0.53) is the
  sole exception — its base sits in the *lower* half of the band, so it steps *lighter* instead
  (`Sync Docs` = base + 0.065). This is exactly the asymmetry the current ticket's Scope item 3
  correctly identifies and continues. `plan.md` also fixed the parity-ledger placement precedent
  (append a new entry rather than editing an older one) — not directly reused here since this
  ticket is an evidence *refresh* of the same `INFRA-302` entry that ticket created, not a new
  entry.
- **`TCK-20260803-DOC-UPDATER-CORE-WIRING`** (done) and **`TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`**
  (done) — both siblings independently confirmed the literal phase name is exactly
  `'Document-Update'` (hyphenated, capital D on both words) — `CORE-WIRING`'s `phase('Document-Update')`
  wiring into `implement-ticket.js` and `VOCAB-REGISTRATION`'s literal addition to
  `WORKFLOW_PHASES["implement-ticket"]` both use this exact string, matching this ticket's own
  Scope. No divergence found between the three tickets' literal spelling.
- **`TCK-20260720-PROGRESS-TIMELINE-VIEW`** / **`TCK-20260730-PROGRESS-TIMELINE-VIEW-HOTFIX`**
  (done) — the only consumers of `phasePalette.ts` for actual chart rendering
  (`ProgressTimelineView.tsx`, via `toChartOption.ts`). Confirmed out of scope for this ticket
  (data module only); graphify's dependency traversal shows `toChartOption.ts`/`toChartOption.test.ts`
  import `PHASE_PALETTE`/`CHART_LEGEND_ENTRIES` but neither is touched by this ticket's diff.
- REGISTRY.yaml query (`related_code_areas`/`tags` overlap for `dashboard`) surfaced ~28 dashboard-
  tagged tickets; none besides `TCK-20260720-ECHARTS-PHASE-PALETTE` and the two just-closed
  siblings reference `phasePalette.ts` specifically.

## Risks and Open Questions

- **Why "Docs Requiring Update" is None (rationale).** The only `docs/`-tree path this ticket's
  Scope touches is `docs/parity_ledger/infrastructure.yaml` (`INFRA-302`'s evidence refresh). Per
  `docs/architecture/doc_updater_agent.md`'s scope-boundary table and the sibling
  `TCK-20260803-DOC-UPDATER-CORE-WIRING` ticket's own confirmed Out-of-Scope note, `docs/parity_ledger/*.yaml`
  entries are explicitly excluded from the `Document-Update` phase's/doc-updater agent's remit —
  they are Parity phase's (parity-updater agent's) job, which runs later in the same standard-tier
  pipeline regardless of what this section lists. This ticket's own Scope section (item 4) already
  directs that update as a first-class Implement-time deliverable in its own right, independent of
  the `## Docs Requiring Update` → doc-updater mechanism. No other `docs/` prose path (guideline,
  mechanics chapter, engine contract, `docs/guides/*`, etc.) describes `phasePalette.ts`'s content
  or the `WorkflowPhase` union — `docs/architecture/doc_updater_agent.md` is cited in this ticket's
  Related Docs only as the authoritative *source* design doc this ticket implements a sub-item of,
  not as a doc requiring an update itself.
- **Exact hex value for `Document-Update` is not pre-determined and requires the actual validator
  run, not hand-derivation** — flagged for Plan's decision, per the ticket's own explicit
  instruction ("Invoke the actual `dataviz` skill to do this... do not hand-derive the numbers").
  This investigation independently recomputed the underlying OKLCH math (same matrix constants as
  `validate_palette.js`) purely to characterize headroom, not to select a final value: continuing
  the `build` family's established +0.065 ΔL step from `'Sync Docs'` (L=0.5929) lands at L≈0.658,
  only ≈0.012 below the dark-mode band ceiling of 0.67. This is tight but should still pass the
  ordinal check's `ORDINAL_MIN_DL = 0.06` floor and the band ceiling — however, the exact hex
  requires holding hue and chroma consistent with the other two `build`-family members (same green
  hue, `CHROMA_FLOOR = 0.10` respected) which only the actual `validate_palette.js` run can confirm
  deterministically; a naive lightness-only interpolation risks a hue or chroma drift the validator
  would catch. **Recommendation for Plan**: continue the same upward-step direction and
  approximately the same ΔL magnitude (~0.065) as the `Implement → Sync Docs` step, derive the
  candidate hex by adjusting `#289724` lighter while holding hue constant (i.e., roughly following
  the same RGB-channel scaling pattern `#008300 → #289724` already used), then run
  `validate_palette.js` the three ways the Scope section specifies to confirm/adjust before
  finalizing. Do not skip the actual validator invocation even though this investigation's
  headroom math suggests the step should pass — the ticket's acceptance criteria requires cited
  validator output in Implementation Notes, not a hand-derived number.
- **Contrast ratio outcome is unknown until the hex is fixed**, which determines whether
  `Document-Update` must be added to `KNOWN_CONTRAST_WARN` in the test file (acceptance criterion,
  ticket lines 120-122). All three current `build`-family/adjacent-lightness-stepped-darker
  families' WARN-band members happen to be the *base* (lightest, in 7-of-8 families) or otherwise
  darker members; `Document-Update` would be the *lightest* member of `build` if the step direction
  holds, and lighter colors generally have *higher* contrast against a dark surface, not lower —
  so it is plausible (not certain) that `Document-Update` clears the ≥3.0 floor without needing the
  WARN allowlist, unlike `Implement` (`build`'s base, at 2.97:1, already WARN-listed). This must
  still be measured, not assumed — the acceptance criteria treats "which of the two paths" as a
  live decision, not foreclosed.
- **`docs/parity_ledger/infrastructure.yaml`'s `INFRA-302` entry has no distinct `v2_evidence` key**
  visible in the grepped block (lines 6472-6487) — it uses a single `text` field that reads more
  like a combined text+evidence narrative than this repo's more common `v2_evidence`-as-separate-
  field schema. Plan/Implement should re-confirm this entry's exact schema shape (via
  `docs/parity_ledger/schema.json`) before editing, since "update `v2_evidence`" as literally
  phrased in the ticket's Scope may map to editing this entry's `text` field rather than a
  separate `v2_evidence:` key. Not a blocking ambiguity — either way the target is the same YAML
  entry — but worth Plan flagging precisely which sub-field changes.

## Anti-Drift Hazards

- Do not touch any other phase's existing `PHASE_FAMILY` or `PHASE_PALETTE` entry, or any hex
  value outside the new `Document-Update` addition — the ticket's Out of Scope and acceptance
  criteria (diff review) both require additive-only changes.
- Do not touch the 8-family `PhaseFamily` union itself (lines 52-54) — `Document-Update` joins the
  existing `build` family; it does not need or justify a 9th family. The dataviz skill's own
  categorical hue cap (8 slots, `references/anti-patterns.md`) is architecture, not a soft
  guideline.
- Do not re-run the categorical check across all 22 palette values as one list — per the existing
  header comment's explicit warning (lines 18-21), the categorical check's CVD/normal-vision-floor
  gates assume every adjacent pair is meant to be hue-distinct, which is false by design for
  same-family members; misapplying it would produce spurious FAILs/WARNs unrelated to the real
  8-family categorical set.
- Do not introduce a new automated cross-language sync mechanism between `phasePalette.ts` and
  `vocabulary.py` — the manual-sync convention is intentional and explicitly preserved (ticket Out
  of Scope item 5); this ticket is that manual sync step for `Document-Update`, not a mechanism
  change.
- Do not edit `chartPalette.ts`, `--color-accent-*` tokens, or the `#242835` dark surface constant
  — none are in scope, and `chartPalette.ts`'s own prior investigation already rejected the
  `--color-accent-*` tokens for chart fills (header comment lines 42-44).
- Do not let the `INFRA-302` v2_evidence/text refresh drift into a `status` change — the ticket is
  explicit that `status: verified` is unchanged, this is an evidence-only correction.
- Do not treat this ticket's landing as requiring `TCK-20260803-DOC-UPDATER-CORE-WIRING` to have
  landed first — confirmed independently by both this ticket and its own Assumptions section: no
  ordering dependency exists, and `CORE-WIRING` is in fact already done, so this concern is now
  moot in practice, but the code path itself still has no coupling either direction.
