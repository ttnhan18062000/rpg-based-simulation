---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-RUNTIME-SHADOW
artifact_type: investigation
tags: [ai, workflows, testing, process-improvement]
---

# Investigation — TCK-20260730-CODEX-RUNTIME-SHADOW

## Current Behavior

### `agent-orchestration/workflows/implement-ticket.yaml` (the canonical phase/tier contract)
Full file read. Defines `workflow_version: 1`, `workflow_id: implement-ticket`, 11 phases in
order (Scope, Investigate, Plan, Review, Implement, Architecture-Verify, Test, Parity,
Security-Review, Verify, Finalize), each with a `tiers: {standard: X, hotfix: Y}` behavior value
drawn from `{full, skipped_event, conditional, conditional_absent}`. Only Scope/Implement/Test/
Verify/Finalize are `full` for both tiers; Investigate/Plan/Review/Architecture-Verify are `full`
for `standard` but `skipped_event` for `hotfix`; Parity/Security-Review are `conditional`. This is
the file this ticket must derive its phase/tier support matrix from — no other file in the repo
declares this per-phase, per-tier behavior table.

### `tools/agent_replay/` (the canonical fixture/runner — read-only, unmodified by any Codex-adjacent ticket)
- `tools/agent_replay/fixture_envelope.py:46` `load_fixture()` — fail-closed YAML loader for the
  fixture envelope (`version`, `source{ticket_id, ticket_path, events_run_id, ...}`,
  `phases[]{phase, agent, input, output, transition}`). No artifact-path or required-artifact
  field exists in the envelope schema at all.
- `tools/agent_replay/runner.py:62` `replay_slice(fixture) -> ReplayOutcome` — re-executes the
  Scope→Investigate→Plan→Review branch logic by calling the real `tag_registry.
  check_tags_registered()` (Scope) and `gate_checks.plan_gate_static.
  plan_has_unresolved_questions_heading()` (Plan) functions, and inspecting `fixture.output.verdict`
  for Review. `ReplayOutcome` (runner.py:44) has exactly two fields: `final_status: str` and
  `phases_completed: list[str]`. **There is no `gate_result` field and no `artifacts` field
  anywhere in `ReplayOutcome` or `FixtureEnvelope`.**
- `tests/fixtures/agent_replay/` contains exactly **one** fixture file:
  `TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`. `source.tier: standard`. `phases:` covers
  exactly `Scope, Investigate, Plan, Review` (4 entries) — no fixture anywhere in the repo covers
  Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize, or the `hotfix`
  tier's `skipped_event` behavior.
- `docs/ai/replay_fixture_spec.md`'s "Phase-slice scope statement" (read in full) states this
  explicitly: the fixture format and runner cover only Scope→Review "before Implement... those
  phases require a `files_changed`/diff payload this fixture format does not define."

### `tools/agent_replay_codex/` (the "limited replay predecessor," TCK-20260721-CODEX-REPLAY-PARITY)
All 9 non-empty modules read in full (`__init__.py` is empty).
- `invoker.py:37` `run_codex_replay()` — spawns a REAL `codex exec` subprocess (`invoker.py:55-61`)
  against `wrapper_script.py`, gated by `consent_gate.py:18` `require_live_consent()`
  (`CODEX_REPLAY_PARITY_LIVE_CONSENT=1`, strict equality). `wrapper_script.py` just calls the same
  `load_fixture()`/`replay_slice()` this ticket's own canonical runner uses — it is a real-CLI
  execution-environment proof, not a distinct validation logic.
- `shadow_mode.py:28` `compare_claude_and_codex(fixture, codex_outcome) -> ShadowModeComparison` —
  **already exists and already does phase-order + gate-result comparison**, but: (1) it requires a
  real `CodexReplayOutcome` produced by `run_codex_replay()` (i.e. a real, paid, consent-gated
  `codex exec` call) — it has no path that produces a comparable "Codex output" without one; (2)
  `match` (shadow_mode.py:44-47) is computed from `phases_completed` and `gate_result` only —
  `claude_artifact_refs`/`codex` artifact data is carried on the dataclass but **never included in
  `match`**; (3) there is no phase/tier support-matrix concept anywhere in this package — it
  blindly replays whatever the fixture says, with no rejection path for an unsupported phase or
  tier.
- `containment.py`, `codex_config_guard.py`, `provenance_check.py` — reusable, `repo_root`-
  parameterized containment primitives (git-porcelain/content-hash snapshot diff, `.codex/
  config.toml` hook-free check + byte-diff, `provider=="codex"` corpus scan). None of these are
  coupled to the real-`codex exec` path; all operate purely on filesystem/monitoring-corpus state.

### `tools/agent_codex_pilot_guardrails/` (all 6 modules read in full)
Pilot request manifest/loader, ticket-selection owner/rollback gate, concurrent-provider-claim
guard, evidenced hook-event/writer-function subset guard, baseline-manifest fail-closed gate, and
a scratch-only config-toggle + rollback-proof mechanism. Its own module docstring
(`__init__.py:1-13`) states it "has no live-execution entry point," never invokes `codex exec`,
and never governs phase/gate/artifact validation. No overlap with this ticket's phase/tier-matrix
or shadow-comparison scope.

### `tools/agent_codex_posttool_adapter/` (the just-landed prerequisite, all 9 modules read in full)
Parses a captured Codex `PostToolUse` hook stdin payload into the shared 13-field `tools.jsonl`
record shape and delegates the append to `tools/agent-monitoring/writer.py::write_line` (via
`writer_bridge.py`, mirroring `agent_replay_codex/entry_criterion.py`'s
`importlib.util.spec_from_file_location` technique). Its own docstring (`__init__.py:1-15`)
explicitly disclaims both `codex exec` invocation ("that is `tools/agent_replay_codex/`'s
responsibility") and pilot governance ("that is `tools/agent_codex_pilot_guardrails/`'s
responsibility"). It is a monitoring-event-shape adapter (one hook payload → one `tools.jsonl`
line), not a phase/gate/artifact-lifecycle validator. No overlap with this ticket's scope beyond
both being "Codex-adjacent."

### `agent-orchestration/hook-surface-policy.yaml` (just-landed, TCK-20260730-PROVIDER-HOOK-POLICY)
Declares `codex.enabled_events: []` (nothing enabled), `PostToolUse` as the sole
`activation_candidates` entry, and 9 unmet `activation_prerequisites` (human_approval,
scratch_first_verification, project_trust_review, hook_trust_review, failure_timeout_fail_open,
redacted_output, out_of_band_diagnostics, reviewed_config_diff, one_action_rollback). This policy
governs hook *registration*, not `implement-ticket` phase/gate/artifact runtime validation — this
ticket's scope (a phase/tier-matrix + shadow comparison adapter) does not touch or depend on any
of these 9 prerequisites; it is orthogonal, not blocked by them.

### `tools/agent_orchestration_claude_adapter/divergence_log.py` (found via graphify, read in full)
`load_divergences(path)` / `is_approved(divergences, axis, value)` — parses
`agent-orchestration/intentional-divergences.md`'s `## <axis>:<value-or-id>` sections and returns
`True` only for a `Status: RATIFIED` entry with non-empty `Approved-by` + valid `Approved-date`.
The doc's own `## Entry Format` section (read in full) declares exactly 4 axis values:
`terminal_status | phase_order | gate_policy | artifact_requirements` — these map almost 1:1 onto
AC #3's four comparison dimensions ("phase order, final status, gate result, and artifacts").
**Precedent inconsistency found:** `tests/agent_replay_codex/test_shadow_mode_comparison.py:45`
and `test_phase_parity.py:29` both call `is_approved(divergences, "codex_parity", <ticket_id>)` —
`"codex_parity"` is not one of the 4 documented axis values and no `## codex_parity:...` entry
exists in the real `agent-orchestration/intentional-divergences.md` (confirmed: `## Entries` says
"None"). This is flagged under Risks below.

### `.codex/config.toml`
Comment-only, zero `[hooks]` table at any depth (confirmed by direct read). Unrelated to this
ticket's scope except as a containment target this ticket's own tests must continue to prove
byte-identical (reusing `codex_config_guard.py::assert_config_bytes_unchanged`).

## Mechanics / Engine Constraints

Not applicable. This ticket is agent-orchestration/developer-tooling only — no `src/` simulation
code, `docs/mechanics/` chapter, or `docs/engine/` contract governs its semantics, consistent with
`support_boundary` language on INFRA-263/264/265/277-282/305/306 (the closest analogous
agent-tooling entries in `docs/parity_ledger/infrastructure.yaml`).

## Parity Ledger Overlap

Searched all `docs/parity_ledger/*.yaml` for `codex`, `agent_replay_codex`, `CODEX-REPLAY-PARITY`,
`shadow_mode`, `compare_claude_and_codex`, `runtime`, `shadow`.

- **INFRA-306** (`docs/parity_ledger/infrastructure.yaml:6698`) — TCK-20260730-CODEX-POSTTOOL-ADAPTER,
  `status: verified`, `priority: P2`. Documents the PostToolUse monitoring adapter. Not directly
  touched by this ticket's work but is the nearest sibling entry and the pattern to follow for this
  ticket's own new entry (agent-orchestration/developer-tooling `support_boundary` language, no
  `src/` coupling).
- **Gap found:** TCK-20260721-CODEX-REPLAY-PARITY (the ticket that built `tools/agent_replay_codex/`,
  including `shadow_mode.py` and `invoker.py`) has **no parity ledger entry anywhere** — grepped
  every `docs/parity_ledger/*.yaml` for `agent_replay_codex`, `CODEX-REPLAY-PARITY`, `invoker.py`,
  `run_codex_replay`; zero hits. This is a pre-existing gap this ticket does not need to backfill
  (out of this ticket's scope — it did not create the gap) but should be flagged to the ticket
  owner; a new entry from THIS ticket must not be mistaken for retroactively covering that one.
- No P0 entries in `docs/parity_ledger/*.yaml` reference this subsystem. This ticket's own new
  entry (to be added at Parity phase) should be `priority: P2`, matching INFRA-306/305 sibling
  entries, since no P0-tagged behavior is touched.

## Prior Work

- `tickets/done/TCK-20260721-CODEX-REPLAY-PARITY.md` (read in full) — built `tools/agent_replay_codex/`.
  Its own "Implementation Notes" Step 11 records a **real bug found during that ticket's Implement
  pass**: `claude_gate_result` was initially read as the raw fixture verdict string `"APPROVED"`
  while `codex_gate_result` was `codex_outcome.final_status` (`"ok"`) — a vocabulary mismatch, not
  a real divergence, fixed by normalizing `claude_gate_result` the same way `replay_slice()`
  normalizes verdicts. This is directly relevant: this ticket's own new comparison logic must not
  reintroduce that same vocabulary bug when it builds its own (non-Codex-CLI) "Codex output" side.
- `stored_artifacts/TCK-20260721-CODEX-REPLAY-PARITY/{investigation,plan,test_plan}.md` exist;
  not re-read in full detail beyond what the done ticket's Implementation Notes already summarize,
  per the instruction to prioritize direct source-code reads.
- `docs/plans/archive/agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`
  (read in full) — Section 4 "Runtime workflow orchestration," **Activation plan** (lines 139-147)
  states almost verbatim what this ticket must do: "(1) Specify a minimal Codex runtime adapter
  from the canonical workflow contract. (2) Limit the first live slice to one low-risk ticket and
  explicitly supported phases... (3) Make phase transitions and required artifacts
  machine-checkable before enabling writes. (4) Preserve Claude as the default/only production
  executor..." and its "Exit verification" (lines 149-154) lists exactly this ticket's AC #1-#4.
  The "Recommended activation sequence" diagram (lines 228-240) places "Minimal Codex runtime
  adapter + shadow parity" immediately after "Execution identity (Claude first)" and "Hook-surface
  policy + isolated Codex PostToolUse verification" — both of which are the two just-landed
  prerequisite tickets (TCK-20260730-CLAUDE-EXECUTION-IDENTITY, TCK-20260730-PROVIDER-HOOK-POLICY)
  plus TCK-20260730-CODEX-POSTTOOL-ADAPTER. This ticket is exactly the next step in that documented
  sequence, not a redundant restart of it.

## Risks and Open Questions

### Resolved — Open Question 1: minimal phase/tier slice
**Decision: `tier: standard` only; phases `Scope, Investigate, Plan, Review` only.** Reject every
other tier value and every other phase name.

Justification, grounded in code, not preference:
- The entire replay fixture corpus (`tests/fixtures/agent_replay/`) contains exactly one file,
  `tier: standard`, covering exactly `Scope, Investigate, Plan, Review`. There is zero fixture
  evidence for `hotfix` tier or for `Implement, Architecture-Verify, Test, Parity, Security-Review,
  Verify, Finalize`. A shadow-comparison adapter with no ground truth to compare against cannot
  produce a meaningful "match"/"mismatch" result for those phases/tiers — it would either fabricate
  ground truth (forbidden — CLAUDE.md's Durable State Rule / Uncertainty Rule) or silently no-op,
  which is worse than an explicit, tested rejection.
- `docs/ai/replay_fixture_spec.md`'s own "Phase-slice scope statement" gives the identical
  rationale for the underlying fixture/runner: Implement onward "require a `files_changed`/diff
  payload this fixture format does not define." This ticket inherits that exact boundary rather
  than inventing a new one — extending the fixture envelope format is explicitly out of scope for
  both the predecessor ticket and this one.
- `hotfix` tier is qualitatively different, not just "a smaller slice": per
  `agent-orchestration/workflows/implement-ticket.yaml`, `hotfix` makes Investigate/Plan/Review/
  Architecture-Verify `skipped_event` (an event IS written, with `status: skipped`) rather than
  `full`. Supporting it would require the adapter to validate a second, structurally different
  tier-behavior contract with literally zero real fixture evidence to shadow-compare against —
  exactly the "smallest useful... slice" the ticket's own Assumptions section asks Investigate to
  select, inverted: `hotfix` is not smaller, it is a different, unvalidatable contract shape.
- Every intentionally-unsupported item must be listed explicitly and rejected with a typed error
  (mirroring `EntryCriterionNotMetError`/`ConsentNotGrantedError`'s precedent in
  `tools/agent_replay_codex/errors.py`), not silently ignored: `tier != "standard"` → reject;
  `phase not in {Scope, Investigate, Plan, Review}` → reject; any phase present in a ticket-shaped
  input beyond that set (e.g. an `Implement` entry) → reject the whole input, do not partially
  validate.

### Resolved — Open Question 2: new package name and responsibility statement
**Decision: `tools/agent_codex_runtime_shadow/`.**

Responsibility statement (for the package `__init__.py` docstring, mirroring the precedent set by
`agent_replay_codex/__init__.py` being empty — but the sibling packages `agent_codex_pilot_
guardrails/__init__.py` and `agent_codex_posttool_adapter/__init__.py` both use a substantial
module docstring for exactly this disambiguation purpose, so this ticket should follow that
precedent, not the empty one):

> Defines the minimal `implement-ticket` phase/tier support matrix (`standard` tier,
> `Scope→Investigate→Plan→Review` only) read from `agent-orchestration/workflows/
> implement-ticket.yaml`, validates a ticket-shaped input against it (rejecting any unsupported
> phase or tier with a typed error rather than silently accepting it), and produces a
> machine-checkable phase-transition/gate/required-artifact record for that input entirely
> in-process — never invoking a real `codex exec` subprocess (that remains
> `tools/agent_replay_codex/`'s narrower, paid-invocation-gated integration proof) and never
> governing pilot ticket-selection/rollback/signoff (that remains
> `tools/agent_codex_pilot_guardrails/`'s responsibility). Shadow-compares its own record against
> `tools/agent_replay`'s canonical fixture/runner output; a mismatch fails unless a matching
> RATIFIED entry exists in `agent-orchestration/intentional-divergences.md`.

Distinctness check against the two named sibling packages:
- vs. `tools/agent_replay_codex/`: that package's job is "prove a real, authenticated `codex exec`
  process can execute the identical Python replay functions" (an execution-*environment* proof,
  consent-gated, costs real account usage, N=1 today). This ticket's package's job is "define and
  enforce the phase/tier *contract* a Codex-driven execution would have to satisfy, and validate a
  ticket-shaped input against it without spending a real invocation" (a contract-*shape* proof,
  runs unconditionally, no consent gate needed because it never shells out). These are genuinely
  different questions ("can the CLI run our code" vs. "does this input satisfy our declared
  contract") — not a renamed duplicate.
- vs. `tools/agent_codex_pilot_guardrails/`: that package governs human sign-off, rollback, and
  enabled-surface restriction for a *future live pilot run of a specific ticket* — it has no
  phase/gate/artifact validation logic at all (confirmed by reading all 6 of its modules). No
  overlap.

### Resolved — Redundancy question: is this ticket redundant with `agent_replay_codex`'s existing comparison logic?
**No — but two-thirds of what AC #3 needs is genuinely new, and the new package must NOT call
`agent_replay_codex.invoker.run_codex_replay()` or `agent_replay_codex.shadow_mode.
compare_claude_and_codex()` to produce its comparison, because both of those require a real,
paid, consent-gated `codex exec` invocation — which this ticket's own Out of Scope explicitly
forbids ("A real hook registration, paid Codex invocation, or production monitoring write").**

Precise reuse-vs-new breakdown:

**Reused as-is (import, do not reimplement):**
- `tools/agent_replay/fixture_envelope.py::load_fixture` / `FixtureEnvelope` — "the canonical
  fixture."
- `tools/agent_replay/runner.py::replay_slice` / `ReplayOutcome` — "the canonical runner." This
  ticket's own shadow-comparison ground truth on the Claude side should be `replay_slice()`'s
  output directly (consistent field vocabulary), not a second re-derivation from the fixture like
  `shadow_mode.py`'s `compare_claude_and_codex` currently does (see the vocabulary-bug precedent
  above) — reusing `ReplayOutcome` directly sidesteps that whole class of bug.
- `tools/agent_replay_codex/containment.py::capture_snapshot` / `assert_no_diff` /
  `snapshot_monitoring_lines` / `assert_monitoring_prefix_preserved` — already `repo_root`-
  parameterized, no coupling to the real-`codex exec` path. Directly satisfies AC #4's "no
  repository ticket/config mutation."
- `tools/agent_replay_codex/provenance_check.py::assert_no_codex_provider_writes` — directly
  satisfies AC #4's "no `provider=codex` monitoring corpus record."
- `tools/agent_replay_codex/codex_config_guard.py::assert_committed_config_hook_free` /
  `snapshot_config_bytes` / `assert_config_bytes_unchanged` — directly satisfies the scope item
  "leave committed `.codex/config.toml` hook-free."
- `tools/agent_orchestration_claude_adapter/divergence_log.py::load_divergences` / `is_approved`
  — directly satisfies AC #3's "mismatch requires a ratified intentional divergence."

**Genuinely new (does not exist anywhere in the repo today):**
1. A phase/tier support-matrix reader/validator sourced from `agent-orchestration/workflows/
   implement-ticket.yaml` (AC #1) — no existing module parses this file's `phases`/`tiers`
   structure at all; `implement-ticket.yaml` is currently read only by humans and by
   `tools/agent-monitoring/vocabulary.py`'s one-time bootstrap (per that file's own header
   comment), not by any phase/tier *acceptance-matrix* consumer.
2. A contract-version check (AC #2's "Contract-version... validation") — `implement-ticket.yaml`
   has a `workflow_version: 1` field; nothing in `tools/agent_replay*` or
   `tools/agent_codex_pilot_guardrails/` reads or validates it today.
3. A required-artifact check (AC #2's "required-artifact... validation," AC #3's "artifacts"
   comparison dimension) — `ReplayOutcome`/`FixtureEnvelope` carry no artifact-path field at all;
   `shadow_mode.py`'s `ShadowModeComparison.claude_artifact_refs` exists but is excluded from
   `match`. This ticket must define what "required artifact" means per phase (e.g., Investigate →
   `staging_artifacts/{ticket_id}/investigation.md` + `test_plan.md` must exist; Plan →
   `staging_artifacts/{ticket_id}/plan.md` must exist) and build the check from scratch — no
   existing gate-check module in `tools/gate_checks/` does this generically (they are Verify-phase-
   specific, e.g. `done_checker_static.py`'s `frontmatter_valid`, not a general per-phase artifact-
   existence check usable mid-replay).
4. A "process this input without a real `codex exec` call" execution path — the functional
   replacement for what `invoker.run_codex_replay()` does, but entirely in-process (likely: run the
   new adapter's own phase/tier-matrix + gate/artifact validation directly against the ticket-shaped
   input, treating that computed record as the "Codex output" side of the comparison, since a real
   Codex CLI call is explicitly out of scope here). This is the crux of what makes this ticket a
   "shadow" proof rather than a repeat of the predecessor's "real, consent-gated" proof.
5. A comparison function that includes artifacts in its `match` computation (fixing the gap in
   `shadow_mode.py`'s current `match`, which only checks `phases_completed`/`gate_result`) — new
   code, new dataclass or an extension, not a copy of `ShadowModeComparison`.
6. AC #5's "consent-gated skips still classified as authorization gates rather than successful live
   runtime evidence" — this is a NEW test-classification concern specific to this ticket's own
   suite (it must not accidentally treat "test skipped because no live consent" as if it were a
   passing runtime-parity proof); the predecessor's own `real_codex_replay` fixture pattern
   (session-scoped, `pytest.skip` on missing consent/CLI) is the thing to model the *skip
   behavior* on, but this ticket's core comparison tests should not need that fixture at all, since
   they must run unconditionally without any real Codex invocation.

### Open — divergence-log axis precedent
`tests/agent_replay_codex/test_shadow_mode_comparison.py` and `test_phase_parity.py` both use a
single ad hoc `"codex_parity"` axis for `is_approved()`, which is not one of the 4 axis values
`agent-orchestration/intentional-divergences.md`'s own `## Entry Format` section documents
(`terminal_status | phase_order | gate_policy | artifact_requirements`). Since AC #3 explicitly
lists 4 separate comparison dimensions (phase order, final status, gate result, artifacts) that
map cleanly onto those 4 documented axes, this ticket should use the 4 specific documented axes
(e.g. `## phase_order:TCK-...`, `## artifact_requirements:TCK-...`) rather than reintroduce the
undocumented `codex_parity` catch-all — this gives finer-grained, individually-ratifiable
divergence entries instead of one entry that silently suppresses all four dimensions at once. This
is a judgment call with a clear code-traceable justification, not a blocking open question — flag
it in plan.md but do not block Investigate on it.

### Open — required-artifact semantics for a "real ticket-shaped input" that has no `stored_artifacts_dir` yet
The one real fixture's `source.stored_artifacts_dir` points at an already-`DONE` ticket's
permanent `stored_artifacts/` location. A "real ticket-shaped input" fed through this ticket's new
shadow adapter (per Scope: "Map a real ticket-shaped input... in a scratch/shadow environment")
needs a defined artifact-location convention for the *scratch* case — most likely
`staging_artifacts/{ticket_id}/` (the live, in-flight convention CLAUDE.md already defines) rather
than `stored_artifacts/{ticket_id}/` (post-close only). This must be decided explicitly in plan.md;
Investigate flags it rather than assuming an answer, per CLAUDE.md's Uncertainty Rule.

## Anti-Drift Hazards

- **Do not let the new package call `codex exec`, even conditionally/optionally.** The moment any
  code path in `tools/agent_codex_runtime_shadow/` can spawn a real `codex` subprocess, it
  collapses back into being a second, redundant copy of `agent_replay_codex/invoker.py` and
  violates this ticket's own Out of Scope line. Enforce this with an AST/string-constant scan
  test mirroring `tests/agent_replay/test_runner_no_forbidden_calls.py` and
  `tests/agent_codex_posttool_adapter/test_no_subprocess_and_no_live_wiring.py`'s existing
  precedent (both already proven patterns in this repo — reuse the technique, not the code).
- **Do not extend the fixture envelope format to add an artifact-path field "just for this
  ticket."** `docs/ai/replay_fixture_spec.md`'s Phase-slice scope statement and both this ticket's
  and the predecessor's Out-of-Scope lines forbid extending the fixture envelope format. Required-
  artifact checking must be built as a separate, additive check layered on top of the existing
  `FixtureEnvelope`/`ReplayOutcome` shapes, not a schema change to `tools/agent_replay/
  fixture_envelope.py`.
- **Do not silently widen the enabled/supported phase or tier set "to be more useful."** Every
  phase/tier outside `standard`/`Scope,Investigate,Plan,Review` must be a deterministic, tested
  rejection with a typed error — not a soft warning, not a best-effort partial validation.
- **Do not write a live `provider="codex"` record anywhere**, including in a test's temp fixture
  that accidentally points at the real `agent-monitoring/` directory instead of a `tmp_path`. The
  existing `provenance_check.py::assert_no_codex_provider_writes` negative-control test pattern
  (`tests/agent_replay_codex/test_monitoring_provenance.py`) is the model to copy.
- **Do not touch `tools/agent_replay/{runner.py,fixture_envelope.py}`,
  `tools/agent_replay_codex/*`, or `tools/agent_codex_pilot_guardrails/*`.** All are read-only
  dependencies for this ticket; the predecessor ticket's own Files Changed section confirms these
  stayed byte-for-byte untouched across its own Implement pass, and this ticket must preserve that
  same discipline (CLAUDE.md Out of Scope: "Weakening current replay containment or pilot
  guardrail protections").
- **Do not conflate `docs/guidelines/intentional_divergences.md` (Mechanics Bible divergences) with
  `agent-orchestration/intentional-divergences.md` (this subsystem's divergences).** Both files
  exist in this repo with nearly identical names; `tools/agent_orchestration_claude_adapter/
  divergence_log.py`'s own docstring explicitly warns about this. Any new divergence entries this
  ticket registers belong exclusively in `agent-orchestration/intentional-divergences.md`.
- **Pre-existing baseline test noise, not to be "fixed" by this ticket:**
  `tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py::
  test_terminal_status_conformance_finalize_incomplete_appears_once_on_both_sides` and
  `test_terminal_status_extractor.py::
  test_extract_all_terminal_statuses_dedupes_by_value_not_call_site_count` currently FAIL on a
  clean run of `tests/agent_orchestration_claude_adapter/` (hardcoded expected line numbers
  `[1234, 1246]` vs. the real current `implement-ticket.js` lines `[1344, 1356]` — the file grew
  from unrelated tickets landing since those line numbers were hardcoded). This is unrelated,
  pre-existing drift, not caused by this ticket's prerequisites; Verify must not misattribute it to
  this ticket's own work, and this ticket must not "fix" it as a drive-by (out of scope).
