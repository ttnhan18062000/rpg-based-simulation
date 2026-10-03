---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP
phase: done
date: 2026-09-23
tags: [agent-monitoring, data-quality]
---

# TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP

## Title
Register `architecture-reviewer-shadow`/`security-reviewer-shadow` agent literals to fix the
vocabulary-drift ratchet CI failure caused by shadow-reviewer collection going default-on

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
PR #241 (branch `status-vocabulary-reconciliation`, containing
`TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` and `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION`)
is failing CI job "API / tools / logging" on
`tests/tools/test_monitoring_anomaly_validator.py::test_real_corpus_is_at_or_below_every_ratchet_ceiling`
and `::test_cli_prints_marker_output_not_merely_a_return_code`. Root cause confirmed by direct
investigation, not the fault of either ticket in PR #241: `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON`
(PR #240, merged onto `main` at `75ab942b4`) flipped `implement-ticket.js`'s shadow-reviewer
collection from opt-in to opt-out (default-on) for the Architecture-Verify and Security-Review
phases. Every ticket that now goes through those phases emits an agent-monitoring event with
agent literal `"architecture-reviewer-shadow"` (and, for security-tagged tickets,
`"security-reviewer-shadow"`) — grep-confirmed real literals at
`.claude/workflows/implement-ticket.js:1074`/`:1099` (Architecture-Verify shadow block) and
`:1519`/`:1539` (Security-Review shadow block). Neither literal was ever added to
`tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` canonical set.
`tools/gate_checks/monitoring_anomaly_validator.py`'s `check_vocabulary_drift()`
(`AGENT_DRIFT_CEILING = 162`, docstring: "May only decrease") now measures 164 real corpus
occurrences — the +2 traced by diffing `agent-monitoring/data/2026-W39/events.jsonl` between
`origin/main` (`75ab942b4`) and the PR branch tip (`25b159b49`): exactly 2 new
`"architecture-reviewer-shadow"` events, one per ticket in this PR's Architecture-Verify phase,
nothing else new. This file's own docstring establishes the exact precedent for this situation:
six prior literals (`orchestrator`, `context-packet-wrapper`, `concern-investigator`,
`implement-ticket`, `implement-epic`, `write-sequence`) were "registered there instead of ratcheted
here" when `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` found the ratchet was measuring registry
gaps, not real drift — a legitimate new agent literal gets registered in `vocabulary.py`
(removing it from the drift count), not fixed by raising the ceiling (which the module's own
docstring explicitly forbids). Since shadow-reviewer collection is now default-on for every future
ticket, this is not a one-off: every subsequent PR going through Architecture-Verify (and every
security-tagged ticket going through Security-Review) keeps adding to this same non-canonical
count until it's fixed, so this blocks CI repo-wide starting now, not just this one PR.

A second, smaller finding from investigation: `docs/agent-monitoring/schema.md`'s Shadow-reviewer-
event field family section (lines ~413-416) currently documents these two literals as
*intentionally* unregistered ("neither in `WORKFLOW_AGENTS[...]`... expected to show... the same
non-gating precedent as `context-packet-wrapper`, not a vocabulary regression to chase"). That
comparison is now stale: `context-packet-wrapper` was itself later registered into `WORKFLOW_AGENTS`
by `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` for exactly this reason (a real, documented
mechanism the registry hadn't caught up to yet) — it is not an example of an intentionally-
unregistered literal anymore. This ticket's fix follows that same corrected precedent, so the
doc paragraph needs a small update alongside the code change or it will contradict the fix it
describes on the same day it lands.

## Scope
- Add `"architecture-reviewer-shadow"` and `"security-reviewer-shadow"` as two new literals inside
  `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set, each with its
  own comment following the file's existing documentation standard for every other entry in that
  set (what it is, how it was confirmed — cite the grep line references above — and why it is not
  drift), citing this ticket's own ID (`TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP`) as the source,
  the same way the six prior entries cite their own originating tickets.
- Update `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event field family paragraph
  (~lines 411-416) so it no longer states these two literals are unregistered/expected-drift;
  state instead that they are now canonical in `WORKFLOW_AGENTS["implement-ticket"]` as of this
  ticket, mirroring how `vocabulary.py`'s own `context-packet-wrapper` comment already documents
  its registration history.
- Confirm (re-run) that both previously-failing tests in
  `tests/tools/test_monitoring_anomaly_validator.py`
  (`test_real_corpus_is_at_or_below_every_ratchet_ceiling`,
  `test_cli_prints_marker_output_not_merely_a_return_code`) pass against the real corpus after the
  registration change, with `AGENT_DRIFT_CEILING` left untouched.

## Out of Scope
- Do NOT modify `AGENT_DRIFT_CEILING` or `TIER_DRIFT_CEILING` in
  `tools/gate_checks/monitoring_anomaly_validator.py`. The module's own docstring states the
  ceiling "May only decrease" — the fix is registering the literal so it drops OUT of the drift
  count (164 → 162, at-or-below the existing ceiling), not raising the ceiling to tolerate a higher
  count. Whether the ceiling should later be tightened to reflect the new lower real count is a
  separate, future decision, not this ticket's.
- Do NOT modify PR #240's own already-merged, already-DONE ticket
  (`TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON`) or its behavior — the default-on flip
  itself is correct and out of scope for reversal or adjustment here.
- Do NOT change the shadow-reviewer event schema, `shadow_reviewer_events.py`,
  `shadow_reviewer_window.py`, or the sample-window sizing (50/10) — only the vocabulary
  registration and its one paragraph of doc drift.
- Do NOT touch `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` or
  `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` (the two tickets actually bundled in PR #241) —
  this hotfix addresses a CI blocker orthogonal to their own scope, caused by an unrelated
  already-merged PR.
- Do NOT re-derive or lower the `SHADOW_MAX_SAMPLES` bounded window — unrelated cost cap, unchanged.

## Acceptance Criteria
- [x] `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set contains
      both `"architecture-reviewer-shadow"` and `"security-reviewer-shadow"`, each with a comment
      following the file's existing documentation standard (what/how-confirmed/why-not-drift),
      citing this ticket's ID.
- [x] `pytest tests/tools/test_monitoring_anomaly_validator.py -v` passes in full, including
      `test_real_corpus_is_at_or_below_every_ratchet_ceiling` and
      `test_cli_prints_marker_output_not_merely_a_return_code`.
- [x] `AGENT_DRIFT_CEILING` and `TIER_DRIFT_CEILING` in
      `tools/gate_checks/monitoring_anomaly_validator.py` are byte-identical to their pre-ticket
      values (162 and 2 respectively) — verified by diff, not just by not being mentioned in the
      Files Changed list.
- [x] `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event field family paragraph no longer
      states these two literals are unregistered/expected-drift; it states they are canonical as of
      this ticket.
- [x] `tests/tools/test_shadow_reviewer_call_site.py` and
      `tests/tools/test_current_run_sidecar_orchestrator.py` (which assert the literal agent string
      values themselves) still pass unmodified — this ticket only affects vocabulary
      classification, not the literals emitted at the call sites.
- [x] `make agent-monitoring-validate` (or the equivalent `monitoring_anomaly_validator.py` CLI
      invocation) reports `PASS` for `vocabulary_drift` against the real corpus.

## Related Tickets
- `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON` (done) — caused this gap by flipping shadow-
  reviewer collection to default-on; not itself modified by this ticket.
- `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` (done) — built the ratchet this ticket satisfies and
  established the exact "register the literal, don't raise the ceiling" precedent this ticket
  follows.
- `TCK-20260904-SHADOW-REVIEWER-LOGGING` (done) — original shadow-reviewer collection mechanism
  (opt-in); introduced the `architecture-reviewer-shadow`/`security-reviewer-shadow` literals and
  the schema.md paragraph this ticket updates.
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`, `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION`
  (PR #241, in progress) — blocked by this same CI failure; not modified by this ticket, but this
  hotfix unblocks their PR.

## Related Docs
- `docs/agent-monitoring/schema.md` — Shadow-reviewer-event field family section (~lines 380-416),
  updated by this ticket.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409` entry — describes the shadow-reviewer
  mechanism this ticket's literals belong to; read for context, not expected to need a status/
  evidence change since this ticket doesn't change the mechanism's behavior, only its monitoring
  vocabulary classification (confirm during implementation; if the entry's `text` also quotes the
  "not in WORKFLOW_AGENTS" framing verbatim, it needs the same small correction as schema.md).

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MONITORING-ANOMALY-VALIDATOR/` — original investigation and
  precedent for this exact "registry gap, not drift" fix shape.
- `stored_artifacts/TCK-20260904-SHADOW-REVIEWER-LOGGING/` — original build of the shadow-reviewer
  mechanism and its schema.md documentation.
- `stored_artifacts/TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON/` — background on the
  default-on flip that caused this gap to start mattering.

## Related Code Areas
- `tools/agent-monitoring/vocabulary.py` — `WORKFLOW_AGENTS["implement-ticket"]`, the registry to
  edit.
- `tools/gate_checks/monitoring_anomaly_validator.py` — the ratchet that will pass once the
  registration lands; `AGENT_DRIFT_CEILING`/`TIER_DRIFT_CEILING` read-only (must not change).
- `tests/tools/test_monitoring_anomaly_validator.py` — the two currently-failing tests this ticket
  must turn green.
- `.claude/workflows/implement-ticket.js` — read-only reference for the grep-confirmed literal call
  sites (Architecture-Verify ~1074/1099, Security-Review ~1519/1539); not edited by this ticket.
- `docs/agent-monitoring/schema.md` — Shadow-reviewer-event field family paragraph, edited.

## Assumptions / Open Questions
- Assumes the +2 drift measured against `origin/main` at `75ab942b4` vs. the PR branch tip is fully
  explained by the two `architecture-reviewer-shadow` events from this PR's own two tickets going
  through Architecture-Verify, per the request's own diff — not independently re-verified line-by-
  line in this scoping pass, but consistent with `monitoring_anomaly_validator.py`'s own
  `check_vocabulary_drift()` evidence format (`agent_total: 164 exceeds ceiling 162 by 2`) which
  the implementer should re-confirm at implementation time.
- Assumes `layer: observability` is the correct registered layer (matches
  `TCK-20260915-MONITORING-ANOMALY-VALIDATOR`, the closest precedent ticket touching this exact
  file/mechanism); `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON` instead used `layer: ai`
  for the broader default-on-flip ticket, but this narrower vocabulary-registry fix is judged closer
  in kind to the anomaly-validator ticket's own scope.
- Assumes `AGENT_DRIFT_CEILING` should NOT be tightened downward to the new real count (162) in this
  same ticket, per the request's explicit Out of Scope instruction and the module's own "may only
  decrease" framing (a decrease is technically allowed, but the request explicitly asked this
  ticket not to touch either ceiling constant at all) — if this assumption is wrong, it changes the
  Acceptance Criteria's byte-identical-ceiling check into a ceiling-lowering task instead.
- Did not independently verify whether `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409`
  entry's own `text` field repeats the "not in WORKFLOW_AGENTS" framing verbatim (only confirmed
  the entry exists and describes the shadow-reviewer mechanism generally) — implementer should
  check this during Implement and apply the same small correction there too if so.

## Implementation Notes
- Added `"architecture-reviewer-shadow"` and `"security-reviewer-shadow"` to
  `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set, each with a
  comment following the file's existing documentation standard: what the literal is, the
  grep-confirmed call site (`.claude/workflows/implement-ticket.js:1074`/`:1099` for
  architecture-reviewer-shadow, `:1519`/`:1539` for security-reviewer-shadow), the two-ticket
  origin history (`TCK-20260904-SHADOW-REVIEWER-LOGGING` built it opt-in,
  `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON` flipped it to default-on and is what pushed
  real corpus volume over the ratchet ceiling), and this ticket's own ID as the registration source.
- Corrected `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event field family paragraph
  (previously ~lines 413-416): removed the "neither in `WORKFLOW_AGENTS[...]`... expected to show...
  same non-gating precedent as `context-packet-wrapper`" framing (stale since
  `context-packet-wrapper` was itself registered by `TCK-20260915-MONITORING-ANOMALY-VALIDATOR`) and
  replaced it with a statement that both literals are now canonical as of this ticket, plus one
  sentence of context on why the gap only became CI-blocking after the default-on flip.
- Checked `docs/parity_ledger/infrastructure.yaml`'s `INFRA-409` entry in full: it describes the
  shadow-reviewer mechanism's construction, gating, and seq-bucketing but never mentions
  `WORKFLOW_AGENTS` or an "unregistered" framing anywhere in its `text` field. No edit made there —
  confirmed not a duplicate of the schema.md staleness per the ticket's own "confirm during
  implementation" instruction.
- Did not touch `AGENT_DRIFT_CEILING`/`TIER_DRIFT_CEILING` in
  `tools/gate_checks/monitoring_anomaly_validator.py` — confirmed byte-identical via `git diff`
  (empty diff on that file) both before and after the fix.
- No deviations from `staging_artifacts/` — this hotfix ticket has no staging artifacts (per the
  Workflow Rule, hotfix tier requires none) and the fix matched the ticket's own Scope exactly.
- **Second Test-phase finding (this run):** the first Test-phase pass under-scoped and only ran
  `tests/tools/test_monitoring_anomaly_validator.py` plus the two literal-call-site tests named in
  the Acceptance Criteria. It missed `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`,
  which also directly imports `vocabulary.py` and asserts `WORKFLOW_AGENTS["implement-ticket"]`
  (minus a documented pseudo-agent exclusion set) equals `agent-orchestration/workflows/
  implement-ticket.yaml`'s own `agents:` list. Adding the two new literals to `WORKFLOW_AGENTS`
  without also excluding them here broke `test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`
  (`AssertionError` showing `'security-reviewer-shadow'` and `'architecture-reviewer-shadow'` as
  extra items on the right side). A re-scoped Test-phase run (this one) caught it.
- Before editing, independently re-verified the fix direction: read `agent-orchestration/workflows/
  implement-ticket.yaml`'s `agents:` list directly (11 entries: ticket-scoper, investigator,
  planner, architecture-reviewer, implementer, doc-updater, test-scoper, parity-updater,
  security-reviewer, done-checker, finalizer) and confirmed via `grep -n shadow` that it contains
  no "shadow" literal at all. This confirms the existing comment's claim that the contract YAML
  never declares any of the pseudo-agent literals — `architecture-reviewer-shadow` and
  `security-reviewer-shadow` are the same category (the shadow-reviewer mechanism's own synthetic
  advisory-logging agent labels, not real dispatchable subagent roles), so the correct fix is
  extending the test's `expected_agents` exclusion set, not adding the two literals to the YAML's
  `agents:` list.
- Added both literals to `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`'s
  `expected_agents` exclusion set in `test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`,
  following the exact same what/how-confirmed/why-not-drift comment pattern already used for the
  five prior exclusions (citing this ticket's own ID, the grep-confirmed call sites at
  `.claude/workflows/implement-ticket.js:1074`/`:1099` and `:1519`/`:1539`, and the parallel to
  `context-packet-wrapper`'s existing entry). The module docstring and the meta-test
  (`test_bootstrap_equality_test_docstring_states_one_time_not_permanent`) were left untouched, per
  instruction.

## Test Summary
- `pytest tests/tools/test_monitoring_anomaly_validator.py -v` — 12/12 passed, including
  `test_real_corpus_is_at_or_below_every_ratchet_ceiling` and
  `test_cli_prints_marker_output_not_merely_a_return_code`.
- `pytest tests/tools/test_shadow_reviewer_call_site.py tests/tools/test_current_run_sidecar_orchestrator.py -v`
  — 35/35 passed unmodified, confirming the vocabulary registration did not touch the actual
  call-site literals.
- Direct re-run of `check_vocabulary_drift()` against the real corpus: `agent_total: 162` (ceiling
  162, was 164 before the fix) → `PASS`; `tier_total: 2` (ceiling 2) → `PASS`.
- `python3 tools/gate_checks/monitoring_anomaly_validator.py` (the Makefile's own invocation for
  this check) — full run reports `vocabulary_drift` as `PASS` for both the agent and tier
  sub-checks against the live corpus.
- **Second Test-phase pass (this run):** re-scoped to include `tests/agent_orchestration/` since it
  directly imports `vocabulary.py`. Found and fixed
  `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py::test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`
  failing (extra items `'security-reviewer-shadow'`, `'architecture-reviewer-shadow'` in the
  vocabulary-vs-contract-YAML comparison). Independently confirmed
  `agent-orchestration/workflows/implement-ticket.yaml`'s `agents:` list declares neither literal
  (11 real subagent roles, no "shadow" entries), matching the file's existing precedent for the
  five prior pseudo-agent exclusions. Added both literals to the test's `expected_agents`
  exclusion set with matching documentation. Re-ran
  `pytest tests/agent_orchestration/test_bootstrap_vocabulary_equality.py -v` — 2/2 passed
  (including the docstring meta-test, left untouched). Re-ran
  `pytest tests/tools/test_monitoring_anomaly_validator.py tests/tools/test_shadow_reviewer_call_site.py tests/tools/test_current_run_sidecar_orchestrator.py -q`
  — 47/47 passed, confirming no regression from this second fix.

## Files Changed
- `tools/agent-monitoring/vocabulary.py` — registered the two shadow-reviewer agent literals with
  documentation comments.
- `docs/agent-monitoring/schema.md` — corrected the Shadow-reviewer-event field family paragraph to
  reflect the literals' now-canonical status.
- `tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` — added
  `"architecture-reviewer-shadow"` and `"security-reviewer-shadow"` to the
  `expected_agents` pseudo-agent exclusion set in
  `test_bootstrap_phase_agent_vocabulary_matches_vocabulary_py`, with matching
  what/how-confirmed/why-not-drift documentation, citing this ticket's ID. Found necessary only in
  a second, correctly-scoped Test-phase pass (the first pass omitted this test file).
- `tickets/inprogress/TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP.md` — this ticket file itself
  (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary sections filled in across both Implement/Test passes).
- `docs/REGISTRY.yaml` — auto-regenerated (per CLAUDE.md's standard close convention: this file is
  never hand-edited, `make docs-registry`/the Finalize post-migration self-check regenerate it
  unconditionally). Picks up this ticket's own new `tickets/inprogress/` entry, plus unrelated
  entries reflecting other concurrent work already present in this shared worktree's live tree at
  regeneration time (e.g. a `tickets/todos/mechanism-registry/` ticket move) — not a change this
  ticket itself authored.

## Completion Summary
Registered `architecture-reviewer-shadow` and `security-reviewer-shadow` as canonical agent
literals in `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` set,
each documented per the file's existing what/how-confirmed/why-not-drift comment standard, which
drops the real corpus's non-canonical agent count from 164 to 162 (at or below
`AGENT_DRIFT_CEILING = 162`, left untouched) and turns the two previously-failing CI tests in
`tests/tools/test_monitoring_anomaly_validator.py` green. Also corrected the now-stale
"intentionally unregistered" framing in `docs/agent-monitoring/schema.md`'s Shadow-reviewer-event
field family paragraph to state both literals are canonical as of this ticket. Checked
`docs/parity_ledger/infrastructure.yaml`'s `INFRA-409` entry and confirmed it does not repeat the
stale framing, so it required no edit. A second, correctly-scoped Test-phase run (this run) found
that the same registration broke a dependent test,
`tests/agent_orchestration/test_bootstrap_vocabulary_equality.py`, which independently compares
`vocabulary.py`'s `WORKFLOW_AGENTS["implement-ticket"]` against the contract YAML's own `agents:`
list using its own pseudo-agent exclusion set; the two new literals needed the same exclusion-set
treatment as the five prior pseudo-agent literals it already excludes. Confirmed via direct read
that `agent-orchestration/workflows/implement-ticket.yaml` declares neither literal, then extended
the exclusion set with matching documentation; both tests in that file now pass, and no other
scoped test regressed. `docs/REGISTRY.yaml` was regenerated (per the standard Finalize
post-migration self-check, never hand-edited) and staged as part of ticket close; its diff is the
routine auto-generated shape — this ticket's own new `tickets/inprogress/` entry declared, plus
unrelated entries reflecting other concurrent work already live in this shared worktree at
regeneration time (a `tickets/todos/mechanism-registry/` folder move and a `tickets/todos/
TCK-20260914-VENV-NAMING-CI-PARITY-SWAP.md` removal, neither authored by this ticket). Verified
by direct diff read that nothing in the regenerated file misrepresents this ticket's own frontmatter
or classification.
