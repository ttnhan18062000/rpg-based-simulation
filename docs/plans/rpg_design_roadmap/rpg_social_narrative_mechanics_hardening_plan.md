---
status: active
layer: mechanics
authority: P1
audience: agent
tags: [content, architecture]
---

# Plan — Social/Political Mechanics Hardening: the missing Mechanics Bible chapter

**Status, re-verified 2026-09-05:** item 5 (the `CanonicalStateHasher` determinism gap) is fully fixed and
shipped, and items 2 and 4 are now also fully closed (see below) — only item 1 (writing/promoting the
actual chapter) and part of item 3 (ideas 56/62's own read-requirement scoping) remain open. No
`docs/mechanics/07_*.md` (or any new-numbered chapter) exists yet, and `docs/simulation/
social_systems_contract.md` (a pre-existing, differently-scoped doc) does not satisfy this plan's
own Target Shape as-is, though it may substantially reduce the remaining authoring effort if promoted
rather than duplicated — see the ticket below. Item 1 of a 5-item hardening backlog identified 2026-09-02
(see the parent roadmap's "Hardening backlog" section) — the same code-verification treatment the temporal
axis and idea 66 already received, applied to the social/reputation/political surface. **Ticketed,
2026-09-05:** `TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER` (`tickets/todos/`), scope-only —
chapter-authoring is real content work, left for whoever picks it up next. That ticket also carries a new
finding this same re-verification surfaced: `social_systems_contract.md`'s own Reputation section
describes `ReputationService` as live, which conflicts with this plan's own hardening-backlog item 5
finding that the same service has zero callers anywhere in `src/` — an inconsistency the chapter's
implementer must resolve directly, not assume either doc is right.

**Superseded in scope, not replaced, 2026-09-02:** the fuller axis-level treatment now lives in
[`docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md`](../../brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md) —
same depth and structure as the temporal-axis proposal, including a resolved determinism finding
(`CanonicalStateHasher` covers only 10 of `SocialComponent`'s 15 fields) this plan's own scope item 5 named
as an open question. This plan's scope items 1-4 (write the missing chapter, relocate the misplaced
reputation fragment, fold in existing partial contracts, spot-check `SOC-FAC-*`/`SOC-CHRON-*`) remain the
actual chapter-authoring work; the axis proposal is the evidence base to write it from, not a replacement
for doing so.

**Source:** direct investigation, 2026-09-02, of `docs/parity_ledger/social_narrative.yaml` (276 entries),
`src/core/models/social.py`, `src/systems/social_systems/relationships.py`,
`src/systems/social_systems/memory.py`, `src/replay/fingerprint.py`, and the three existing partial
contracts (`docs/simulation/domains/social_memory_contract.md`,
`docs/simulation/domains/chronicle_contract.md`, `docs/systems/faction_contract.md`).

## Problem

Unlike every other subsystem (combat has `docs/mechanics/02_combat_laws.md`, economy has
`docs/mechanics/03_economic_laws.md`), reputation/relationships/social consequence has no Mechanics Bible
chapter. The initial framing of this gap (from `social_narrative.yaml`'s 276-entry size) overstated its
scope — **direct investigation found only 94 of those 276 entries (34%) are genuinely social/narrative
content**; 117 (42%) are regression-test-catalog entries for unrelated subsystems (combat/melee/ranged
behavior, arena determinism, watchdog/hang detection, CLI argument parsing, replay-file format semantics)
that happen to live in the same ledger file for historical reasons. Any chapter-authoring ticket should
scope against the real ~94-entry social subset, not the file's headline count.

**"Zero documentation" is also not quite right — the real gap is fragmentation, not a blank page.** Three
real domain contracts already exist and are genuinely good: `social_memory_contract.md` (cross-episode
memory, thorough, with real formulas), `chronicle_contract.md`, and `faction_contract.md`. One reputation
formula fragment is even filed inside `03_economic_laws.md` (a misplaced cross-reference, not a duplicate).
**What has zero contract coverage anywhere is the within-episode `SocialComponent`/`SocialBond` state and
its authoritative apply-path (`RelationshipService`)** — the bigger, more foundational surface that the
three existing contracts all implicitly assume but never themselves document.

## Target Shape

A new Mechanics Bible chapter (next available number after `06_worldbuilding_foundation.md`) whose core is
the genuinely-undocumented `SocialComponent`/`SocialBond`/`RelationshipService` contract, with the three
existing partial contracts folded in as cross-linked sub-sections rather than rewritten.

**`SocialComponent`** (`src/core/models/social.py`, 15 fields (corrected count, 2026-09-02), confirmed real, none previously documented
in one place): `trust_history`, `familiarity_history`, `debt_history`, `fear_history`, `grudge_history`,
`combat_loss_counts`, `salience_history`, `bonds: Dict[int, SocialBond]`, `nemesis_ids`, `place_attachment`,
`betrayal_count`/`betrayal_records`, `public_reputation` (range 0.0–2.0), `heroism_score`, `notoriety_score`.

**`RelationshipService.process_update()`** (`src/systems/social_systems/relationships.py:16-100`) is the
real authoritative apply-path. Confirmed clamp ranges: trust ±1.0, familiarity 0–1.0, grudge 0–5.0,
reputation 0–2.0 (computed as `heroism_delta - notoriety_delta`).

**Nemesis promotion formula** (`src/systems/social_systems/memory.py:38-52`,
`check_nemesis_promotion()`), spot-checked and confirmed: an entity promotes from `grudge_history` to
`nemesis_ids` at `grudge_history >= 3.0`. Independently cross-confirmed against the M9 corpus-test-coverage
epic doc's own citation for idea 22's test design (`grudge ≥ 3.0`) — not a doc-only claim, matches real code.

## Scope (not yet broken into child tickets)

1. **Write the missing `SocialComponent`/`SocialBond`/`RelationshipService` contract as the chapter's core.**
   This is the genuinely zero-coverage surface — document the 15 fields, the clamp ranges, and the apply
   path above as the chapter's foundation, the same way `01_entity_anatomy.md` documents `EntityState`'s
   core attribute components.
2. **Relocate or cross-link the reputation formula fragment currently misfiled in
   `docs/mechanics/03_economic_laws.md`.** It belongs in the new chapter; leave a pointer behind rather than
   duplicating the formula in two places.
3. **Fold in the three existing contracts as sub-sections, not rewrites**: `social_memory_contract.md`
   (cross-episode memory), `chronicle_contract.md`, `faction_contract.md`. These are already good — the
   chapter should cross-link and summarize, not redo this work.
4. **Spot-check the ~10 `SOC-FAC-001`–`010` and `SOC-CHRON-001`–`006` parity-ledger entries against real
   `FactionState`/diplomacy code directly**, the same way nemesis-promotion (`SOC-196`) was independently
   confirmed in this investigation pass. **Done, confirmed 2026-09-05:** all 16 entries (10 `SOC-FAC-*`, 6
   `SOC-CHRON-*`) spot-checked directly against `src/domains/chronicle/{significance,grouper}.py`,
   `src/domains/faction/diplomatic_state_machine.py`, `src/domains/campaigns/orchestrator.py`, and
   `src/api/routes/chronicle.py` — every numeric constant (event-type significance weights,
   `INCIDENT_TICK_WINDOW=50`, `ERA_EPISODE_MIN=3`, the `_SIGNIFICANCE_MAP` entries) and every structural
   claim (the `ALLIED→HOSTILE` betrayal-transition condition, the REST route paths) matched exactly.
   Cited tests (`tests/unit/domains/chronicle/test_significance.py`,
   `tests/unit/domains/faction/test_betrayal_ledger.py`) run directly and confirmed passing (17/17).
   Unlike `SUB-327`, no correction was needed here — this batch of citations was accurate as recorded.
5. **`CanonicalStateHasher` social-field-coverage question — RESOLVED and FIXED, confirmed 2026-09-05.**
   `TCK-20260902-SOCIAL-CANONICAL-HASH-GAP` (`tickets/done/`) added all 5 missing fields
   (`debt_history`, `salience_history`, `nemesis_ids`, `place_attachment`, `betrayal_records`) to
   `EntityState.to_canonical_dict()` — confirmed directly present in `src/core/state.py` today, not
   just a recorded finding. Original finding text preserved below for context.
   `replay/fingerprint.py`'s `StateFingerprinter` (the lightweight, explicitly-non-canonical replay tracker)
   only tracks `bonds` as a count and `reputation` rounded to 3 decimals — not the concern here.
   `EntityState.to_canonical_dict()` (the real, canonical hash used for `world_compile_report.json`'s
   `state_hash`) covers only **10 of `SocialComponent`'s 15 fields** — missing `debt_history`,
   `salience_history`, `nemesis_ids`, `place_attachment`, and the detailed `betrayal_records` list (only its
   count is hashed). A divergence in any of these 5 fields between two same-seed runs would go undetected
   today. See the full Social/Relationship Axis proposal (References below) for the complete finding; this
   plan's own chapter-authoring work should record the same finding, not re-derive it. Whether to add all 5
   fields or document specific ones as intentionally non-authoritative remains an open decision.

## Out of Scope

- Rewriting or re-scoping the 117 `social_narrative.yaml` entries that are not social/narrative content
  despite the filename (combat, arena, watchdog, CLI, replay-format entries) — those stay where they are.
- Building any new social mechanic or Chronicle feature — this plan documents and hardens what already
  exists, it does not extend the mechanic itself.
- M5's own ideas (53/54/55/58/60/62 — inherited reputation, guilt by association, generational
  misremembering, etc.) — this plan is a prerequisite documentation/verification pass those tickets can
  cite, not a substitute for their own scoping.

## Acceptance Signal

- The new chapter exists, is Certified Level 1 per this repo's Mechanics Bible convention, and every formula
  it states is cited against real code, spot-checked the way nemesis promotion was in this pass — not
  transcribed from the parity ledger's own claims unverified.
- The `03_economic_laws.md` reputation fragment is cross-linked, not duplicated.
- The `SOC-FAC-*`/`SOC-CHRON-*` entries have been independently spot-checked against real diplomacy code, with
  results recorded (confirmed or corrected) in the new chapter or the parity ledger itself.
- The `CanonicalStateHasher` social-field-coverage question has a definite answer (covered / gap found and
  ticketed), not left open.

## References

- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` — the fuller axis-level
  proposal this plan's findings feed into
- `docs/parity_ledger/social_narrative.yaml` — 276 entries, ~94 genuinely social/narrative
- `src/core/models/social.py` — `SocialComponent`, **15 fields** (corrected count, 2026-09-02 — an earlier
  pass in this same investigation miscounted 13), no prior contract
- `src/systems/social_systems/relationships.py:16-100` — `RelationshipService.process_update()`, real clamp
  ranges
- `src/systems/social_systems/memory.py:38-52` — `check_nemesis_promotion()`, grudge ≥ 3.0, spot-check
  confirmed
- `src/replay/fingerprint.py:68-69` — `StateFingerprinter`, explicitly non-canonical, social-field coverage
  gap named in its own docstring
- `docs/simulation/domains/social_memory_contract.md`, `docs/simulation/domains/chronicle_contract.md`,
  `docs/systems/faction_contract.md` — existing partial contracts to fold in, not rewrite
- `docs/mechanics/03_economic_laws.md` — currently holds the misplaced reputation formula fragment
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md` — parent roadmap, Hardening backlog section
- `docs/plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md` — the milestone this hardening pass most
  directly serves (ideas 53/54/55/58/60/62)
