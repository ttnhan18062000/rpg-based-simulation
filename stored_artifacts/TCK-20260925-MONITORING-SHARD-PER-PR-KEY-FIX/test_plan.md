---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX
artifact_type: test_plan
phase: inprogress
date: 2026-09-25
tags: [observability, testing]
---

# Test Plan — TCK-20260925-MONITORING-SHARD-PER-PR-KEY-FIX

## New: `tests/tools/test_monitoring_batch_identifier.py`

Real git repo fixtures (matching this repo's own established pattern for proving merge/branch
claims — `test_delivery_pre_push_advisory.py`'s Check C, `test_monitoring_consolidation.py`'s AC1 —
never a synthetic mock of git state):

1. `test_resolves_branch_name_on_attached_head` — a real scratch repo on a named branch;
   `resolve_batch_identifier()` returns that exact name.
2. `test_resolves_via_worktree_gitlink` — a real `git worktree add` off the scratch repo (mirrors
   this project's own normal deployment shape, where `.git` is a gitlink file, not a directory);
   confirms the worktree-specific branch is returned, not the main checkout's.
3. `test_detached_head_without_sidecar_falls_back_to_labeled_identifier` — real
   `git checkout --detach <sha>`; no `.claude/current_batch` present; asserts the
   `detached-<sha_prefix>` shape and a printed warning, never the bare shared filename or `"HEAD"`.
4. `test_detached_head_with_sidecar_self_heals` — resolve once on an attached branch (sidecar gets
   written), then detach in the same working dir; confirms the sidecar's branch name is returned,
   not the SHA fallback.
5. `test_slash_in_branch_name_sanitized` — a branch named `feature/foo`; confirms
   `sanitize_for_filename` yields `feature-foo`, no literal `/` in the returned identifier.
6. `test_resolver_module_makes_no_subprocess_call` — source-scans
   `monitoring_batch_identifier.py` for `subprocess`/`Popen`/`os.system`; must find none.

## New: end-to-end real-closure test (extends `tests/tools/test_record_hand_orchestrated_closure.py`
or a new file, decided during Implement based on which keeps the existing suite's shape cleanest)

7. `test_real_closure_produces_exactly_three_per_pr_files_and_leaves_shared_files_untouched` — a
   real scratch repo, on a real named branch, with a pre-existing shared
   `{runs,events,tools}.jsonl` seeded with unrelated rows (simulating "another ticket already
   closed on a different branch, shared files exist"). Invoke
   `record_hand_orchestrated_closure.py` as a **real subprocess** (not by importing and calling its
   internal functions — the whole point is proving the wrapper's actual write path, the exact gap
   unit tests over `record_run.py`/`record_events.py` alone did not catch). Assert:
   - Exactly one `<branch>.runs.jsonl`, one `<branch>.events.jsonl` created (plus
     `post_tool_hook.py`'s pre-existing `<branch>.tools.jsonl` behavior, unchanged by this ticket).
   - The seeded shared files' content is byte-identical before and after (untouched).

## Updated: existing tests broken by the rewire (found by running, not assumed)

Every existing test asserting the old `run_id`-keyed or `ticket_id`-keyed filename shape in
`record_run.py`, `record_events.py`, `retrieval_events.py`, `post_tool_hook.py`,
`shadow_reviewer_events.py`, and their own test files needs updating to the new per-PR shape. Run
the full suite before and after each file's edit, not just once at the end, to attribute each
breakage to the specific rewire that caused it (mirrors this session's own established practice
from the earlier per-ticket-keying ticket, which found five broken files exactly this way).

## Updated: `tests/tools/test_monitoring_consolidation.py`

Add a mixed-shape fixture: one old per-ticket-named file (`TCK-XXXX.tools.jsonl`) and one new
per-PR-named file (`some-branch.tools.jsonl`) in the same week directory; confirm
`consolidate_jsonl_kind()` folds both into the canonical file and deletes both sources.

## Regression scope

- `tests/tools/test_record_run.py`, `test_record_events.py`, `test_post_tool_hook.py`,
  `test_retrieval_events.py`, `test_record_hand_orchestrated_closure.py`,
  `test_monitoring_consolidation.py`, `test_shadow_reviewer_events.py` (if it exists — confirm
  during Implement) — full suite.
- `tests/tools/` full regression (`-m "not slow and not extra_slow"`) before claiming completion,
  per the Testing Rule.
- Manual check of the `implement-ticket.js:631` fix: `SHADOW_CONTEXT_PACKET_ENABLED=1` +
  a real `.claude/current_run` sidecar, confirm no `AttributeError` (previously silent, now fixed)
  and a real seq value computed — no automated test added for this path (documented as
  out-of-scope in plan.md), so this is a manual, disclosed check only.

## Acceptance evidence beyond tests

Per the plan's Acceptance-criteria map: after this fix is pushed to `github-delivery-process-epic`,
the very next tool call/hand-orchestrated write on this branch must land in a single new
`github-delivery-process-epic.{runs,events,tools}.jsonl` file (or whatever the sanitized identifier
resolves to) — checked directly against the real file on disk after the push, not inferred from
green tests. Reported in the ticket's Completion Summary with the exact filename observed.
