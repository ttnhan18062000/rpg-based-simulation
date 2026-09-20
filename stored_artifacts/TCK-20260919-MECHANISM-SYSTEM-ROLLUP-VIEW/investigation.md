---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation — TCK-20260919-MECHANISM-SYSTEM-ROLLUP-VIEW

## What already existed
- `mechanisms_by_system(data)` (foundation ticket, done 2026-09-18): `{system: [mechanism ids]}`
  plus a real `"unassigned"` key. Consumed unmodified — this ticket adds counting on top, never
  re-derives groups.
- Three existing view generators (`generate_mechanism_verification_view.py`,
  `generate_mechanism_priority_view.py`, `generate_mechanism_registry_view.py`) establish the CLI
  shape (`--output`/`--registry`/`--check`) and the "explicit absence, never omit" rendering
  discipline this ticket follows.
- Two known constraints already recorded before this ticket started, not rediscovered:
  counts-never-a-badge (`mechanism_tier_model_initiative.md` §5) and rates-against-baseline (the
  value investigation's own `faction` finding — 77% unverified looked informative until checked
  against the whole-registry baseline of 74% and found statistically indistinguishable).

## What this ticket needed to determine
1. **Exactly what "counts" means for a rollup row.** Chose: mechanism count, bound count/rate,
   verified count/rate (split runtime/static — matching the verification view's own established
   static-vs-runtime distinction, not a new one), and a full 6-state breakdown. Every `VALID_STATES`
   value rendered explicitly per system, including zero counts, mirroring the verification view's
   own "unverified rendered explicitly, not omitted" rule at the state-count level.
2. **How to make the baseline comparison real rather than decorative.** The value investigation's
   own 74%/30% baseline figures are already stale (this session's coverage-extension work moved the
   bound count from 24/89-ish to 33/93 in the same week). Decision: the baseline must be computed
   live from whatever registry data is passed to `build_system_rollup()`, using the exact same
   `_rollup_stats()` counting path as every per-system row — never a hardcoded snapshot number.
   Verified directly: `test_rollup_baseline_computed_live_not_hardcoded` constructs a synthetic
   4-mechanism fixture and asserts the baseline reflects that fixture's own 50% rate, not any real
   registry number.
3. **The 0-member edge case.** `unassigned` is genuinely empty on the real registry today (0 of 93).
   `_rollup_stats([], ...)` returns `bound_rate: 0.0`/`verified_rate: 0.0` by construction (guarded
   division). Rendering that as "-35.5pt vs baseline" in the table would misrepresent "no members to
   measure" as "this group underperforms baseline." Fixed in the renderer (not the stats function,
   which correctly returns 0.0 as a mathematical fact) — a 0-count row shows `n/a` for both rate
   cells.

## Real registry findings (2026-09-19, informational — this ticket doesn't act on them)
`combat` (7 mechanisms) is the one system that clearly separates from baseline in both directions
that matter: 71.4% bound (baseline 35.5%) and 71.4% verified (baseline 26.9%), with 4 of its 5
verified mechanisms runtime-verified rather than static — the highest runtime-verification density
of any system. `economy` and `social` both show 0% verified against the same baseline despite
having real `implemented_by` bindings (`economy` 1/8, `social` 4/12) — bound code exists, none of it
has been runtime- or even code-trace-verified. This is the "loose versus deep" signal the epic's own
Request Summary asked for; not chased further here, since this ticket's own scope is the view
itself, not investigating what it reveals.
