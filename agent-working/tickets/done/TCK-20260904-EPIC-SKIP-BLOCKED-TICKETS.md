---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS
phase: done
date: 2026-09-04
tags: [ai, workflows]
---

# TCK-20260904-EPIC-SKIP-BLOCKED-TICKETS

## Title
implement-epic.js has no mechanism to skip an individual BLOCKED ticket inside a folder/epic batch

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Discovered live while assembling a 13-ticket batch under `tickets/todos/ai-first-hardening-governance-guardrail-batch/`: one ticket (`TCK-20260904-BASH-SECRET-SCAN-HOOK`) had to carry `## Status: BLOCKED` because its hard prerequisite (a separate knowledge-gateway re-ratification) does not exist yet. `.claude/workflows/implement-epic.js`'s folder-mode and epic_id-mode both determine "already done, skip" purely by checking `ls tickets/done/` for a matching ticket ID (Step 2/comment at line 15: "discovers all TCK-*.md files, skips ones already in tickets/done/"; line 106-107, 136-137: "A ticket is already done if tickets/done/{ticket_id}.md exists"). Neither branch reads a candidate ticket's own `## Status` body field at all. If a `BLOCKED` ticket is left inside a todos folder or epic child list, `/implement-epic` would attempt it in normal sequence (SEQUENCE.md order, or alphabetical) and either fail mid-pipeline or produce unusable work against a ticket that cannot structurally proceed — there is no early, cheap skip. This repo already has the identical fix shipped for a sibling tool: `epic_staleness_check.py`'s `discover_candidate_epics()` reads a candidate's `## Status` and treats `BLOCKED` as a distinct, non-stale bucket (`tools/agent-monitoring/epic_staleness_check.py:23,66,146,306` — `is_blocked()` returns `(candidate.status or "").strip().upper() == "BLOCKED"`), following `TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC` and its folder-mode extension `TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP`. `implement-epic.js` never received the equivalent fix — it is a different tool (an implementation workflow, not a staleness reporter) that never inherited the pattern. This session's workaround was to physically move the blocked ticket out of the todos folder into `tickets/inprogress/` (matching the established convention used by `TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC`/`TCK-20260730-CODEX-CONTROLLED-PILOT`) — a manual step that should not be required every time a batch contains a blocked ticket.

## Scope
- In `.claude/workflows/implement-epic.js`'s folder-mode Step 2 (and the epic_id-mode equivalent), when building `ticket_ids`/`already_done`, also read each candidate ticket's `## Status` body field.
- Introduce a third bucket alongside "to implement" and "already done": tickets whose `## Status` is `BLOCKED` are reported separately and excluded from the implementation attempt order, mirroring `epic_staleness_check.py`'s "Informational: BLOCKED epics" framing (a status to surface, not an error).
- Update the workflow's final summary/return value to name any `BLOCKED` tickets found, so the user sees them without needing to grep the folder manually.
- Add a regression test proving a synthetic folder containing one normal ticket and one `## Status: BLOCKED` ticket produces an implementation order that excludes the blocked one and reports it separately.

## Out of Scope
- Any change to `epic_staleness_check.py` — it already handles this correctly and is not the tool with the gap.
- Automatically re-including a `BLOCKED` ticket once some external condition changes — that stays a manual re-scope step (flip `## Status` back to `OPEN`), not something this workflow should try to detect on its own.
- Any change to how `## Status: BLOCKED` tickets are stored/located (`tickets/inprogress/` vs `tickets/todos/`) — this ticket only fixes `implement-epic.js`'s in-run detection, not ticket file placement conventions.

## Acceptance Criteria
- [x] `implement-epic.js`'s folder-mode reads each non-done candidate ticket's `## Status` field before adding it to the implementation order.
- [x] A ticket with `## Status: BLOCKED` is excluded from `ticket_ids` (the order to implement) and reported in a distinct, named bucket in the phase summary/return value.
- [x] A synthetic two-ticket folder (one normal, one `## Status: BLOCKED`) demonstrates the blocked ticket is skipped and named in the summary, not silently dropped or silently attempted.
- [x] The epic_id-mode code path (child tickets, not folder tickets) receives the equivalent fix, verified by an analogous synthetic test.
- [x] A normal (non-blocked) folder's behavior is unchanged — this must not weaken or slow down the existing done/not-done detection.

## Related Tickets
- TCK-20260817-EPIC-STALENESS-STATUS-AWARE-EPIC (original BLOCKED-aware fix, different tool — epic_staleness_check.py)
- TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP (extended that fix to epic_staleness_check.py's own folder-mode branch — same "fix landed on one code path, not its sibling tool" class of gap, one layer up: a different tool entirely this time)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC, TCK-20260730-CODEX-CONTROLLED-PILOT (the real BLOCKED tickets whose `tickets/inprogress/`, `phase: blocked` placement this session's manual workaround matched)
- TCK-20260904-BASH-SECRET-SCAN-HOOK (the concrete case that surfaced this gap this session; moved to `tickets/inprogress/` as a manual workaround)

## Related Docs
- docs/ai/ticket-lifecycle.md ("Epic Batch Workflow" section — updated to document the new BLOCKED filtering)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- .claude/workflows/implement-epic.js (folder-mode Step 2, epic_id-mode child-ticket discovery)
- tools/agent-monitoring/epic_staleness_check.py (the pattern mirrored: `is_epic_blocked()`, `_section_body()` — confirmed the actual current function name differs slightly from this ticket's own citation of `is_blocked()`)
- tools/gate_checks/epic_blocked_status_static.py (new — the deterministic mechanism, mirroring `epic_tracking_doc_static.py`'s own "give Discover a real mechanism instead of opaque agent-prompt English" precedent)

## Assumptions / Open Questions
- Whether the fix should hard-skip a BLOCKED ticket unconditionally, or only skip with a warning that a caller could override, is left to the implementer — the safer default (matching this session's manual workaround) is an unconditional skip with a clearly named report, since attempting a structurally-blocked ticket cannot succeed.
- Whether this same gap exists in any other batch-processing tool beyond `implement-epic.js` was not swept in this session (matching `TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP`'s own out-of-scope precedent for a fuller sweep) — a future session should decide if a broader audit is warranted.

## Implementation Notes
Investigation found the ticket's own citation of `epic_staleness_check.py`'s pattern
(`is_blocked()`) is slightly stale — the current function name is `is_epic_blocked()`, paired with
`_section_body()` for the body-field read. Confirmed and cited the real current names.

`implement-epic.js`'s Discover phase is not deterministic code — it's a natural-language prompt fed
to an `agent()` call, with a JSON schema (`DISCOVER_SCHEMA`) for structured output. This repo
already has an established precedent for exactly this situation
(`tools/gate_checks/epic_tracking_doc_static.py`, built for
`TCK-20260826-IMPLEMENT-EPIC-ROADMAP-DOC-STALENESS-GAP`): give the Discover/Report phases a real,
deterministic, testable Python mechanism instead of leaving logic as opaque agent-prompt English,
invoked via a single `bash()` call using the same `python3 -c "import sys;
sys.path.insert(0,'tools'); from gate_checks.X import Y; ..."` style already used at Step 4b for
`tracking_doc`. Followed this pattern exactly rather than asking the LLM agent to freeform-parse
`## Status` fields itself (unreliable, untestable).

New module `tools/gate_checks/epic_blocked_status_static.py`: `read_ticket_status()` (mirrors
`_section_body()`'s body-field-not-frontmatter reading convention), `find_ticket_path()` (resolves
a ticket_id to its real file, checking each search root directly and one level of subdirectories —
covers both folder-mode's single-folder case and epic_id-mode's scattered-across-3-directories
case), and `find_blocked_ticket_ids()` (the public entry point). Avoided passing a JSON mapping
through the shell (a risk this same file's own comments already flag elsewhere as "established
quote-corruption risk") — the CLI only ever receives a Python list literal of ticket-ID strings
(no spaces/quotes) and search-root paths, both plain and safe to embed directly.

Wired into both `implement-epic.js` branches: folder-mode (new Step 4a, searching just `${folder}`)
and epic_id-mode (new Step 3a, searching `tickets/inprogress`, `tickets/todos`, `tickets/done` —
matching Discover's own existing epic-ticket search precedent from Step 1). Added `blocked` to
`DISCOVER_SCHEMA` (now `required`, so `request`-mode's own return also needed `blocked = []`),
added logging (`Skipping blocked: ...`, mirroring the existing `Skipping already-done: ...` line),
added a `Blocked (excluded, not attempted):` section to the final report and `blocked` to the final
returned object. Also fixed the `NOTHING_TO_DO` early-return branch's message, which previously
only distinguished "already done" vs "none found" — a batch where everything remaining is blocked
now gets its own accurate message instead of a misleading fallback.

Updated `docs/ai/ticket-lifecycle.md`'s "Epic Batch Workflow" section (the only doc describing this
workflow's behavior) to mention the new BLOCKED filtering.

`node --check .claude/workflows/implement-epic.js` confirms the file is still syntactically valid
JS after the prompt-text edits.

## Test Summary
- `pytest tests/tools/test_epic_blocked_status_static.py -v` — 14 passed, including the exact
  synthetic-folder scenario this ticket's own AC #3 describes (one normal + one `## Status:
  BLOCKED` ticket → the blocked one is excluded and named, the normal one is not), an epic_id-mode
  equivalent with children scattered across 2 search roots (AC #4), and a normal all-non-blocked
  batch producing an empty `blocked` list (AC #5).
- `pytest tests/tools/test_epic_tracking_doc_static.py tests/tools/test_monitoring_bypass_fix.py tests/tools/test_retrieval_event_wrapper_single_source.py tests/tools/test_workflow_meta_conformance.py tests/tools/test_step0_ts_orchestrator.py -q` —
  53 passed, 1 xfailed (targeted regression check against other tests that reference
  `implement-epic.js`/this file's conventions — confirmed no existing structural guard broke).
- `pytest tests/tools/ -m "not slow and not extra_slow" -q` (broader sweep) — 2666 passed, 5
  failed, 25 skipped, 31 deselected, 1 xfailed. Confirmed all 5 failures are pre-existing and
  unrelated (none reference `implement-epic.js` or `epic_blocked_status_static.py` — direct grep
  confirms zero overlap): 4 are kgmcp live-corpus/timing-plausibility tests (environment/load-
  sensitive), and 1 (`test_only_knowledge_context_and_knowledge_status_registered`) is the same
  pre-existing `ModuleNotFoundError: No module named 'mcp'` environment gap already confirmed
  pre-existing earlier this session (`TCK-20260904-HOTFIX-KGMCP-FROZEN-FILE-BASELINE-UPDATE`).
- `python3 tools/validate_frontmatter.py docs/ai/ticket-lifecycle.md --content-type doc` — OK.
- `node --check .claude/workflows/implement-epic.js` — syntax valid.
- `make knowledge-index-update` — ran (docs/ was modified): 56 files re-embedded, 3316 from cache.

## Files Changed
- `tools/gate_checks/epic_blocked_status_static.py` (new) — the deterministic mechanism.
- `tests/tools/test_epic_blocked_status_static.py` (new) — 14 tests.
- `.claude/workflows/implement-epic.js` — `DISCOVER_SCHEMA` gains `blocked` (required); folder-mode
  and epic_id-mode prompts gain a new BLOCKED-check step each; `request`-mode returns `blocked: []`;
  logging, final report, `NOTHING_TO_DO` message, and the final returned object all updated.
- `docs/ai/ticket-lifecycle.md` — "Epic Batch Workflow" section updated.

## Completion Summary
Fixed the real gap: `implement-epic.js`'s folder-mode and epic_id-mode Discover phases now read
each non-done candidate ticket's `## Status` field and exclude any `BLOCKED` ticket from the
implementation order, reporting it in a distinct, named bucket (log line, final report section,
and the workflow's returned object) rather than silently attempting or silently dropping it.
Mirrored this repo's own existing precedent (`epic_tracking_doc_static.py`) for giving an
LLM-prompt-driven Discover phase a real, deterministic, unit-testable Python mechanism instead of
opaque agent-prompt English — new module `epic_blocked_status_static.py`, 14 new tests including
the exact synthetic-folder scenario the ticket's own ACs describe for both folder-mode and
epic_id-mode. Confirmed a normal (non-blocked) batch's behavior is unchanged. Updated the one doc
describing this workflow's behavior. Broader regression sweep confirms 5 pre-existing, unrelated
failures (kgmcp/timing tests, one already-known environment gap) — zero relation to this ticket's
own files, confirmed via direct grep, not assumed.
