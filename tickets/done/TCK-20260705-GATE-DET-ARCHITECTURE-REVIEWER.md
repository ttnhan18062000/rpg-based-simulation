---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
phase: done
date: 2026-07-05
tags: [ai, workflows, determinism]
---

# TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER

## Title
Add deterministic static scans backing architecture-reviewer's durable-state/API-boundary judgments

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Fourth and hardest of 4 gate-determinism tickets (see
`tickets/todos/gate-determinism-followups/SEQUENCE.md` for shared design decisions and full context;
deliberately sequenced last). Per `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md`'s
table: "AST scan for direct durable-state mutation outside `src/engine/authoritative_pipeline*`;
grep-scoped check for raw domain objects returned from `src/api/`; regex check for known 'meaning
smuggled into `reason`/`metadata` string' patterns." What stays LLM-judged: whether the *design* is
sound — strategic/tactical boundary, whether an abstraction is premature.

## Scope
- **Durable-state-mutation AST scan**: given the plan's proposed changed files (or, more practically,
  the *actual* diff once Implement has run — Investigate should determine whether this check is more
  useful pre-Implement against `plan.md`'s described files, or post-Implement against the real diff,
  since architecture-reviewer today runs pre-Implement against a plan, not code), parse each proposed/
  actual `src/` file with Python's `ast` module and flag any direct mutation of durable state (e.g.
  attribute assignment on a known `AuthoritativeState`/`EntityState` object) occurring outside
  `src/engine/authoritative_pipeline*`. This is the most technically ambitious check of the 4 tickets —
  Investigate must scope realistic precision/recall before committing to a specific AST pattern set;
  a first version that catches only the clearest violations (and is honest about its false-negative
  rate) is preferable to an over-ambitious one that's unreliable.
- **Raw-domain-object API-boundary grep**: a scoped grep/AST check over `src/api/` for functions
  returning a raw domain model type (not a shaped read model/presenter) — reuse whatever naming/typing
  convention already distinguishes the two (Investigate should confirm this convention exists and is
  consistent enough to check mechanically before assuming it).
- **Reason/metadata-smuggling regex check**: a pattern check for known anti-patterns (e.g. durable
  meaning encoded as a parsed/split string inside a `reason` or `metadata` field) — Investigate should
  gather a small corpus of confirmed historical violations (if any exist in `git log`/past architecture-
  review findings) to derive realistic patterns, rather than guessing patterns with no evidence base.
- Add a `verified_by` field to `REVIEW_SCHEMA` in `implement-ticket.js`.
- At least one coverage-honesty test per scan (a fixture file with a known violation must be caught; a
  clean fixture file must not false-positive).

## Out of Scope
- The other 3 gates' static verifiers — see SEQUENCE.md.
- Re-deciding strategic/tactical boundary soundness or abstraction-premature-ness — remains LLM-judged.
- Achieving perfect precision/recall on the AST scan — an honest, documented, imperfect-but-useful first
  version is the target, not a complete static-analysis framework.
- Token/cost telemetry.

## Acceptance Criteria
- [ ] `tools/gate_checks/architecture_reviewer_static.py` exists with 3 documented check functions
      (durable-state mutation, raw-domain-object API exposure, reason/metadata smuggling), each with an
      explicit, disclosed precision/recall caveat.
- [ ] The Review phase's prompt instructs architecture-reviewer to run these checks first and address
      any flagged item, or explain why a flagged item is a false positive.
- [ ] `REVIEW_SCHEMA` gains a `verified_by` field.
- [ ] At least one coverage-honesty test per check function, including a clean-fixture negative control.
- [ ] `docs/ai/agents.md`'s `architecture-reviewer` section and the other 3 shared docs updated.

## Related Tickets
- TCK-20260705-GATE-DET-DONE-CHECKER, TCK-20260705-GATE-DET-PARITY-UPDATER,
  TCK-20260705-GATE-DET-MECHANICS-AUDITOR (siblings — do this one last per SEQUENCE.md)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_gate_determinism.md
- tickets/todos/gate-determinism-followups/SEQUENCE.md
- docs/ai/agents.md, docs/ai/workflows.md, docs/ai/system_overview.md, docs/ai/ticket-lifecycle.md
- CLAUDE.md's Architecture Rule / Durable State Rule (the authoritative definitions these checks encode)

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/agents/architecture-reviewer.md
- .claude/workflows/implement-ticket.js (Review phase)
- src/core/, src/engine/authoritative_pipeline*, src/api/ (read-only reference — the actual code shapes
  these checks must recognize)

## Assumptions / Open Questions
- Whether the AST scan should run against `plan.md`'s described files (pre-Implement, matching when
  architecture-reviewer currently runs) or the actual post-Implement diff (more accurate but a pipeline-
  ordering change) — left for Investigate/Plan, this is a genuine design decision that may need
  surfacing back to the user given it could change *when* in the pipeline this check fires.
- Whether a reliable, mechanically-checkable convention already distinguishes "raw domain model" from
  "shaped read model" types in `src/api/` — left for Investigate to confirm before assuming.

## Implementation Notes

Implemented all 8 steps of `staging_artifacts/TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER/plan.md` in order.

**Steps 1-4 — `tools/gate_checks/architecture_reviewer_static.py` (new):**
- `check_durable_state_mutation(file_path, source)` — AST scan for 3 violation shapes: (1)
  `object.__setattr__` bypass outside `_ALLOWLISTED_SETATTR_FIELDS` (the `_cache`-suffix convention
  plus a named-exception set), (2) nested mutable-container mutation by field-name heuristic
  against `_KNOWN_MUTABLE_CONTAINER_FIELDS = {"items", "global_resources", "trust_history"}`, (3)
  direct nested attribute assignment (depth ≥2 attribute chain), excluding `.return_value`/
  `.side_effect` (see Deviations below).
- `_collect_domain_class_names` + `check_api_boundary_exposure(file_path, source,
  domain_class_names)` — dynamically derives raw-domain-model class names from
  `src/core/state.py`, `src/core/strategic.py`, `src/core/self_model.py`, `src/core/models/*.py`;
  flags top-level `src/api/` functions (leading-underscore names excluded) whose return annotation
  names a raw domain class instead of `Dict`/`*Response`.
- `check_reason_metadata_smuggling(file_path, source)` — regex scan for a delimiter-packed
  `reason`/`metadata` value (≥2 placeholders joined by a non-alphanumeric delimiter) later unpacked
  via a matching `.split(...)` in the same file. Docstring explicitly discloses zero confirmed
  historical incidents in this repo (per investigation.md's corpus search).
- `run_architecture_checks(files_changed, base_dir)` — aggregator; filters to `.py` files under
  `src/`, runs all 3 checks (API-boundary check only for `src/api/` paths, caching
  `_collect_domain_class_names` across the loop), returns `list[dict]` with
  `condition`/`status`/`evidence` keys, matching `done_checker_static.run_static_precheck`'s shape.
  No CLI/argparse entry point.

**Step 5 — `.claude/workflows/implement-ticket.js`:** Inserted a new `Architecture-Verify` phase
between Implement and Test, gated on `tier !== 'hotfix'` (skipped event pushed otherwise). Runs
`run_architecture_checks` via `bash()` (files passed as individually shell-quoted argv elements,
mirroring the Parity phase's own documented shell-quoting hazard), parses the
`ARCH_CHECK_JSON:`-prefixed output with a `try/catch` → `null` fallback, then calls
`agentType: 'architecture-reviewer'` again with a new `ARCH_VERIFY_SCHEMA` (`verdict`, `violations`,
`summary`, `ts`, `verified_by`) and a prompt scoped to judging only the flagged items against the
real diff. On non-`APPROVED`, uses the corrected Security-Review-style remediation message ("Fix the
flagged code in the files changed for {tid}, then re-run with ticket_id=...") — NOT the original
Review phase's plan.md-referencing message. Added a `meta.phases` entry for `Architecture-Verify`
(between `Implement` and `Test`) and updated the top-level `description` string.

**Step 6 — `.claude/agents/architecture-reviewer.md`:** Added `## Post-Implementation Verification
(Architecture-Verify phase)` section after `## Output`, describing the second invocation mode, the
3 checks' disclosed limitations, and the self-reference bootstrapping disclosure sentence.

**Step 7 — 4 shared docs** (`docs/ai/agents.md`, `docs/ai/workflows.md`,
`docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`): added the Architecture-Verify phase
row/section to each, updated the standard-tier phase count from 9 to 10 (system_overview.md,
ticket-lifecycle.md), and updated the `architecture-reviewer` Gate-behavior/Inputs/Outputs
description in agents.md to cover both call sites.

**Step 8 — `tests/tools/test_architecture_reviewer_static.py` (new):** 17 tests (one more than the
15 explicitly named in test_plan.md — added `test_module_has_no_authoritative_pipeline_path_reference`
per the "No-nonexistent-path guard" in test_plan.md's Anti-Drift Test Guards, and
`test_does_not_flag_mock_return_value_configuration` per the real false positive found below). No
pytest marker.

**Deviations from plan.md (recorded in plan.md's own Deviations section too):**
1. Named-exception set for `object.__setattr__` (Step 1, point 1) — re-grepped `object\.__setattr__`
   across `src/` at implementation time as the plan instructed; confirmed `src/simulation_quality/
   weights.py`'s `ScoringWeights` uses `_flat_rules` and `_pillar_weights` (neither `_cache`-suffixed)
   — both added to `_ALLOWLISTED_SETATTR_FIELDS`, exactly as plan.md anticipated needing confirmation.
2. Found and fixed a real false positive not anticipated by plan.md: `src/lab/workflows.py`
   (production code) configures `MagicMock` instances via `mock_world_repo.list_worlds.return_value
   = [...]`, which matches Step 1 point 3's "depth ≥2 attribute chain assignment" shape identically
   to `entity.combat.hp = 5` — contradicting plan.md's claim that this pattern has "no sanctioned
   legitimate use" in this codebase. Added a narrow `_MOCK_CONFIGURATION_ATTRS = {"return_value",
   "side_effect"}` exclusion (not a broad allowlist) and disclosed it in the docstring, rather than
   silently leaving a known, demonstrable false-positive source undisclosed.
3. Broadened the durable-state-mutation docstring's disclosed-limitation language beyond the two
   files plan.md named (`src/engine/apply.py`, `src/core/state.py`) after confirming at
   implementation time that the same false-positive shape also recurs in `src/engine/kernel.py` and
   `src/engine/pipeline_phases/actions.py` — both are legitimate engine-internal state-construction/
   reset code using ordinary domain field names via `object.__setattr__`/nested assignment. No
   allowlist expansion was made for these (per plan.md's explicit "do not attempt high precision/
   recall" instruction and its own Anti-Drift Notes) — only the docstring disclosure was widened to
   match observed reality.

## Test Summary

- `pytest tests/tools/test_architecture_reviewer_static.py -v` — 17 passed.
- `pytest tests/tools/ -v` — 514 passed, 30 failed. All 30 failures are in
  `tests/tools/test_knowledge_search.py` (BM25/embedding build + live-query tests) and
  `tests/tools/test_search_mcp.py` (MCP JSON config tests) — pre-existing, unrelated to this
  ticket's files (confirmed: this ticket touches no knowledge-search/MCP code; these tests were not
  added, modified, or exercised by any change here).
- `pytest tests/ -m "architecture" --collect-only -q` — confirmed zero tests collected from
  `test_architecture_reviewer_static.py` (not in `lane-architecture`, per SEQUENCE.md decision 1).
- `node --check .claude/workflows/implement-ticket.js` — syntax OK.
- Manually verified `run_architecture_checks` against real repository files (not just fixtures):
  correctly PASSes `src/world/environment.py`, `src/systems/strategic_systems/intelligence.py`,
  `src/simulation_quality/weights.py`, `src/api/routes/{economy,campaigns,decisions}.py`, and
  `src/lab/workflows.py`; correctly (and per-docstring-disclosed) FAILs on `src/engine/apply.py`,
  `src/core/state.py`, `src/engine/kernel.py`, and `src/engine/pipeline_phases/actions.py` due to
  their own internal field-replacement/reset code using ordinary domain field names — a known,
  disclosed limitation of the field-name-only allowlist design, not a bug.

## Files Changed
- `tools/gate_checks/architecture_reviewer_static.py` (new)
- `tests/tools/test_architecture_reviewer_static.py` (new)
- `.claude/workflows/implement-ticket.js` (new `Architecture-Verify` phase, `ARCH_VERIFY_SCHEMA`,
  `meta.phases` entry, `description` string)
- `.claude/agents/architecture-reviewer.md` (new Post-Implementation Verification section)
- `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/system_overview.md`,
  `docs/ai/ticket-lifecycle.md` (Architecture-Verify phase documented)

## Completion Summary
Added `tools/gate_checks/architecture_reviewer_static.py` with 3 deterministic, deliberately-imperfect
static checks (durable-state mutation via AST, raw-domain-object API-boundary exposure via AST,
reason/metadata-smuggling via regex — each with an explicit, disclosed precision/recall caveat) and
an aggregator, wired into a new post-Implement `Architecture-Verify` phase in
`implement-ticket.js` that re-invokes `architecture-reviewer` against the real diff. 17 coverage-honesty
tests added, all passing; `verified_by` field added via the new `ARCH_VERIFY_SCHEMA`. This ticket's own
run does not exercise the new phase against itself (the workflow script was already loaded before its
own edits landed) — expected, documented in Step 5/6 per architecture review round 1's disclosure.
