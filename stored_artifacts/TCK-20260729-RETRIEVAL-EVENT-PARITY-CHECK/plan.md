---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK
artifact_type: plan
tags: [testing, observability, agent-monitoring]
---

# Implementation Plan — TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK

## Summary

Add a new, standalone structural/field-shape check — `tools/retrieval_event_parity_check.py` —
that asserts `tools/retrieval_events.py`'s `RETRIEVAL_EVENT_FIELDS` constant contains no
provider-specific field name (exact match or provider-token prefix/suffix), and explicitly that
`execution_id`/`provider` are absent. The module mirrors the *style* of
`tools/agent_replay_codex/provenance_check.py` (small, read-only, always-runnable, single
narrowly-scoped exception) but is structurally its own module because the artifact under test is
an in-memory schema constant, not a JSONL corpus on disk. A new test module,
`tests/tools/test_retrieval_event_parity_check.py`, adds the 5 tests from test_plan.md — two
positive checks against the real constant, a negative control with a realistic injected
provider-specific field name, a docstring/naming contract test, and a read-only/no-file-I/O
architecture guard. No existing file is modified; no new parity-ledger entry is added (see
Resolved Decisions). The check is purely additive and changes no runtime behavior.

## Resolved Decisions

These three items were flagged as open questions in investigation.md. Each is resolved here with
a stated default per the planner's mandate to not leave live design forks unresolved when the
investigation itself already supplies enough evidence to decide.

### Decision 1 — Module/exception placement: `tools/retrieval_event_parity_check.py`, NOT inside `tools/agent_replay_codex/`

Investigation.md's Risks section (lines 159-172) frames this as a fork between (a) inside
`tools/agent_replay_codex/` — matching the ticket's "Related Code Areas" listing, or (b) beside
`tools/retrieval_events.py` — matching where the actual artifact under test lives.

**Resolved: (b).** Rationale, citing investigation.md directly: `tools/agent_replay_codex/` is "a
purpose-built package for actually invoking/replaying Codex" (investigation.md line 169) — it
carries consent-gate, invoker, and shadow-mode machinery this ticket's Out of Scope explicitly
forbids importing or exercising ("No live Codex pilot execution... must never accidentally pull in
the live-Codex-pilot machinery from the sibling package it borrows *style* from," Anti-Drift
Hazards, investigation.md lines 207-212). Placing the new check inside that package — even without
calling the forbidden symbols — creates an unnecessary coupling between a pure schema-constant
assertion and a package whose other 10+ modules are about live subprocess invocation. Placing it
beside `tools/retrieval_events.py` (the actual artifact under test) keeps the dependency graph
honest: the check imports only `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS`, nothing from
`agent_replay_codex`. The new exception `ProviderFieldViolationError` is defined locally inside
`tools/retrieval_event_parity_check.py` (no new `errors.py` file — this module is small enough,
consistent with how `tools/retrieval_events.py` itself has no separate errors module) rather than
added to `tools/agent_replay_codex/errors.py`, because none of that file's 4 existing exceptions
semantically fits "a provider-specific field name was found in a schema constant"
(investigation.md lines 45-49), and adding a 5th, semantically-unrelated exception to a
Codex-package-specific `errors.py` would misfile it the same way reusing
`ContainmentViolationError` would.

### Decision 2 — No new `INFRA-298` parity ledger entry

Investigation.md's Risks section (lines 173-179) flags this as needing planner resolution.

**Resolved: no new entry.** Rationale, citing investigation.md's own precedent directly:
`TCK-20260721-CODEX-REPLAY-PARITY` — the ticket that built `provenance_check.py`/`errors.py`/
`test_monitoring_provenance.py`, the exact style this ticket mirrors, and a "substantially larger
change than this ticket" (investigation.md lines 121-127) — has **zero**
`docs/parity_ledger/infrastructure.yaml` entries referencing it. CLAUDE.md's Authoritative
Mechanics Rule requires a ledger update "if logic changes" / "if a behavior changes"; this ticket
changes no runtime behavior — it adds a read-only structural check with no effect on
`RETRIEVAL_EVENT_FIELDS`, `emit_retrieval_event()`, or any wrapper. This is the same
"support_boundary" category investigation.md's Mechanics/Engine Constraints section already
applies to `INFRA-281` through `INFRA-297`: "no simulation behavior, Mechanics Bible chapter, or
engine contract governs this module's semantics" (investigation.md lines 105-108). INFRA-297
itself (the existing entry covering `tools/retrieval_events.py`'s field-shape constant) needs no
edit — its `status`/`v2_evidence` already correctly describe the constant this ticket only reads,
never modifies.

### Decision 3 — Provider-token list: closed, explicit, documented set `{"codex", "claude", "claude-code"}`

Investigation.md's Risks section (lines 180-186) flags the exact token list as undecided beyond
the ticket's two illustrative examples (`codex_*`/`claude_*`).

**Resolved:** the check ships with a closed, explicit, documented constant,
`_KNOWN_PROVIDER_TOKENS: frozenset[str] = frozenset({"codex", "claude", "claude-code"})`, defined
in `tools/retrieval_event_parity_check.py` and passed as the default `provider_tokens` argument to
`assert_no_provider_specific_fields()`. This matches the actual provider vocabulary this repo
uses today, per `docs/architecture/agent_orchestration_contract.md:137-143`'s quoted
`execution_id` format example — `claude-code-TCK-...` — and the contract's `provider` values are
drawn from exactly `{"claude-code", "codex"}` (the two adapters named throughout that doc's
Provider-Adapter Boundary section). The check matches exact-name, prefix (`{token}_...`), and
suffix (`..._{token}`) forms, case-insensitively, so a hypothetical `codex_session_id` or
`claude_model` or `cache_status_claude` field would all be caught. The list is NOT open-ended
heuristic guessing — it is documented in the module docstring/constant comment with an explicit
note that expanding the provider vocabulary later (e.g. a third provider adapter) means updating
`_KNOWN_PROVIDER_TOKENS` too. `execution_id`/`provider` are checked as a separate, unconditional
exact-name rule (not token-matching), since neither literally contains a provider token.

## Steps

### Step 1 — Create the check module

**Files:** `tools/retrieval_event_parity_check.py` (new file)

**Change:** Create a new module with:
- A module docstring that explicitly states, in plain language, that this check is
  **structural/field-shape parity only, not live cross-provider parity**, and that no real Codex
  pilot execution occurs or is required (mirrors `provenance_check.py`'s "always-runnable
  structural invariant" framing, `provenance_check.py:1-7`, but reworded for the schema-constant
  case — do not copy the Codex-specific wording verbatim since this check involves no file I/O).
- `_KNOWN_PROVIDER_TOKENS: frozenset[str] = frozenset({"codex", "claude", "claude-code"})` — the
  closed token list from Decision 3 above, with an inline comment citing
  `docs/architecture/agent_orchestration_contract.md:137-143` and noting future expansion requires
  updating this constant.
- `class ProviderFieldViolationError(Exception):` with a docstring describing exactly what it
  means: a field name in a retrieval-event field-shape constant is `execution_id`/`provider`, or
  literally equals/starts-with/ends-with a known provider token. Defined locally in this module —
  do NOT import or subclass anything from `tools/agent_replay_codex/errors.py`.
- `def assert_no_provider_specific_fields(fields: frozenset[str], provider_tokens: frozenset[str] = _KNOWN_PROVIDER_TOKENS) -> None:`
  — iterates `fields`; raises `ProviderFieldViolationError` if any name equals `"execution_id"` or
  `"provider"` (unconditional identity-field rule), or if the lowercased name equals, starts with
  `f"{token}_"`, or ends with `f"_{token}"` for any `token` in `provider_tokens` (lowercased).
  No file I/O anywhere in this function or module — it operates purely on the in-memory
  `frozenset`/iterable passed in. No `open(`, `Path(` usage, and no `agent-monitoring` string
  literal anywhere in the file.
- No import of `tools.retrieval_events` at module scope is required (the function takes `fields`
  as a parameter, keeping it generic/reusable) — callers pass
  `tools.retrieval_events.RETRIEVAL_EVENT_FIELDS` explicitly. This keeps the check itself
  artifact-agnostic and easily reusable against future field-shape constants if any appear later.

**Do NOT touch:** `tools/retrieval_events.py` (read-only reference only, not edited — its
`RETRIEVAL_EVENT_FIELDS` constant and all 17 field names must remain byte-for-byte unchanged),
`tools/agent_replay_codex/errors.py` (no new exception added there), `tools/agent_replay_codex/provenance_check.py`
(not edited, only read for style), `tools/agent-monitoring/writer.py` (not imported, not called).

**Verify:** No test yet at this step (module is inert until Step 2 imports it); confirm via
`python3 -c "from tools.retrieval_event_parity_check import assert_no_provider_specific_fields, ProviderFieldViolationError"`
that the module imports cleanly with no side effects.

### Step 2 — Add positive-check tests against the real constant

**Files:** `tests/tools/test_retrieval_event_parity_check.py` (new file)

**Change:** Create the new test module. Start with:
- Module docstring stating this test module exercises structural/field-shape parity only.
- Imports: `from tools.retrieval_event_parity_check import assert_no_provider_specific_fields, ProviderFieldViolationError`
  and `from tools import retrieval_events as re_mod` (same import-path convention as
  `tests/tools/test_retrieval_events.py:20-27`).
- `test_field_set_contains_no_provider_specific_field()` — calls
  `assert_no_provider_specific_fields(re_mod.RETRIEVAL_EVENT_FIELDS)` and asserts it does not
  raise (e.g. call it directly with no `pytest.raises`; an uncaught exception fails the test
  naturally). This is AC1.
- `test_execution_id_and_provider_absent_from_retrieval_event_fields()` — asserts
  `"execution_id" not in re_mod.RETRIEVAL_EVENT_FIELDS` and
  `"provider" not in re_mod.RETRIEVAL_EVENT_FIELDS` directly (documents the precondition), THEN
  calls `assert_no_provider_specific_fields(re_mod.RETRIEVAL_EVENT_FIELDS)` and asserts no
  exception — proving the check function itself (not just an inline literal) confirms the
  absence. This is AC2's positive half.

**Do NOT touch:** `tests/tools/test_retrieval_events.py` — do not add to, edit, or duplicate
`TestSchemaExcludesRawTextAndIdentityFields` in that file. This new test module is additive and
lives in its own file.

**Verify:** `pytest tests/tools/test_retrieval_event_parity_check.py::test_field_set_contains_no_provider_specific_field tests/tools/test_retrieval_event_parity_check.py::test_execution_id_and_provider_absent_from_retrieval_event_fields -v`

### Step 3 — Add the negative-control test

**Files:** `tests/tools/test_retrieval_event_parity_check.py` (same file, append)

**Change:** Add
`test_negative_control_raises_when_provider_specific_field_injected()`:
- Build an in-memory fixture: `injected = frozenset(re_mod.RETRIEVAL_EVENT_FIELDS | {"codex_latency_ms"})`
  (a realistic, plausible accidental field name per investigation.md's Anti-Drift Hazards — not a
  trivially unrealistic token like `"PROVIDER_FIELD_XYZ"`).
- `with pytest.raises(ProviderFieldViolationError): assert_no_provider_specific_fields(injected)`.
- Add a second, distinct injected-fixture assertion in the same test (or a parametrized variant)
  using `"claude_cache_status"` to prove both provider tokens are caught, not just one.
- Include an explicit `isinstance`/type-identity note: the exception raised must be
  `ProviderFieldViolationError`, never `ContainmentViolationError` or a bare `Exception` — this is
  already satisfied by `pytest.raises(ProviderFieldViolationError)` since pytest requires the
  exact type (or subclass), but do not loosen this to `pytest.raises(Exception)`.

**Do NOT touch:** No fixture in this test may write to disk, use `tmp_path`, or import anything
from `tools/agent_replay_codex/`. Unlike `test_monitoring_provenance.py`'s negative control (which
needs `tmp_path` because its check reads files), this fixture is a plain in-memory `frozenset` —
using `tmp_path` here would be a style mismatch signaling scope creep toward file I/O.

**Verify:** `pytest tests/tools/test_retrieval_event_parity_check.py::test_negative_control_raises_when_provider_specific_field_injected -v`
(satisfies AC4).

### Step 4 — Add the docstring/naming-contract test

**Files:** `tests/tools/test_retrieval_event_parity_check.py` (same file, append)

**Change:** Add `test_docstring_and_test_names_state_structural_only_not_live_parity()`:
- Read `tools.retrieval_event_parity_check.__doc__` (via `import tools.retrieval_event_parity_check as parity_check_mod`
  then `parity_check_mod.__doc__`) and assert it contains a phrase equivalent to "structural" and
  "not live" / "not... cross-provider parity" (exact substrings the implementer chooses in Step 1
  — assert on the actual chosen wording, e.g. `assert "structural" in parity_check_mod.__doc__.lower()`
  and `assert "live" in parity_check_mod.__doc__.lower()`).
- Assert `assert_no_provider_specific_fields.__name__` does not contain `"live"` or imply
  execution-output comparison (e.g. assert it is not named anything containing `"output"` or
  `"execution"` — a light sanity check, not a strict allowlist).

**Do NOT touch:** Nothing else. This step only reads `__doc__`/`__name__` attributes already
established in Step 1 — if the Step 1 docstring wording doesn't satisfy this test, come back and
adjust the docstring in Step 1's file, not this test's assertions loosened to match weak wording.

**Verify:** `pytest tests/tools/test_retrieval_event_parity_check.py::test_docstring_and_test_names_state_structural_only_not_live_parity -v`
(satisfies AC3).

### Step 5 — Add the read-only/no-file-I/O architecture guard test

**Files:** `tests/tools/test_retrieval_event_parity_check.py` (same file, append)

**Change:** Add `test_check_is_read_only_and_never_touches_real_monitoring_files()`:
- `import inspect; source = inspect.getsource(tools.retrieval_event_parity_check)` (whole module,
  not just the function, to also cover the module-level constant/imports).
- Assert `"open("` not in source, `"Path("` not in source, `"agent-monitoring"` not in source.
- Assert none of `"CODEX_REPLAY_PARITY_LIVE_CONSENT"`, `"consent_gate"`, `"invoker"`,
  `"shadow_mode"` appear in source — a static grep-style guard mirroring the sibling ticket's
  AC5-style structural check (test_plan.md lines 131-136), confirming this module never pulls in
  live-Codex-pilot machinery even indirectly.

**Do NOT touch:** Nothing else — this is a pure source-inspection test, no fixtures.

**Verify:** `pytest tests/tools/test_retrieval_event_parity_check.py::test_check_is_read_only_and_never_touches_real_monitoring_files -v`

### Step 6 — Full scoped regression run

**Files:** None changed — verification only.

**Change:** Run the full scoped pytest commands from test_plan.md to confirm the new module is
green and nothing existing regressed:
```
pytest tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_wrapper_single_source.py -v
pytest tests/agent_replay_codex/ -v
pytest tests/tools/test_record_events.py tests/tools/test_monitoring_writer_single_source.py -v
pytest tests/tools/test_retrieval_event_parity_check.py -v
```
Confirm: (a) `TestSchemaExcludesRawTextAndIdentityFields` in `test_retrieval_events.py` still
passes unmodified and un-duplicated; (b) all of `tests/agent_replay_codex/` passes with zero
import-time side effects from the new module (proves Step 1's isolation from that package); (c)
the writer-path guards (`test_record_events.py`, `test_monitoring_writer_single_source.py`) are
untouched and green, confirming no new writer mechanism was introduced.

**Do NOT touch:** Do not run the full suite (`pytest tests/`) — stay scoped per CLAUDE.md's
Testing Rule and test_plan.md's explicit scoped-command list.

**Verify:** All 4 commands above exit 0. This step has no dedicated new test of its own — it is
the aggregate proof that Steps 1-5 didn't regress the Regression Surface listed in test_plan.md.

## Scope Guards

Verbatim from the ticket's Out of Scope section — none of the following may be touched by any
step in this plan:

- No live Codex pilot execution; `CODEX_REPLAY_PARITY_LIVE_CONSENT` must never be set as part of
  this work
- No `execution_id` or `provider` fields added to `runs.jsonl`/`events.jsonl` or the
  retrieval-event shape to satisfy a naive notion of parity — the check confirms their absence, it
  does not add them
- No new writer mechanism — `writer.py`'s `write_line`/`write_lines` remains the only verified
  write path
- No wiring into any `.claude/workflows/*.js` file
- No new dashboard frontend/UI surface

Additional guards derived from investigation.md's Anti-Drift Hazards:

- Do not reuse `ContainmentViolationError` for this new check — define `ProviderFieldViolationError`
  locally in the new module instead.
- Do not modify `tools/retrieval_events.py`'s `RETRIEVAL_EVENT_FIELDS` constant or any of its 17
  field names.
- Do not duplicate or fork `TestSchemaExcludesRawTextAndIdentityFields` in
  `tests/tools/test_retrieval_events.py` — the new test module is additive, in its own file.
- Do not import or exercise `tools/agent_replay_codex/consent_gate.py`, `invoker.py`, or
  `shadow_mode.py` from anywhere in the new module or its tests.
- Do not touch `tools/agent-monitoring/writer.py`.
- Do not weaken the negative-control test into a tautology — the injected field name must be
  realistic (`codex_latency_ms`, `claude_cache_status`), not an obviously-fake token.

## Dependency Map

- Step 1 has no dependencies (module is self-contained, reads nothing at import time beyond
  stdlib).
- Steps 2-5 all depend on Step 1 (they import `tools.retrieval_event_parity_check`) but are
  otherwise independent of each other — each appends a distinct test function to the same file and
  can be implemented/verified in any order after Step 1, though the numbered order above is
  recommended since it follows AC1 → AC2 → AC4 → AC3 → architecture-guard sequencing for a clean
  incremental diff.
- Step 6 depends on Steps 1-5 all being complete (it is the aggregate regression check).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: test asserts the new retrieval-event field-name set contains no field literally naming or prefixing a single provider | Step 1 (function), Step 2 | `test_field_set_contains_no_provider_specific_field` |
| AC2: check/module explicitly asserts `execution_id`/`provider` are absent, fails loudly if present | Step 1 (unconditional identity-field rule + `ProviderFieldViolationError`), Step 2, Step 3 | `test_execution_id_and_provider_absent_from_retrieval_event_fields` (positive), `test_negative_control_raises_when_provider_specific_field_injected` (loud-failure proof) |
| AC3: docstring/test names state structural/field-shape parity only, not live cross-provider parity | Step 1 (docstring wording), Step 4 | `test_docstring_and_test_names_state_structural_only_not_live_parity` |
| AC4: negative-control test proves the check raises when a provider-specific field is deliberately injected | Step 3 | `test_negative_control_raises_when_provider_specific_field_injected` |

## Anti-Drift Notes

- The artifact under test is an **in-memory schema constant**, not a JSONL corpus — the new check
  function must take zero file-path arguments and perform zero file I/O (enforced by Step 5's
  source-inspection test). Do not generalize `assert_no_codex_provider_writes()` by adding a
  file-reading branch to it or to the new function; they are structurally different checks by
  design (investigation.md lines 39-43).
- `tests/tools/test_retrieval_events.py`'s existing `TestSchemaExcludesRawTextAndIdentityFields`
  class already inline-asserts `execution_id`/`provider` absence but is not reusable and has no
  negative control (investigation.md lines 61-86) — this plan's Step 2/3 must produce a genuinely
  new, importable, negative-control-tested check, not a restatement of that existing coverage.
  Step 6's regression run is the checkpoint that catches accidental duplication.
- `TCK-20260721-CODEX-REPLAY-PARITY` (zero `infrastructure.yaml` entries despite being a larger
  change) is the load-bearing precedent for Decision 2 (no new ledger entry) — if a future
  reviewer questions this, point to that ticket, not to a general rule, since CLAUDE.md's default
  posture is "add one if no entry exists for a behavior change" and this ticket's exemption rests
  specifically on "no behavior changes" plus that direct precedent.
- The provider-token list (`codex`, `claude`, `claude-code`) is a closed set anchored to
  `docs/architecture/agent_orchestration_contract.md`'s actual adapter vocabulary — if a third
  provider adapter is added to the repo in a future ticket, `_KNOWN_PROVIDER_TOKENS` in
  `tools/retrieval_event_parity_check.py` must be updated in that future ticket; this plan does
  not attempt to future-proof the list with a heuristic.
