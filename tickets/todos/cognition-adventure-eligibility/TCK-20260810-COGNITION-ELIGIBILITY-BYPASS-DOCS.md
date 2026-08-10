---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS
phase: open
date: 2026-08-10
tags: [cognition, strategy]
---

# TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS

## Title
Update authoritative docs for cognition-driven eligibility and generalized bypass

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Once C1's cognition-profile eligibility gate and C2's generalized interruption-bypass rule are actually landed, the durable documentation describing them must be brought back into parity per the Authoritative Mechanics Rule: docs/mechanics/04_strategic_cognition.md's stale hardcoded-HERO and "score>80 emergency bypass" language, docs/simulation/domains/adventure_contract.md's eligibility table, and docs/parity_ledger/strategic_cognition.yaml's entries all need updating to describe the actual landed mechanism, not a speculative paraphrase written ahead of the code.

## Scope
- Update docs/mechanics/04_strategic_cognition.md §1-2, including the stale L39 line ("Emergency Bypass: High-urgency Danger concerns (score>80) ignore interruption margin"), to describe eligibility as driven by CognitionProfileDefinition.supports_adventure_routing and the bypass rule exactly as landed in C2 (score clears both effective_current_score and urgency floor, for any kind, with detour as sole unconditional structural bypass) — matching the ACTUAL landed code, not a paraphrase
- If §6.6's System A/System B scale mismatch is resolved via normalization in C2, document that resolution in §6.6 or a new subsection
- Update docs/simulation/domains/adventure_contract.md's eligibility table (L27-36), replacing the Role=EntityRole.HERO(0) row with the real supports_adventure_routing cognition-profile check, and correct the "What It Reads" (L56) hero-only framing
- Add new STRAT-252+ entries to docs/parity_ledger/strategic_cognition.yaml following the STRAT-243/250/251 field pattern (id/text/status/priority/legacy_evidence/v2_evidence/proof_type/test_path/divergence_note/support_boundary), with v2_evidence written from C1/C2's actual landed code
- Run make knowledge-index-update since docs/ files are being modified

## Out of Scope
- docs/audits/D22_dormant_content_wiring.md — that belongs to TCK-20260810-D22-DORMANT-WIRING-AUDIT (C4), not this ticket
- The intentional_divergences.md entry for the bypass-tightening behavior change — owned by TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION (C2), per CLAUDE.md's rule that divergence-recording belongs to whichever ticket changes the logic
- Any code changes to src/domains/adventure/phase.py, src/content/schema.py, or src/systems/strategic_systems/intelligence.py — this is a pure docs ticket, strictly downstream of C1 and C2's landed implementations

## Acceptance Criteria
- [ ] 04_strategic_cognition.md §1-2 describes eligibility as driven by CognitionProfileDefinition.supports_adventure_routing (not hardcoded EntityRole.HERO) and describes the bypass rule exactly as landed in C2 — matching the actual code, not a paraphrase
- [ ] Stale line 39 ("Emergency Bypass: High-urgency Danger concerns (score>80) ignore interruption margin") is replaced with the real generalized rule; if the §6.6 scale-mismatch was resolved via normalization in C2, that resolution is documented in §6.6 or a new subsection
- [ ] adventure_contract.md's eligibility table replaces the Role=EntityRole.HERO(0) row with the real supports_adventure_routing cognition-profile check; the "What It Reads" hero-only framing is corrected
- [ ] strategic_cognition.yaml gains new STRAT-252+ entries following the STRAT-243/250/251 field pattern, each with v2_evidence written from C1/C2's actual landed code, not written speculatively ahead of their landing
- [ ] tests/tools/test_cognition_strategy_skill_content.py, test_parity_ledger_scan.py, test_parity_index.py, and test_parity_index_baseline.py continue to pass after the structural edits (updated alongside if needed)

## Related Tickets
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml
- docs/guidelines/intentional_divergences.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/mechanics/04_strategic_cognition.md
- docs/simulation/domains/adventure_contract.md
- docs/parity_ledger/strategic_cognition.yaml
- src/content/schema.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- this ticket is explicitly sequenced after C1 and C2 — writing doc content before their implementations land would document a proposal, not reality
- the design doc's scale-mismatch open question is only as resolved as C2's actual landed fix; this ticket reflects that resolution, it does not resolve the ambiguity itself
- intentional_divergences.md ownership belongs to C2 (the logic-changing ticket), not this ticket, per CLAUDE.md

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
