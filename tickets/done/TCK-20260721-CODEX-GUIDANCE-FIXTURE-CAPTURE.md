---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
phase: open
date: 2026-07-21
tags: [ai, workflows, process-improvement, hooks, skills]
---

# TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE

## Title
Codex guidance/skills arrangement and real hook-payload fixture capture

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add the corrected root AGENTS.md and regenerate .agents/skills/ generated from the validated shared contract (not merely "reviewed canonical material" — never reactivating stale legacy .agents content), then add minimal trusted .codex/ configuration only after isolated scratch-directory fixture experiments confirm project trust, matcher behavior, and the real hook-payload schema/timing for each event the first slice needs — without enabling any production hook yet. This matters because the live repo currently has 18 legacy SKILL.md files still auto-discoverable with no containment decision, and no Codex pilot may be authorized until that is quarantined or atomically replaced with a preserved reviewable copy.

**Corrected per Codex review (2026-07-22):** this ticket now has an explicit intra-batch dependency on `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` — the plan's approved architecture treats the shared contract as the sole canonical semantic source, so a manually curated Codex delivery catalog produced before that contract exists would create a second semantic authority. Legacy-skill containment stays inside this ticket (Codex confirmed no separate ticket is needed), but the atomic replacement must now produce the catalog from the validated contract, not merely from "reviewed material."

## Scope
- **Entry criterion: `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` must have landed** — the validated `agent-orchestration/` contract is this ticket's source for AGENTS.md/skills content, not an independently curated set
- Quarantine or atomically replace the legacy .agents/skills/ tree (18 SKILL.md files) BEFORE any new AGENTS.md/skills go live, preserving a byte-identical reviewable copy and leaving agent-monitoring/*.jsonl unchanged
- Add a corrected root AGENTS.md generated from the validated contract, verifiably not a copy of the stale .agents/rules/AGENTS.md draft (which has confirmed 17-phase vs real 32-phase pipeline drift)
- Regenerate .agents/skills/ content generated from the validated contract's skills.yaml (not from independently human-curated material once the contract exists — human review applies to the contract's own skills.yaml, not to a second, parallel AGENTS.md/skills curation pass)
- Run isolated scratch-directory Codex CLI fixture experiments to confirm project trust behavior, matcher behavior, and capture the real hook-payload JSON schema/timing for each event needed by the first slice
- Add minimal trusted .codex/ configuration only after fixture experiments confirm behavior — with no production hook enabled

## Out of Scope
- Does not enable a working live Codex pilot (that is the live-Codex-pilot-guardrails ticket's scope)
- Does not build the contract's own code-generation tooling (owned by TCK-20260721-ORCHESTRATION-CONTRACT-CORE) — this ticket consumes the contract's generation command, it does not build it
- Does not enable any production hook as a result of this ticket's work
- Does not begin AGENTS.md/skills generation before TCK-20260721-ORCHESTRATION-CONTRACT-CORE has landed

## Acceptance Criteria
- [x] This ticket's AGENTS.md/skills generation work does not begin until TCK-20260721-ORCHESTRATION-CONTRACT-CORE has landed and its validator/generator is available to consume
- [x] Legacy .agents/skills/ tree (18 SKILL.md files) is quarantined/archived with a preserved byte-identical copy, OR atomically replaced, BEFORE the new AGENTS.md/skills content goes live — verified by a test asserting no stale SKILL.md remains on Codex's auto-discovery path while the archived copy still exists
- [x] The replacement AGENTS.md/skills catalog is generated from the validated `agent-orchestration/` contract (via its explicit generation command), not independently hand-curated — verified by tracing the generated content back to contract source fields, not merely asserting human review occurred
- [x] Root AGENTS.md exists and is verifiably NOT a copy of the stale .agents/rules/AGENTS.md draft (e.g. does not repeat the confirmed 17-phase pipeline drift; documents the real 32-phase pipeline)
- [x] Committed fixture record(s) capture the real hook-payload JSON schema/matcher/timing via an isolated scratch-directory Codex CLI invocation (distinct from prior documentation-citation-only evidence)
- [x] No production hook is enabled as a result of this ticket's work (verified by explicit check of .codex/ config state at ticket close)
- [x] agent-monitoring/*.jsonl is unchanged (append-only diff, i.e. zero rewritten/reordered/deleted lines) after the containment action
- [x] The containment action (quarantine/replace of legacy .agents/skills/) is sequenced first within this ticket's own execution, as a hard entry criterion, before AGENTS.md/skills regeneration proceeds

## Related Tickets
- TCK-20260721-ORCHESTRATION-CONTRACT-CORE (hard predecessor — validated contract is this ticket's generation source, added per Codex's 2026-07-22 review correction)
- TCK-20260721-AGENTS-DIR-DISPOSITION
- TCK-20260721-CODEX-CAPABILITY-MATRIX
- TCK-20260721-AGENTS-DISPOSITION-FIX
- TCK-20260721-AGENTS-DISPOSITION-DISCOVERABILITY-FIX
- TCK-20260721-CODEX-REPLAY-PROOF
- TCK-20260721-ORCHESTRATION-CONTRACT-ADR
- TCK-20260721-PROVIDER-AGNOSTIC-EPIC

## Related Docs
- docs/ai/agents_dir_disposition.md
- docs/ai/codex_capability_matrix.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/ai/replay_fixture_spec.md
- docs/architecture/agent_orchestration_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/ai/agents_dir_disposition.md
- docs/ai/codex_capability_matrix.md
- docs/plans/agent_infrastructure/provider_agnostic_orchestration/implementation_plan.md
- docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration_discovery_gate_closure_final_corrections_response_codex.md
- docs/ai/replay_fixture_spec.md
- docs/architecture/agent_orchestration_contract.md
- tests/tools/test_codex_capability_diagnostics.py
- tests/tools/test_post_tool_hook.py
- .agents/rules/AGENTS.md
- tickets/done/provider-agnostic-discovery/SEQUENCE.md

## Assumptions / Open Questions
- Real hook-payload capture consumes real API usage under the user's authenticated account — must be flagged to the ticket owner before running, consent to be obtained during Plan/Implement
- WebFetch is blocked in this sandbox — live doc re-verification for canonical AGENTS.md material may need WebSearch or cached sources as fallback
- Per Codex's 2026-07-22 review correction, "reviewed canonical material" is superseded: the AGENTS.md/skills catalog must be generated from the validated `agent-orchestration/` contract via its explicit generation command, once TCK-20260721-ORCHESTRATION-CONTRACT-CORE lands — human review applies at the contract's own skills.yaml authoring stage (that ticket's scope), not as a second independent curation pass in this ticket

## Implementation Notes

- Step 3 containment (2026-07-22): captured raw pre-containment snapshots of `runs.jsonl` (705 lines), `events.jsonl` (3673 lines), and `tools.jsonl` (65756 lines) outside the repository; atomically moved `.agents/skills/` to `docs/archive/legacy_agents_skills_20260722/`; captured post-move snapshots with the same counts; `assert_prefix_preserved(pre, post)` passed. No pre-existing monitoring line was rewritten, reordered, or deleted.
- Step 10/11 operator consent (2026-07-22T10:04:06Z): the operator (session user, ttrungnhan1806@gmail.com per this session's context) gave explicit, contemporaneous consent for Claude to execute Step 11's real Codex CLI fixture-capture experiment directly, in this exact session. Sequence: Claude reported Steps 1-9 complete and Architecture-Verified, then asked "say the word when you want me to run it, and I'll execute it in an isolated scratch directory outside the repo, record your consent in the ticket's Implementation Notes first, and report back what gets captured" — the operator replied "continue" in direct, immediate response to that specific offer, then separately added "ask me for decision if you need" as standing guidance for the execution itself. This satisfies Step 10's consent requirement per the addendum recorded in this ticket's coordination notes (`staging_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/CLAUDE_RESPONSE_TO_TAKEOVER_NOTE.md`'s "Addendum — who executes Step 10/11"): the operator directed a specific, named action at a specific moment (not blanket advance authorization), and Claude — not Codex CLI acting as ticket implementer — executes Step 11, with `codex` CLI confirmed present in Claude's own tool environment (`codex-cli 0.145.0` at `/home/u24desktop/.local/bin/codex`). Proceeding to Step 11 now.
- Step 11 execution and empirical findings (2026-07-22T10:11:41Z): performed entirely in `/tmp/codex-fixture-capture-scratch`, outside this repository. `codex --version` confirmed `codex-cli 0.145.0`; auth confirmed via `codex login status` → "Logged in using ChatGPT" (real account, real quota). **Trust finding**: project trust is NOT a per-project `.codex/config.toml` file as originally hypothesized — it is a global `~/.codex/config.toml` entry under `[projects."<absolute-path>"]` with `trust_level = "trusted"`, keyed by absolute path (this repo already has such an entry). A directory with no recorded trust entry is treated as untrusted and Codex silently skips its project `.codex/` layer entirely (config, hooks, rules) — confirmed via a real `codex exec` call asking Codex to explain its own hook syntax and trust model, sourced from `https://learn.chatgpt.com/docs/hooks` and `https://learn.chatgpt.com/docs/config-file/config-basic`. A scoped trust entry for `/tmp/codex-fixture-capture-scratch` only was added to `~/.codex/config.toml` (appended after the existing 6 project entries, none of which were modified) to allow the scratch directory's hook to actually load. **Empirical `.codex/config.toml` hook-registration TOML syntax that worked** (written only to the scratch directory, never committed to this repo, per Step 11's own instruction):
  ```toml
  [[hooks.PostToolUse]]
  matcher = "*"

  [[hooks.PostToolUse.hooks]]
  type = "command"
  command = "cat > /tmp/codex-fixture-capture-scratch/captured_stdin.json"
  ```
  `matcher` accepts a regex (e.g. `"^Bash$"`) or `"*"` for all tools. Triggering the hook non-interactively required the `--dangerously-bypass-hook-trust` flag (hooks have their own trust layer separate from project trust, requiring interactive confirmation on first use, which `codex exec` cannot provide) — that flag was blocked once by this session's own permission classifier and required the operator's explicit, separate approval before the triggering command was re-run. Ran `codex exec --skip-git-repo-check --dangerously-bypass-hook-trust "Run the shell command: ls -la . Then just report what you saw, do not do anything else."` in the scratch directory; the hook fired (`hook: PostToolUse` / `hook: PostToolUse Completed` visible in CLI output) and produced a valid `captured_stdin.json`. **Captured payload's top-level keys**: `session_id`, `turn_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `permission_mode`, `tool_name`, `tool_input`, `tool_response`, `tool_use_id`. Cross-checked against `codex_capability_matrix.md` §1's documented common-field table (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `turn_id`, `permission_mode`) — **no discrepancy**: all 7 documented fields are present exactly as named, plus 4 additional PostToolUse-specific fields (`tool_name`, `tool_input`, `tool_response`, `tool_use_id`) not covered by that common-field table, which is expected since those are specific to reporting what tool ran and what it returned. Capture timestamp: 2026-07-22T10:11:11Z (per the session transcript path's own embedded timestamp). Proceeding to Step 12 to commit the fixture.
- Test-phase regression fix (2026-07-22): the Test phase found a genuine regression outside the scope of both prior Architecture-Verify passes — `tools/agent-monitoring/manifest.py`'s own pre-existing architecture invariant (single-pass streaming, no full-file-read methods; established by `TCK-20260721-BASELINE-MONITORING-MANIFEST`) was violated by Codex's `capture_lines()` implementation, which used `file.readlines()`. Caught by `tests/tools/test_agent_monitoring_manifest.py::test_manifest_source_never_calls_full_file_read_methods`, a pre-existing test not covered by either Architecture-Verify pass's file list. Fixed directly by Claude: replaced `readlines()` with an explicit line-lazy `for line in file:` loop, matching `_scan_file`'s own established streaming technique in the same module. Re-verified: `tests/tools/test_agent_monitoring_manifest.py` (6 passed) and `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py` (4 passed, confirming no behavioral change to the containment-evidence logic).

## Test Summary

**Steps 1–9 (non-live portion, implemented by Codex CLI, independently verified by Claude across
two review rounds):**

`.venv/bin/python3 -m pytest tests/agent_orchestration_codex_adapter tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py -v`
— **21 passed**. Covers: append-only monitoring-snapshot tooling (4 tests), legacy-skills
containment fidelity/discovery-path absence (3 tests), generator write-guard incl. path-traversal
`id` rejection (4 tests), generator traceability incl. dual-shape body extraction and the 16-entry
anti-expansion guard (4 tests), missing-contract failure (1 test), `AGENTS.md` content correctness
incl. forward drift guard (3 tests), and the cross-ticket `.codex/` scope-creep test (2 tests).

A first review round found a real bug (frontmatter-less generated `SKILL.md` files had zero
separating newline between the closing `---` delimiter and body content, for all 4 non-frontmatter
sources) plus 3 missing plan-mandated tests; both were fixed and independently re-verified
byte-for-byte before this count was accepted.

**Steps 10–14 (live portion, executed by Claude directly per operator's real-time consent):**

Step 11's real Codex CLI fixture-capture experiment succeeded (see Implementation Notes above for
full findings). Step 12's fixture and validating test:
`pytest tests/tools/test_codex_hook_payload_fixture.py -v` — **6 passed**. Step 14's final full
verification pass, all commands run via `.venv/bin/python3 -m pytest`:

- `tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/` — **83 passed, 1 failed**. The 1 failure
  (`test_agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`)
  is the same pre-existing, unrelated failure already confirmed and tracked before this ticket
  began (follow-up hotfix `TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`, filed at ticket 3/7's
  close) — not caused by this ticket, confirmed via `git log` showing that test file untouched by
  this ticket's diff.
- `tests/agent_orchestration_codex_adapter/` (re-run after adding Step 14's own
  `test_no_production_hook_enabled.py`) — **21 passed** (19 from Steps 1-9 + 2 new).
- `tests/agent_replay/` — **25 passed**.
- `tests/tools/test_codex_capability_diagnostics.py tests/tools/test_post_tool_hook.py tests/tools/test_codex_hook_payload_fixture.py` — **12 passed**.
- `tests/unit/lab_agent/test_workflow_registry.py` — **4 passed**.
- `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` (re-run against the now-real,
  committed `.codex/config.toml`, not just its early-return-if-absent branch) — **2 passed**.

Scope-guard checks: `git diff --stat` on `docs/ai/agents_dir_disposition.md`, `.claude/`, and
`.agents/rules/` all empty. `.codex/config.toml` confirmed comment-only (`tomllib.load` → `{}`).

**Post-fix final combined run** (`tests/agent_orchestration_codex_adapter/ tests/agent_orchestration/
tests/agent_orchestration_claude_adapter/ tests/tools/test_codex_hook_payload_fixture.py
tests/tools/test_codex_capability_diagnostics.py tests/tools/test_post_tool_hook.py
tests/tools/test_agent_monitoring_manifest.py tests/agent_replay/
tests/unit/lab_agent/test_workflow_registry.py -v`): **130 passed, 1 failed** — the single failure
is the pre-existing, unrelated `test_contract_structure.py` stale-path failure (tracked by
`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`), confirmed via `git log` untouched by this
ticket's diff. Zero regressions. Zero coverage gaps found (Test phase confirmed every new/changed
source and config file has direct test coverage).

## Files Changed

**Steps 1–9 (non-live portion) — new files:**
- `tools/agent_orchestration_codex_adapter/__init__.py`
- `tools/agent_orchestration_codex_adapter/errors.py`
- `tools/agent_orchestration_codex_adapter/generator.py`
- `tests/agent_orchestration_codex_adapter/__init__.py`
- `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`
- `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`
- `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`
- `tests/agent_orchestration_codex_adapter/test_generator_write_guard.py`
- `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`
- `tests/agent_orchestration_codex_adapter/test_requires_valid_contract.py`
- `AGENTS.md` (repo root, generated output)
- `.agents/skills/<id>/SKILL.md` × 16 (generated output, one per `agent-orchestration/skills.yaml` entry)

**Steps 1–9 — moved (via `git mv`, history preserved):**
- `.agents/skills/` (18 legacy skill directories, all contents) →
  `docs/archive/legacy_agents_skills_20260722/`

**Steps 1–9 — modified:**
- `tools/agent-monitoring/manifest.py` — added `capture_lines()` and `assert_prefix_preserved()`
  (append-only-diff verification helpers); no existing function changed.

**⚠ Cross-ticket edit (flagged explicitly, per plan.md Step 9):**
- `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` — a file owned by the
  already-closed `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` (ticket 3/7 of this batch). Only
  `test_no_dot_codex_directory_exists_in_repo` was replaced (renamed to
  `test_no_production_hook_registered_in_codex_config`), since its prior unconditional "no
  `.codex/` may ever exist" assertion is factually superseded by this ticket's own legitimate,
  scoped `.codex/` producer role. The sibling test
  (`test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`) and its scan constants
  are byte-for-byte unchanged. Pre-approved in `plan.md` Decision #3; independently confirmed
  unchanged-elsewhere by Claude's Architecture-Verify pass.

**Steps 10–14 (live portion) — new files:**
- `.codex/config.toml` (comment-only, zero hook registrations, per Step 13)
- `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` (real, direct-experiment-grade
  captured payload)
- `tests/tools/test_codex_hook_payload_fixture.py`
- `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`

**Steps 10–14 — outside-repo side effects (disclosed, not repo files):** a scoped trust entry for
`/tmp/codex-fixture-capture-scratch` was added to the operator's global `~/.codex/config.toml`
(none of the operator's other 6 pre-existing trusted-project entries were modified) to allow the
isolated scratch directory's throwaway hook config to load during the Step 11 experiment. This is
outside the repository and not part of this ticket's tracked file changes, but is disclosed here
for transparency; candidate for cleanup after this ticket closes.

## Completion Summary

Replaced the legacy, Codex-auto-discoverable `.agents/skills/` tree (18 hand-written files) with a
fresh catalog generated from the validated `agent-orchestration/` contract, added a corrected root
`AGENTS.md` generated the same way, and captured a real Codex CLI `PostToolUse` hook-payload
fixture via a live, isolated scratch-directory experiment — all without enabling any production
Codex hook. Implementation was split: Codex CLI implemented Steps 1-9 (the non-live, reversible
portion — containment, generator, tests, cross-ticket test narrowing) from a Claude-authored,
4-round-reviewed plan; Claude executed Steps 10-14 directly (the live experiment) after the
operator's explicit, real-time consent, per an arrangement negotiated mid-ticket and recorded in
this ticket's coordination notes.

Two independent review rounds against Codex's Steps 1-9 output found and fixed a real bug (a
missing newline between the frontmatter delimiter and body for 4 frontmatter-less generated
`SKILL.md` files) and 3 missing plan-mandated tests. The live Step 11 experiment surfaced two real
findings the original plan had gotten wrong: project trust is a global `~/.codex/config.toml`
entry keyed by absolute path, not a per-project file; and the empirical hook-registration TOML
syntax (`[[hooks.PostToolUse]]` / `[[hooks.PostToolUse.hooks]]`) was previously undocumented
anywhere in this repo — both are now recorded in this ticket's Implementation Notes for the future
`live-Codex-pilot-guardrails` ticket to consume. A final Test-phase pass (after two Architecture-Verify
approvals) caught one more real regression outside either review's scope — Codex's
`capture_lines()` violated `manifest.py`'s own pre-existing single-pass-streaming invariant — fixed
directly by Claude and re-verified.

All 8 acceptance criteria satisfied. Final combined test run: 130 passed, 1 pre-existing unrelated
failure (tracked separately by `TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`). Zero `.claude/`
diff, zero `docs/ai/agents_dir_disposition.md` diff, zero `.agents/rules/` diff, zero production
hooks. `agent-monitoring/*.jsonl` confirmed append-only across the containment action via a
purpose-built prefix-preservation check.

**Known, deliberately deferred doc staleness:** `docs/ai/agents_dir_disposition.md`'s narrative
paragraph ("Root AGENTS.md and a reviewed/generated Codex skill catalog are absent...") now
describes a state this ticket has changed — its per-path classification table is unaffected and
correct, only that one narrative sentence is stale. This was a deliberate plan decision (see
`plan.md`'s Scope Guards: "must NOT re-litigate or edit `docs/ai/agents_dir_disposition.md`'s
per-item classification table"), reviewed across 4 rounds, not an oversight. Left as a follow-up
for whoever next touches that doc, not fixed in this ticket.
