---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260730-CODEX-POSTTOOL-ADAPTER
artifact_type: investigation
tags: [ai, hooks, agent-monitoring, observability, testing]
---

# Investigation — TCK-20260730-CODEX-POSTTOOL-ADAPTER

## Current Behavior

**Claude's PostToolUse hook (the thing this ticket must NOT reuse by assumption)**
`tools/agent-monitoring/post_tool_hook.py:1-95` reads one JSON payload from stdin, builds an
`_input_summary()` (lines 12-23: truncates `tool_input` per tool-type — 80-120 chars, and for
`mcp__*` tools extracts only `query`/`q`/`text`) — **it never touches `tool_response` content**,
only inspects it structurally to derive `status` ("ok"/"failed", lines 65-71). It reads
`.claude/.tool_start` for duration and `.claude/current_run` for `run_id`/`seq`/`phase`/`agent`/
`execution_id`/`provider`/`ticket_id` (lines 45-63, all inside one fail-open `try/except`). It
assembles a 13-field record (lines 73-87: `session_id, run_id, seq, phase, agent, ts, tool,
input_summary, status, duration_ms, execution_id, provider, ticket_id`) and appends via
`write_line(tools_file, json.dumps(record, separators=(",", ":")))` (line 91). The whole body is
wrapped in a top-level `try/except Exception: pass` (lines 26/93-94) — never raises to the caller.
This record shape **is** the target output shape the new Codex adapter must produce (with
`provider="codex"`), but the input side (Claude's stdin payload, Claude-specific sidecar reads)
does not match Codex's payload or environment, so this file cannot be imported/reused as-is — the
ticket's Out-of-Scope bullet is correct to forbid reusing it "by assumption."

**The real captured Codex PostToolUse fixture** (Question 1)
`tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` — top-level envelope:
`fixture_schema_version` (1), `capture_grade` ("direct_experiment"), `hook_event_name`
("PostToolUse"), `codex_cli_version`, `captured_at_utc`, `capture_method` (prose), and
`raw_stdin_payload` (the actual hook stdin object). `raw_stdin_payload` fields, confirmed present
by direct read and cross-checked against `tests/tools/test_codex_hook_payload_fixture.py`'s own
assertions (lines 43-67): 7 common fields (`session_id`, `turn_id`, `transcript_path`, `cwd`,
`hook_event_name`, `model`, `permission_mode`) + 4 `PostToolUse`-specific fields (`tool_name`,
`tool_input` — a dict, e.g. `{"command": "ls -la ."}`, `tool_response` — a **raw string** of
command stdout, `tool_use_id`). This exactly matches `docs/ai/codex_capability_matrix.md` §1's
documented field tables (VERIFIED, direct-experiment-grade). Critically: **none of
`transcript_path`, `cwd`, `model`, `permission_mode`, `turn_id`, `tool_use_id` have a home in the
shared `tools.jsonl` record shape** post_tool_hook.py produces — the adapter must explicitly drop
them, not silently pass them through.

**The shared append writer** (Question 2)
`tools/agent-monitoring/writer.py` exposes exactly two public functions:
`write_line(target_path: Path, line: str) -> bool` (line 107) and
`write_lines(target_path: Path, lines: list[str]) -> bool` (line 137). Both never raise (internal
`try/except`, failures routed to a best-effort `.writer_health.jsonl` sidecar via `_write_diagnostic`,
line 78) and return a plain `bool`. `post_tool_hook.py` (one record per call) uses `write_line`;
`record_events.py`/`record_run.py` use `write_lines`/`write_line` respectively. Per AC #2 ("uses
the shared append writer interface rather than a new append mechanism"), the Codex adapter must
call `write_line` (one record per PostToolUse invocation, matching `post_tool_hook.py`'s own
call pattern exactly) — never open/append the file directly.

**Guardrail packages already in `tools/`** (resolves the Scope's open module-location question,
see Risks/Open Questions below): `tools/agent_codex_pilot_guardrails/` (pilot
selection/rollback/signoff *mechanisms*, no execution entry point —
`tools/agent_codex_pilot_guardrails/__init__.py:1-13`) and `tools/agent_replay_codex/`
(consent-gated real `codex exec` subprocess invocation for replay/shadow-mode proof —
`invoker.py:37-82`). Neither owns "parse a captured Codex hook payload into the shared monitoring
record shape."

**Existing evidenced-surface guard**: `tools/agent_codex_pilot_guardrails/enabled_surface.py`
already declares `EVIDENCED_HOOK_EVENTS = frozenset({"PostToolUse"})` and
`EVIDENCED_WRITER_FUNCTIONS = frozenset({"write_line", "write_lines"})` (lines 19-20) — this
ticket's chosen hook event and writer function are already inside that evidenced subset, so no
new evidence-gap is created.

**Policy this ticket must consume**: `agent-orchestration/hook-surface-policy.yaml` lists Codex's
`PostToolUse` as `activation_candidates[0]` with `writer_functions: [write_line, write_lines]`
(lines 14-18) and enumerates 9 `activation_prerequisites` (lines 19-38) — `human_approval`,
`scratch_first_verification`, `project_trust_review`, `hook_trust_review`,
`failure_timeout_fail_open`, `redacted_output`, `out_of_band_diagnostics`, `reviewed_config_diff`,
`one_action_rollback` — none marked satisfied; every one is "a requirement still to be satisfied
by a later ticket, never a completed checkbox" (file header comment). This ticket's own AC map
onto `failure_timeout_fail_open` (AC #3), `redacted_output` (AC #2), `reviewed_config_diff`/
`one_action_rollback` (AC #5, #4) — but `human_approval`/`project_trust_review`/
`hook_trust_review` remain explicitly unsatisfied and out of this ticket's scope (Out of Scope:
"Enabling the proposed hook command in project configuration").

**Execution identity convention this ticket must parallel** (from
`.claude/workflows/implement-ticket.js:202-215` and `agent-orchestration/monitoring-schema.yaml`):
`execution_id` format is `f"{provider}-{ticket_id}-{unix_ts_ms}-{secrets.token_hex(4)}"`
(monitoring-schema.yaml lines 8-12). The real Claude call site (implement-ticket.js lines ~205-215)
generates `PROVIDER = 'claude'`, a suffix `f"{unix_ts_ms}-{token_hex(4)}"` via a `python3 -c`
subprocess emitting `EXECID:<suffix>`, then `executionId = f"{PROVIDER}-{tid}-{execIdSuffix}"`.
The Codex adapter must produce the parallel shape with `provider="codex"` literal:
`f"codex-{ticket_id}-{unix_ts_ms}-{token_hex_8}"` — same format string, different provider
literal, generated fresh once per (would-be) execution, never reused, never a join key.

**Redaction** (Question 4) — no existing importable redaction helper module exists anywhere in
the repo. Confirmed by a full-repo grep for `redact` (`tools/`, `docs/`): the only hits are
`docs/observability/retrieval_retention_redaction_policy.md` (a **policy doc** with a MAY/
PROHIBITED field-list for retrieval events/cache entries — a different subsystem, not code) and
prose references to it. There is no `redact.py`, no shared summarization helper. The closest
in-repo **code pattern** is `post_tool_hook.py`'s own `_input_summary()` (lines 12-23): a
per-tool-type field-allowlist-and-truncate function that (a) only ever touches `tool_input`, never
`tool_response`, and (b) truncates every extracted string to 80-120 chars. The Codex adapter must
build a new, analogous function — not reuse an existing helper, because none exists — and must
additionally decide what to do with `tool_response` (a field Claude's hook never persists at all,
only inspects structurally for a status flag). Per Scope bullet 2 ("do not route raw tool
input/output into monitoring") and the policy's `redacted_output` prerequisite, the adapter should
mirror Claude's own discipline: derive only a `status` flag from `tool_response`, never store its
content.

**Existing project-config guard, directly reusable**: `tools/agent_replay_codex/codex_config_guard.py`
already provides `assert_committed_config_hook_free(repo_root)` (walks the parsed
`.codex/config.toml` TOML for any `hooks` key at any depth) and
`snapshot_config_bytes`/`assert_config_bytes_unchanged` (byte-identity check). AC #4 ("A
project-config guard proves committed `.codex/config.toml` remains byte-identical/hook-free
throughout the test suite") is best satisfied by **importing this existing function**, exactly as
`tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py:23,175-178` already does
(`from tools.agent_replay_codex.codex_config_guard import assert_committed_config_hook_free`) —
not reimplementing it a third time.

**Existing proposed-activation-fragment mechanism, directly relevant to AC #5**:
`tools/agent_codex_pilot_guardrails/config_toggle.py` already defines `_HOOK_BLOCK` (lines 23-30,
a `[[hooks.PostToolUse]]` registration with `command = "true"`, a deliberate inert no-op
placeholder) and `render_enabled_config()`/`enable()`/`disable()`, all scratch-target-only
(`_assert_scratch_target` refuses to ever point at the real `.codex/config.toml`, lines 38-44).
This is very close to what Scope's last bullet asks for ("Produce a reviewable proposed hook
command/config fragment... leave `.codex/config.toml` byte-identical and hook-free"). The open
design question for Plan is whether this ticket updates `_HOOK_BLOCK`'s placeholder
`command = "true"` to reference the new adapter's real (but still never-enabled) invocation
command, or defines its own separate proposed-fragment constant alongside it — either way, this
existing scratch-only toggle mechanism should be reused, not duplicated.

## Mechanics / Engine Constraints

None. This ticket is entirely agent-orchestration/monitoring-pipeline tooling — no `src/`
simulation code, no `docs/mechanics/` or `docs/engine/` chapter governs any part of it (confirmed:
Related Code Areas and Related Docs list only `tools/`, `tests/`, `.codex/`, and
`agent-orchestration/`/`docs/ai/`/`docs/plans/` paths). The closest analogs to "engine contracts"
for this ticket's domain are `agent-orchestration/hook-surface-policy.yaml` (the provider
hook-surface contract) and `agent-orchestration/monitoring-schema.yaml` (the execution-identity
field model) — both read above and treated as authoritative for this ticket's shape, per this
project's general Durable State Rule (any code appending `.jsonl` records is durable state and
must go through a typed record/authoritative append path — satisfied here by routing through
`writer.py`).

## Parity Ledger Overlap

- **INFRA-281** (`docs/parity_ledger/infrastructure.yaml:5150`) — directly overlapping: documents
  `post_tool_hook.py` reading `execution_id`/`provider`/`ticket_id` off the `.claude/current_run`
  sidecar (built by MONITORING-WRITER-UNIFICATION, populated for real by
  TCK-20260730-CLAUDE-EXECUTION-IDENTITY) and persisting them into every `tools.jsonl` record.
  Status: `verified`, priority: `P2`. This entry documents the **Claude** side of the identity
  model this ticket must parallel for Codex — it does not need its own `status`/`v2_evidence`
  update from this ticket (this ticket does not touch `post_tool_hook.py` or `implement-ticket.js`),
  but the new adapter's own parity entry should cross-reference it as the identity-shape
  precedent it matches.
- **INFRA-273/276/281/282** and the general `TCK-20260721-MONITORING-WRITER-UNIFICATION` /
  `TCK-20260719-COST-PROXY-WRITE-PATH` entries around line 4478/4838/5150/5222 establish
  `writer.py` as the single production append implementation and `record_events.py`/
  `record_run.py`/`post_tool_hook.py` as its only current call sites — this ticket adds a fourth
  call site (the new adapter), consistent with that established pattern, not a divergence from it.
- **No existing entry** covers `agent-orchestration/hook-surface-policy.yaml` (from the
  just-landed TCK-20260730-PROVIDER-HOOK-POLICY) or this ticket's own new adapter module — grep
  across all `docs/parity_ledger/*.yaml` for "PROVIDER-HOOK-POLICY", "CODEX-POSTTOOL", and
  "hook-surface-policy" returned zero hits. **A new `infrastructure.yaml` entry (next available ID
  is `INFRA-306`, since the last entry on this branch is `INFRA-305` at line 6635) should be added
  by the Parity phase** for this ticket's own change, at `priority: P2` (matching every other
  agent-orchestration/monitoring-tooling entry in this file — none of that category is P0/P1).
  **No P0 entries are touched by this ticket** — nothing here requires a passing `test_path`
  beyond this ticket's own new tests.

## Prior Work

- `stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/` — source of the fixture this
  ticket consumes; its `investigation.md`/`plan.md` document the isolated scratch-directory
  capture methodology (Step 11) that produced `post_tool_use_stdin_capture.json`. No code
  overlap with this ticket beyond the fixture file itself.
- `stored_artifacts/TCK-20260721-MONITORING-WRITER-UNIFICATION/` — establishes `writer.py` as the
  single production append implementation this ticket must reuse (per this ticket's own Scope).
- `tools/agent_codex_pilot_guardrails/` (TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS) — closest
  sibling precedent for "real, tested, gated code with no live execution path": its
  `__init__.py` docstring pattern ("mechanisms only... no live-execution entry point... proven
  mechanically by `test_no_live_execution_path.py`"), its env-var signoff gate
  (`signoff_gate.py::require_pilot_signoff`, `CODEX_LIVE_PILOT_HUMAN_SIGNOFF`), and its
  scratch-only config toggle (`config_toggle.py`) are all directly reusable patterns/precedent
  for this ticket's own gating design (see Risks/Open Questions, Question 3 below).
- `tools/agent_replay_codex/` (TCK-20260721-CODEX-REPLAY-PARITY) — closest sibling precedent for
  a strict env-var consent gate (`consent_gate.py::require_live_consent`,
  `CODEX_REPLAY_PARITY_LIVE_CONSENT`) checked as the literal first statement before any
  subprocess/side-effecting call, and for the reusable `codex_config_guard.py` this ticket's
  AC #4 should import rather than reimplement.

## Risks and Open Questions

**RESOLVED — module location** (this ticket's own flagged open question): create a new package
at **`tools/agent_codex_posttool_adapter/`** with tests at
**`tests/agent_codex_posttool_adapter/`**. Responsibility statement: *"Parses and validates a
captured Codex `PostToolUse` hook stdin payload into the shared `tools.jsonl` record shape
(provider="codex", redacted summary fields, validated execution identity), and delegates the
actual append to `tools/agent-monitoring/writer.py`'s `write_line` — never a second append
mechanism, never invoking `codex exec` (that is `tools/agent_replay_codex/`'s responsibility),
and never governing pilot ticket-selection/rollback/signoff (that is
`tools/agent_codex_pilot_guardrails/`'s responsibility)."* This does not overlap any existing
package's stated scope:
  - `tools/agent_replay_codex/` = consent-gated **real subprocess invocation** of `codex exec`
    against fixtures, for replay/shadow-mode parity proof (`invoker.py`). It does not parse a
    real captured hook payload into a monitoring record at all.
  - `tools/agent_codex_pilot_guardrails/` = pilot **ticket-selection/rollback/signoff**
    mechanisms for a future live pilot (`__init__.py:1-13`). It has no payload-parsing code and
    explicitly has "no live-execution entry point."
  - `tools/agent-monitoring/writer.py` = the physical, provider-agnostic append primitive. It
    has no concept of "Codex" or "hook payload" at all — it just appends a pre-serialized line.

**RESOLVED — Question 3 (dead code vs. gated code)**: this ticket builds **real, tested,
importable code that is operationally inert in production by construction**, matching the exact
"capability built, live switch never left flipped" discipline `config_toggle.py`'s own docstring
states for its sibling ticket (line 6-8). It is inert for two independent, stacking reasons: (1)
nothing in the committed `.codex/config.toml` ever invokes it — AC #5 requires the proposed
activation fragment to stay unapplied, and Out of Scope explicitly forbids enabling any hook
command; (2) even if a human ran the adapter's entrypoint directly, `docs/plans/archive/
agent_infrastructure/current_codex_runtime_status_and_activation_plan.md`'s status table
confirms "Codex writes still unsupplied" — no real runtime path today generates a genuine
`provider="codex"` execution identity for it to validate and pass. This is **not** "dead code" in
the unreachable-branch sense (it is fully exercised by this ticket's own test suite against
fixtures/test doubles) — it is the same category as `tools/agent_codex_pilot_guardrails/` as a
whole: real, reachable-by-direct-call, but never wired into any live trigger path. **Recommendation
for Plan**: follow `consent_gate.py`/`signoff_gate.py`'s established pattern exactly — gate the
adapter's real-corpus-append path behind its own strict-equality env var (e.g.
`CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1`), checked as the first statement, in addition to (not
instead of) the AC's identity-field validation. Field-shape validation alone (provider/
execution_id/ticket_id) is necessary but not sufficient to match this repo's established
precedent for "an adapter is permitted to append... in an approved later runtime path" language —
every sibling live-capable module in this batch pairs identity/shape validation with an explicit,
separately-named env-var gate. This is a **design recommendation with strong precedent**, not a
blocking open question — Plan should decide the exact env var name and whether it lives in this
new package or is threaded from a caller.

**OPEN — what makes a `ticket_id` "known"?** Scope requires "a known ticket ID before an adapter
is permitted to append." No existing precedent in this exact adapter context defines "known."
Two readings are plausible and were not disambiguated by any read file: (a) format-valid only
(matches `TCK-YYYYMMDD-SHORT-SCOPE` shape), or (b) format-valid **and** a real file exists at
`tickets/inprogress/{id}.md` or `tickets/done/{id}.md` — the latter mirrors
`ticket_selection.select_pilot_candidate`'s own "load the real file, fail if absent" precedent
(`tools/agent_codex_pilot_guardrails/ticket_selection.py:14-25`) and
`assert_no_concurrent_claim`'s use of real `runs.jsonl` ticket_id values. **This should be decided
explicitly in Plan, not assumed** — it changes whether the adapter needs filesystem access to
`tickets/` at all, which affects its test isolation story.

**Risk — fixture is singular.** Only one real captured payload exists (one `Bash` tool call, one
successful outcome). The adapter's malformed/unsupported-payload handling (AC #1) and its
`tool_response`-is-an-error-string handling (mirroring `post_tool_hook.py`'s own `status`
derivation, lines 65-71) have no real-world captured counterexample to validate against —
malformed/failure-shaped fixtures must be **synthetically constructed** in this ticket's own test
suite (consistent with `test_codex_hook_payload_fixture.py`'s own scope, which only validates the
one real fixture and does not itself construct malformed variants).

## Anti-Drift Hazards

- **Do not let the adapter write to the real `agent-monitoring/*.jsonl` corpus from any default
  or test-suite code path.** Every test must inject a `tmp_path`-based target (matching
  `writer.py`'s own `target_path: Path` parameter design) — never the literal
  `Path("agent-monitoring/tools.jsonl")` default `post_tool_hook.py` hardcodes at its module
  level (line 89). A single missed default-path fallback would silently violate Out of Scope's
  "Running Codex or writing provider=codex into real agent-monitoring/*.jsonl during ordinary
  implementation/test execution."
- **Do not let AC #5's "proposed activation fragment" leak into the committed
  `.codex/config.toml`.** Any test or fixture file that constructs an enabled-hook TOML string
  must use `config_toggle.py`'s existing `_assert_scratch_target` discipline (or an equivalent
  local guard) — never write directly to the real path.
- **Do not silently pass through `tool_response` content.** The fixture's `tool_response` is a
  raw string containing real directory-listing output; a naive "copy the payload into the
  summary" implementation would violate Scope bullet 2 and the policy's `redacted_output`
  prerequisite. `post_tool_hook.py`'s own precedent (never touches `tool_response` content, only
  structurally inspects it) is the bar to match or exceed.
- **Do not widen the evidenced surface.** `enabled_surface.py`'s `EVIDENCED_HOOK_EVENTS`/
  `EVIDENCED_WRITER_FUNCTIONS` already constrain this ticket to `PostToolUse` +
  `write_line`/`write_lines` — the adapter must not introduce a second hook event or a raw
  `open(...).write(...)` append path "for convenience."
- **Do not conflate this adapter's identity-validation with `agent_codex_pilot_guardrails`'s
  ticket-selection/signoff gates.** They are structurally independent concerns in every existing
  sibling module (`signoff_gate.py`'s own docstring is explicit that ticket-selection success
  must never be mistaken for execution authorization) — the new adapter should not import from or
  delegate to `agent_codex_pilot_guardrails` for its own identity checks.
- **Do not reimplement `assert_committed_config_hook_free` or the writer's lock protocol.** Both
  already exist and are directly importable; a parallel reimplementation would violate this
  repo's own established "single implementation" precedent (`writer.py`'s own module docstring:
  "replacing 3 previously separate ad hoc implementations").
