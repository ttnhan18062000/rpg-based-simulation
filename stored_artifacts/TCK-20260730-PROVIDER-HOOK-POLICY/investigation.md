---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-PROVIDER-HOOK-POLICY
artifact_type: investigation
tags: [ai, hooks, workflows, documentation, testing]
---

# Investigation — TCK-20260730-PROVIDER-HOOK-POLICY

## Current Behavior

### `agent-orchestration/hook-events.yaml` (the existing normalized-vocabulary file)
Full current content (4 data lines):
```yaml
hook_schema_version: 1
hook_types:
  - id: PreToolUse
    description: Fired before a tool call executes.
  - id: PostToolUse
    description: Fired after a tool call completes; feeds tools.jsonl writes.
```
Its own header comment (lines 1-3) is explicit about scope: "Normalizes exactly the two
hook types actually wired in `.claude/settings.json` today. No speculative
SessionStart/Stop/other hook type — this file documents the real, current vocabulary only."
This is a **deliberate narrowness policy already in force**, restated independently in
`agent-orchestration/intentional-divergences.md`'s "Known Configuration Gaps" section
(lines 49-56): "This is a deliberate scoping choice, not an oversight... Expand
`hook-events.yaml` only when a real workflow needs one of the 8 missing entries — do not
add them speculatively."

### `agent-orchestration/contract.yaml` (top-level manifest)
`governs:` (lines 12-27) lists exactly 5 governed paths, each with its own
`version_field`: `workflows/implement-ticket.yaml` (`workflow_version`), `roles/`
(`role_version`, per-file), `skills.yaml` (`skills_version`), `monitoring-schema.yaml`
(`schema_version`), `hook-events.yaml` (`hook_schema_version`). No 6th entry exists.

### `agent-orchestration/README.md` (versioning-scheme documentation)
Lines 23-34, "Versioning scheme": "Each file carries its own independent **integer
generation counter**... starting at `1`." Bump rule (line 31): "increment a file's own
counter by exactly 1 on any breaking schema change to that file... A non-breaking addition
(a new optional field, a new role/skill entry) does not bump the counter. **Each file's
counter is independent** — a breaking change to `roles/*.yaml` does not force-bump
`hook-events.yaml`." The `Layout` table (lines 14-21) lists exactly the same 6 files as
`contract.yaml`'s `governs:` (contract.yaml itself + 5 governed paths).

### `tools/agent_orchestration/loader.py` (validator entry point — what "contract
validation independently checks" (AC #1) must hook into)
`load_contract(root)` (lines 173-200) is a **fixed sequence of 6 named loads**, not a
generic directory walk: `_load_contract_yaml`, `_load_workflow_yaml`, N ×
`_load_role_yaml`, `_load_skills_yaml`, `_load_monitoring_schema_yaml`,
`_load_hook_events_yaml`, assembled into a frozen `ContractBundle` dataclass (lines 44-51,
fields: `contract`, `workflow`, `roles`, `skills`, `monitoring_schema`, `hook_events`).
`_load_hook_events_yaml` (lines 156-170) requires `hook_schema_version` +
non-empty `hook_types` list, each entry requiring `id` + `description` — it has **no
concept of `available`/`normalized`/`enabled`, per-provider structure, or activation
metadata**; it is a flat single-list schema. Every load function follows the same shape:
required-keys check via `_require_keys`, then structural assertions, raising
`ContractValidationError` (from `errors.py`, a single flat exception type) naming the
exact file/field.

### `tools/agent_orchestration/generator.py`
`generate()` (lines 54-98) is also a **fixed sequence** mirroring `load_contract`'s 6
outputs 1:1 — `contract.yaml`, `workflows/implement-ticket.yaml`, `roles/*.yaml`,
`skills.yaml`, `monitoring-schema.yaml`, `hook-events.yaml` — each written via `_write_yaml`
under the structural write-guard `_assert_write_allowed` (lines 28-37, refuses writes
outside `agent-orchestration/` without `allow_outside_contract=True`).

### `.claude/settings.json` (Claude's real enabled hook surface)
Lines 54-122, `"hooks"` key: exactly two top-level event keys, `"PreToolUse"` (4 matcher
groups, lines 55-83) and `"PostToolUse"` (4 matcher groups, lines 84-121). **No other event
key exists** (no `SessionStart`, `Stop`, `SubagentStop`, etc.). This directly confirms the
ticket's claim ("Claude enables PreToolUse and PostToolUse") — matches `hook-events.yaml`'s
existing vocabulary exactly, 1:1.

### `.codex/config.toml` (committed Codex project config)
Entire file (9 lines) is a comment block; zero TOML keys/tables at any nesting level. This
is independently proven, not just asserted, by
`tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py::test_committed_codex_config_parses_to_empty_dict`
(`tomllib.load(...) == {}`). Confirms "the committed Codex project configuration enables
zero hooks" verbatim.

### `tools/agent_codex_pilot_guardrails/enabled_surface.py` — does an "enabled_surface"
concept already exist that overlaps this ticket's axes?
Yes, but it is a **different axis than available/normalized/enabled**, not a duplicate.
`EVIDENCED_HOOK_EVENTS = frozenset({"PostToolUse"})` and `EVIDENCED_WRITER_FUNCTIONS =
frozenset({"write_line", "write_lines"})` (lines 19-20) are hardcoded module constants,
explicitly documented (module docstring, lines 1-10) as "Sourced from the investigation's
direct-read trace, not re-derived at runtime, since no existing file declares the
*evidenced* (as opposed to *schema-valid*) subset in one place." Two functions:
`assert_evidenced_events_are_schema_valid()` (lines 27-41) cross-checks
`EVIDENCED_HOOK_EVENTS` is a subset of `hook-events.yaml`'s `hook_types` ids (i.e., against
the **normalized** vocabulary specifically — proving `PreToolUse` is schema-valid-but-not-
evidenced today, per its own test
`test_schema_valid_but_not_evidenced_hook_event_is_rejected`). `assert_enabled_surface_subset()`
(lines 44-58) asserts a caller-supplied enabled set is a subset of the evidenced constants —
this is a **runtime pilot-request guard**, not a contract-file-declared policy. So today:
"evidenced" (⊆ normalized, proven safe by direct experiment) is a third concept this
package already tracks informally, sitting between "normalized" and "enabled." The new
policy's `available`/`normalized`/`enabled` triad does not yet exist anywhere as declared,
machine-checkable, versioned contract data — `enabled_surface.py`'s hardcoded constants are
the closest analog and a natural cross-check target for the new file, not a
replacement for it (Out of Scope explicitly forbids "Replacing existing pilot guardrails").

### `tools/agent_replay_codex/codex_config_guard.py`
`assert_committed_config_hook_free()` (lines 32-40) walks the parsed TOML for any `hooks`
key at any depth and raises `ContainmentViolationError` if found — a second, independent
proof (beyond the adapter test above) that the committed config stays hook-free. Also
provides `snapshot_config_bytes`/`assert_config_bytes_unchanged` (lines 43-58) for
pre/post-invocation byte-identity checks, used elsewhere in the replay/pilot suites.

### Test files already covering adjacent ground
- `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py` — AC-level
  guard, asserts committed `.codex/config.toml` is hook-free (both the walk and the
  `== {}` parse check).
- `tests/agent_codex_pilot_guardrails/test_enabled_surface.py` — table-driven tests over
  `enabled_surface.py`'s subset-assertion functions, including the specific negative case
  proving `PreToolUse` is schema-valid-but-rejected.
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` — AST/import-graph
  scan over every `.py` file in `tools/agent_codex_pilot_guardrails/`, banning any static or
  dynamic import of `tools.agent_replay_codex.invoker`, any `subprocess`/`os.system` call or
  import, and any execution-shaped function name (`run_pilot`, `execute_pilot`,
  `invoke_codex` substrings). Its own docstring calls this "the single most important test
  in this ticket's entire suite" and instructs future changes never to weaken it to make it
  pass. **This is the primary anti-drift guard any new code this ticket's implementation
  touches must not weaken or route around.**
- `tests/tools/test_codex_hook_payload_fixture.py` — validates the direct-experiment-grade
  `PostToolUse` stdin fixture (`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json`),
  confirming the 7 documented common fields + 4 `PostToolUse`-specific fields are present.

## Mechanics / Engine Constraints

None. This ticket touches `agent-orchestration/` (the provider-neutral workflow contract)
and its validator/generator tooling under `tools/agent_orchestration/`,
`tools/agent_codex_pilot_guardrails/`, `tools/agent_replay_codex/` — all agent-infrastructure
tooling, entirely outside `src/` simulation code. No `docs/mechanics/` chapter or
`docs/engine/` contract governs this area; the relevant authority is
`docs/architecture/agent_orchestration_contract.md` (the ADR) plus this directory's own
README/versioning-scheme rules, both read above.

## Parity Ledger Overlap

**None.** Grepped all `docs/parity_ledger/*.yaml` for "codex" and "hook"; every hit is a
false-positive on the word "hook" in an unrelated simulation-mechanics or dashboard-tooling
context (e.g. `town_resource.yaml:1923` — a `PERSISTENCE phase hook` in
`src/engine/kernel.py`'s alert dispatch; `social_narrative.yaml:2505` — social-memory import
hooked into `CampaignOrchestrator._advance_state()`; `infrastructure.yaml:6513` — a React
`useRunTimelinesPolling` hook in the dashboard frontend). No entry anywhere references
Codex, `.codex/`, `agent-orchestration/`, or provider hook-surface policy. This is
consistent with the Parity Ledger's documented scope (`docs/parity_ledger/schema.json`,
the 8 subsystem files in CLAUDE.md's table) — it tracks Mechanics-Bible-vs-code parity for
simulation subsystems, not agent-workflow/orchestration meta-tooling. **No parity ledger
entry needs to be added or updated by this ticket.**

## Prior Work

- `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/` — origin of
  `agent-orchestration/` itself and the loader/generator pattern this ticket must extend
  consistently with. `tests/agent_orchestration/test_contract_structure.py` (read directly)
  is the precedent for how a new contract file's structural expectations get pinned down
  in tests (file-existence + YAML-mapping check in
  `test_agent_orchestration_dir_has_required_files`, `load_contract` smoke test in
  `test_load_contract_succeeds_against_the_real_contract`).
- `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/` — origin of the
  `PostToolUse` direct-experiment payload fixture this ticket's future-activation-candidate
  claim rests on. `.codex/config.toml`'s current comment header cites this ticket by ID.
- `stored_artifacts/TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS/` — origin of
  `tools/agent_codex_pilot_guardrails/`, including `enabled_surface.py`'s
  evidenced-hook-event/writer-function constants this ticket's activation-candidate
  declaration should stay consistent with (not contradict, not silently duplicate-and-drift
  from).
- `docs/ai/codex_capability_matrix.md` (TCK-20260721-CODEX-CAPABILITY-MATRIX) — the sole
  in-repo evidenced source for Codex's full 10-event lifecycle-hook list (see Risks section
  below for the exact list and citation).
- `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`
  §"3. Codex project configuration and hooks" already names this exact policy as Activation
  Prerequisite #1 ("Record a provider hook-surface policy separating **available**,
  **normalized**, and **enabled** events per provider") and Prerequisite #3 (failure
  behavior, timeout, output redaction, out-of-band diagnostics) and #4 (explicit human
  approval) — this ticket is that prerequisite's direct implementation. The doc's "Required
  decision record for every activation step" list (lines 244-253) is a second, independent
  source for the "future activation requirements" AC #5 needs to capture (consent/sign-off
  evidence, pre/post monitoring baseline, rollback command+result, intentional divergences).
- `docs/plans/agent_infrastructure/provider_agnostic_orchestration/final_configuration_parity_verification_response_codex.md`
  §"Recommended follow-up boundaries" is the earliest documented articulation of this exact
  ticket's scope (surfaced first by the mandatory `search_docs` step), confirming this is a
  long-standing, previously-identified gap rather than a newly invented requirement.
- **Stale-reference correction**: the activation-status plan doc (line 265-267) still warns
  about "one separately tracked stale staging-artifact path failure
  (`TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH`)" that "must remain distinguished from
  activation regressions until repaired." Direct read of
  `tickets/done/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md` and the live
  `tests/agent_orchestration/test_contract_structure.py` (both read directly) confirm this
  is **already fixed** — the test now correctly reads
  `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md`, not a stale
  `staging_artifacts/` path, and the full scoped suite run below shows it passing. The
  activation-status doc's Baseline Verification Commands section is stale on this one point
  and could be corrected as a drive-by note if this ticket updates that doc, but is not
  itself part of this ticket's scope.

## Risks and Open Questions

### RESOLVED: new contract file vs. overloaded extension of `hook-events.yaml`
**Recommendation: a new contract file**, e.g. `agent-orchestration/hook-surface-policy.yaml`,
sibling to the existing 5 governed files — not an extension of `hook-events.yaml`. This is
the smallest change consistent with the codebase's own already-stated policy, for three
concrete, code-traceable reasons:

1. **`hook-events.yaml`'s own header comment forbids exactly this kind of addition.** It
   declares itself scoped to "exactly the two hook types actually wired in
   `.claude/settings.json` today. No speculative... other hook type." Adding Codex's 8
   unnormalized events (even as `available`-only entries, not `enabled`) into this file
   would directly contradict its own docstring and the matching policy statement in
   `agent-orchestration/intentional-divergences.md` lines 53-56 ("adding capability-only
   entries for hooks no real provider workflow currently uses would make the contract
   falsely imply support... do not add them speculatively").
2. **Schema shape mismatch.** `hook-events.yaml`'s schema (`hook_schema_version` +
   flat `hook_types: [{id, description}]`) has no per-provider dimension at all — it is a
   single shared vocabulary list. The new policy is inherently 3-dimensional
   (available/normalized/enabled) × per-provider (Claude, Codex) × per-event, plus
   activation-candidate metadata (evidenced writer-function subset) and a list of named
   future-activation prerequisites (AC #5). Retrofitting that shape into
   `hook_types: [{id, description}]` would require either breaking the existing schema
   (bumping `hook_schema_version`, a breaking change per the README's own bump rule) or
   bolting on unrelated sibling keys that make one file serve two different semantic
   purposes — exactly the "overloaded extension" the ticket's own Assumptions section
   warns against.
3. **Existing consumers read `hook-events.yaml` for a narrower, still-valid purpose.**
   `enabled_surface.py::assert_evidenced_events_are_schema_valid()` and
   `test_no_production_hook_enabled.py` both read `hook-events.yaml` today expecting it to
   mean exactly "the two Claude-wired, normalized events." Changing its meaning to also
   carry Codex's 8 non-normalized available-only events (even if `enabled` stays correctly
   `[]`) risks a consumer accidentally treating `hook_types` membership as "safe to enable,"
   which is precisely the available/normalized conflation this ticket exists to prevent.

**Concrete shape recommendation** (Plan phase should treat as a starting draft, not a
final spec): reuse `loader.py`'s existing validation idiom exactly — a
`hook_surface_policy_version: 1` counter (added to `contract.yaml`'s `governs:` list and
`README.md`'s Layout table + versioning-scheme enumeration, per the file's own documented
process), a `providers:` mapping with `available_events`/`enabled_events` lists per
provider, an `activation_candidates:` list (provider, event, constrained writer-function
subset, status), and an `activation_prerequisites:` list of named, described items covering
AC #5's nine items (human approval, scratch-first verification, project trust review, hook
trust review, failure/timeout fail-open, redacted output, out-of-band diagnostics, reviewed
config diff, one-action rollback). The **normalized** vocabulary element AC #2 requires is
already fully satisfied by the existing, unmodified `hook-events.yaml` — the new file should
cross-validate against it (assert its own event ids are consistent with
`hook-events.yaml`'s `hook_types` ids) rather than re-declare it, keeping `hook-events.yaml`
the single source of truth for "normalized." Wiring points for AC #1 ("contract validation
independently checks"): `loader.py` needs one new `_load_hook_surface_policy_yaml()`
function + one new `ContractBundle` field, following the exact pattern of
`_load_hook_events_yaml`; `generator.py` needs one new write step in `generate()`;
`contract.yaml` needs one new `governs:` entry; `README.md`'s Layout table and
versioning-scheme paragraph need one new row/bullet each;
`tests/agent_orchestration/test_contract_structure.py`'s
`test_agent_orchestration_dir_has_required_files` needs the new path added to
`required_files`.

**Optional, not required by this ticket's scope**: `enabled_surface.py`'s hardcoded
`EVIDENCED_HOOK_EVENTS`/`EVIDENCED_WRITER_FUNCTIONS` constants could gain an additional
cross-check against the new file's `activation_candidates` (mirroring
`assert_evidenced_events_are_schema_valid()`'s existing pattern against `hook-events.yaml`).
This is purely additive (a new function, not a replacement) and therefore does not conflict
with the ticket's Out-of-Scope line "Replacing existing pilot guardrails or their
no-live-execution-path tests" — but it is optional polish, not required to satisfy any AC,
and Plan should decide explicitly rather than default into it.

**Open sub-question needing Plan-phase or human resolution, not silently assumed**: should
the new file also declare a `claude.available_events` list? The ticket's own AC #2 only
requires representing "Claude's two enabled events" — it does not require a documented
Claude *available* count. Unlike Codex, no in-repo evidenced capability matrix exists for
Claude's full hook surface (no `docs/ai/claude_capability_matrix.md` or equivalent was
found). Two defensible options: (a) omit `available_events` for Claude entirely and make
that key Codex-only/optional in the schema, or (b) set `claude.available_events` equal to
its `enabled_events` (2) with an explicit note that this is not independently verified
against Claude's full documented hook surface (Claude Code's real product surface is known
to expose more hook types than `PreToolUse`/`PostToolUse` in general, e.g. `Stop`,
`SessionStart`, `Notification` — but none of those are evidenced or wired in *this repo's*
`.claude/settings.json`, and fabricating an "available" count for Claude without a citation
would repeat exactly the mistake this ticket exists to prevent for Codex). **Do not assume
option (a) or (b) — flag for the Plan phase to decide explicitly, since it changes the new
file's schema shape.**

### The real Codex 10-event list (fully evidenced — no guessing required)
Source: `docs/ai/codex_capability_matrix.md` §1 "Lifecycle Hook Events" (verification date
2026-07-21, sourced from a locally cached official Codex manual, `manual lines 9144-9567`,
cross-corroborated by WebSearch in that ticket's own investigation). All ten are marked
**VERIFIED**:

`PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`,
`UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart`.

Per-event scope/matcher/field detail is in that doc's table (§1); the key facts this
ticket's policy needs: only `PreToolUse`/`PermissionRequest`/`PostToolUse`/`PreCompact`/
`PostCompact`/`UserPromptSubmit`/`SubagentStop`/`Stop` run at "turn" scope,
`SessionStart`/`SubagentStart` run at "thread/subagent-start" scope; `PostToolUse` is the
only one of the ten with **direct-experiment-grade** (not merely documentation-citation-
grade) payload evidence in this repo, per
`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` and its validating
test `tests/tools/test_codex_hook_payload_fixture.py`.

### Current `.claude/settings.json` state (confirmed, not guessed)
`.claude/settings.json` lines 54-122: exactly two `"hooks"` top-level keys, `"PreToolUse"`
and `"PostToolUse"`, each with 2-4 matcher-scoped command entries (monitoring writers,
graphify nudges, context-search nudges, retro/staleness checks). No other hook event key
is present. This is a **direct file read**, matching the ticket's own claim exactly.

### Current `.codex/config.toml` state (confirmed, not guessed)
`.codex/config.toml`: 9 lines, entirely comments (verbatim explanation that it is a
"comment-only, hook-free project marker" and that a "future, separate ticket... owns
actually wiring a production hook"). `tomllib.load()` on it parses to `{}` — zero keys of
any kind, confirmed by both a direct read and the existing passing test
`test_committed_codex_config_parses_to_empty_dict`.

### Pre-existing, unrelated test failures found during the scoped regression run
Running the full baseline-verification command set from the activation-status plan doc
(see Test Plan) surfaces 3 pre-existing failures **unrelated to this ticket's scope**:
`test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides` and
`test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count` (both fail on
stale hardcoded line numbers for `FINALIZE_INCOMPLETE` call sites in
`.claude/workflows/implement-ticket.js`, now at lines 1344/1356 instead of the
hardcoded-expected 1234/1246 — line drift from unrelated later edits to that file), and
`test_provider_field_coverage_against_real_corpus_is_currently_zero` (asserts 0, real value
is now 1 — stale because `TCK-20260730-CLAUDE-EXECUTION-IDENTITY` shipped real
`provider="claude"` writes after that test's assumption was written). **None of these three
touch `hook-events.yaml`, `enabled_surface.py`, `codex_config_guard.py`, or any file this
ticket's scope names** — they are pre-existing baseline noise, not regressions this ticket
introduces, and this ticket's implementation must not "fix" them as a side effect (out of
scope) but should note them so Verify does not misattribute them.

## Anti-Drift Hazards

- **Do not expand `hook-events.yaml`'s normalized vocabulary.** The 8 non-Claude-wired
  Codex events must land only in `available_events`, never in anything read as
  `normalized` or `enabled`. This is the ticket's central purpose (Out of Scope line
  "Expanding normalized hook vocabulary merely because a provider documents an event").
- **Do not touch `.codex/config.toml`.** Out of Scope forbids "Registering any actual Codex
  hook or changing committed `.codex/config.toml` into a hook-bearing configuration" — the
  new policy file only *declares* `PostToolUse` as a future candidate; it must not itself
  register anything.
- **Do not weaken or route around
  `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py`.** Its own docstring
  calls it the single most important test in the whole guardrails suite; if implementation
  touches `tools/agent_codex_pilot_guardrails/` at all (e.g. adding an optional cross-check
  function against the new policy file), that new code lands in the same package and is
  therefore automatically subject to this test's subprocess/dynamic-import/execution-name
  bans — do not add an exemption.
- **Do not conflate `enabled_surface.py`'s "evidenced" concept with the new file's
  "available"/"normalized"/"enabled" triad.** "Evidenced" (⊆ normalized, proven safe by
  direct experiment) is a fourth, narrower concept sitting between normalized and enabled —
  keep it distinct in naming and in any cross-check added, per the Prior-Work section above.
- **Do not silently invent Claude's "available" hook count.** Flagged above as an explicit
  open question — resolve it with a decision, not a guess.
- **Do not let `activation_candidates`/`activation_prerequisites` metadata imply
  authorization.** The current status plan doc is explicit: recording the policy "is not
  authorization to enable a hook, write monitoring data, invoke paid Codex work, or run a
  live pilot." Any wording in the new file's `activation_prerequisites` entries must read as
  requirements still to be satisfied by a later ticket, not as already-granted approval.
- **Keep each contract file's version counter independent.** Adding a new
  `hook_surface_policy_version: 1` file must not bump `hook_schema_version` in
  `hook-events.yaml` (it is untouched) nor `contract.yaml`'s own `version` unless the
  `governs:` list addition is judged a breaking change to `contract.yaml`'s own schema
  (it plausibly is, per the bump rule's "a required-field addition" clause — Plan should
  decide explicitly whether adding a `governs:` entry counts as a required-field addition
  to `contract.yaml` itself, since `governs:` is a list, not a fixed key set, and existing
  entries don't change).
