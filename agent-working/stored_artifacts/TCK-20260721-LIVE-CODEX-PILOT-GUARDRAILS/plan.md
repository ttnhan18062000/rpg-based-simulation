---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS
artifact_type: plan
tags: [ai, workflows, hooks, rollback]
---

# Implementation Plan — TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Summary

This plan builds a new, self-contained `tools/agent_codex_pilot_guardrails/` package (following the
batch's established one-ticket-one-package convention) delivering five independent guardrail
mechanisms — typed human-owner/rollback-plan manifest + loader, ticket-selection rejection rules
(missing owner/rollback-plan, concurrent same-work claim), an evidenced-subset guard for the
enabled hook/writer surface, a pre/post baseline-manifest fail-closed gate (reusing
`tools/agent-monitoring/manifest.py` unmodified), a scratch-only config enable/disable toggle with a
zero-byte-diff rollback proof, and a human sign-off gate distinct from and later than ticket
selection — plus an architecture-guard test proving the package has no live-execution entry point at
all. Every mechanism is built, tested, and left inert: the committed `.codex/config.toml` stays
hook-free, no real ticket is ever run through Codex, and this ticket's own scope-boundary text (AC #7)
is asserted mechanically, not just documented. Four decisions flagged by investigation.md are resolved
directly in this plan (see the four decision notes embedded in Steps 1, 3, 4, and 5) rather than left
open, per the main session's instruction that they be settled before Implement begins.

## Steps

### Step 1 — Package scaffold, typed exceptions, and the pilot-request manifest (AC #1, part 1)

**Files:**
- `tools/agent_codex_pilot_guardrails/__init__.py` (new, empty except a module docstring stating
  this package builds guardrail/rollback/sign-off *mechanisms only* — no live-execution entry point;
  reinforces AC #7 in code, not just in this plan/ticket)
- `tools/agent_codex_pilot_guardrails/errors.py` (new) — one file for all of this package's
  exceptions, mirroring `tools/agent_replay_codex/errors.py`'s own stated convention:
  - `PilotManifestValidationError` — raised by the manifest loader on a missing file or a
    missing/empty `human_owner`/`rollback_plan_summary` field
  - `MissingHumanOwnerError(PilotManifestValidationError)`
  - `MissingRollbackPlanError(PilotManifestValidationError)`
  - `ConcurrentProviderClaimError(Exception)`
  - `EnabledSurfaceExceedsEvidenceError(Exception)`
  - `PilotManifestDriftError(Exception)`
  - `PilotSignoffNotGrantedError(Exception)`
  - `PilotConfigToggleGuardError(Exception)` (refuses to target the real committed config)
  - `PilotRollbackVerificationError(Exception)`
- `tools/agent_codex_pilot_guardrails/pilot_manifest.py` (new) — **DECISION (resolves
  investigation.md Risk #2 / open question #2, per this plan's authority — not deferred):** define a
  frozen dataclass `PilotRequest(ticket_id: str, human_owner: str, rollback_plan_summary: str)` plus
  `load_pilot_request(path: Path) -> PilotRequest`, which parses a YAML file and raises
  `MissingHumanOwnerError`/`MissingRollbackPlanError` if the respective field is absent or empty/
  whitespace-only after `.strip()`. Do **not** extend the universal ticket template/frontmatter
  schema (`CLAUDE.md`'s Ticket Format, `tools/ticket_field_values.py`) — that is a repo-wide change
  affecting every ticket and is out of this ticket's scope. Instead, storage convention (documented
  in this module's own docstring): one YAML file per candidate at
  `pilot_requests/<ticket_id>.yaml`, a **new, dedicated top-level directory** — justified because
  (a) `stored_artifacts/{ticket_id}/` is that ticket's *own* build artifacts, migrated only after
  *that* ticket closes, and is semantically wrong for "a human's standing authorization record about
  a *different*, not-yet-selected candidate ticket"; (b) `staging_artifacts/{ticket_id}/` is
  this-ticket's-own in-flight artifacts, same mismatch; (c) a new top-level directory gives the
  record its own stable location, lifecycle (authored by a human before pilot selection ever runs,
  independent of any one ticket's phase), and inspection visibility (`ls pilot_requests/`), matching
  the Durable State Rule's requirements without hijacking an existing directory's meaning.
- `pilot_requests/README.md` (new) — documents the YAML schema (`ticket_id`, `human_owner`,
  `rollback_plan_summary`, all required non-empty strings) and the loader contract. No real
  candidate `.yaml` file is added here — investigation.md confirmed no real pilot candidate is named
  anywhere in this repo, and this tooling must stay ticket-agnostic (resolves Risk #6: built to
  evaluate *any* candidate, never hardcoded to one).
- `tests/agent_codex_pilot_guardrails/__init__.py` (new, empty)
- `tests/agent_codex_pilot_guardrails/test_pilot_manifest.py` (new)

**Change:** Implement `PilotRequest`, `load_pilot_request`, and the error hierarchy exactly as
above. The loader must be a strict fail-clear check — no default/fallback value, no coercion of a
missing field to `""`-then-pass.

**Do NOT touch:** `CLAUDE.md`'s Ticket Format section; `tools/ticket_field_values.py`;
`tools/validate_frontmatter.py`; any existing ticket file (no ticket is retrofitted with owner/
rollback fields as part of this step).

**Verify:** New test file covers: (a) a well-formed fixture YAML (built inline via `tmp_path` in the
test, not a checked-in fixture under `pilot_requests/`) with both fields present loads successfully
into a `PilotRequest`; (b) owner present/rollback-plan absent → `MissingRollbackPlanError`; (c)
rollback-plan present/owner absent → `MissingHumanOwnerError`; (d) a fixture whose free-text body
*mentions* "owner" or "rollback" in prose without the structured YAML fields still raises — proving
the check reads structured data, not keyword-greps ticket prose (per test_plan.md's Anti-Drift Test
Guards). This is the manifest-loading half of test_plan.md's New Test #1.

---

### Step 2 — Ticket-selection step: owner/rollback-plan gate + concurrent-claim gate (AC #1, AC #2)

**Files:**
- `tools/agent_codex_pilot_guardrails/ticket_selection.py` (new)
- `tests/agent_codex_pilot_guardrails/test_ticket_selection.py` (new)
- `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py` (new)

**Change:**
1. `select_pilot_candidate(ticket_id: str, pilot_requests_dir: Path) -> PilotRequest` — calls
   `pilot_manifest.load_pilot_request(pilot_requests_dir / f"{ticket_id}.yaml")`; if the file itself
   is missing, raise `PilotManifestValidationError` (not a bare `FileNotFoundError`) naming the
   ticket_id, so the rejection is always a named, catchable result per test_plan.md's requirement
   ("not a silent pass, not a generic exception"). `pilot_requests_dir` is an injected parameter
   (never hardcoded to the real `pilot_requests/`) so tests point it at `tmp_path`.
2. `assert_no_concurrent_claim(ticket_id: str, run_records: list[dict]) -> None` — given a list of
   dicts shaped like `agent-monitoring/runs.jsonl` records (each with at minimum `ticket_id`,
   `provider`, `end_ts` — `end_ts` absent/`None` meaning in-progress), raises
   `ConcurrentProviderClaimError` if two or more records for the same `ticket_id` with no `end_ts`
   carry two *different* `provider` values.
3. `provider_field_coverage(agent_monitoring_dir: Path) -> int` — **DECISION (resolves
   investigation.md Risk #3):** streams the real `agent-monitoring/runs.jsonl` (line-lazy, mirroring
   `manifest.py::_scan_file`'s streaming technique — never a full read) and counts records that carry
   a non-null `provider` key. This function exists specifically so a test can assert the real corpus
   currently has zero `provider`-bearing records, making the gap visible rather than silently
   assumed away. `assert_no_concurrent_claim` itself is proven only against **synthetic** fixture
   `run_records` lists constructed in-test — it is not, and does not claim to be, validated against
   real production data today. This is documented as a real, currently-unexercised-by-real-traffic
   limitation, not fixed here: populating `provider`/`execution_id` in
   `.claude/workflows/implement-ticket.js` is explicitly out of this ticket's scope (a separate,
   not-yet-filed ticket's work per the one-ticket-one-concern convention).

**Do NOT touch:** `.claude/workflows/implement-ticket.js` (must not be edited to start populating
`provider`/`execution_id` — that is the exact scope-creep this plan's Risk #3 resolution forbids);
`tools/agent-monitoring/record_run.py`, `record_events.py`, `writer.py` (read-only consumption via
streaming scan only, in `provider_field_coverage`, never a write).

**Verify:** `test_ticket_selection.py` implements test_plan.md New Test #1's selection-step half
(positive case + two independent negative cases via `select_pilot_candidate`).
`test_concurrent_claim.py` implements New Test #2: synthetic two-provider-same-ticket_id fixture →
`ConcurrentProviderClaimError`; a companion test calls `provider_field_coverage` against the real
`agent-monitoring/runs.jsonl` and asserts it returns `0` today, with an inline comment stating this
proves the check currently has no real signal to validate against (per test_plan.md's Anti-Drift
Test Guards — "must not be allowed to quietly pass as a false proof of real-world coverage").

**Dependency:** requires Step 1 (`pilot_manifest.py`, `errors.py`).

---

### Step 3 — Enabled hook-event/writer-function evidenced-subset guard (AC #3)

**Files:**
- `tools/agent_codex_pilot_guardrails/enabled_surface.py` (new)
- `tests/agent_codex_pilot_guardrails/test_enabled_surface.py` (new)

**Change:** Define two module-level frozensets sourced from the investigation's direct-read trace
(not re-derived at runtime, since no existing file declares the *evidenced* — as opposed to
*schema-valid* — subset in one place; investigation.md Risk #5, resolved here):
```python
EVIDENCED_HOOK_EVENTS: frozenset[str] = frozenset({"PostToolUse"})
EVIDENCED_WRITER_FUNCTIONS: frozenset[str] = frozenset({"write_line", "write_lines"})
```
Also load `agent-orchestration/hook-events.yaml` (read-only) and assert
`EVIDENCED_HOOK_EVENTS <= {t["id"] for t in hook_types}` at import time or via a dedicated
`assert_evidenced_events_are_schema_valid()` function — this cross-checks the evidenced set against
the *broader* schema-declared vocabulary (which also includes `PreToolUse`, never fixture-captured
for Codex), without conflating "schema-valid" with "evidenced." Provide
`assert_enabled_surface_subset(enabled_hook_events: frozenset[str], enabled_writer_names: frozenset[str]) -> None`
raising `EnabledSurfaceExceedsEvidenceError` if either argument is not a subset of the corresponding
evidenced constant.

**Do NOT touch:** `agent-orchestration/hook-events.yaml` itself (read-only; that file is owned by
`ORCHESTRATION-CONTRACT-CORE`, never edited here); `tools/agent-monitoring/writer.py` (read-only —
only its function *names* are referenced as string constants, no import of the module's internals
beyond what's needed to prove the names exist, if the implementer chooses to assert
`hasattr(writer_module, name)` for extra rigor).

**Verify:** New Test #3 — asserts `EVIDENCED_HOOK_EVENTS == {"PostToolUse"}`,
`EVIDENCED_WRITER_FUNCTIONS == {"write_line", "write_lines"}`; a passing case with a subset input; a
failing case where `enabled_hook_events` includes `"PreToolUse"` (schema-valid but not evidenced) →
`EnabledSurfaceExceedsEvidenceError`, proving this is a real subset assertion, not a hardcoded
equality check that trivially passes.

**Dependency:** requires Step 1 (`errors.py`). Independent of Steps 2, 4, 5, 6.

---

### Step 4 — Pre/post baseline-manifest fail-closed gate (AC #4)

**Files:**
- `tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py` (new)
- `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py` (new)

**Change:** **DECISION (resolves investigation.md Risk #4 — the AC #4 "hash changes" vocabulary
mismatch):** the gate's enforced check is `tools/agent-monitoring/manifest.py::assert_prefix_preserved`,
reused unmodified via direct import (this package has no hyphen in its own name, but
`tools/agent-monitoring` does — mirror `tools/agent_replay_codex/containment.py`'s own
`importlib.util.spec_from_file_location` technique to load it, do not attempt a dotted-path import).
This plan explicitly documents *why* prefix-preservation, not a naive whole-file hash-diff, is the
correct interpretation of AC #4's "fails closed if any pre-existing line's hash changes": a legitimate
pilot run **appends** new lines to `agent-monitoring/*.jsonl` between the pre- and post-snapshot,
which necessarily changes any naive whole-file SHA-256 (`manifest.py::build_manifest()`'s hash field)
even when nothing pre-existing was touched — a literal whole-file-hash-equality gate would falsely
reject every successful pilot run. `assert_prefix_preserved` is therefore not a looser substitute for
"hash changes" but the *stricter, mechanically correct* implementation of the AC's intent (reject
rewrite/reorder/deletion of anything pre-existing; tolerate only new appended lines) — it subsumes
what a correct hash-based check would need to detect, while additionally localizing which file broke.
`build_manifest()`'s whole-file hash is retained only as an optional diagnostic log field in this
gate's wrapper (never asserted equal), for operators who want the coarser signal too.

Implement:
```python
def capture_pilot_baseline(agent_monitoring_dir: Path) -> dict[str, list[str]]:
    ...  # thin wrapper around the dynamically-loaded capture_lines
def assert_pilot_baseline_preserved(pre: dict, post: dict) -> None:
    ...  # calls assert_prefix_preserved, catches AssertionError, raises PilotManifestDriftError
```

**Do NOT touch:** `tools/agent-monitoring/manifest.py` itself (consumed via import only, per the
ticket's own Out-of-Scope line — zero edits); do not re-implement `capture_lines`/
`assert_prefix_preserved`'s logic from scratch.

**Verify:** New Test #4 — round-trip against a `tmp_path` copy of a small synthetic
`agent-monitoring/` directory (three `.jsonl` files with a few lines each): (a) positive case —
append-only change between pre/post → no raise; (b) **negative control** — deliberately mutate one
pre-existing line in the `tmp_path` copy between snapshots → `assert_pilot_baseline_preserved` raises
`PilotManifestDriftError` (the wrapper's own typed error, proving the *wrapper*, not just the
underlying `manifest.py` function, is under test, per test_plan.md's explicit requirement).

**Dependency:** requires Step 1 (`errors.py`). Independent of Steps 2, 3, 5, 6.

---

### Step 5 — Config toggle mechanism (scratch-only) + rollback zero-byte-diff proof (AC #5)

**Files:**
- `tools/agent_codex_pilot_guardrails/config_toggle.py` (new)
- `tests/agent_codex_pilot_guardrails/test_config_rollback.py` (new)

**Change:** **DECISION (resolves investigation.md Risk #1 — the `.codex/config.toml` comment's
"owns actually wiring a production hook" tension):** build the enable/disable **mechanism** as code —
a function capable of producing a hook-registered config when explicitly invoked — while the
*committed* `.codex/config.toml` at this ticket's close remains byte-identical to its current
hook-free state. This is the same "capability built, live switch never left flipped" discipline every
sibling ticket in this batch already follows (see `tests/agent_orchestration_codex_adapter/
test_no_production_hook_enabled.py` and `tests/agent_orchestration_claude_adapter/
test_no_codex_scope_creep.py::test_no_production_hook_registered_in_codex_config`, both of which this
step's own tests must not regress). Concretely:
```python
def render_enabled_config(base_toml_bytes: bytes) -> bytes:
    # appends the empirically-discovered [[hooks.PostToolUse]] / [[hooks.PostToolUse.hooks]] block
    # (recorded in stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/) to base_toml_bytes
def _assert_scratch_target(path: Path, repo_root: Path) -> None:
    # raises PilotConfigToggleGuardError if path resolves to repo_root/.codex/config.toml
def enable(scratch_config_path: Path, repo_root: Path) -> None:
    _assert_scratch_target(scratch_config_path, repo_root)
    ...  # writes render_enabled_config(scratch_config_path.read_bytes()) to scratch_config_path
def disable(scratch_config_path: Path, repo_root: Path, baseline_bytes: bytes) -> None:
    _assert_scratch_target(scratch_config_path, repo_root)
    scratch_config_path.write_bytes(baseline_bytes)  # restores exact pre-enable bytes, never a delete
```
Also add a narrow rollback-scope snapshot (AC #5's own wording is scoped to "agent-monitoring/*.jsonl
and the pilot ticket file" — one specific file, not all of `tickets/`, so this is intentionally
narrower than reusing `tools/agent_replay_codex/containment.py` verbatim, matching investigation.md's
own recommendation):
```python
def snapshot_rollback_scope(agent_monitoring_dir: Path, pilot_ticket_path: Path) -> dict[str, str]:
    # sha256 of each of runs.jsonl/events.jsonl/tools.jsonl + pilot_ticket_path, whole-file
    # (strict hash-equality IS correct here, unlike Step 4 — the rollback drill must leave these
    # files completely untouched, not merely append-safe)
def assert_rollback_scope_unchanged(pre: dict[str, str], post: dict[str, str]) -> None:
    # raises PilotRollbackVerificationError on any mismatch
```
Reuse `tools/agent_replay_codex/codex_config_guard.py::snapshot_config_bytes`/
`assert_config_bytes_unchanged` directly (import, not reimplement) for the config-bytes-unchanged
half of the round trip.

**Do NOT touch:** the real, committed `.codex/config.toml` — every test in this step operates on a
`tmp_path` copy; `tools/agent_replay_codex/codex_config_guard.py` itself (import-only, zero edits).

**Verify:** New Test #5 — full round trip against a `tmp_path` scratch config: capture baseline bytes
→ `enable()` → assert the scratch file now contains a `hooks` key (proves the toggle is real and
capable, not a no-op) → `snapshot_rollback_scope` + `codex_config_guard.snapshot_config_bytes` taken
pre-disable → `disable()` → assert zero bytes differ across the rollback scope AND
`assert_config_bytes_unchanged` on the config restoring exactly the pre-enable baseline. A
session-scoped fixture (or a final assertion in this test module) additionally calls
`codex_config_guard.assert_committed_config_hook_free(repo_root)` against the *real* repo root to
prove this step's own test run never touched the real file — satisfies test_plan.md's Anti-Drift
Test Guards requirement to verify this at the test-suite level, not just inside one test.

**Dependency:** requires Step 1 (`errors.py`). Independent of Steps 2, 3, 4, 6.

---

### Step 6 — Human sign-off gate, distinct from and later than ticket selection (AC #6)

**Files:**
- `tools/agent_codex_pilot_guardrails/signoff_gate.py` (new)
- `tests/agent_codex_pilot_guardrails/test_signoff_gate.py` (new)

**Change:** Mirror `tools/agent_replay_codex/consent_gate.py::require_live_consent`'s pattern exactly
(strict env-var equality, no truthy coercion, checked as the first statement, zero dependency on
`subprocess`) with its own distinct env var:
```python
PILOT_SIGNOFF_ENV_VAR = "CODEX_LIVE_PILOT_HUMAN_SIGNOFF"
def require_pilot_signoff(env: Mapping[str, str] | None = None) -> None:
    if env is None:
        env = os.environ
    if env.get(PILOT_SIGNOFF_ENV_VAR) != "1":
        raise PilotSignoffNotGrantedError(...)
```
Critically, this function takes **no arguments derived from `select_pilot_candidate`'s result** — it
is a structurally independent gate, not a second call site reusing the selection step's return value,
so that "ticket-selection succeeded" can never be mistaken for "human signed off on execution."

**Do NOT touch:** `tools/agent_replay_codex/consent_gate.py` (pattern reused by re-implementation
with a new env var, not by import — this ticket's own gate is conceptually distinct: pre-*designation*
consent to run replay tooling at all, versus pre-*execution* authorization for one specific pilot, per
investigation.md's own distinction).

**Verify:** New Test #6 — (a) unset/wrong-value env → `PilotSignoffNotGrantedError`; (b)
`env={PILOT_SIGNOFF_ENV_VAR: "1"}` → no raise; (c) an explicit test asserting that calling
`select_pilot_candidate` successfully (Step 2) followed by *not* calling `require_pilot_signoff` at
all still leaves no code path that proceeds — i.e., the two gates are asserted as independently
invoked, not one gate whose result the other silently trusts.

**Dependency:** requires Step 1 (`errors.py`). Independent of Steps 2–5.

---

### Step 7 — No-live-execution-path architecture guard + scope-boundary self-assertion (AC #7)

**Files:**
- `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` (new, test-only — no new
  production code)

**Change:** An AST/import-graph scan over every `.py` file in `tools/agent_codex_pilot_guardrails/`,
mirroring `tests/agent_orchestration/test_validator_no_network_calls.py`'s existing
`_SCOPE_CREEP_MARKERS` pattern, asserting:
- no file in the package imports `tools.agent_replay_codex.invoker` (static `Import`/`ImportFrom`
  nodes)
- no file calls `importlib.util.spec_from_file_location` or `importlib.import_module` with any
  string argument (literal or f-string) containing `"invoker"` or `"agent_replay_codex"` — this
  package's own Step 4 already normalizes dynamic module loading via
  `importlib.util.spec_from_file_location` (mirroring `tools/agent_replay_codex/containment.py`'s
  real precedent) as the idiomatic way to load a module without a static `import` statement, so the
  static-import check alone would miss a hidden entry point using that same already-idiomatic
  technique to reach `invoker.py`
- **no file anywhere in the package calls `subprocess.run`, `subprocess.Popen`, `subprocess.call`,
  `subprocess.check_call`, `subprocess.check_output`, or `os.system` — full ban, not scoped to calls
  containing the literal string `"codex"`.** Nothing in Steps 1–6 has any legitimate reason to spawn
  a subprocess at all, so a blanket ban is strictly stronger than a substring-matched one and closes
  the indirection gap where a binary name supplied via an env var, string concatenation, or a
  config-assembled argument list would never contain the literal substring `"codex"` in source and
  would otherwise slip through a substring check
- the package exposes no function whose name matches `run_pilot`/`execute_pilot`/`invoke_codex` or
  similar execution-shaped verbs (a simple denylist substring check on top-level function names is
  sufficient — this is a guard against accidental scope creep, not a general-purpose linter)

Also assert, in the same test module, that the real committed `.codex/config.toml` is still
hook-free at collection time, via `tools.agent_replay_codex.codex_config_guard.assert_committed_config_hook_free(repo_root)`
— a second, independent confirmation beyond Step 5's own suite-level check.

**Do NOT touch:** anything under `tools/agent_codex_pilot_guardrails/` — this step adds no
production code, only a guard test. If this test ever needs to *pass* by deleting/renaming an
existing legitimate function to dodge the denylist, that is a signal the function itself is
out-of-scope, not that the test should be loosened.

**Verify:** the test itself, run clean against the completed package from Steps 1–6. This is also
the mechanical, code-level assertion of AC #7 (the ticket's own scope-boundary claim), distinct from
—and in addition to— the ticket-file/plan-file prose already stating the boundary.

**Dependency:** requires Steps 1–6 to exist (it scans their files). Must be implemented and run
**last**.

---

## Scope Guards

Explicit list of things this plan must not touch, derived from the ticket's Out of Scope section and
investigation.md's Anti-Drift Hazards:

- **No live pilot execution in any form.** No step in this plan adds a code path that actually
  invokes `codex exec` or any real Codex subprocess against any real ticket. Step 7 mechanically
  enforces this.
- **No committed hook wiring.** `.codex/config.toml` in the repo at ticket close must be
  byte-identical to its current content (verified by Step 5's suite-level check and Step 7's
  independent re-check). The enable/render mechanism built in Step 5 is exercised only against
  `tmp_path` scratch copies.
- **No rewrite/deletion of historic JSONL records.** Rollback logic (Step 5) never truncates,
  rewrites, or deletes `agent-monitoring/*.jsonl` — `disable()` only ever restores previously-captured
  baseline bytes of the *config* artifact; it never touches the monitoring corpus at all except to
  read it for the zero-diff proof.
- **No re-implementation of `tools/agent-monitoring/manifest.py`.** Step 4 imports
  `capture_lines`/`assert_prefix_preserved` unmodified.
- **No edits to any predecessor ticket's package**: `tools/agent-monitoring/*.py`,
  `tools/agent_replay_codex/*.py`, `tools/agent_orchestration_codex_adapter/*.py`,
  `tools/agent_orchestration_claude_adapter/*.py`, `tools/agent_orchestration/*.py`,
  `agent-orchestration/*.yaml`/`*.md` — all consumed by import/read only.
- **No edits to `.agents/`, `.claude/workflows/*.js`, `.claude/agents/*.md`, `.claude/skills/*`,
  `CLAUDE.md`.** The pilot-manifest design (Step 1) does not require touching `CLAUDE.md`'s Ticket
  Format — it deliberately avoids that route (see Step 1's decision note) precisely so this
  constraint holds without needing an exception.
- **No population of `provider`/`execution_id`/`ticket_id` in `.claude/workflows/implement-ticket.js`.**
  Step 2's `provider_field_coverage` only *reads and reports* the current gap; it does not fix it.
- **No expansion of the universal ticket template/frontmatter schema** — the pilot-manifest structure
  (Step 1) is a new, separately-scoped sidecar artifact, not a `## Owner`/`## Rollback Plan` ticket
  body field.
- **No hardcoded real pilot-candidate ticket ID** anywhere in production code — all selection logic
  (Step 2) is ticket-agnostic, taking `ticket_id` as a parameter.
- **`pytest tests/` must never be run** — use the scoped commands in test_plan.md's "Scoped Pytest
  Commands" section, plus `pytest tests/agent_codex_pilot_guardrails/ -v` for this ticket's own new
  suite.

## Dependency Map

- Step 1 — no dependencies (foundation: errors.py, pilot_manifest.py).
- Step 2 — depends on Step 1.
- Step 3 — depends on Step 1 only (independent of Steps 2, 4, 5, 6).
- Step 4 — depends on Step 1 only (independent of Steps 2, 3, 5, 6).
- Step 5 — depends on Step 1 only (independent of Steps 2, 3, 4, 6).
- Step 6 — depends on Step 1 only (independent of Steps 2, 3, 4, 5).
- Step 7 — depends on Steps 1–6 (scans the completed package); must run last.

Steps 2–6 may be implemented and verified in any order relative to each other once Step 1 lands.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — selection rejects candidates lacking recorded human owner and rollback plan, verified against actual ticket/run state | Step 1 (`pilot_manifest.py`), Step 2 (`ticket_selection.select_pilot_candidate`) | `tests/agent_codex_pilot_guardrails/test_pilot_manifest.py`, `test_ticket_selection.py` |
| AC #2 — selection rejects a candidate concurrently claimed by both providers | Step 2 (`ticket_selection.assert_no_concurrent_claim`, `provider_field_coverage`) | `tests/agent_codex_pilot_guardrails/test_concurrent_claim.py` |
| AC #3 — only Phase-2/Phase-3-evidenced hook events registered; test enumerates subset | Step 3 (`enabled_surface.py`) | `tests/agent_codex_pilot_guardrails/test_enabled_surface.py` |
| AC #4 — pre/post baseline manifests captured and diffed; fails closed on pre-existing line change | Step 4 (`baseline_manifest_gate.py`) | `tests/agent_codex_pilot_guardrails/test_baseline_manifest_gate.py` |
| AC #5 — Codex-adapter disable via single config/flag flip; zero-byte-diff test | Step 5 (`config_toggle.py`) | `tests/agent_codex_pilot_guardrails/test_config_rollback.py` |
| AC #6 — explicit programmatically-checked human sign-off gate, distinct from and later than ticket designation | Step 6 (`signoff_gate.py`) | `tests/agent_codex_pilot_guardrails/test_signoff_gate.py` |
| AC #7 — ticket's own scope explicitly states live execution stays blocked; only guardrail/rollback/sign-off design-and-build is in scope now | Already true of the ticket file text (confirmed verbatim in investigation.md); mechanically enforced by Step 7 | `tests/agent_codex_pilot_guardrails/test_no_live_execution_path.py` |

## Anti-Drift Notes

- **This is "the only concern touching genuinely irreversible-risk territory" in the whole 7-ticket
  batch** (the ticket's own Request Summary). Step 7's guard test is the single most important test
  in this plan — do not weaken, skip, or defer it.
- **All 5 hard predecessors and the `.agents/skills/` quarantine gate are confirmed landed** — this
  unblocks *building* the guardrails (this plan), never *executing* a live pilot. Nothing in this
  plan changes that; do not read "preconditions satisfied" as license to add an execution path.
- **The concurrent-claim check (Step 2) is real, tested code that is currently unexercised by real
  production data** — `provider_field_coverage` exists specifically to keep this honest. Do not let a
  green test suite be read as proof the check works against live traffic; the companion test against
  the real `agent-monitoring/runs.jsonl` returning `0` is the documentation of that gap, not a bug to
  "fix" by fabricating `provider` values in real records.
- **AC #4's "hash changes" wording is deliberately reinterpreted, with justification recorded in Step
  4**, as prefix-preservation rather than whole-file hash-equality — because whole-file hash-equality
  would be *incorrect* here (it would reject every legitimate append). If a future reviewer questions
  this, point to Step 4's decision note, not just "manifest.py already does it this way."
- **The known pre-existing failure** `tests/agent_orchestration/test_contract_structure.py::test_contract_yaml_has_versioning_field_and_documented_scheme`
  (tracked by `tickets/todos/TCK-20260722-CONTRACT-STRUCTURE-TEST-STALE-PATH.md`) is not this
  ticket's to fix — if still failing at Verify, report it explicitly as pre-existing/unrelated in the
  ticket's own Test Summary, per every predecessor ticket's precedent.
- **`pilot_requests/README.md` (Step 1) is documentation of a convention, not a live registry entry**
  — do not populate it with a real candidate ticket's data as part of this ticket; that would be
  scope creep into designating an actual pilot, which this ticket does not do (confirmed: no
  candidate is named anywhere in the batch).

## Deviations

None from the production-code design. All 7 steps' function signatures, error hierarchy, file
paths, and Do-NOT-touch lists were implemented exactly as specified above.

One test-fixture-shape correction during Step 5's own test-writing (not a deviation from this
plan's `config_toggle.py` design, which was implemented exactly as written and never changed): the
first draft of `test_config_rollback.py`'s round-trip test built a scratch "fake repo" whose
`.codex/config.toml` lived at a path structurally identical to the real repo's own relative layout,
then passed that fake repo itself as the `repo_root` argument to `enable`/`disable`. This made
`_assert_scratch_target` correctly refuse the target, since `repo_root/.codex/config.toml`
trivially resolved to the scratch file being operated on — confirming the guard function works
exactly as designed, not exposing a design flaw. The fix was to the test fixture only: `repo_root`
is always the real project root (as every real caller would pass, matching every other step's own
`repo_root`-is-the-real-root convention), and the scratch config file lives at an unrelated path
never nested under a `.codex/` directory. `config_toggle.py`'s implementation required zero
changes.
