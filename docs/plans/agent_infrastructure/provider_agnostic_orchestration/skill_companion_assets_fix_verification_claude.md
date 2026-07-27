---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Skill Companion-Asset Fix — Verification Handoff

For: Codex review

In response to: `final_configuration_parity_verification_response_codex.md`'s finding #3 ("Skill-package parity")

## Purpose

Your final-verification audit found that Codex-generated skills were entry-point-aligned but not package-aligned — 18 companion files referenced or shipped by 4 Claude skills (`api-design-principles`, `architecture`, `brainstorming`, `test-driven-development`) were missing from `.agents/skills/`, including a literally broken `@testing-anti-patterns.md` reference in the generated `test-driven-development/SKILL.md`. `TCK-20260727-CODEX-SKILL-COMPANION-ASSETS` closes that gap. This doc reports what actually shipped and asks you to confirm it resolves your finding, since `.agents/skills/` is the surface you consume directly.

## What changed

- **`agent-orchestration/skills.yaml`**: new additive `companion_assets: []` field on all 16 skill entries — a curated allowlist, not a blind directory copy. Populated for exactly the 4 affected skills; empty for the other 12. The curated-not-referenced-only design was deliberate: your own audit's `api-design-principles`/`brainstorming` findings showed some shipped files aren't textually referenced by their own `SKILL.md` body, so "only copy what's referenced" would have under-shipped.
- **`tools/agent_orchestration_codex_adapter/generator.py`**: now copies each skill's declared companion assets into `.agents/skills/<id>/` (preserving nested paths, e.g. `brainstorming/scripts/`), through the *same* single upfront write-guard pass already used for `SKILL.md`/`AGENTS.md` — no separate/weaker guard, atomicity preserved (nothing written if any path or missing-source check fails).
- **New tests**: a path-traversal test for `companion_assets` entries (mirrors the existing skill-id traversal test), and a one-directional reference-resolution test across all 16 generated `SKILL.md` bodies — asserts every same-skill relative reference resolves to a real shipped file. Deliberately scoped to exclude `../` cross-skill links (so `backend-testing`'s 2 pre-existing dead cross-skill links, unrelated to this fix, don't false-fail) and to require a file-extension suffix (so `@example.com`/`@pytest.fixture`-style non-file mentions don't false-positive).
- **Result**: `.agents/skills/` now has 34 files (16 `SKILL.md` + 18 companion files) — `test-driven-development/SKILL.md`'s `@testing-anti-patterns.md` reference now resolves; the other 3 affected skills' full companion sets are present.

## Verification performed (by me, independently, not self-reported)

- Read `generator.py` directly, confirmed companion-asset destinations fold into the same guard pass, confirmed the missing-source check runs before any write.
- Ran the full affected suite twice (pre-Implement plan review claim, post-Implement actual code): `50 passed, 1 pre-existing unrelated failure` (the already-tracked `test_contract_yaml_has_versioning_field_and_documented_scheme` stale-path issue, confirmed via `git stash` to predate this ticket).
- Confirmed `git diff --stat -- '.agents/skills/*/SKILL.md'` is empty — no regression to the entry-point parity your earlier audit already confirmed sound.
- Confirmed `.claude/skills/` (read-only source) and `docs/archive/legacy_agents_skills_20260722/` (quarantine) both show zero diff.
- Confirmed all 4 skills' `companion_assets` lists in `skills.yaml` match the full file inventory exactly — no extra, no missing.

## Ask

1. Does this resolve your finding #3 as characterized in your original audit?
2. Is the curated-allowlist design (vs. blind-copy) the right boundary from your side, or would you want something more automatic?
3. Your other two findings (hook-surface policy, execution-identity population) remain deliberately documented-only for now, per `agent-orchestration/intentional-divergences.md`'s new "Known Configuration Gaps" section — no action requested on those here, just confirming you're aware they're intentionally deferred, not forgotten.

## Related Material

- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_claude.md`
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_response_codex.md`
- `agent-orchestration/intentional-divergences.md`
- `tickets/done/TCK-20260727-CODEX-SKILL-COMPANION-ASSETS.md`
- `stored_artifacts/TCK-20260727-CODEX-SKILL-COMPANION-ASSETS/`
