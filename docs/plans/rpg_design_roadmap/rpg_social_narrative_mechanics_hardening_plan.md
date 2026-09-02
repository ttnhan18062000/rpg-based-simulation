---
status: active
layer: mechanics
authority: P1
audience: agent
tags: [content, architecture]
---

# Plan — Social/Political Mechanics Hardening: the missing Mechanics Bible chapter

**Status:** high-level plan, not yet ticketed. Item 1 of a 5-item hardening backlog identified 2026-09-02
(see the parent roadmap's "Hardening backlog" section) — the same code-verification treatment the temporal
axis and idea 66 already received, applied to the social/reputation/political surface.

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

**`SocialComponent`** (`src/core/models/social.py`, 13 fields, confirmed real, none previously documented
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
   This is the genuinely zero-coverage surface — document the 13 fields, the clamp ranges, and the apply
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
   confirmed in this investigation pass — not yet done for these, and per this project's own caution against
   trusting a ledger's `verified` status without a direct check.
5. **Resolve the `CanonicalStateHasher` social-field-coverage open question.** `replay/fingerprint.py`'s
   `StateFingerprinter` (the lightweight, explicitly-non-canonical replay tracker) only tracks `bonds` as a
   count and `reputation` rounded to 3 decimals — its own docstring names "social changes silently ignored"
   as a failure mode it exists to catch, meaning `trust_history`, `grudge_history`, `nemesis_ids`, etc. are
   *not* covered by it at all. Whether the separate, canonical `CanonicalStateHasher` (used for
   `world_compile_report.json`'s `state_hash`) covers the rest of `SocialComponent` was not checked in this
   investigation pass — this must be answered directly (confirmed covered, or confirmed a real determinism
   gap) before this plan is considered scoped, not left as an assumption either way.

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

- `docs/parity_ledger/social_narrative.yaml` — 276 entries, ~94 genuinely social/narrative
- `src/core/models/social.py` — `SocialComponent`, 13 fields, no prior contract
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
