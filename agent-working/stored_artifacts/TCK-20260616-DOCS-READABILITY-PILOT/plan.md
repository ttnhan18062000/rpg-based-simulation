# Plan — TCK-20260616-DOCS-READABILITY-PILOT

## Goal
Validate the rewrite style for stripping implementation-history phase/milestone language across `docs/` before scaling to all remaining flagged files (218 total, 64 already removed from scope via archival).

## Files chosen and why
- `docs/mechanics/attribute_progression_contract.md` (P0-adjacent mechanics bible companion) — heaviest legitimate case: uses "Phase N — Title" as a *sequential execution order* label (not a dev milestone), plus a genuine dev-milestone reference ("Phase 8" for unimplemented breakthroughs).
- `docs/systems/strategic_cognition.md` — mixes a pure dev-tracking parenthetical ("(Phase 7)") with genuine named pipeline-stage architecture ("Strategic Derivation Phase", "Phase 4 (Resolution)").
- `docs/simulation/domains/campaigns_contract.md` — a header metadata line ("Pipeline phase: Phase 9 — Campaign Lifecycle") that's pure dev-tracking with no architectural content.
- `docs/simulation/quest_contract.md` — heavy use of the authoritative pipeline's numbered stage ("Phase 14 — Objective Reward") as a load-bearing cross-reference throughout the doc.

These four cover every pattern found across the 218 flagged files: false-positive sequential-step numbering, mixed dev-tracking/architecture language, pure metadata cruft, and pipeline-stage cross-references.

## Rewrite rules applied
1. **Pure dev-tracking labels** (e.g. "(Phase 7)", "Pipeline phase: Phase 9 —") — deleted outright, no replacement needed since they added no architectural meaning.
2. **Genuine named pipeline/lifecycle stages** (kernel phases, Cognitive Pipeline stages, the 17-stage authoritative pipeline) — keep the *name*, drop the bare number, phrase as "the `<Name>` stage" rather than "Phase N (`<Name>`)". Matches `docs/engine/kernel.md`'s own convention of naming phases without numbering them in prose.
3. **Sequential execution-order labels that used the word "Phase" for non-pipeline, multi-step procedures** (e.g. stat recalculation's 6 internal steps) — renamed to "Step N — Title" since the order is real and worth keeping, but "Phase" specifically implies engine-lifecycle/dev-milestone meaning that doesn't apply here.
4. **Deferred-work status callouts** ("until Phase 8 is complete") — rephrased around actual implementation status ("until `apply_bonuses()` is implemented") rather than a project-phase number.

## Verification
- grep sweep per file for `\bphase[ _-]?[0-9]+|\bmilestone[ _-]?[0-9]+` (case-insensitive) — zero remaining matches in all 4 files.
- `make knowledge-index-update` run after edits.
