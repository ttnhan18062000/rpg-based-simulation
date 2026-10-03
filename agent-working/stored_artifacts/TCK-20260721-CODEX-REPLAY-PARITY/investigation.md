---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-REPLAY-PARITY
artifact_type: investigation
tags: [ai, workflows, process-improvement, hooks]
---

# Investigation — TCK-20260721-CODEX-REPLAY-PARITY

## Current Behavior

### Entry criteria — all 4 hard predecessors confirmed DONE and landed
`tickets/inprogress/TCK-20260721-CODEX-REPLAY-PARITY.md`'s Scope names 4 hard predecessors. All
confirmed present and functioning in the repo today:
- `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` — `agent-orchestration/` (6 files) +
  `tools/agent_orchestration/{loader,generator,errors}.py`. `load_contract()` loads cleanly.
- `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER` — `agent-orchestration/terminal-statuses.yaml` (15
  terminal statuses), `agent-orchestration/rendered/claude-adapter.yaml` (generated, committed:
  `phase_order` + full `phases` incl. `tiers`/`condition`/`if_false`), `agent-orchestration/intentional-divergences.md`
  (format defined, zero entries), `tools/agent_orchestration_claude_adapter/`.
- `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` — root `AGENTS.md` (generated, exists), 16
  `.agents/skills/<id>/SKILL.md` (generated, exists — verified `ls .agents/skills | wc -l` = 16),
  legacy tree quarantined at `docs/archive/legacy_agents_skills_20260722/`, committed
  `.codex/config.toml` (comment-only, zero hooks, `tomllib.load` → `{}` — verified directly),
  and — **critical, load-bearing finding for this ticket** — a real captured Codex `PostToolUse`
  hook payload at `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json`, plus the
  **empirical `.codex/config.toml` hook-registration TOML syntax**, recorded in that ticket's
  Implementation Notes (not in any committed file, since the committed config stays hook-free by
  design):
  ```toml
  [[hooks.PostToolUse]]
  matcher = "*"

  [[hooks.PostToolUse.hooks]]
  type = "command"
  command = "cat > /tmp/codex-fixture-capture-scratch/captured_stdin.json"
  ```
  and the finding that Codex project trust is a **global** `~/.codex/config.toml` entry keyed by
  absolute path (`[projects."<path>"].trust_level = "trusted"`), not a per-project file.
- `TCK-20260721-MONITORING-WRITER-UNIFICATION` — `tools/agent-monitoring/writer.py` (shared
  `write_line`/`write_lines`, never raises, diagnostic sidecar
  `agent-monitoring/.writer_health.jsonl`), all 3 call sites (`post_tool_hook.py`, `record_run.py`,
  `record_events.py`) migrated. New records carry `execution_id`/`provider`/`ticket_id` — the exact
  fields this ticket's "monitoring-record provenance confirms Claude is the sole live writer" AC
  needs to check against. Confirmed via direct read of `writer.py` and the ticket's own plan.md:
  `execution_id` format is `f"{provider}-{ticket_id}-{unix_ts_ms}-{token_hex_8}"`.
  **Provider-string naming is not perfectly consistent across docs**: the ADR/writer-decision doc's
  synthetic illustration (`docs/ai/monitoring_writer_decision.md:132-141`) uses `"claude-code"` as
  the `provider` value, while other places in this batch (e.g. this ticket's own AC text) simply
  say "Claude"/"Codex". No real record has been written with either value yet (writer-unification
  ticket made no real corpus write). This ticket's own shadow-mode comparison tooling should decide
  and document one canonical provider string for each side (e.g. `"claude"` / `"codex"`) rather than
  inventing a third variant — flagged in Risks, not decided here.

All 4 predecessors' own regression suites currently pass except one known, pre-existing, unrelated
failure (see Anti-Drift Hazards).

### `tools/agent_replay/` — the existing Python-only replay proof (read in full)
- `fixture_envelope.py::load_fixture()` — validates a versioned YAML envelope
  (`version`, `source: {ticket_id, ticket_path, events_run_id}`, `phases: [{phase, agent, input,
  output, transition}]`), fail-closed (`FixtureValidationError` naming exact field/phase index).
- `runner.py::replay_slice()` — re-executes the **Scope → Investigate → Plan → Review** branch
  logic by calling the *same real* Python functions the live orchestrator calls
  (`tag_registry.check_tags_registered`, `gate_checks.plan_gate_static.plan_has_unresolved_questions_heading`),
  with `_fake_write_monitoring`/`_fake_hook_boundary` as pure in-memory no-op stand-ins for the 4
  forbidden monitoring/hook scripts. Returns `ReplayOutcome(final_status, phases_completed)`.
- Exactly **one** real fixture is committed:
  `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`.
- Containment proof today is **two Python-native techniques**, both explicitly out of this
  ticket's reach per its own Out-of-Scope line ("does not modify the Python-only replay runner's
  existing AST-scan/content-hash containment proof"):
  1. `tests/agent_replay/test_runner_no_forbidden_calls.py` — `ast`-based static scan: no
     import/subprocess/importlib call anywhere in `tools/agent_replay/*.py` references the 4
     forbidden script names, plus a whole-file string-constant scan (catches indirect
     variable-based construction).
  2. `tests/agent_replay/test_no_mutation_snapshot.py` — runs against the **real** repo tree
     (never `tmp_path`): git-porcelain-if-clean, else whole-file content-hash-if-dirty, asserting
     zero diff in `tickets/` + `agent-monitoring/*.jsonl` immediately before/after `replay_slice()`.
  Both currently pass: `pytest tests/agent_replay/ -q` → 25 passed (verified directly).
- **AST scanning cannot extend to a real Codex CLI process** — Codex is an opaque, separately
  compiled external binary; there is no Python source tree to `ast.parse()`. This is exactly the
  gap this ticket's own Scope names explicitly ("a real Codex CLI/session is a separate opaque
  external process that needs a materially different, process-level verification technique") and
  is the reason the ticket forbids reusing the AST-scan half of the existing proof.

### No "Codex execution adapter" exists anywhere in this repo today — the central gap
Searched every package this batch has built (`tools/agent_orchestration/`,
`tools/agent_orchestration_claude_adapter/`, `tools/agent_orchestration_codex_adapter/`,
`tools/agent_replay/`). None of them **drives a real Codex CLI invocation through the
Scope→Review phase-slice decision logic** the way `runner.py::replay_slice()` drives it in pure
Python:
- `tools/agent_orchestration_codex_adapter/generator.py` — the closest-sounding candidate by
  name — is a **static-content generator only** (`render_codex_guidance()` builds `AGENTS.md` and
  per-skill `SKILL.md` files from the contract). It never invokes `codex` as a subprocess, never
  drives workflow-phase logic, and its write-guard only permits writes to `AGENTS.md`/
  `.agents/skills/` — it is not extensible in-place into an execution adapter without violating
  its own write-guard's allowed-target set.
- `tools/agent_orchestration_claude_adapter/generator.py` similarly only renders a static YAML
  projection (`claude-adapter.yaml`) — never executes anything.
- `tests/tools/test_codex_capability_diagnostics.py` only runs `codex features list` (a read-only
  diagnostic, no hook, no `codex exec`).
- The one place a real `codex exec` invocation was actually performed in this repo's history —
  `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`'s Step 11 — was a manually-run, one-off scratch
  experiment (its commands live only in that ticket's `Implementation Notes` prose, not in any
  committed, re-runnable script) whose sole purpose was capturing one raw hook `stdin` payload; it
  never attempted to reproduce the Scope/Plan/Review branch decisions.

**Conclusion: this ticket must build genuinely new code** — a package that (a) reads the same
fixture envelope `runner.py` reads, (b) drives a real `codex` CLI process through some concrete
mechanism to reproduce the Scope→Review branch decisions, and (c) returns a result shaped
comparably to `ReplayOutcome` (`final_status`, `phases_completed`) for the parity comparison. Two
structurally different designs are both defensible and neither is decided by any doc read in this
investigation (see Risks #1):
- **(a) Prompt-driven**: construct a prompt from the fixture's `input`/`output` data instructing
  Codex to evaluate the same branch conditions (conflicts, unregistered tags, unresolved-questions
  heading, review verdict) and emit a structured JSON verdict Codex itself reasons about — this
  tests Codex's own comprehension of the workflow's gate logic, closer to "real agent" behavior.
- **(b) Execution-driven**: have Codex CLI (via `codex exec`) invoke a wrapper script that itself
  calls the exact same real Python functions `runner.py` calls
  (`check_tags_registered`/`plan_has_unresolved_questions_heading`) and reports the result back —
  this tests whether Codex *as a process* can be driven through the same deterministic code path
  Claude's orchestrator uses, with less "does the LLM reason correctly" variance and more "can the
  provider boundary/tooling/containment work" signal.
  The ticket's own AC wording ("execute the replay fixture through the real Codex adapter") reads
  slightly more consistent with (b), but does not rule out (a) — a genuine Plan-phase decision.

### Real Codex CLI — confirmed genuinely usable in this environment right now
- `which codex` → `/home/u24desktop/.local/bin/codex`; `codex --version` → `codex-cli 0.145.0`
  (was `0.144.6` at `CODEX-CAPABILITY-MATRIX`/`CODEX-REPLAY-PROOF` investigation time — minor
  version drift since, not independently re-verified against the manual for behavior changes).
- `codex login status` → `Logged in using ChatGPT` — a real, authenticated account with real
  quota, not a stub.
- `codex features list` → `hooks stable true` (consistent with the capability matrix's prior
  finding).
- `~/.codex/config.toml`'s `[projects."..."]` table already contains
  `[projects."/home/u24desktop/Working/rpg-based-simulation"] trust_level = "trusted"` — **this
  repo's own absolute path is already globally trusted**, confirmed directly (not merely
  documented). Practical consequence: if `codex` is invoked with this repo as its cwd, its
  project-local `.codex/config.toml` (committed, hook-free) *would* load — but since it registers
  zero hooks, nothing production-facing fires either way. Running Codex with this repo as cwd is
  therefore not itself unsafe on the hook-registration axis, but it is a materially different
  containment posture than running Codex in a directory with no relationship to this repo at all
  (the pattern `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s Step 11 used, `/tmp/codex-fixture-capture-scratch`).
- **Environment tools available for a process-level containment technique** (checked directly,
  none currently used anywhere in this repo — `grep` for `strace|bubblewrap|unshare|firejail` across
  `tools/`, `tests/`, `docs/` → zero hits):
  - `strace` — present at `/usr/bin/strace`.
  - `bwrap` (bubblewrap) — present at `/usr/bin/bwrap`.
  - `unshare` — present at `/usr/bin/unshare`.
  No prior ticket in this repo has used any of the three. Using one would be genuinely new
  tooling, not a reuse of an existing pattern.

### Containment-technique tradeoffs (for Plan's required single-method decision — not decided here)
The ticket's own AC requires this ticket's Investigate/Plan phase to "select and document ONE
auditable process-level containment-verification technique... before any paid/live invocation
occurs." Candidates, with what this investigation found about each:
1. **`strace -f` file-open monitoring** — traces every `openat`/`open` syscall the `codex` process
   (and its children) makes; can assert none names a path under this repo's `tickets/` or
   `agent-monitoring/`. Strongest "did it even attempt" guarantee. Tooling exists (`/usr/bin/strace`)
   but has zero precedent in this repo, adds real complexity (parsing strace output, handling a
   CLI that spawns child processes, potential signal/TTY interaction issues with an interactive-ish
   CLI), and needs its own new test-shape design from scratch.
2. **Filesystem-permission / namespace sandboxing (`bwrap`/`unshare`)** — runs `codex` inside a
   restricted mount namespace with this repo bind-mounted read-only (or not mounted at all).
   Strongest *preventive* (not merely detective) guarantee — a write attempt would fail at the OS
   level, not just get detected after the fact. Also zero precedent in this repo; highest
   implementation complexity of the three; unverified whether `codex`'s own runtime (network calls,
   its own config/session state under `~/.codex/`) tolerates running inside a namespace without
   breaking auth/session behavior.
3. **Isolated scratch directory + git-porcelain/content-hash snapshot diff of the real repo** —
   directly reuses two already-proven patterns in this exact repo: `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s
   own Step 11 (`codex exec` run entirely inside `/tmp/codex-fixture-capture-scratch`, outside the
   repo's working tree) for structural avoidance, plus `test_no_mutation_snapshot.py`'s
   porcelain-if-clean/content-hash-if-dirty pattern (already extended once, in
   `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s `manifest.py::capture_lines`/`assert_prefix_preserved`, for
   the "legitimately-appending" case) for detective proof. Weaker than strace/namespace sandboxing
   in the abstract (it proves zero *resulting* diff, not zero *attempted* access), but it is the
   only option with direct, working precedent in this codebase, and cwd-isolation makes an
   *accidental* real-repo touch structurally unlikely (Codex would need an absolute path into this
   repo to touch it at all, and nothing in a fixture-derived prompt would supply one).

This investigation does not pick one — the ticket's own text assigns that decision to this
ticket's Plan phase explicitly. Recorded here so Plan is not starting from zero: option 3 has by
far the strongest in-repo precedent and lowest net-new-tooling risk; options 1/2 are more rigorous
but unprecedented here and add real implementation surface for a first slice.

### Fixture-envelope reuse constraint
The ticket's Out of Scope is explicit: it does not extend the fixture-envelope format (no
`files_changed`/diff payload) and covers only Scope-through-Review. This means the "same fixture"
this ticket runs through both the Python runner and the real Codex adapter must be the existing
Scope→Investigate→Plan→Review-only shape `fixture_envelope.py` already validates — most directly,
the one already-committed `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`
fixture, or a structurally identical new one. Nothing in this ticket's scope permits inventing a
richer envelope to make Codex's job easier.

### Human-consent-gate precedent exists, but this ticket's own bar is explicitly higher
`CODEX-GUIDANCE-FIXTURE-CAPTURE`'s Step 10 is the one real precedent for gating a real Codex
invocation on human consent — but that gate was **honor-based by the plan's own admission**
("a plan-doc instruction cannot mechanically stop an external actor from skipping straight to
Step 11 — this gate is honor-based by construction"), enforced only by a documented procedural
step plus a post-hoc `Implementation Notes` append. This ticket's own AC text asks for something
strictly stronger: "An explicit, **programmatically-checked** human-consent gate... the workflow
**refuses to proceed** without it." A prose-only Step-10-style gate would not satisfy this ticket's
own AC as literally worded — Plan needs a mechanism code can actually check (e.g., a required
environment variable, a signed/dated consent-token file the invocation code asserts exists and is
fresh, or an explicit CLI flag requiring a human-typed confirmation string), not merely a
documented step in a plan.

## Mechanics / Engine Constraints

Not applicable. This ticket touches only agent-orchestration/replay tooling
(`tools/agent_replay/`, `agent-orchestration/`, a new adapter package, tests) — no `src/`
simulation code, no `docs/mechanics/` chapter, no `docs/engine/` contract governs this subsystem.
Consistent with the "not applicable" finding independently reached by all 4 predecessor tickets in
this batch.

## Parity Ledger Overlap

None. Grepped all 8 `docs/parity_ledger/*.yaml` files for `codex|orchestrat|agent_replay` and for
`replay` specifically: every "replay" hit belongs to the unrelated simulation-engine
`ReplayManager`/`replay_metrics` subsystem (`src/engine/replay_manager.py`,
`tests/unit/engine/test_replay_backpressure.py`, etc.) — a coincidentally-named different
subsystem, not agent-orchestration tooling. No P0 entry anywhere references this ticket's
subsystem; no entry needs updating. Consistent with the identical "not applicable" finding all 4
predecessor tickets in this batch independently reached.

## Prior Work

- **`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`**, **`TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`**,
  **`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`**, **`TCK-20260721-MONITORING-WRITER-UNIFICATION`**
  (all DONE, `stored_artifacts/`) — the 4 hard predecessors, detailed in Current Behavior above.
  Each established one repeated structural convention this ticket should follow: a new,
  independent `tools/agent_orchestration_<name>/` (or in this case, likely
  `tools/agent_replay_codex/`-shaped) package per ticket, never editing a predecessor's package
  in place; a local write-guard structurally refusing writes outside an explicit allowed-target
  set; and an explicit, flagged note whenever a cross-ticket file edit is genuinely required.
- **`TCK-20260721-CODEX-REPLAY-PROOF`** (DONE, discovery epic) — built the Python-only replay
  proof and its two containment techniques (AST scan, porcelain/hash snapshot) this ticket must
  not modify, and the one committed fixture this ticket should reuse or structurally mirror.
- **`TCK-20260721-CODEX-CAPABILITY-MATRIX`** (DONE, discovery epic) — the hook I/O contract
  reference (`docs/ai/codex_capability_matrix.md`), now partially superseded/completed by
  `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s real empirical findings (hook-registration TOML syntax,
  global trust-file location) recorded in that ticket's `Implementation Notes` rather than in the
  matrix doc itself — worth cross-referencing both, since the matrix doc was not updated with the
  empirical findings.
- **`tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`** — a follow-up hotfix
  ticket referenced in `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s completion summary as tracking a known
  pre-existing test failure. **Confirmed still open/unfiled-as-done and the failure it describes
  is still live today** (see Anti-Drift Hazards) — relevant because this ticket's own regression
  surface includes the same test file.

## Risks and Open Questions

1. **BLOCKING for Plan — what "real Codex adapter" concretely means as a deliverable is not
   decided by any doc.** Two structurally different designs (prompt-driven vs.
   execution-driven, detailed in Current Behavior) are both consistent with the ticket's AC
   wording. This is the single largest open question and directly determines what code gets
   written. Flagging per this role's instruction not to assume an answer — Plan must choose and
   justify.
2. **BLOCKING for Plan — the process-level containment-verification technique is unchosen.**
   Three real candidates with concrete tradeoffs are documented above (strace, namespace
   sandboxing, isolated-scratch-dir + snapshot diff). The ticket's own AC requires Plan to pick
   exactly one and justify it before any paid/live invocation — not left to Implement.
3. **The ticket's own consent-gate bar ("programmatically-checked... refuses to proceed") is
   stricter than the one real precedent in this repo (`CODEX-GUIDANCE-FIXTURE-CAPTURE`'s
   honor-based Step 10).** Plan must design an actually-enforceable mechanism, not copy the
   precedent verbatim — flagged explicitly so this isn't silently downgraded to the weaker,
   already-precedented pattern.
4. **"N real implement-ticket inputs" for shadow mode is unspecified.** The ticket's AC says
   "across N real implement-ticket inputs" without naming N or defining what counts as an input
   (an existing `tests/fixtures/agent_replay/*.yaml` fixture? a freshly-derived fixture from
   another real done ticket? a live, currently-open ticket?). Given the fixture-envelope-reuse
   constraint (Current Behavior above), the most conservative reading is N new fixtures derived
   from other real `tickets/done/` tickets, following the one existing fixture's own derivation
   pattern — but this is not stated anywhere and is a genuine Plan-phase decision, including
   justifying the chosen N.
5. **Provider-string naming is not perfectly consistent across this batch's own docs**
   (`"claude-code"` in one synthetic example vs. bare `"claude"`/`"Codex"` elsewhere) — no real
   corpus record uses either value yet, so this ticket is free to pick one canonical pair
   (recommend `"claude"`/`"codex"`, matching the ticket's own prose and this ticket's own AC
   wording most directly), but should state the choice explicitly rather than let it drift.
6. **Codex CLI version has drifted since the capability matrix's investigation** (`0.144.6` →
   `0.145.0`) — not independently re-verified for hook-payload-shape or trust-model behavior
   changes in this investigation. Low risk (same major-version-0 line, `codex features list`
   still reports `hooks stable true`), but if Implement's real invocation surfaces any
   discrepancy from `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s recorded empirical findings, that should be
   treated as a real, recordable divergence, not silently reconciled.
7. **`tools/agent_orchestration_codex_adapter/generator.py`'s existing write-guard cannot be
   reused as-is for this ticket's new code** — its allowed-target set is exactly `AGENTS.md` +
   `.agents/skills/`, which has nothing to do with this ticket's own output (replay-comparison
   results, shadow-mode reports). This ticket needs its own independent write-guard scoped to
   wherever its own new package decides to write, following the established per-ticket pattern
   rather than trying to extend an unrelated predecessor's guard.

None of these block starting the Plan phase — they are exactly the kind of decisions the ticket's
own Scope/AC text explicitly assigns to this ticket's own Investigate/Plan phase.

## Anti-Drift Hazards

- **Known, pre-existing, unrelated test failure in this ticket's own regression surface —
  confirmed still live, not fixed by this investigation.** `pytest tests/agent_orchestration/
  tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/` currently
  reports **83 passed, 1 failed**: `test_agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`
  fails with `FileNotFoundError` because it still references the old
  `staging_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/plan.md` path, which was migrated to
  `stored_artifacts/` at that ticket's close. The tracking hotfix,
  `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`, **is still an open/unfiled
  todo, not done** — confirmed directly by listing `tickets/todos/` and `tickets/done/`. This
  ticket must not treat this failure as a regression it introduced, and should not silently "fix"
  it either (out of scope, owned by that other ticket) — just record it as a pre-existing known
  failure in the baseline, exactly as `CODEX-GUIDANCE-FIXTURE-CAPTURE` did.
- **Do not modify `tools/agent_replay/{runner.py,fixture_envelope.py}`** — owned by the closed
  `CODEX-REPLAY-PROOF` ticket, and this ticket's own Out-of-Scope line explicitly forbids touching
  its containment proof. Add new, sibling code instead.
- **Do not enable a production Codex hook.** `.codex/config.toml` must remain comment-only/zero
  hooks (currently enforced by `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py::test_no_production_hook_registered_in_codex_config`
  and `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`) — this ticket's
  own real-Codex-invocation work must not regress either guard, even transiently.
  If Plan's chosen adapter design needs a hook (e.g. to capture Codex's own tool-call trace for
  comparison), any such hook config must live in an isolated scratch location outside this repo,
  mirroring `CODEX-GUIDANCE-FIXTURE-CAPTURE`'s own precedent exactly — never committed to this
  repo's `.codex/config.toml`.
- **Do not let "shadow mode" become a live pilot.** Every real Codex invocation this ticket
  performs is comparison-only; nothing Codex produces may be applied, committed, or written to the
  live monitoring corpus. This is now directly, mechanically checkable thanks to
  `MONITORING-WRITER-UNIFICATION`'s `execution_id`/`provider` fields — a verification step should
  assert zero real `agent-monitoring/{runs,events,tools}.jsonl` record carries
  `provider == "codex"` after any of this ticket's own test/shadow runs.
  `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` (next in `SEQUENCE.md`, not yet started) is the only
  ticket authorized to move toward a live pilot — this ticket must not preempt it.
  `LIVE-CODEX-PILOT-GUARDRAILS`'s own next-in-sequence status (per
  `tickets/todos/provider-agnostic-implementation/SEQUENCE.md`) further confirms shadow-mode
  output feeding a live pilot decision is explicitly this ticket's downstream neighbor's job, not
  this ticket's own.
- **Do not conflate three now-distinct fixture concerns**: `tests/fixtures/agent_replay/*.yaml`
  (phase-slice replay envelope, `CODEX-REPLAY-PROOF`), `tests/fixtures/codex_hook_payloads/*.json`
  (raw hook `stdin` payload capture, `CODEX-GUIDANCE-FIXTURE-CAPTURE`), and whatever this ticket
  adds for shadow-mode comparison output — each has a distinct purpose and directory; do not reuse
  one format for another.
- **Do not silently spend real Codex API usage during Investigate/Plan.** This investigation
  performed only read-only diagnostics (`codex --version`, `codex login status`,
  `codex features list`, reading `~/.codex/config.toml`'s trust table) — none of which trigger a
  hook or consume meaningful quota beyond a CLI diagnostic call. No `codex exec` or any prompted
  invocation was run. The real-API-consent gate (Risk #3) governs Implement, not this phase.
