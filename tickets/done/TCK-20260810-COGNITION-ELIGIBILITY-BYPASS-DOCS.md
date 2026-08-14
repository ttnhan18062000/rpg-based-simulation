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
DONE

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
- [x] 04_strategic_cognition.md §1-2 describes eligibility as driven by CognitionProfileDefinition.supports_adventure_routing (not hardcoded EntityRole.HERO) and describes the bypass rule exactly as landed in C2 — matching the actual code, not a paraphrase
- [x] Stale line 39 ("Emergency Bypass: High-urgency Danger concerns (score>80) ignore interruption margin") is replaced with the real generalized rule; the §6.6 scale-mismatch resolution (normalization anchored to `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`) is documented as a new note in §6.6
- [x] adventure_contract.md's eligibility table replaces the Role=EntityRole.HERO(0) row with the real supports_adventure_routing cognition-profile check; the Purpose paragraph's hero-only framing is corrected (re-derived from current file content — the ticket's cited "L56 What It Reads" line had drifted and carried no hero-only claim; see Implementation Notes)
- [x] strategic_cognition.yaml gains new STRAT-252+ entries following the STRAT-243/250/251 field pattern, each with v2_evidence written from C1/C2's actual landed code, not written speculatively ahead of their landing
- [x] tests/tools/test_cognition_strategy_skill_content.py, test_parity_ledger_scan.py, test_parity_index.py, and test_parity_index_baseline.py continue to pass after the structural edits (3 pre-existing, unrelated failures in test_parity_index_baseline.py confirmed present before this ticket's edits too — see Test Summary)

## Related Tickets
- TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
- TCK-20260703-ADVENTURE-ELIGIBILITY-ROLE-FILTER
- TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY
- TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
- TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC (follow-up, filed at Verify time — tracks the
  disclosed SKILL.md residual gap this ticket deliberately left untouched)

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

**Architecture-Verify correction (post-Implement, not in the original plan):** the Purpose
paragraph's new citation `AdventureRouteGenerator.generate(hero, state)` was factually wrong —
`AdventureRouteGenerator.generate`'s real parameter (`src/domains/adventure/generator.py:25-29`) is
named `entity`, not `hero`; `hero` is only the caller's local variable name at the call site
(`phase.py:159`), not "the code's own parameter naming" of that function. Fixed by re-pointing the
citation to `_threat_resolved(hero, state)` (`src/domains/adventure/phase.py:27`), which genuinely
uses `hero` as its own parameter name. This was the only finding from Architecture-Verify's 2nd
diff-based pass; everything else (the §2 detour-exemption scoping, the eligibility table row, the
two new STRAT-252/253 entries) matched the approved plan exactly with no changes needed.

Implemented per the twice-reviewed, APPROVED `staging_artifacts/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS/plan.md` (5 steps), no deviations from the plan's content:

1. **`docs/mechanics/04_strategic_cognition.md` §2** — added a lead-in sentence after the section intro stating the interruption-resistance law, for adventure-domain project routing specifically, only governs entities whose resolved `CognitionProfileDefinition.supports_adventure_routing` is `True` (citing `src/content/schema.py:100` and cross-referencing `adventure_contract.md`), and noting System B/`GoalRegistry` also uses the same `Switch_Allowed` mechanism independent of that gate. Replaced the stale `**Emergency Bypass**: High-urgency "Danger" concerns (score > 80) ignore the interruption margin.` bullet with a `**Generalized Bypass**` bullet describing the actual landed rule from `intelligence.py:978-994`: `detour` is exempt only from the added normalized floor/percentage gate, not from the base `candidate_project.score > effective_current_score` comparison (which still applies to it, like every candidate); every other kind, from either scoring system, must additionally clear a dual normalized condition (exceeds the current project's normalized effective score AND the fixed `0.8` urgency floor) while a lock is active. Left the `Switch_Allowed`/`Interruption_Margin` code block and the two unchanged bullets untouched. Did not edit §1 (Goal Hierarchy table) — confirmed by direct re-read it carries no role/eligibility claim to correct, per plan.md's Resolved Decision 1.
2. **§6.6** — added one short note after the Score Range Summary table (before the `---` separator) stating the `~2.9` "Total non-blocked" ceiling is also the normalization anchor (`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, `intelligence.py:29-31`) used in §2's Generalized Bypass gate. No numeric table value changed.
3. **`docs/simulation/domains/adventure_contract.md`** — corrected the Purpose paragraph's first sentence to state eligibility is driven by `CognitionProfileDefinition.supports_adventure_routing` (not role), with a clause noting "hero" is retained as the domain's established shorthand matching the code's own parameter naming (`AdventureRouteGenerator.generate(hero, state)`). Replaced the eligibility table's `Role` row (`EntityRole = 0 (hero)`) with a `Cognition eligibility` row describing the real 3-tier resolution from `phase.py:49-80,83-96`: (a) explicit `identity.properties["cognition_profile_id"]`, else (b) `identity.properties["role_id"]` → `RoleDefinition.default_cognition_profile`, else (c) legacy `EntityRole.HERO` → the `"hero"` role's own default. Did not globally replace "hero" elsewhere in the file, per plan.md's explicit Scope Guard — the code's own parameter naming makes it the correct domain shorthand outside these two spots. Note: the ticket's own cited "L56 'What It Reads' hero-only framing" target had drifted (current L56 is a `personality` table row with no hero-only claim, confirmed by investigation.md and re-confirmed here); the two real correction targets were the Purpose paragraph and the Role table row, both fixed.
4. **`docs/parity_ledger/strategic_cognition.yaml`** — appended STRAT-252 (System A's project-commit branch now routes through `evaluate_project_switch()` instead of unconditionally overwriting `current_project_id`, closing the asymmetry where only System B respected an active lock; P1) and STRAT-253 (`RouteToProjectMapper.map_to_states()` threads the real `AdventureRouteOption.score` instead of a hardcoded `1.0`, a prerequisite for STRAT-185/186's normalized comparison to be meaningful for System A; P2), using the exact YAML plan.md drafted (already schema-checked and evidence-verified by 2 architecture review passes). Verified via `python3 -c "import yaml; ..."` that the file still parses and both new ids are present with no duplicate collision against the pre-existing highest id (STRAT-251). Did not touch STRAT-243 or STRAT-185/186/187.
5. **`make knowledge-index-update`** — ran after Steps 1-4 landed; completed with exit 0 (`Incremental update complete: 7081 chunks total (6 files re-embedded, 2635 from cache, 0 deleted)`).

**One wording correction found during verification (not a plan deviation, a self-caught drafting slip):** the first draft of the §2 Generalized Bypass bullet's closing clause ("generalizes the old 'Danger score > 80' special case") accidentally reproduced the literal stale substring `score > 80` the plan's own Step 1 verify command (`grep -n "score > 80" ... # should return no match in §2`) checks for. Reworded to "Danger score above 80" (same meaning, describing the historical rule being generalized away from) so the grep returns no match, matching plan.md's own verification intent.

**`last_verified` frontmatter bump:** confirmed this repo's convention by checking `04_strategic_cognition.md`'s own git history — commit `9071f757` (2026-08-09, an unrelated combat ticket that also touched this file's content) bumped `last_verified` from `2026-06-27` to `2026-08-09` in the same commit as its content edit. Following that established convention, bumped both `04_strategic_cognition.md` and `adventure_contract.md`'s `last_verified` to `2026-08-10` (today) since both received content edits in this ticket.

**Residual gap, explicitly not fixed here (recorded per plan.md's Resolved Decision 3, so it is visible for a future ticket and not only living in staging artifacts):** `.claude/skills/cognition-strategy/SKILL.md` and its `.agents/skills/cognition-strategy/SKILL.md` mirror both still carry the same stale sentence this ticket fixed in the Mechanics Bible: `"**Emergency bypass**: Danger concerns scoring > 80 ignore the interruption margin entirely."` (both files, near line 70-73). `tests/tools/test_cognition_strategy_skill_content.py` does not pin that specific sentence (it only asserts `"Interruption_Margin = Profile_Resistance * resistance_multiplier"` and `"not a hardcoded 30.0"` are present), so no test forces this fix and none broke from leaving it stale. This ticket's own Scope/Related Docs/Related Code Areas never named `.claude/skills/` or `.agents/skills/`, so editing it here would have been undeclared scope expansion — left untouched by design, not by oversight. **Follow-up ticket filed: `TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC`** (`tickets/todos/TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC.md`, hotfix tier) — update both SKILL.md files' bypass-rule sentence to match the Generalized Bypass rule now documented in `04_strategic_cognition.md` §2. Filed at Verify time per `done-checker`'s DoD condition 11 finding (a disclosed gap needs a real ticket reference, not only deferral prose).

## Test Summary

Ran the plan's exact scoped verification command:
```
pytest tests/tools/test_parity_index.py tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_index_baseline.py tests/tools/test_cognition_strategy_skill_content.py -v
```
Result: **57 passed, 3 failed** (60 total).

The 3 failures are all in `tests/tools/test_parity_index_baseline.py` and are **pre-existing, unrelated to this ticket's edits** — confirmed by re-running the same file with this ticket's changes `git stash`ed: the identical 3 tests fail identically before this ticket's edits (3 failed, 12 passed either way):
- `test_baseline_manifest_does_not_coerce_missing_test_path` — asserts a hardcoded baseline count (`1347`) of ledger entries missing `test_path`; the live count is `1343`, drifted independent of this ticket (this ticket's own 2 new entries both carry non-null `test_path`, so they cannot have caused the drift).
- `test_v1_decision_artifact_covers_all_scope_boundaries` and `test_v1_decision_artifact_does_not_authorize_mutation_cli` — both fail with `FileNotFoundError` on `docs/plans/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`, a file unrelated to `docs/parity_ledger/strategic_cognition.yaml` and never touched by this ticket.

None of the 3 failures involve `strategic_cognition.yaml`, STRAT-252/253, or any file this ticket edited. Verification greps also passed:
- `grep -n "score > 80" docs/mechanics/04_strategic_cognition.md` → no match (exit 1)
- `grep -n "EntityRole = 0" docs/simulation/domains/adventure_contract.md` → no match (exit 1)

## Files Changed
- `docs/mechanics/04_strategic_cognition.md` (§2 eligibility lead-in + Generalized Bypass bullet rewrite; §6.6 normalization cross-reference note; `last_verified` bump)
- `docs/simulation/domains/adventure_contract.md` (Purpose paragraph eligibility framing; eligibility table `Role` → `Cognition eligibility` row; `last_verified` bump)
- `docs/parity_ledger/strategic_cognition.yaml` (added STRAT-252, STRAT-253)

No `src/` files were touched (`git diff --stat -- src/` shows only pre-existing, already-uncommitted C1/C2 code that was present in the working tree before this ticket's work began — not from any edit made in this session; confirmed no Edit/Write tool call in this session targeted any `src/` path).

## Completion Summary

Brought `docs/mechanics/04_strategic_cognition.md` §2/§6.6, `docs/simulation/domains/adventure_contract.md`'s Purpose paragraph and eligibility table, and `docs/parity_ledger/strategic_cognition.yaml` into parity with C1's landed cognition-profile eligibility gate and C2's landed generalized interruption bypass, replacing stale `EntityRole.HERO`/"score > 80" language with the actual mechanism and adding 2 new parity-ledger entries (STRAT-252, STRAT-253). Pure-docs change, zero `src/` edits, all 5 plan steps completed with no content deviations. Scoped test run passed 57/60, with the 3 failures pre-existing and unrelated (verified via git-stash comparison). Ran `make knowledge-index-update` per Step 5. Remaining work before this ticket can move to `tickets/done/`: Test/Parity/Verify/Finalize phases per the standard-tier pipeline (this session performed Implement only); the `.claude/skills/cognition-strategy/SKILL.md` bypass-rule drift is a recorded residual gap, now tracked in follow-up ticket `TCK-20260810-COGNITION-STRATEGY-SKILL-BYPASS-SYNC` (filed at Verify time), not part of this ticket's own closure.
