---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE
artifact_type: investigation
tags: [social, combat]
---

# Investigation — TCK-20260904-SOCIAL-NEMESIS-ROLE-PRECEDENCE

Confirmed via direct code read: `SocialComponent.nemesis_ids` (promoted from `grudge_history >= 3.0`,
`SocialMemoryService.check_nemesis_promotion()`, `src/systems/social_systems/memory.py`) and
`SocialBond.role` (`RelationshipRole.FRIEND`/`RIVAL`/`NEUTRAL`) are written on fully independent paths —
`check_nemesis_promotion()` never reads or writes `bond.role`, and `RelationshipRole`'s own docstring
already states "Independent of nemesis_ids/grudge_history." An entity pair can genuinely hold
`bond.role == FRIEND` while the same target is also a confirmed `nemesis_ids` member.

Two real consumers read these fields independently:
- `PartyCompositionScorer._candidate_role_value()` (`src/systems/social_systems/party_composition.py`)
  returned `+1.0` for a `FRIEND` bond regardless of `nemesis_ids` — a confirmed nemesis contributed
  positively to party composition score.
- `src/domains/adventure/generator.py`'s `FORM_PARTY` route's nemesis-block check only read a
  locally-derived proxy from `entity.strategic.blockers` (`BlockerKind.SOCIAL`), never the canonical
  `nemesis_ids` field — a confirmed nemesis with no matching strategic blocker was not blocked at all.

Fix: `nemesis_ids` takes precedence over `bond.role == FRIEND` in `_candidate_role_value()` (a sustained
real-harm signal outweighs a coarser, independently-written tag). `generator.py`'s block check now unions
the canonical `nemesis_ids` field with the existing strategic-blocker proxy, rather than replacing it —
the two may catch different real scenarios.
