---
status: active
layer: core
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH
date: 2026-09-07
---

# Plan: TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH

## Summary
Wire a real writer for `SocialBond.role`, derived from the bond's own `sentiment` inside
`RelationshipService.process_update()` (the confirmed real, live, per-update apply-path), rather than
mirroring the ticket's own suggested nemesis-promotion precedent (found to be itself dead code).

## Steps
1. `src/systems/social_systems/relationships.py`: import `RelationshipRole`; add
   `FRIEND_SENTIMENT_THRESHOLD`/`RIVAL_SENTIMENT_THRESHOLD` class constants (0.8 / -0.8, reusing
   `appraisal.py`'s real `TOTAL_DISTRUST` bound); in the `bond_updates` loop, derive `role` from the
   resulting `sentiment` whenever `b_upd.sentiment_delta != 0` and `role_set` is not explicitly given.
2. `tests/unit/social/test_relationships.py`: 8 new tests covering FRIEND/RIVAL derivation, mid-band
   no-op, sticky-against-later-mid-band, cross-boundary flip (FRIEND→RIVAL on an extreme reversal),
   explicit `role_set` override priority, and zero-`sentiment_delta` no-touch (re-asserting the
   pre-existing guarantee directly against the new code path).
3. `docs/mechanics/07_social_political_dynamics.md` §2: disclose the new write path and its real
   reachability (`PartyCompositionScorer` via `FORM_PARTY`). §3: correct the "per-tick" framing for
   nemesis promotion/place attachment (found dormant during this ticket's own investigation) for
   internal chapter consistency.
4. `docs/parity_ledger/social_narrative.yaml`: new `SOC-248` entry via `parity_ledger_writer.py`.
5. Ticket closure: move to `tickets/done/`, record disposition (wire, not remove) with evidence,
   append `working_log.csv`, regenerate `docs/REGISTRY.yaml`, record monitoring.

## Acceptance Criteria Map
- AC1(a) — wire a real, tested trigger: satisfied by step 1+2 (8 tests, including a real bond
  transition test through `process_update()`).
- AC2 — evidenced disposition: satisfied by investigation.md's "Removal considered and rejected"
  section (a real, live, starved consumer already exists).

## Scope Guards
- Do not touch `nemesis_ids`/`grudge_history`/`check_nemesis_promotion()`/`tick_place_attachment()` —
  disclosed as a separate dormant finding, not fixed here.
- Do not touch the other 5 sibling tickets in the Dormant Mechanism Closure epic, or the epic ticket
  itself, or move the `tickets/todos/dormant-mechanism-closure/` folder.
- Do not add a fingerprint/`StateFingerprinter` entry for `SocialBond` fields — a pre-existing gap
  (familiarity/sentiment were already excluded before this ticket), disclosed but out of scope.
- Do not break either pre-existing role test
  (`test_social_bond_role_set_via_authoritative_update_only`,
  `test_process_update_role_set_none_preserves_existing_role`).

## Risks
None outstanding.
