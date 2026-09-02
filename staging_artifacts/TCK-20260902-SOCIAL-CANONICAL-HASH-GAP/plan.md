---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: plan
tags: [social, determinism]
---

# Plan — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

1. Re-verify the 5-field gap from `investigation.md` directly against current `src/core/state.py`.
2. For each field, decide covered-vs-excluded and record the reasoning inline as a code comment where
   excluded (avoids re-litigating the same question later, per the systemic fabricated-citation lesson
   this session already surfaced — decisions need a real, checkable reason, not a vague one).
3. Implement `to_canonical_dict()` changes for the fields decided as covered.
4. Add/update a determinism test per added field: construct two entities differing only in that field,
   assert their canonical hashes differ (fails pre-fix, passes post-fix).
5. Run existing canonical-hash/replay determinism test suite unchanged — must still pass.
6. Update `docs/parity_ledger/social_narrative.yaml` via `tools/parity_ledger_writer.py` with the new
   coverage status and real test-path evidence.
7. Update `docs/core/state.md` if it states a `SocialComponent` field count.
8. Check whether any committed `world_compile_report.json` fixture's `state_hash` changes as a result;
   if so, regenerate and note it explicitly in Implementation Notes — do not silently accept a diff.
