---
status: historical
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER
phase: done
date: 2026-09-05
tags: [content, architecture]
---

# TCK-20260905-SOCIAL-MECHANICS-BIBLE-CHAPTER

## Title
Write the missing Social/Political Mechanics Bible chapter (items 1-4 of the social/political hardening plan)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` (2026-09-02 hardening
backlog item 1) found reputation/relationships/social consequence has no Mechanics Bible chapter,
unlike every other subsystem. Its own item 5 (a `CanonicalStateHasher` determinism gap) already
shipped (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`); items 1-4 (the actual chapter-authoring work)
remain fully pending as of 2026-09-05.

**Real scope narrower than the plan doc's own framing, found during this pickup's own re-verification
(confirm directly, don't re-assume):** `docs/simulation/social_systems_contract.md` (`status: active`,
`authority: P1`, `last_verified: 2026-09-02`) already exists and is substantially thorough — it
documents `SocialComponent`'s field clamp ranges, `SocialBond`, the nemesis-promotion formula
(`grudge_history >= 3.0`), decay (confirmed none exists on live gameplay state), and more, in real
depth. It is **not**, however, in the Mechanics Bible's own numbered chapter series
(`docs/mechanics/0N_*.md`) or marked `Certified Level 1` per this repo's own convention — the real
remaining gap may be narrower than "author from scratch": promoting/restructuring this existing
content into proper Mechanics Bible form, rather than duplicating it, is worth checking first.

**Second inconsistency, RESOLVED 2026-09-07 (re-verified against current code before handoff, per
this ticket's own instruction not to assume either doc is right):** `social_systems_contract.md`'s
"Reputation" section describes `ReputationUpdateService.process_witnessed_event()`/
`PublicReputationProfile` as actively updating on witnessed events — the roadmap's Hardening backlog
item 5 (2026-09-02) claimed this had zero callers, but that is now stale. Confirmed directly:
`ReputationUpdateService.process_witnessed_event()` (`src/domains/commitment/reputation.py:15`) has a
real, live, non-test caller at `src/engine/quests.py:233` — fires on ESCORT quest completion,
threading a `"successful_escort"` event through a typed cognition-bundle `replace()`, no feature flag
gating it off. Separately, `ReputationService.combine_public_reputation()`
(`src/systems/social_systems/reputation.py:32`, a distinct class in a distinct file, easy to conflate
by name) also has a real caller: `src/core/builder.py:676`, wired by idea 53's
`TCK-20260904-INHERITED-REPUTATION-SEED` (M5, shipped 2026-09-05, after the original hardening pass).
**Both were dead or unconfirmed at the 2026-09-02 investigation; both are live now.** `social_systems_
contract.md`'s framing was accurate all along for `ReputationUpdateService`; the hardening backlog's
claim was either wrong from the start or overtaken by M5's own later work — not re-derived further
here. Write the chapter's Reputation section citing both as live, real mechanisms.

## Scope
- Determine whether the new Mechanics Bible chapter should be authored fresh, or whether
  `docs/simulation/social_systems_contract.md`'s existing content should be promoted/restructured
  into the Mechanics Bible's own numbered series (next available number after
  `06_worldbuilding_foundation.md`) and certified `Level 1` — check first, don't assume either shape.
- ~~Resolve the `ReputationService`/`PublicReputationProfile` liveness inconsistency above before
  writing the chapter's own Reputation section~~ — **done, 2026-09-07**: both are confirmed live with
  real callers (`quests.py:233`, `builder.py:676`). Write the chapter citing both as live.
- Relocate or cross-link the reputation formula fragment currently misfiled in
  `docs/mechanics/03_economic_laws.md` — leave a pointer behind, don't duplicate.
- Fold in (cross-link, not rewrite) the three existing partial contracts:
  `docs/simulation/domains/social_memory_contract.md`, `docs/simulation/domains/chronicle_contract.md`,
  `docs/systems/faction_contract.md`.
- ~~Spot-check the ~10 `SOC-FAC-001`–`010` and `SOC-CHRON-001`–`006` parity-ledger entries against real
  `FactionState`/diplomacy code directly~~ — **done, 2026-09-05**: all 16 entries confirmed accurate
  against `src/domains/chronicle/{significance,grouper}.py`,
  `src/domains/faction/diplomatic_state_machine.py`, `src/domains/campaigns/orchestrator.py`, and
  `src/api/routes/chronicle.py`; cited tests re-run and passing (17/17). No corrections needed.

## Out of Scope
- Rewriting the 117 `social_narrative.yaml` entries that are not social/narrative content despite the
  filename (combat, arena, watchdog, CLI, replay-format entries).
- Building any new social mechanic or Chronicle feature — this documents and hardens what already
  exists.
- M5's own ideas (53/54/55/58/60/62) — this is a prerequisite documentation/verification pass those
  tickets can cite, not a substitute for their own scoping.
- The `CanonicalStateHasher` determinism gap — already shipped
  (`TCK-20260902-SOCIAL-CANONICAL-HASH-GAP`).

## Acceptance Criteria
- [x] A Mechanics Bible chapter (new or promoted-and-restructured) exists, is `Certified Level 1`, and
      every formula it states is cited against real code, spot-checked directly — not transcribed from
      the parity ledger's own `verified` claims unverified. **Done** —
      `docs/mechanics/07_social_political_dynamics.md`, promoted from `social_systems_contract.md`
      with 5 sections corrected after independent verification found them materially diverged from
      real code (see Implementation Notes).
- [x] The `ReputationService`/`PublicReputationProfile` liveness question is resolved with a direct
      code check, not assumed from either existing doc. **Done** — both are live, but they are two
      structurally distinct, differently-typed fields sharing a confusingly similar name; see
      Chapter 07 §4.
- [x] The `03_economic_laws.md` reputation fragment is cross-linked, not duplicated. **Done** —
      relocated to Chapter 07 §6, a pointer left in `03_economic_laws.md`.
- [x] The `SOC-FAC-*`/`SOC-CHRON-*` entries are independently spot-checked against real diplomacy code,
      with results recorded (confirmed or corrected). **Done, 2026-09-05** — all 16 confirmed accurate,
      no corrections needed.

## Related Tickets
- `TCK-20260902-SOCIAL-CANONICAL-HASH-GAP` (this plan's item 5, already shipped)
- `TCK-20260905-SUB-327-FABRICATED-CITATION-FIX` (the precedent this ticket's own liveness-check
  requirement is modeled on)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md` (source finding)
- `docs/simulation/social_systems_contract.md` (existing content, may substantially satisfy this
  ticket if promoted rather than duplicated)
- `docs/brainstorm/2026-09-02-core-rpg-social-relationship-axis-proposal.md` (evidence base)
- `docs/mechanics/03_economic_laws.md` (misplaced reputation fragment)
- `docs/parity_ledger/social_narrative.yaml`

## Related Stored Artifacts
None yet — scope-only, staging artifacts to be created by whoever picks this up.

## Related Code Areas
- `src/core/models/social.py` (`SocialComponent`, 15 fields)
- `src/systems/social_systems/{relationships,memory,reputation}.py`
- `src/replay/fingerprint.py`

## Assumptions / Open Questions
- Whether `social_systems_contract.md` should be promoted into the Mechanics Bible numbering or a new
  chapter written alongside it — not decided here, first task for whoever picks this up.
- `SocialComponent`'s exact current field count should be re-confirmed against real code during
  Investigate — this ticket's "15 fields" citation is inherited from the 2026-09-02 investigation and
  has not been re-counted since M5/M6 shipped (several social-adjacent fields landed in that window).

## Implementation Notes
Chose promote-with-correction over author-from-scratch: `social_systems_contract.md` is a genuinely
thorough starting structure, but independently spot-checking every formula against real code (per
this ticket's own AC1 and the SUB-327 precedent) found 5 sections materially diverged from real code
— not stale numbers, but describing mechanisms with no basis in `src/` at all:
1. **Appraisal trust formula** — missing the real `(clan_trust - 0.5) * 0.2` term (idea 54) and the
   `bond.sentiment < -0.8` hard-reject OR-condition.
2. **Reputation** — conflated two structurally distinct, differently-typed fields sharing a name:
   `SocialComponent.public_reputation` (the real clamped scalar) vs. `PublicReputationProfile.labels`
   (a separate label bag `ReputationUpdateService.process_witnessed_event()` actually writes, at a
   different component path entirely, with different event names/deltas than the doc claimed).
3. **Contracts** — cited a non-existent `ESCORT` `ContractKind` (ESCORT is a `QuestKind`) and a
   per-kind breach table that doesn't exist; the real mechanism (`resolve_contract_outcome()`) is one
   generic function applied uniformly across all 10 real `ContractKind` members.
4. **Guilds** — described a `GuildMembership`/dues/rank system with zero real code; the real
   mechanism (`GuildIntelSystem`) is unrelated intel-gathering (visiting a guild building generates a
   rumor Lead about the world's most dangerous region).
5. **Party** — described a `PartyRecord` type that doesn't exist anywhere in `src/`; the real state
   type is `GroupRecord`, with real leadership-influence/election/defection mechanics
   (`PartyCoordinationSystem`/`PartyLifecycleService`) substantially different from what was described.

All 5 corrected in both the new chapter and `social_systems_contract.md` itself (in place, with
inline correction notes and a top-of-file provenance summary) — leaving a known-inaccurate P1/active
doc uncorrected while a new "Certified Level 1" chapter contradicts it would itself be a semantic-
parity violation. Sections confirmed accurate (Relationships clamp table, Social Memory, Party
Composition, Decay) were promoted with presentation changes only. A new finding not in either prior
doc — the real write paths to `public_reputation` (contract fulfillment, party defection, birth-seed,
Campaign carry-forward) — is documented in Chapter 07 §4 with a disclosed dead-code gap (the
contract-betrayal branch has no production caller today, matching this session's own established
"built, not yet reachable" disclosure pattern).

Also relocated the `03_economic_laws.md` §4.1 reputation-discount fragment (pointer left behind) and
updated both roadmap-tracking docs to reflect the whole 5-item hardening backlog is now shipped.

## Test Summary
Docs-only ticket, no `src/`/`tests/` code authored. Every formula in the new chapter was
independently verified against its cited source file/function before writing (see
`staging_artifacts/.../test_plan.md` for the exact commands run). Regression:
`tests/tools/test_generate_registry.py tests/tools/test_doc_staleness_check.py
tests/tools/test_add_frontmatter_live.py` — 176 passed, 0 failed (confirmed clean after
`docs/REGISTRY.yaml` regeneration). `tools/validate_frontmatter.py` clean on every touched/created
file. `make knowledge-index-update` run successfully (docs/ changed).

## Files Changed
- `docs/mechanics/07_social_political_dynamics.md` (new)
- `docs/mechanics/README.md`
- `docs/mechanics/06_worldbuilding_foundation.md`
- `docs/mechanics/03_economic_laws.md`
- `docs/simulation/social_systems_contract.md`
- `docs/plans/rpg_design_roadmap/rpg_social_narrative_mechanics_hardening_plan.md`
- `docs/plans/rpg_design_roadmap/rpg_design_roadmap.md`
- `docs/REGISTRY.yaml` (regenerated)

## Completion Summary
Authored `docs/mechanics/07_social_political_dynamics.md`, the missing Social & Political Mechanics
Bible chapter, `Certified Level 1`, promoted from `docs/simulation/social_systems_contract.md` with
every formula independently re-verified against real code. Found and corrected 5 real, material
inaccuracies in the promoted-from doc (Reputation, Appraisal's trust formula, Contracts, Guilds,
Party) — not transcribed unverified, matching this ticket's own explicit warning against the
SUB-327 fabricated-citation failure mode. Resolved the pre-flagged liveness question: both
`ReputationUpdateService` and `ReputationService.combine_public_reputation()` are live, but are two
structurally distinct fields sharing a confusing name. Relocated the misfiled reputation-discount
fragment and cross-linked the 3 existing partial contracts without rewriting them. Closes out the
whole 5-item Social/Political hardening backlog (`rpg_social_narrative_mechanics_hardening_plan.md`).
No production code touched.
