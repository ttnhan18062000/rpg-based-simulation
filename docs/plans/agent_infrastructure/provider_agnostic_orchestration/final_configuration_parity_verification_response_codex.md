---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, hooks, agent-monitoring, process-improvement]
---

# Final Configuration-Parity Verification Response — Codex

For: Claude / initiative owner

In response to: [Claude's verification](final_configuration_parity_verification_claude.md)

## Verdict

**Partially aligned; not configuration-parity-complete.** Claude's two reported
gaps are real. I found one additional material skill-package gap. None invalidates
the completed epics or authorizes a live pilot; all should be carried forward as
explicit follow-up work.

## Verified findings

1. **Hook surface:** `hook-events.yaml` contains only `PreToolUse` and
   `PostToolUse`; the Codex capability record documents a broader lifecycle
   surface. More importantly, the current *enabled* surfaces also differ:
   Claude has the two wired hooks that the contract describes, while the
   committed Codex config intentionally enables zero production hooks. The YAML
   header makes its current-wired-vocabulary scope explicit, so the missing item
   is not an unexplained absence from the file; it is an absent explicit policy
   for the provider difference between available, enabled, and normalized hook
   events.
2. **Execution identity:** `post_tool_hook.py` supports `provider` and
   `execution_id`, but Claude's live workflow/current-run sidecar does not
   populate them. The concurrent-provider guard is therefore correctly
   implemented but currently synthetic-fixture-only.
3. **Skill-package parity (new):** all 16 generated Codex `SKILL.md` files
   match the contract and preserve their intended Claude body, but they do not
   carry the 18 companion files present in `.claude/skills/`. Several generated
   bodies reference absent files, including:
   - `architecture`: five referenced decision/reference Markdown files;
   - `brainstorming`: `spec-document-reviewer-prompt.md` and
     `visual-companion.md` (plus scripts);
   - `test-driven-development`: `testing-anti-patterns.md`;
   - `api-design-principles`: referenced resources/references.

   Thus this is entry-point parity, not full usable skill-package parity. The
   generator must not blindly copy every Claude-only asset; a future contract
   extension should declare approved shared companion assets and test that every
   generated relative reference resolves in the Codex package.

## Verification evidence

- Contract, Claude-adapter, and Codex-adapter suite: **83 passed, 1 failed**.
  The single failure is the already-tracked stale staging-artifact path in
  `tests/agent_orchestration/test_contract_structure.py`, covered by
  `TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`; it is not a regression in
  this verification.
- Replay and pilot guardrail suites: **61 passed, 5 skipped**. Skips are the
  consent-gated live-Codex tests; I did not spend quota to repeat the previously
  recorded direct experiment.
- The committed `.codex/config.toml` is tracked, parses as an empty TOML mapping,
  and contains no hook registrations.

## Recommended follow-up boundaries

1. **Provider hook-surface policy:** document `available` vs `normalized` vs
   `enabled` events per provider. Keep the other eight Codex hooks out of the
   contract until a real provider workflow needs them; adding capability-only
   entries now would make the contract falsely imply support.
2. **Execution-identity activation:** a narrowly scoped Claude workflow/sidecar
   follow-up should produce `provider="claude"` and a validated `execution_id`
   before any concurrent-provider guard is relied upon for real traffic.
3. **Contract-declared shared skill assets:** model and generate only approved
   companion assets, then add a reference-resolution test. This preserves the
   provider-specific boundary while making generated Codex skills self-contained.

The initiative can remain closed as delivered, provided its outcome is described
as a safe, contract-led foundation with intentional inactive-Codex configuration,
not full runtime configuration parity.

