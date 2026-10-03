---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-UPDATE-DISCIPLINE
artifact_type: investigation
tags: [workflows, documentation]
---

# Investigation — TCK-20260802-DOC-UPDATE-DISCIPLINE

## Current Behavior

**Investigate phase** (`.claude/workflows/implement-ticket.js:470-571`, agent `investigator`):
Calls `investigator` with no `schema` — the return is free text captured via
`investigation.toString().trim()` into `investigationText` (line 508). The prompt already tells
the agent to read `docs/mechanics/`, `docs/engine/`, `docs/parity_ledger/` and cite constraints
(`.claude/agents/investigator.md:15-16, 56-62`), and `investigation.md`'s template already has a
"Mechanics / Engine Constraints" and "Parity Ledger Overlap" section — but nothing forces a
concrete, structured "these exact docs/ paths must change" obligation that a later phase could
check against. `investigation`/`investigationText` are the only two places this variable is used
downstream (confirmed via grep — no other reads of `investigation.*`).

**Implement phase** (`implement-ticket.js:710-802`, agent `implementer`): `IMPL_SCHEMA` requires
`behavior_changed: boolean` with no description of what counts. The implementer agent
(`.claude/agents/implementer.md`) has no guidance distinguishing "modified existing behavior" from
"added new logic/feature/setting with no prior behavior to diverge from" — an agent could plausibly
report `false` for a brand-new feature on the reasoning that nothing *existing* changed.

**Doc-staleness gate** (`tools/gate_checks/doc_staleness_check.py::check_doc_staleness`, wired at
`implement-ticket.js:769-802`): `FAIL`s only when `behavior_changed=true`, at least one path in
`files_changed` starts with `src/` or is a `.claude/workflows/*.js` file, and zero paths start with
`docs/`. Confirmed gaps:
- `config/` is not in the flagged-prefix set. `config/simulation_quality/{scoring_weights,
  grade_thresholds, detection_params}.yaml` and `config/simulation_quality/profiles/*.yaml` are
  real behavior-driving settings (SimQ scoring/grading logic) that live outside `src/` — a ticket
  that only edits these currently gets a free pass on the doc-staleness gate even with
  `behavior_changed=true`.
- The gate is satisfied by *any* `docs/` path — it does not know which doc is actually relevant, so
  a trivial/unrelated `docs/` edit passes exactly the same as a correct, targeted update.

**Finalize phase** (`implement-ticket.js:1259-1421`): Confirmed via `grep -n
"knowledge-index-update\|docs/REGISTRY" implement-ticket.js create-tickets.js` — zero references to
`make knowledge-index-update` anywhere in either workflow file. `docs/REGISTRY.yaml` regeneration
IS wired (`run_finalize_selfcheck`'s `registry_entry_regenerated` condition,
`TCK-20260709-REGISTRY-REGEN-ON-CLOSE`), but the semantic-search index (`knowledge-index/`,
consumed by `search_docs`/MCP) is not refreshed by anything in the ticket lifecycle. This directly
contradicts CLAUDE.md's "After Work" rule ("If any files under `docs/` were created or modified: run
`make knowledge-index-update`") and `docs/guidelines/agent_working_environment.md`'s Index Lifecycle
Rules table (same requirement, doubly documented).

**create-tickets.js**: Confirmed it never touches `docs/` — `concern-investigator` reads Mechanics
Bible constraints during Investigate but the workflow's only file-write phase (`Write`, `ticket-scoper`)
only creates `tickets/todos/**/TCK-*.md` files. No doc-write step exists here and none is being added
— out of scope, confirmed by reading the full file.

## Mechanics / Engine Constraints

None — this is agent-orchestration/process tooling (`.claude/workflows/`, `.claude/agents/`,
`tools/gate_checks/`), not simulation mechanics. No Mechanics Bible chapter governs it.

## Docs Requiring Update

- `docs/ai/ticket-lifecycle.md` — Investigate/Implement/Finalize sections describe exactly the
  behavior being changed here (doc-staleness gate mechanics, Finalize step list) and must stay in
  parity with the code per CLAUDE.md's Parity rule.
- No `docs/mechanics/` or `docs/engine/` chapter needs updating — process tooling only.

## Parity Ledger Overlap

None. `docs/parity_ledger/` tracks simulation-mechanics/source parity (`substrate`, `combat_movement`,
etc.) — this ticket touches none of those subsystems. No entry ID applies.

## Prior Work

- `TCK-20260711-DOC-STALENESS-GATE-CHECK` — shipped `doc_staleness_check.py` unwired.
- `TCK-20260720-GATE-CHECK-WIRING-DECISIONS` — wired it in as a hard blocking gate
  (`DOC_STALENESS_BLOCKED`).
- `TCK-20260705-WORKFLOWS-DOC-STALENESS-REPAIR` — fixed stale phase-list drift in
  `docs/ai/workflows.md`, a related but distinct problem (doc *describing* the workflow going stale,
  not doc *required by* a behavior change going missing).
- `tests/tools/test_doc_staleness_gate_wiring.py` — static regex/substring tests against the raw
  `implement-ticket.js` source (no JS test runner exists for `.claude/workflows/*.js` in this repo).
  Any change to the doc-staleness wiring block must keep these five tests passing: exactly one
  `pushEvent` call in the Implement→Architecture-Verify range, no `reason_code` 6th arg on it,
  `writeMonitoring` called before the `DOC_STALENESS_BLOCKED` return, and the bash() invocation line
  containing both `implementation.behavior_changed` and `docStalenessFilesArgs`.

## Risks and Open Questions

- **Resolved via AskUserQuestion during scoping**: the new specific-doc-relevance check (comparing
  investigator's `docs_to_update` against Implement's actual `files_changed`) is **advisory-only** —
  it must never introduce a new blocking status or change the existing `PASS`/`FAIL` verdict from
  `check_doc_staleness`. Confirmed design: append a separate `ADVISORY` entry to the returned list,
  which `implement-ticket.js` folds into the *existing* single `pushEvent`'s summary text (never a
  second `pushEvent` call, to keep `test_doc_staleness_failure_folds_into_the_single_implement_event_not_a_second_one`
  passing) and a `log()` warning, never a status change.
- The Investigate phase currently has **no schema at all** (free-text return) — adding one changes
  `investigation` from a string to an object. Confirmed via grep this is safe: `investigation` is
  used in exactly one downstream expression (`investigation.toString().trim()`), so changing that to
  `investigation.findings_summary` is the only touch point. The hotfix-tier default
  (`let investigation = '(hotfix — investigation skipped)'`) must become an object with the same
  shape (`{ docs_to_update: [], findings_summary: '...' }`) so the later `investigation.docs_to_update`
  read at Implement-time doesn't need a tier-conditional branch.
- CLI backward compatibility: `doc_staleness_check.py`'s `__main__` block currently treats all of
  `sys.argv[2:]` as `files_changed`. Existing tests (`test_cli_entrypoint_prints_marker_prefixed_json`,
  `test_doc_staleness_check_passes_behavior_changed_and_files_changed`) call it with exactly
  `[behavior_changed, *files_changed]` and no `docs_to_update` — the new `docs_to_update` CLI param
  must be introduced behind a `--docs-to-update` sentinel token so these existing 2-shape calls are
  completely unaffected (confirmed no test passes a bare 3rd-positional-style arg that would collide).

## Anti-Drift Hazards

- Do not let the new `ADVISORY` result accidentally get treated as `FAIL` anywhere downstream —
  `implement-ticket.js`'s existing `docStalenessResults.find(r => r.status === 'FAIL')` lookup is
  unaffected by an added list entry with a different `status` value, but any *new* code reading
  `docStalenessResults` must filter explicitly by status, never assume a 1-entry array.
  test_doc_staleness_gate_wiring.py already checks the `pushEvent` comma-count for the FAIL branch;
  a mistake here (e.g. adding a second `pushEvent` call) breaks that test — precompute the summary
  string in a `const` first, then pass it as a single argument to `pushEvent`, mirroring the pattern
  already used for `parityEvidence` in the Parity phase to avoid the same class of test breakage.
- Do not narrow or change the *existing* `src/`/`.claude/workflows/*.js` blocking behavior — only add
  `config/` to the flagged set. `tests/tools/test_doc_staleness_check.py`'s existing 9 tests must all
  keep passing unmodified.
- Keep the `make knowledge-index-update` Finalize step orchestrator-run (`bash()`), not an
  agent-prompt-text instruction — `docs/ai/ticket-lifecycle.md`'s own "Reliability caveat" for the
  post-Test cleanup checkpoint already documents that a bare, non-`phase()`-anchored agent-prompt
  bash instruction has been observed to silently not execute; this must not repeat that mistake for
  a step whose whole purpose is closing a silent-gap complaint.
