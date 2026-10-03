---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: investigation
tags: [social, determinism]
---

# Investigation — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

Re-verified directly against current code on pickup (2026-09-03), superseding the original
scoping-time investigation (which undercounted, see the ticket's own "Correction on pickup" note):

- `SocialComponent` (`src/core/models/social.py:32-57`) has 17 real fields; `EntityState.to_canonical_dict()`'s
  `"social"` sub-dict (`src/core/state.py`, pre-fix ~lines 800-811) covered only 10, leaving 7 uncovered:
  `debt_history`, `salience_history`, `nemesis_ids`, `place_attachment`, `betrayal_records`,
  `last_offer_tick`, `rejection_count`.
- Unlike the parallel Knowledge-axis ticket, this gap was NOT introduced by code drift since the
  investigation (M3's merge added no `SocialComponent` fields) — the original count was simply wrong at
  scoping time.
- All 7 confirmed real, actively-consumed: `nemesis_ids` gates cognition target evaluation
  (`src/engine/cognition.py:47,94`), `rejection_count` feeds contract appraisal
  (`src/systems/social_systems/appraisal.py:97`), `salience_history` gates memory pruning
  (`src/systems/social_systems/memory.py:46`), all 7 read/written in
  `src/systems/social_systems/relationships.py`.
- The real consumer of `to_canonical_dict()` is `CanonicalStateHasher.to_canonical_data()`/`get_hash()`
  (`src/engine/checkpoint.py:63-93`), called directly by `src/engine/kernel.py:1161-1162`/`:1230-1231` —
  same verified consumer chain as `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`, not re-derived here.
- No field carried a "derived" rationale (unlike `StrategicComponent.profile`), so no exclusions were
  made — all 7 added.
