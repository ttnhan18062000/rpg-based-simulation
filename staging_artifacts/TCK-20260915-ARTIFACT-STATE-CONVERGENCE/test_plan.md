---
status: active
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-ARTIFACT-STATE-CONVERGENCE
artifact_type: test_plan
tags: [architecture, documentation, schema]
---

# Test Plan — TCK-20260915-ARTIFACT-STATE-CONVERGENCE

New file: `tests/unit/tools/test_mechanism_artifact_convergence.py`, mirroring the structure and
discipline of `tests/unit/tools/test_mechanism_wiring_map_classdef.py` (T3) and
`tests/unit/tools/test_mechanism_priority_derivation.py` (T3) — fixture-based, re-derives against
real committed files where relevant, never hardcodes an expected output that could silently drift
from the generator itself.

## Atlas (`mechanism_atlas_card_mapping.py`, `mechanism_atlas_regenerate.py`)

1. **Mapping table integrity** (extends existing coverage from the T4 camp-fix commit's inline
   check, now as a real test): every `CARD_TO_MECHANISM_ID`/`SPLIT_CARD_MECHANISMS`/
   `PARTIAL_COVERAGE_CARDS` entry resolves to a real mechanism id in `mechanisms.yaml`; no
   duplicate `(section, index, badge_index)` key across all three tables; `all_mechanism_card_badge_positions()`
   covers exactly 73 of the 75 registered mechanism ids (the `nest`/`lair` exclusion is asserted
   explicitly, not just "not covered").
2. **Expected-cls computation**: for a synthetic fixture registry with each of the 6 states present,
   `compute_expected_atlas_state()` (or equivalent) returns exactly that state as the badge `cls`
   for a single-mapped card; for a split card, returns the correct state per badge index
   independently (test with the two mechanisms in different states, not both `done`).
3. **Drift-check on the real file**: run in `--check` mode against the real committed
   `rpg_feature_atlas.html` + `mechanisms.yaml`; assert zero drift post-regeneration (proves Step 1
   was applied correctly, not just that the tool runs).
3a. **[Load-bearing per peer review] Prose preservation**: after a real regeneration run, every
    mapped card's `title`, `fromNote`, `desc`, `src`, and every badge's `text` field are
    byte-identical to the pre-regeneration parse — only `cls` may differ, and only for badges whose
    mechanism's state actually changed. This is the test that matters most in this ticket: a diff
    showing "139 cards changed" would look identical to a correct, cls-only diff at a glance without
    this assertion. Prove it field-by-field, not by eyeballing a diff.
4. **Idea-level cards untouched**: assert the regenerator's write path never touches a
   `(section, index)` key absent from `all_mechanism_card_badge_positions()` — parse the file before
   and after, diff only the JSON, assert no key outside the mapped set changed.
5. **`--check` exits non-zero on real drift**: inject a single fixture mismatch (a copied card JSON
   with a wrong `cls`), assert non-zero exit and a message naming the specific card and mechanism.

## Capabilities (`mechanism_capabilities_card_mapping.py`, `mechanism_capabilities_tier.py`,
`mechanism_capabilities_regenerate.py`)

6. **Mapping table integrity**: same shape as test 1, against the capabilities card set (99 cards);
   assert every registered mechanism id with an atlas card also has a capabilities entry unless
   explicitly listed as a known exception (mirrors the atlas's own `nest`/`lair` carve-out — capabilities
   may have a different exception set, confirm by reading, don't assume it matches the atlas's).
7. **Tier function, all 6 states × verified presence/absence**: parametrized test over
   `(state, verified_verdict_or_None) -> tier`, asserting the exact table from investigation.md
   Finding 4/plan.md Step 2.2 — explicitly including `done + contradicted -> built` (the camp case)
   and `done + None -> live` (the common case) as two independently-asserted rows, not inferred from
   each other.
8. **`partial` override enforcement**: every key in `PARTIAL_TIER_OVERRIDES` has a non-empty
   `reason` string (fails loud on an empty/missing reason, proven with an injected bad fixture entry,
   not just checked against the real table); every key corresponds to a mechanism whose registry
   `state` is actually `partial` (an override on a non-`partial` mechanism is a real error, asserted
   as such — proves the override table can't silently apply to the wrong state class as the registry
   evolves).
9. **camp proof case**: after regeneration, the real capabilities file's "Goblin & Orc Camps" card
   has `tier: built` (not `planned`), and its `tierLabel` no longer contains the word "confirmed not
   working" paired with a `built` tier's own contradiction pattern (parse it back out and assert
   directly, not just eyeball the diff).
10. **Drift-check on the real file**: same shape as atlas test 3, `--check` mode, real committed
    files, zero drift after regeneration.
10a. **[Load-bearing per peer review] Body preservation**: same shape as atlas test 3a — every
     mapped card's `title`/`desc` (the plain-language body) is byte-identical pre/post
     regeneration; only `tier` and (deliberately, where hand-written) `tierLabel` may differ. The
     capabilities page exists specifically because its prose is written for a non-dev reader; no
     mapping can generate that, and none should try.

## Wiring map (scope item 4 — no new code)

11. Existing `tests/unit/tools/test_mechanism_wiring_map_classdef.py` (7 tests, T3) reconfirmed to
    still pass unmodified — no new test needed, this scope item adds no code.

## Taxonomy / Scorecard (scope items 2/5 — no code, decision recorded)

No new tests — nothing converges. The zero-overlap evidence (grep check against all 13 orphan/gated
ids) is recorded in investigation.md and the corrected scoping docs, not asserted by a test, since
there's no ongoing generator behavior to regression-test here — the finding is a one-time
correction to a static claim, not a build-time invariant.

## Propagation (AC #2) — the cross-cutting proof, three consumers per peer's explicit correction

12. **`test_state_change_propagates_to_all_consumers`**: construct a fixture registry (small,
    synthetic, not the real 75-mechanism file) with one mechanism mapped in the atlas fixture, the
    capabilities fixture, AND the wiring map's `OPERATING_LOOP_NODE_TO_MECHANISM_ID` mapping. Run
    the atlas regenerator, the capabilities regenerator, and
    `mechanism_wiring_map_classdef.compute_expected_classdef()` against the SAME fixture registry
    twice — once with the mechanism at `state: done`, once at `state: gap` — and assert, **in one
    test, all three**:
    - the atlas fixture's badge `cls` changed between the two runs, matching the state exactly both
      times
    - the capabilities fixture's `tier` changed between the two runs, matching the tier function's
      own table both times
    - `compute_expected_classdef()`'s result for that node changed between the two runs, matching
      the wiring map's own 4-class derivation both times
    - no other card/mechanism/node in any of the three changed
    This is the ticket's own explicit anti-cherry-picking requirement (AC #2: "a convergence that
    works only for the states that happen to be correct today isn't converged"), tightened by peer
    review to name all three real consumers explicitly — "two out of three passing would look like
    success." Proven on states that are NOT today's real seeded values, so it can't pass by
    coincidence.
13. **Cycle/malformed-fixture safety**: reuse (not reimplement) `mechanism_registry.py`'s own
    `validate()` ahead of either regenerator — assert both regenerators refuse to run (non-zero
    exit, no partial write) against a registry fixture that fails validation, rather than writing
    inconsistent output. Mirrors the "report, never silently proceed on bad input" discipline
    already established by the graphify-check tool (T1) and the priority derivation's
    `DependencyCycleError` (T3).

## Whole-suite re-verification

Full scoped run:
```
.venv313/bin/python3 -m pytest tests/unit/tools/ tests/unit/engine/test_capability_registry.py -v
```
with `graphify-out/` genuinely moved aside and restored immediately after, matching every prior
ticket in this epic's own standing discipline — not skipped for this ticket just because it touches
docs/HTML rather than `src/`.
