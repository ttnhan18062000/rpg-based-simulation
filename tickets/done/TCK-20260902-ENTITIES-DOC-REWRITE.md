---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260902-ENTITIES-DOC-REWRITE
phase: done
date: 2026-09-02
tags: [documentation]
---

# TCK-20260902-ENTITIES-DOC-REWRITE

## Title
Reconcile `docs/core/entities.md` with the real Component-based architecture (remove fictional Aspect-Oriented Model)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
`docs/core/entities.md` (P0-authoritative per its own frontmatter, `docs/core/` family) describes
an "Aspect-Oriented Model" — `Entity` shell class at `src/core/entities/entity.py`, and
`IdentityAspect` / `SpatialAspect` / `CombatAspect` / `ProgressionAspect` / `MindAspect` classes —
that does not exist anywhere in the current codebase. Confirmed via direct filesystem/grep search:
no `src/core/entities/` directory exists, and no `class .*Aspect` definitions exist anywhere under
`src/`. This was discovered and independently confirmed during
TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION's Document-Update phase (2026-09-01, done). The real
architecture is the Component-based system in `src/core/state.py` (`IdentityComponent`,
`CombatComponent`, `NavigationComponent`, `InteractionComponent`, `BiologicalComponent`,
`AttributeComponent`, `PersonalityComponent`, `AptitudeComponent`, `EquipmentComponent`,
`LifecycleComponent`, etc., all `@dataclass(frozen=True, slots=True)`, composed onto the frozen
`EntityState` container) plus `StrategicComponent`/`ObjectiveState`/`ProjectState` in
`src/core/strategic.py` — this is what the sibling doc `docs/core/state.md` (also P0-authoritative,
already accurate) correctly describes. Some content in `entities.md` happens to still be roughly
accurate by coincidence despite the wrong framing — e.g. it already lists
`status_effects: List of active StatusEffect objects` under its (fictional) `CombatAspect`, which
matches the real `Combat` component's `status_effects` field per `docs/core/state.md`'s own table.

Historical note (non-blocking context, not part of the fix): `search_docs` surfaced three closed
tickets (`TCK-20260405-DOCS`, `TCK-20260330-AOA-COMPOSITION-COMPLETED`,
`TCK-20260330-CORE-STABILIZATION`) indicating an actual "Aspect-Oriented Architecture (AOA)" pivot
was implemented and documented in the codebase's earlier history, then apparently later replaced by
the current Component-based system without `entities.md` ever being updated to follow. This
explains *why* the doc is wrong (stale relative to a real prior architecture, not an
aspirational/never-built doc) but does not change the fix: `entities.md` must describe what exists
today.

## Scope
- Rewrite `docs/core/entities.md` end to end to describe the real Component-based architecture,
  using `docs/core/state.md` as the accuracy/structure reference and `src/core/state.py` (plus
  `src/core/strategic.py` for the Strategic component) as the field-level ground truth.
- Remove every reference to the fictional `Entity` shell class, `src/core/entities/entity.py`
  module path, and the `IdentityAspect` / `SpatialAspect` / `CombatAspect` / `ProgressionAspect` /
  `MindAspect` class names and their "Aspect Decomposition" section structure.
- Preserve/carry forward any content that is coincidentally still accurate under the new framing
  (e.g. the `status_effects` field mention, the Factions & Relations table, the Genetic
  Seeds/`deterministic_seed`/Aptitude description if verified accurate against
  `AptitudeComponent`).
- Keep the doc's existing frontmatter shape (`status: authoritative`, `layer: core`,
  `authority: P0`, `audience: developer`) and update `last_verified` to the date this ticket
  closes.
- Cross-check every retained or rewritten field/class claim against `src/core/state.py` (and
  `src/core/strategic.py` for Strategic-component fields) so the rewritten doc is accurate, not
  merely restructured to match `state.md`'s prose without verification.

## Out of Scope
- Do not modify `docs/core/state.md` — it is already accurate and is the reference this ticket
  reconciles against, not a target of change.
- Do not modify `docs/core/attributes_and_classes.md` — read-only reference for attribute/class
  content; already accurate.
- Do not modify any file under `src/` — this is documentation-only; the real Component
  architecture is correct as implemented, only the doc describing it is wrong.
- Do not re-litigate or restore the historical Aspect-Oriented Architecture (AOA) — it was
  superseded by the Component system per the historical tickets found in this scan; this ticket
  documents current reality, not prior design history.
- Do not update the parity ledger (`docs/parity_ledger/`) — this is a doc-to-doc/doc-to-code
  accuracy fix with no behavior change, so no parity ledger entry applies.
- Do not touch other `docs/core/*.md` files beyond reading them as reference (`state.md`,
  `attributes_and_classes.md`) or other `docs/` families outside `docs/core/`.

## Acceptance Criteria
- [x] `docs/core/entities.md` contains zero occurrences of the strings `Aspect`,
  `src/core/entities/entity.py`, `IdentityAspect`, `SpatialAspect`, `CombatAspect`,
  `ProgressionAspect`, or `MindAspect`.
- [x] Every component name and field the rewritten doc claims exists is verifiable by name in
  `src/core/state.py` or `src/core/strategic.py` (spot-checked: `IdentityComponent`,
  `CombatComponent`, `NavigationComponent`, `InteractionComponent`, `BiologicalComponent`,
  `AttributeComponent`, `PersonalityComponent`, `AptitudeComponent`, `EquipmentComponent`,
  `LifecycleComponent`, and the Strategic component in `src/core/strategic.py`).
- [x] The doc's architectural framing matches `docs/core/state.md`'s Component Composition
  Pattern / Frozen Lifecycle Law description (no contradiction between the two sibling docs).
- [x] `python3 tools/validate_frontmatter.py` (or equivalent frontmatter check used by
  `done-checker`) passes on the rewritten `docs/core/entities.md`.
- [x] `make knowledge-index-update` is run after the doc edit (per project CLAUDE.md's
  "docs/ modified" rule) and completes without error.
- [x] No `src/` files are modified as part of this ticket (diff review confirms doc-only change).

## Related Tickets
- TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION (`tickets/done/`) — where this staleness was
  originally discovered and confirmed during its Document-Update phase (2026-09-01).
- Historical/non-blocking context only (do not re-open, do not treat as scope for this ticket):
  TCK-20260405-DOCS, TCK-20260330-AOA-COMPOSITION-COMPLETED, TCK-20260330-CORE-STABILIZATION —
  record the original AOA pivot and its later replacement by the Component system.

## Related Docs
- `docs/core/state.md` — accurate sibling doc; primary structural/accuracy reference for the
  rewrite.
- `docs/core/attributes_and_classes.md` — accurate sibling doc; secondary reference for
  attribute/class-related claims (`Attributes`, `Aptitudes`, classes) that overlap with
  `entities.md`'s content.

## Related Stored Artifacts
None found. `stored_artifacts/` contains numerous `*ENTITY*` ticket artifacts (e.g.
`TCK-20260609-ENTITY-RUNTIME-CONTRACT`, `TCK-20260609-ARCHETYPE-ENTITY-FACTORY`) but none concern
`docs/core/entities.md`'s own content accuracy — they are prior entity-construction/runtime
implementation work, not documentation fixes.

## Related Code Areas
- `src/core/state.py` — read-only reference for ground-truth Component list and field definitions;
  not to be modified.
- `src/core/strategic.py` — read-only reference for the Strategic component
  (`StrategicComponent`, `ProjectState`, `ObjectiveState`); not to be modified.
- `docs/core/entities.md` — the file being rewritten.

## Assumptions / Open Questions
- Assumes `docs/core/state.md` and `docs/core/attributes_and_classes.md` remain the accurate
  references at the time of implementation (both last verified 2026-06-06 per their own
  frontmatter, same as the stale `entities.md`; if either has drifted since, that would need its
  own separate ticket, not folded into this one).
- Assumes the Factions & Relations table and Genetic Seeds section in the current
  `entities.md` are independent of the Aspect/Component framing question and can be preserved
  largely as-is (pending field-level verification during implementation) — if investigation finds
  these sections are also inaccurate, that inaccuracy should still be fixed under this ticket's
  scope (doc-accuracy of `entities.md` as a whole) rather than deferred, since it is the same file
  and same root cause (doc never reconciled after an architecture change).
- Tier reasoning (moved here from `## Tier` at Verify, since that field must contain only the bare
  canonical value): `standard` was chosen because this is a full content rewrite of an authoritative
  (`authority: P0`) doc — every architecture claim (class names, module paths, the 5-Aspect
  decomposition, the `Entity` shell description) is wrong and must be replaced with accurate content
  grounded in the real `src/core/state.py` component list, not a one-line or self-evident fix. No
  code changes are involved, which keeps it out of `epic`/multi-ticket territory, but the rewrite
  requires real verification work (cross-checking every field claim against source) that warrants
  the standard pipeline's Investigate/Plan/Verify phases rather than a hotfix's
  skip-straight-to-implementation path.
- `layer: core` was chosen because it is the already-registered layer for "Core entity/state/
  attribute primitives shared across subsystems" per `registries/layer_registry.jsonl`, and this
  doc is squarely in that family (sibling to `state.md`/`attributes_and_classes.md`, both already
  tagged `layer: core`). No new layer registration needed.
- `tags: [documentation]` was chosen as the sole tag: `documentation` is registered under
  `process-skill-signal`/meta-process category ("docs/ authoring and maintenance") and directly
  matches this ticket's nature. No subsystem-topic tag (e.g. a hypothetical `entities` tag) exists
  or is warranted — `core` is captured by `layer`, not `tags`, per the project's layer/tags
  distinction.

## Implementation Notes
Followed `staging_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/plan.md`'s 8 ordered steps exactly,
with every claim independently re-verified by reading the cited source directly (not copied from
the plan on trust) before writing:
- Read `src/core/state.py` in full, `src/core/enums.py` in full, `src/core/strategic.py:370-430`,
  `src/core/self_model.py:70-249`, `src/core/cognition.py:540-570`,
  `src/systems/world_systems/generator.py:1-45`, and `src/core/builder.py:75-115` before writing
  any doc content — every file:line citation in the rewrite reflects lines actually read in this
  session, not carried forward verbatim from the plan (a few line numbers differ by 1 from the
  plan's citations, e.g. `IdentityComponent` decorator vs. class line — the rewrite cites the
  class-definition line I read, and full component ranges where useful).
- Step 1: replaced title/intro/"Entity Shell" section with the real `EntityState` atom description
  and a single cross-link sentence to `docs/core/state.md`'s Frozen Lifecycle Law (no
  re-description of that sequence).
- Step 2: replaced "Aspect Decomposition" with a full 16-row Component roster table in
  `state.py:731-748` declaration order, columns Component | Defined In | Key Fields.
- Step 3: added an "Identity" sub-section correcting `role`/`faction` to the real `EntityRole`
  (`HERO, SHOPKEEPER, MONSTER, CITIZEN, WORKER, GUARD`) values and documenting
  `IdentityComponent`'s other real fields. Went slightly beyond the plan's explicit field list by
  also including `territory_maturity`, `properties`, and `latest_intent_results` — these are real
  fields I confirmed by reading `state.py:483-527` directly, and omitting them purely because the
  plan's illustrative list didn't name them would reintroduce the same "coincidentally incomplete"
  failure mode this ticket exists to fix.
- Step 4: rewrote "Genetic Seeds" into an "Aptitudes" sub-section — dropped `deterministic_seed`
  and the 0.8x-1.2x claim entirely, replaced with the real `AptitudeComponent` (9 multipliers +
  `learning_rate`/`stamina_efficiency`, all default `1.0`), cross-linked
  `docs/core/attributes_and_classes.md` §3/§3.5, and explicitly stated aptitudes do not affect
  AP-allocation gains, citing `PROG-069`/`DEV-004` (both independently re-read from
  `docs/parity_ledger/progression.yaml` and confirmed accurate).
- Step 5: replaced "Factions & Relations" with the real 4-value `Faction` enum
  (`HERO_GUILD, MONSTER_HORDE, TOWN_COUNCIL, NEUTRAL`), dropped the 4 fictional factions, added a
  one-line mention of `DiplomaticState` per the plan.
- Step 6: added a new "Entity Construction" section citing `EntityGenerator.get_next_id()`
  (`generator.py:30-32`) and `V2EntityBuilder` (`builder.py:79-111`) as the real spawn/id path,
  plus `AuthoritativeState.__post_init__`'s `next_entity_id` collision guard (`state.py:1218-1263`).
- Step 7: updated `last_verified` to `2026-09-02`; kept `status`/`layer`/`authority`/`audience`
  unchanged. Ran the whole-file forbidden-string grep sweep — it initially caught one stray
  occurrence of the literal word "Aspect" in my own intro sentence ("not a shell class wrapping
  separate 'Aspect' objects"), used in a negating/explanatory sense but still a literal string
  match against the AC's zero-occurrence requirement. Rewrote that sentence to avoid the word
  entirely ("not a shell class wrapping separate sub-objects"); the sweep then returned a clean
  zero count across all forbidden strings from AC #1 plus every additional term flagged in the
  plan's own step-level `grep -c` checks.
- Step 8: ran `pytest tests/docs/ -m "not slow"` (via
  `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3`, since the bare system
  `python3` in this worktree lacks `pydantic` — a known local-sandbox gap, not a real failure) —
  45 passed, 1 skipped, 1 xfailed. Ran `make knowledge-index-update` — completed without error
  (1 file re-embedded, 3224 unchanged, 10295 chunks total).
- `python3 tools/validate_frontmatter.py docs/core/entities.md` passes: "OK: 1 file(s) checked —
  no violations".
- `git status --short` after all steps shows only `docs/core/entities.md` modified under tracked
  paths relevant to source/docs (plus the expected `agent-monitoring/tools.jsonl` auto-update and
  this ticket's own new/untracked artifact files) — no `src/` file was touched.

No deviations from the plan's substance occurred; the only departures were (a) the Identity
section including 3 additional real fields beyond the plan's illustrative list, and (b) one
self-correction to my own drafted prose during the Step 7 sweep (removing a literal "Aspect"
occurrence used in a negating sentence). Both are recorded in
`staging_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/plan.md`'s new "Deviations" section.

## Test Summary
- `python3 tools/validate_frontmatter.py docs/core/entities.md` — PASS (no violations).
- `pytest tests/docs/ -m "not slow"` — 45 passed, 1 skipped, 1 xfailed (0 failures). No test in
  `tests/docs/` targets `docs/core/entities.md`'s content directly (confirmed by test_plan.md
  during planning); the suite was run anyway as the broadest available guard for a docs-content
  change, per test_plan.md's own reasoning.
- `make knowledge-index-update` — completed without error (1 file re-embedded: `docs/core/entities.md`).
- Manual `grep -c` sweeps for every forbidden string named in the ticket's AC #1 and the plan's
  per-step verification commands — all return `0` after the Step 7 self-correction.
- No automated test coverage was added for the string-absence checks, per the plan's explicit
  Scope Guard ruling this out as low-value scaffolding in favor of the manual `grep -c`
  verifications already run above.

## Files Changed
- `docs/core/entities.md` — full content rewrite (this ticket's sole in-scope target).
- `tickets/inprogress/TCK-20260902-ENTITIES-DOC-REWRITE.md` — this ticket file (Status,
  Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `staging_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/plan.md` — added a "Deviations" section.
- `staging_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/investigation.md` — no changes made in this
  implementer run (pre-existing from the Investigate phase; not rewritten here).
- `staging_artifacts/TCK-20260902-ENTITIES-DOC-REWRITE/test_plan.md` — no changes made in this
  implementer run (pre-existing from the Plan phase; not rewritten here).

## Completion Summary
Rewrote `docs/core/entities.md` end-to-end, replacing the fictional "Aspect-Oriented Model" (a
non-existent `Entity` shell class and 5 non-existent `Aspect` classes) with an accurate description
of the real `EntityState` component composition: a full 16-row component roster table sourced
directly from `src/core/state.py` (plus `src/core/strategic.py`, `src/core/self_model.py`, and
`src/core/cognition.py` for the components defined outside `state.py`), corrected `EntityRole`
(6 values) and `Faction` (4 values) enum listings replacing the old doc's wrong/fictional value
lists, a rewritten "Aptitudes" section replacing the unsupported `deterministic_seed`/0.8x-1.2x
claim with the real `AptitudeComponent` mechanism and an explicit PROG-069 divergence note about
AP-allocation, and a new "Entity Construction" section documenting the real
`EntityGenerator`/`V2EntityBuilder` spawn path. Every claim in the rewritten doc was independently
verified against source read directly during this implementation session. No `src/` files were
touched; `docs/core/state.md` and `docs/core/attributes_and_classes.md` were read as reference only
and left unmodified. `pytest tests/docs/ -m "not slow"`, `python3 tools/validate_frontmatter.py`,
and `make knowledge-index-update` all pass.
