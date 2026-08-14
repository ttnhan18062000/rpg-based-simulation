---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260710-FEATURE-FLAGS-GUIDE
artifact_type: plan
tags: [feature-flags, documentation, claude-md]
---

# Implementation Plan — TCK-20260710-FEATURE-FLAGS-GUIDE

## Summary

This is a documentation-only ticket. The plan creates one new consolidated guide
(`docs/guides/feature_flags.md`) that pulls together the `FeatureFlagManager`/`FeatureMode`
contract, the default-OFF policy, DEV-002, the SimQ profile activation mechanism, and the
`RolloutProfile`/`HardwareClass` matrix — all previously scattered across four sources. It links
the guide from `docs/README.md`'s Developer Guides table, corrects the two staleness defects in
`docs/simulation/domains/optimization_contract.md` that the new guide would otherwise either
contradict or propagate (the 7-flag undercount in the Known Flags table, a stale `get_flag()`
method-name citation, and inaccurate `RolloutProfiles` prose), fixes 5 stale
`v2_intentional_divergences.md` filename citations across 3 named files, then runs the standard
frontmatter/knowledge-index/registry closing steps. No source code is touched anywhere in this
plan.

One correction to the investigation's Risk #3 recommendation: the investigation suggested
matching `docs/guides/simulation_quality.md` and `docs/guides/observability.md`'s frontmatter
exactly (no `status:` field). Independently running `python3 tools/validate_frontmatter.py` against
both sampled files confirms **they currently fail validation** (`status: missing required field`) —
this is pre-existing drift in those two files, out of scope to fix here. Since AC #6 requires the
*new* guide to pass validation, Step 1 below uses the full required `doc` schema
(`status`/`layer`/`authority`/`audience`) plus `title`/`tags` for stylistic consistency with the
sibling guides, rather than copying their currently-invalid field set.

## Steps

### Step 1 — Create `docs/guides/feature_flags.md`
**Files:** `docs/guides/feature_flags.md` (new)

**Change:** Create the file with this frontmatter (required fields for `doc` content type per
`tools/validate_frontmatter.py::_validate_doc`, confirmed by testing against
`docs/guides/simulation_quality.md` which lacks `status` and fails validation — do not copy that
gap):

```yaml
---
status: active
layer: engine
authority: P1
audience: developer
title: Feature Flags — Getting Started Guide
tags: [feature-flags, documentation, rollout, guide]
---
```

(Note: `_validate_doc` does not call `_check_tags`, so these tags are not registry-checked for
`docs/` files — unlike ticket/artifact frontmatter. `feature-flags` and `documentation` are
already used elsewhere in this ticket's own artifacts for consistency; `rollout` and `guide`
follow the sibling guides' style of a domain word + `guide`.)

Body sections, in this order (mirrors the `simulation_quality.md`/`observability.md` pattern:
one-line description + "authoritative spec" link, then practical content):

1. **Intro** — one-line description + link to `../simulation/domains/optimization_contract.md`
   (authoritative `FeatureFlagManager` contract) and `../engine/known_limitations.md` §1.5
   (default-OFF policy source).
2. **`FeatureMode` enum** — table of the 4 values (`OFF`, `SHADOW`, `ON`, `STRICT`) with the
   one-line semantics from `optimization_contract.md` lines 69-72 (source of truth:
   `src/domains/optimization/feature_flags.py:4-8`).
3. **The 10 flags** — table of all 10 `ENABLE_*` names (source: `feature_flags.py:14-23`), each
   row: flag name, default (`OFF` for all 10), one-line purpose. Reuse the 7 existing "Controls"
   descriptions from `optimization_contract.md`'s current table verbatim for the first 7 flags
   (`ENABLE_WORLD_CAPABILITY_LAYER` through `ENABLE_SOCIAL_COOPERATION`). For the 3 missing flags
   (`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`), no
   source-code comment or doc currently describes their purpose — write a short, literal,
   naming-derived description in the same style as the existing 7 rows (e.g. "World emergence
   domain activation", "Life-arc campaign domain", "Enhanced trace/observability event emission"),
   and do not assert any behavior beyond what the flag name states. State explicitly that **all
   10 default to `FeatureMode.OFF`** (`docs/engine/known_limitations.md` §1.5, confirmed).
4. **Default-OFF policy** — summarize (do not duplicate verbatim) `known_limitations.md` §1.5:
   why defaults are OFF, the `overrides` constructor arg / `set_flag_mode()` opt-in pattern, the
   `_build_kernel(enable_routing=True)` example in `test_balance_regression.py`, and the rule
   "do not change a default without first re-running `tools/balance_measure.py`". Link to
   `known_limitations.md` §1.5 for the full text.
5. **DEV-002 summary** — 2-3 sentence summary (rationale class **Stabilized**, all 10 flags kept
   OFF, sentinel test `test_adventure_routing_defaults_off`) with a **link only** to
   `../guidelines/intentional_divergences.md` § DEV-002 — do not duplicate the full rationale/
   unblock-condition text (ticket Scope requirement; also an Anti-Drift Hazard from investigation).
6. **SimQ profile activation** — describe the `feature_flags:` YAML block convention in
   `config/simulation_quality/profiles/*.yaml` (optional block; example from `urban_political.yaml`:
   `ENABLE_SOCIAL_COOPERATION: "ON"`, `ENABLE_BELIEF_ASSIMILATION: "ON"` — values are strings).
   Describe `tools/calibrate_simq.py::_load_profile_feature_flags()` (L44-64) reading the block,
   and the precedence rule confirmed in investigation: profile YAML applies first (lower priority),
   env-var overrides of the same flag names apply second and win (higher priority) — cite
   `_run_engine()` L207-220. State this path injects overrides via `dc_replace(state,
   feature_flags=...)` before `Kernel` construction — a **separate mechanism** from
   `FeatureFlagManager`/`RolloutProfileManager` (no `FeatureFlagManager` instance appears in
   `calibrate_simq.py`).
7. **`RolloutProfile`/`HardwareClass` matrix** — table of the 3 real profiles from
   `src/domains/optimization/rollout_profiles.py:36-86`: `CLASS_A` (2 enabled/1 shadow/7 disabled,
   512MB/10ms/1000 events), `CLASS_B` (6 enabled/2 shadow/2 disabled, 2048MB/25ms/5000 events),
   `CLASS_C` (all 10 enabled/0 shadow/0 disabled, 8192MB/50ms/20000 events). Explicitly state, per
   investigation Risk #5: `RolloutProfileManager` has **no method that wires a profile's
   `enabled_phases`/`shadow_phases` into a live `FeatureFlagManager` instance** — it only produces
   declarative `RolloutProfile` descriptor objects; `get_profile()` has no side effect. Do not
   describe this as an "initializer" the way the ticket's own Related Code Areas note loosely
   phrases it — be precise.
8. **Cross-reference caveat** — one paragraph: `docs/combat/rollout_hardening_rulebook.md`
   describes a differently-named flag family (`SimulationConfig.overhaul_features` gating
   `use_legality_v2`, `use_combat_interaction_v2`, `use_movement_model_v2`,
   `use_tactical_evaluator_v2`) that is **not** the same system as `FeatureFlagManager`/
   `FeatureMode` (different naming convention, different default polarity — that doc's flags
   default `True`, not `OFF`). State explicitly, per investigation's independent re-grep: as of
   this writing, no implementation of `overhaul_features` or any `use_*_v2` flag was found
   anywhere in `src/`. Link to the doc but do not fold its content in.
9. **Constraints** — one line carrying `optimization_contract.md`'s existing constraint forward:
   flag values must not change after kernel initialization (flags are set once per run).

**Do NOT touch:** `docs/combat/rollout_hardening_rulebook.md` (cross-reference/link only, per
ticket Out of Scope), `docs/guidelines/intentional_divergences.md` (link only, do not edit
DEV-002's body), any file under `src/`.

**Verify:** `python3 tools/validate_frontmatter.py docs/guides/feature_flags.md` passes (AC #1,
#6). `grep -oE 'ENABLE_[A-Z_]+' docs/guides/feature_flags.md | sort -u` produces exactly the same
10-line set as `grep -oE 'ENABLE_[A-Z_]+' src/domains/optimization/feature_flags.py | sort -u`
(test_plan.md "New Tests Required #2").

---

### Step 2 — Add guide row to `docs/README.md`
**Files:** `docs/README.md`

**Change:** In the "Developer Guides — `guides/`" table (currently lines 198-211, 7 rows), add
one new row after the existing `guides/agent_monitoring.md` row, following the exact existing
format `| [guides/feature_flags.md](guides/feature_flags.md) | <one-line description> |`. One-line
description should name the consolidated scope, e.g. "Feature flag defaults, rollout profiles,
SimQ activation, and the DEV-002 default-OFF policy".

**Do NOT touch:** Any other row or section of `docs/README.md`.

**Verify:** `grep -c "guides/feature_flags.md" docs/README.md` returns ≥1 (test_plan.md "New
Tests Required #5"). `python3 tools/validate_frontmatter.py docs/README.md` still passes (already
passing at baseline — confirmed; the edit must not touch the frontmatter block at the top of the
file).

---

### Step 3 — Fix `docs/simulation/domains/optimization_contract.md` staleness (3 sub-edits, same file/section)
**Files:** `docs/simulation/domains/optimization_contract.md`

**Change (a) — Known Flags table (lines 74-84, AC #5):** Add the 3 missing rows
(`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`, `ENABLE_ENHANCED_TRACE_EVENTS`) to the
existing 7-row table, using the same "Controls" descriptions drafted for the new guide's Step 1
table (keep both documents' wording for these 3 rows identical to avoid re-introducing drift
between them). Table must end at exactly 10 rows, name-matched 1:1 against
`FeatureFlagManager._flags` keys.

**Change (b) — line 86 stale method citation:** Change *"check `FeatureFlagManager.get_flag(flag_name)`"*
to *"check `FeatureFlagManager.get_flag_mode(flag_name)`"* — `get_flag()` does not exist;
`get_flag_mode()` is the real method (`feature_flags.py:33-34`). This is a one-line prose fix in
the same "FeatureFlagManager" section as change (a); included per the investigation's flagged
Risk #1 and the explicit decision in this ticket's tasking (fix adjacent staleness while already
editing this section, since AC #5 already requires touching this exact section).

**Change (c) — RolloutProfiles section (lines 114-116):** Replace the inaccurate prose *"Defines
named rollout configurations (sets of feature flags) for different deployment profiles
(development, staging, production, benchmark). Used by `FeatureFlagManager` initialization."*
with accurate prose describing the real `HardwareClass`-keyed mechanism: 3 profiles
(`CLASS_A`/`CLASS_B`/`CLASS_C`) each carrying `enabled_phases`/`shadow_phases`/`disabled_phases`
plus `max_ram_mb`/`tick_budget_ms`/`max_trace_events`, sourced from
`src/domains/optimization/rollout_profiles.py:36-86`. Also correct the "Used by
`FeatureFlagManager` initialization" claim — per investigation Risk #5, `RolloutProfileManager`
has no method that applies a profile to a live `FeatureFlagManager`; state instead that profiles
are declarative descriptors produced by `RolloutProfileManager.get_profile(hardware_class)`, and
wiring one into a running `FeatureFlagManager` is left to the caller.

**Do NOT touch:** Any other section of this file (`BudgetManager`, `DirtyScheduler`,
`MemoryLimits`, `ProviderEnforcement`, `TraceGovernor`, `Constraints` sections; frontmatter block).

**Verify:** `grep -oE 'ENABLE_[A-Z_]+' docs/simulation/domains/optimization_contract.md | sort -u`
matches the same 10-flag set as Step 1's verify (test_plan.md "New Tests Required #2").
`python3 tools/validate_frontmatter.py docs/simulation/domains/optimization_contract.md` passes.

---

### Step 4 — Fix stale `v2_intentional_divergences.md` citations (3 files, 5 occurrences)
**Files:** `CLAUDE.md`, `docs/plans/audit_fix_plan.md`, `docs/plans/idea_simq_near_perfect_roadmap.md`

**Change:** Replace the exact substring `docs/guidelines/v2_intentional_divergences.md` with
`docs/guidelines/intentional_divergences.md` (drop the `v2_` prefix only — no other text on these
lines changes) at each of these confirmed locations:
- `CLAUDE.md:227` (Divergence bullet under "Authoritative Mechanics Rule")
- `CLAUDE.md:285` (Intentional Divergences section heading)
- `docs/plans/audit_fix_plan.md:55`
- `docs/plans/audit_fix_plan.md:480`
- `docs/plans/idea_simq_near_perfect_roadmap.md:246`

Use a targeted find that matches the full stale string (not a blind single-instance replace) so
both `audit_fix_plan.md` occurrences are caught — test_plan.md's Anti-Drift Test Guards flags this
exact failure mode (fixing only one of two far-apart occurrences in the same file) as the highest
risk in this step.

**Do NOT touch:** `docs/audits/D06_longrun_health.md` (confirmed 0 occurrences at baseline — do
not edit under any circumstance; this is the ticket's explicit Out of Scope item and AC #4). Any
of the ~35+ other files in the repo (closed tickets, `stored_artifacts/`, other docs) that also
carry this stale citation but were not named in the ticket's Scope — leave them untouched, this is
explicit ticket Out of Scope, not an oversight to correct.

**Verify:** `grep -rn "v2_intentional_divergences" CLAUDE.md docs/plans/audit_fix_plan.md
docs/plans/idea_simq_near_perfect_roadmap.md` returns zero matches (AC #3, test_plan.md "New
Tests Required #3"). `git diff --stat docs/audits/D06_longrun_health.md` produces no output (AC
#4, test_plan.md "New Tests Required #4"). `python3 tools/validate_frontmatter.py
docs/plans/audit_fix_plan.md docs/plans/idea_simq_near_perfect_roadmap.md` passes (both already
pass at baseline; the string-only edit must not touch either file's frontmatter block). Do **not**
run `validate_frontmatter.py` against `CLAUDE.md` as a pass/fail gate — confirmed by testing that
`CLAUDE.md` has no frontmatter block at all (`ERROR: frontmatter: missing frontmatter block`) and
always fails this tool regardless of this ticket's edit; it is not governed by this validator and
was never passing. AC #6 ("every doc created or modified under this ticket") is satisfied by the
4 files that do carry frontmatter (Steps 1, 2, 3, and the two `docs/plans/` files here) — see Step
5.

---

### Step 5 — Validate frontmatter on all governed files
**Files:** (validation only, no edits) `docs/guides/feature_flags.md`, `docs/README.md`,
`docs/simulation/domains/optimization_contract.md`, `docs/plans/audit_fix_plan.md`,
`docs/plans/idea_simq_near_perfect_roadmap.md`

**Change:** Run:
```bash
python3 tools/validate_frontmatter.py docs/guides/feature_flags.md
python3 tools/validate_frontmatter.py docs/README.md
python3 tools/validate_frontmatter.py docs/simulation/domains/optimization_contract.md
python3 tools/validate_frontmatter.py docs/plans/audit_fix_plan.md
python3 tools/validate_frontmatter.py docs/plans/idea_simq_near_perfect_roadmap.md
```
All 5 must report `OK`. This is a verification step, not an edit step — if any file fails, return
to the corresponding earlier step and fix the frontmatter block (not the body content) before
proceeding.

**Do NOT touch:** `docs/guides/simulation_quality.md` or `docs/guides/observability.md` — both
confirmed to currently **fail** this same validator (`status: missing required field`); this is
pre-existing drift outside this ticket's scope (neither file is created or modified by this
ticket) and must not be "fixed" as a drive-by. `CLAUDE.md` — not governed by this validator (see
Step 4 Verify).

**Verify:** AC #6 — all 5 invocations above exit 0 with `OK`.

---

### Step 6 — Run scoped sanity tests
**Files:** none (verification only)

**Change:** Run the 3 scoped commands from `test_plan.md`'s "Scoped Pytest Commands":
```bash
pytest tests/integration/test_scenario_feature_flag_defaults.py -m "not slow"
pytest tests/integration/scenarios/test_balance_regression.py -k test_adventure_routing_defaults_off -m "not slow"
pytest tests/docs/ -m "not slow"
```
These are sanity/regression guards, not new tests — they confirm the 10-flag/all-OFF baseline
this guide documents has not drifted since Investigation, and that the DEV-002 sentinel test the
guide links to still exists and passes. No new test file is added (test_plan.md: "No new `pytest`
test function is warranted").

**Do NOT touch:** Do not run unscoped `pytest tests/` (project rule). Do not add new test files —
this ticket's test_plan explicitly requires none.

**Verify:** All 3 commands pass (or, for the first two, pass identically to their pre-ticket
baseline — a failure here indicates the flag system changed underneath this ticket, which would
require revisiting Steps 1 and 3's flag tables, not silently proceeding).

---

### Step 7 — Regenerate knowledge index and doc registry
**Files:** `docs/REGISTRY.yaml` (regenerated), knowledge index (tool-managed, no direct file edit
by implementer)

**Change:** Run `make knowledge-index-update`, then confirm `docs/REGISTRY.yaml` is regenerated
(per the project's standing After-Work rule — this happens automatically as part of Finalize's
post-migration self-check, but should be confirmed present and staged here since `docs/` files
were created/modified in Steps 1-3). Stage `docs/REGISTRY.yaml` and `agent-monitoring/` (including
`tools.jsonl`) in the closing commit alongside the content changes.

**Do NOT touch:** Do not hand-edit `docs/REGISTRY.yaml` — it is fully machine-regenerated.

**Verify:** AC #7 — `make knowledge-index-update` has been run; `docs/REGISTRY.yaml` shows a diff
reflecting the new/modified docs and is staged in the closing commit.

## Scope Guards

- Do not touch `docs/audits/D06_longrun_health.md` under any circumstance (confirmed 0 stale-
  citation occurrences at baseline; named as a suspect in the original request but ruled out by
  investigation; AC #4 is a negative check on this exact file).
- Do not fold `docs/combat/rollout_hardening_rulebook.md`'s `SimulationConfig.overhaul_features`/
  `use_*_v2` content into the new guide as if it is the same flag system — confirmed zero
  implementation in `src/`; cross-reference with an explicit "distinct, unimplemented-as-of-this-
  writing" caveat only (Step 1, section 8). Do not edit `rollout_hardening_rulebook.md` itself.
- Do not change any source code: `src/domains/optimization/feature_flags.py`,
  `src/domains/optimization/rollout_profiles.py`, `tools/calibrate_simq.py`. No new flags, no
  default-value changes, no implementation of `overhaul_features`. This is a documentation-only
  ticket.
- Do not edit the body of `docs/guidelines/intentional_divergences.md` DEV-002 — cite/link only
  (Step 1, section 5).
- Do not touch the ~35+ other files across the repo (closed tickets, `stored_artifacts/`, other
  docs) that also carry the stale `v2_intentional_divergences.md` citation but were not named in
  the ticket's Scope — only the 3 files + `CLAUDE.md` in Step 4 are in scope.
- Do not edit `docs/parity_ledger/infrastructure.yaml` or `social_narrative.yaml` — confirmed no
  behavior change and both already cite the correct non-`v2_` filename.
- Do not "fix" `docs/guides/simulation_quality.md` or `docs/guides/observability.md`'s missing
  `status` frontmatter field as a drive-by — out of scope, pre-existing drift, not created/modified
  by this ticket.
- Do not hand-edit `docs/REGISTRY.yaml`.

## Dependency Map

- Steps 1, 2, 3, 4 are independent content edits — each touches a disjoint set of files and can be
  done in any order (or in parallel).
- Step 5 (frontmatter validation) depends on Steps 1, 2, 3, 4 having landed — it validates the
  frontmatter blocks of files touched in all four.
- Step 6 (sanity pytest) has no file dependency but should run after Step 1 and Step 3 so the
  10-flag content it's sanity-checking against is already final.
- Step 7 (knowledge-index-update / registry regen) must run last, after Steps 1-5 — it indexes the
  final state of all `docs/` changes.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| 1. `docs/guides/feature_flags.md` exists with valid frontmatter and required sections | Step 1 | `validate_frontmatter.py` (Step 5); `ENABLE_*` grep-diff vs source |
| 2. `docs/README.md` Developer Guides table has new row | Step 2 | `grep -c "guides/feature_flags.md" docs/README.md` ≥1 |
| 3. Zero `v2_intentional_divergences` matches in `CLAUDE.md`, `audit_fix_plan.md`, `idea_simq_near_perfect_roadmap.md` | Step 4 | `grep -rn "v2_intentional_divergences" ...` returns nothing |
| 4. `docs/audits/D06_longrun_health.md` unmodified | Step 4 (guard — no edit made), Scope Guards | `git diff --stat docs/audits/D06_longrun_health.md` empty |
| 5. `optimization_contract.md` Known Flags table lists exactly 10 flags | Step 3(a) | `ENABLE_*` grep-diff vs source (Step 3 Verify) |
| 6. `validate_frontmatter.py` passes for every doc created/modified | Steps 1, 2, 3, 4 (content), Step 5 (verification) | Step 5's 5 invocations all `OK` |
| 7. `make knowledge-index-update` run, `docs/REGISTRY.yaml` regenerated and staged | Step 7 | Registry diff present and staged in closing commit |

## Anti-Drift Notes

- **Sibling guide frontmatter is currently invalid** — `docs/guides/simulation_quality.md` and
  `docs/guides/observability.md` both fail `validate_frontmatter.py` today (missing `status`).
  Confirmed by direct tool invocation, not assumed. Step 1 must use the full valid `doc` schema,
  not copy this pattern; do not treat the sibling files' current field set as ground truth for
  what passes validation.
- **`CLAUDE.md` has no frontmatter block and is not governed by `validate_frontmatter.py`** —
  confirmed by direct invocation (`ERROR: frontmatter: missing frontmatter block`). Do not treat a
  failure there as a Step 4 regression; it was already failing (structurally, by design) before
  this ticket and is excluded from the Step 5 validation set.
- **`audit_fix_plan.md` has two far-apart occurrences (lines 55 and 480)** — the single highest
  risk for an incomplete fix per test_plan.md's Anti-Drift Test Guards; use a global/all-
  occurrences replace within the file, not a first-match-only edit.
- **`RolloutProfileManager` does not auto-wire a profile into a live `FeatureFlagManager`** — no
  `apply_profile()`/`activate()` method exists. Both the new guide (Step 1, section 7) and the
  corrected `optimization_contract.md` prose (Step 3(c)) must state this precisely; the doc's
  current wording ("Used by `FeatureFlagManager` initialization") overstates what the code does
  and must not be carried forward.
- **The 3 newly-added flag descriptions (`ENABLE_WORLD_EMERGENCE`, `ENABLE_LIFE_ARC_CAMPAIGNS`,
  `ENABLE_ENHANCED_TRACE_EVENTS`) have no source-level description to draw from** — keep their
  "Controls" text literal and naming-derived, consistent in specificity with the existing 7 rows;
  do not invent mechanics or behavior not evidenced in `feature_flags.py` or
  `rollout_profiles.py`. Keep the wording identical between Step 1's guide table and Step 3(a)'s
  contract table fix to avoid introducing a new cross-doc drift while fixing an old one.
- **`FeatureFlagManager` flags must not be described as changeable after kernel init** — carry
  forward `optimization_contract.md`'s existing Constraints-section rule ("flags are set once per
  run") into the new guide; this governs the `calibrate_simq.py` override-before-`Kernel()`-
  construction pattern documented in Step 1 section 6.
- **Do not imply flag defaults should change** — `known_limitations.md` §1.5's rule ("do not
  change the default to `ON` without first re-running `tools/balance_measure.py`") must be
  represented as a constraint the guide documents, never as something the guide questions or
  proposes revisiting.
