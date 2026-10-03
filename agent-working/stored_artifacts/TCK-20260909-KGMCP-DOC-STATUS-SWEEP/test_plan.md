---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260909-KGMCP-DOC-STATUS-SWEEP
artifact_type: test_plan
tags: [mcp, documentation]
---

# Test Plan — TCK-20260909-KGMCP-DOC-STATUS-SWEEP

## Regression Surface

This is a doc-only, frontmatter-and-prose ticket — no `src/`/`tools/` code changes. The
regression surface is therefore: (a) doc-structure tests that assert on the exact text of the one
doc getting new prose (`redaction_retention_policy.md`), and (b) registry/frontmatter-validation
tooling tests that must keep passing after 11 files' `status:` values change.

**Unit / doc-structure:**
- `tests/docs/test_redaction_retention_policy_doc.py` — all 6 tests. This is the tightly-coupled
  whole-file structure test for `redaction_retention_policy.md` (required headings §1-§7, the §5
  `MAX_PAYLOAD_BYTES` cross-check against `tools/write_path_guard.py`, §8 token-counting phrases,
  §9 SQLite-limit phrases + the anti-scope-creep guard against `tools/retrieval_cache.py`, §10 GC
  deference phrases, §11 ratification phrases). The new scoped-status note must not remove or
  reword any of the substrings these tests assert — this is the single highest-risk regression
  point in this ticket.
- `tests/tools/test_write_path_guard.py` — confirms the live module's own behavior is untouched
  (this ticket makes no code changes, but the doc's live/historical split as written must remain
  accurate against this module's real behavior).

**Unit / registry & frontmatter validation:**
- `tests/tools/test_generate_registry.py` — full file, especially any test asserting `status`
  distribution or `docs/REGISTRY.yaml` sync (`--check` mode). Must reflect the 11 new `historical`
  statuses after regeneration.
- `tests/tools/test_validate_frontmatter.py` — full file, especially the `STATUS_VALUES` enum
  check (`historical` is already a valid value — no schema change needed) and any test that walks
  real `docs/` content.

**Integration / retrieval:**
- `tests/tools/test_knowledge_search.py` — confirms `search_docs`/index-build machinery is
  unaffected by a frontmatter-only change (no schema or code path touched); relevant mainly as a
  smoke check that `make knowledge-index-update` completes cleanly against the changed files.

**No arena-combat / simulation-kernel surface applies** — this ticket touches only
`docs/engine/contracts/knowledge_gateway_mcp/` and `docs/REGISTRY.yaml`, both agent-infrastructure
docs with no engine/combat/economy code dependency.

## New Tests Required

No new test files are required by this ticket's acceptance criteria — it is a status/content
sweep, not new behavior. The verification burden is entirely re-running existing structure and
registry tests plus the two CLI commands AC #4/#5 name directly. If Plan/Implement judges a
regression guard is warranted, the one candidate is:

- **Test name:** `test_redaction_retention_policy_doc_carries_scoped_status_note` (or equivalent)
- **Category:** unit / doc structure
- **What it verifies:** the new scoped-status note text is present in
  `redaction_retention_policy.md` and correctly names both the live section list (§2-§7, plus the
  `open_connection_with_limits()` clause of §9) and the historical section list (§1's framing, §8,
  §9's remainder, §10, §11) — guards against a future editor silently dropping the note or letting
  it drift out of sync with `tools/write_path_guard.py`'s own docstring if that module's
  live/archived boundary ever changes again.
- **Where it should live:** `tests/docs/test_redaction_retention_policy_doc.py` (append to the
  existing file — keeps the "whole-doc structure" convention that file already establishes,
  rather than starting a second doc-structure test file for the same doc).

This is optional/recommended, not mandatory — Plan should decide based on whether the scoped note
is judged likely to drift.

## Scoped Pytest Commands

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -v
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_write_path_guard.py -v -m "not slow"
```

(This worktree has no `.venv` of its own — the shared repo-root venv at
`/home/u24desktop/Working/rpg-based-simulation/.venv` is the one confirmed working; verified live
by running `tests/docs/test_redaction_retention_policy_doc.py` during Investigate — 7 passed.)

Never `pytest tests/` — scoped to the `tests/docs/` doc-structure lane and the `tests/tools/`
registry/frontmatter/write-path-guard files directly touched or asserted-against by this ticket.

## Anti-Drift Test Guards

- `tests/docs/test_redaction_retention_policy_doc.py` itself is the primary anti-drift guard for
  this ticket's one nuanced case: if Implement accidentally deletes or rewords any of §1-§11's
  required headings/phrases while inserting the scoped note, this test fails immediately.
- `tests/tools/test_write_path_guard.py`'s full pass, re-run unchanged, confirms this ticket made
  zero code changes — a doc-only ticket that somehow touched `tools/write_path_guard.py` (e.g. an
  implementer "fixing" the doc by editing the code instead) would be caught here.
- Re-running `python3 tools/generate_registry.py --check` (dry-run diff mode) before and after the
  11 status edits is itself a drift guard: it must show exactly 11 `status` field diffs (the 11
  named docs) and zero unrelated diffs, confirming the sweep touched only its intended targets.
- `python3 tools/validate_frontmatter.py docs/engine/contracts/knowledge_gateway_mcp/ --content-type doc`
  run over the whole directory (not just the changed files) after the sweep — confirms no
  collateral frontmatter damage to `redaction_retention_policy.md` (which changes prose but not
  its `status:` field) or to `keep_or_deprecate_decision.md` (which should show zero diff at all).
- Confirm via `git diff --stat` before closing that no file outside
  `docs/engine/contracts/knowledge_gateway_mcp/` and `docs/REGISTRY.yaml` changed — this ticket's
  Out of Scope explicitly excludes `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s territory
  (`tools/archive/`, parity-entry finalization, `norecursedirs`), and a diff outside the expected
  file set would indicate scope creep.
