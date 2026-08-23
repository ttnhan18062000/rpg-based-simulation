---
status: active
layer: frontend
authority: P2
audience: agent
tags: [audit, hud, design-system]
---

# D27 — Frontend HUD & Visual Design Quality

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | New — no existing group covers frontend/HUD; closest analogues are Group C (Developer Tooling, e.g. D17 Documentation Currency) and D12 (Pattern Consistency), neither of which reaches `frontend/src/` |
| **State** | `none` — not yet audited. This file states *what the audit would check and why*, not findings; per direct instruction, a complete run isn't expected yet. |
| **Impact** | *not yet scored* — no Impact/Interest rating assigned; that's a judgment call for whoever formally schedules this dimension, not asserted here |
| **Interest** | *not yet scored* |
| **Method** | code-read + measure (WCAG contrast/categorical-palette-size checks are directly computable, not just reviewable) |
| **Audit date** | none |

**What this dimension would answer:** Is the player-facing frontend (`frontend/src/**`) well-designed and
internally consistent — information architecture, visual/color encoding, and interaction usability — the
same way D12 (Pattern Consistency) and D17 (Documentation Currency) ask "is this codebase/doc-set internally
consistent" for backend code and docs, but for the frontend's design surface, which no existing dimension
reaches at all.

**Why this gap exists, not asserted from nothing:** confirmed directly — none of D01–D25 touch
`frontend/src/`. D17 (Documentation Currency) audits `docs/mechanics/` and `docs/engine/`, not UI docs. D12
(Pattern Consistency) audits backend architectural patterns (Domain Phase class, decision/mutation
separation), not frontend component/design patterns. The engine's simulation-quality and codebase-health
audit programme has no equivalent for "is the thing a human actually looks at well-designed."

**Related dimensions:**
- D12 (Pattern Consistency) — same *kind* of question (internal consistency, duplication risk), different
  layer (frontend components/constants instead of backend domain phases).
- D17 (Documentation Currency) — same *method* (spot-check claims/values against real source), applied here
  to design claims (e.g. "this color is distinguishable from that one") instead of doc claims.
- `docs/simulation_quality/quality_scoring_contract.md` and
  `docs/plans/world_rendering/idea_world_render_validation.md` — the two existing "sibling scoring system"
  precedents this dimension's eventual scoring, if it gets one, should follow rather than reinvent.

---

## Expected Scope — what this audit would actually check

Two real investigation threads already exist and directly define this dimension's expected checklist —
this section states what's *expected*, sourced from real findings already made, not invented in the
abstract:

### From `docs/plans/idea_hud_quality_measurement.md`

- **Findability** — can an observer locate a named entity/event in bounded time/clicks? (Not yet measured
  against this project's real HUD.)
- **Detection** — does the observer notice a real anomaly/event before it's stale? (Not yet measured.)
- **Context Preservation** — does switching panels/modes lose prior state? **Partially known already**:
  `Sidebar.tsx:43-49`'s auto-switch effect is confirmed one-way with no restore path (a real, already-cited
  finding, not a guess) — `TCK-20260822-DURABLE-SELECTION-STATE` is the ticket meant to fix it. This
  dimension would re-check that fix once implemented, not assume it worked.
- **Density Legibility** — do glance-critical elements read without drill-down; is chrome-vs-canvas
  real-estate reasonable? (Not yet measured; the doc explicitly dropped an unverified "200ms"/"80-20" figure
  rather than assume a threshold — this dimension would need to establish its own real threshold via
  measurement, not import an unverified external number.)

### From `docs/plans/idea_hud_color_asset_system.md`

- **Color-table inventory and duplication** — **already confirmed, not hypothetical**: 9 separate raw-hex
  color tables across 7 files, ~200+ values. The building-type-to-color mapping is independently hardcoded
  in 4 places, already out of sync (`BuildingPanel.tsx`'s copy is missing `class_hall`). This audit would
  track whether that gets consolidated, and whether new duplication creeps back in afterward.
- **WCAG contrast compliance** — **already confirmed, not hypothetical**: computed real contrast ratios
  against this project's actual `STATE_COLORS`; `COMBAT` vs `ALERT` measured at a 1.00 contrast ratio. A
  full pass would need to run the same computation across every color table (`KIND_COLORS`, `TILE_COLORS`,
  `RESOURCE_COLORS`, etc.), not just the one family already spot-checked.
- **Categorical palette size vs. established practice** — **already confirmed**: `KIND_COLORS` (~28) and
  `STATE_COLORS` (~17) both exceed ColorBrewer's verified ~12-class practical qualitative-palette ceiling.
  This audit would check whether a secondary encoding channel (icon/shape, already available via
  `lucide-react`) gets added where color alone can't carry the distinction.
- **Colorblind-safety** — flagged but **not yet run**: the correct method (Brettel-Viénot-Mollon 1997,
  citation verified) is named in the idea doc but no simulation has actually been executed against this
  project's real palette values yet. This is the single largest unexecuted piece of the expected checklist.

### Not yet covered by either existing idea doc — genuinely open

- **Asset consistency beyond color** — icon usage (`lucide-react`, confirmed in 10 files) was checked for
  *existence* but not for *consistency*: is the same icon used for the same concept across every panel that
  references it? Not investigated.
- **Typography, spacing, and density conventions** — neither idea doc investigated whether font sizes,
  spacing units, or information density follow any consistent scale across the ~9 HUD panel components.
  A real gap in what's been checked so far, not just an omission from this summary.
- **Responsive/viewport behavior** — neither idea doc investigated what happens at different screen sizes
  beyond noting it as an open question for the simulated-interaction-testing idea. Not investigated at all
  for the *existing*, already-shipped HUD.

## Scoring — deferred, not decided here

Both `docs/simulation_quality/quality_scoring_contract.md` and
`docs/plans/world_rendering/idea_world_render_validation.md` establish this project's real precedent: a
sibling grade-band system (S/A/B/C/D/F), never forced into SimQ's own event-stream-driven architecture. The
newly-landed Design Merit Scorecard (`docs/brainstorm/rpg_feature_atlas.html`, PR #53) is a third, adjacent
precedent worth noting for a different reason — it deliberately keeps 7 axes **uncollapsed**, citing this
project's own real history with SimQ score-gaming, rather than assuming a single composite number is always
the right shape. Whether D27 eventually gets one composite grade, several separate per-family scores, or
follows the Scorecard's uncollapsed-axes shape is a real decision for whenever this dimension is actually
scheduled — not made here, since the instruction for this pass was to state what's expected, not decide the
scoring shape prematurely.

## Related Documents

| Document | Role |
|---|---|
| `docs/plans/idea_hud_quality_measurement.md` | Source of the Findability/Detection/Context-Preservation/Density-Legibility expected checklist above |
| `docs/plans/idea_hud_color_asset_system.md` | Source of the color/palette expected checklist above, including already-confirmed findings |
| `docs/plans/hud_delivery_roadmap.md` | The active roadmap (M1–M4) this audit dimension would eventually measure against, once M2–M4 ship real content |
| `docs/audits/audit_dimensions.md` | The original 18-dimension audit programme's master index — this file intentionally does not add an entry there, matching the precedent already set by D19–D25, which also exist as standalone files outside that index |
