---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260909-KGMCP-DOC-STATUS-SWEEP
artifact_type: plan
tags: [mcp, documentation]
---

# Implementation Plan — TCK-20260909-KGMCP-DOC-STATUS-SWEEP

## Summary

This is a doc-only frontmatter/content sweep, not a code change. Per `investigation.md`'s fully
resolved per-doc analysis, 11 of the 12 still-`status: active` docs under
`docs/engine/contracts/knowledge_gateway_mcp/` get a single-line `status: active` → `status:
historical` frontmatter edit (mechanical, verified live via `grep -n "^status:"` at Plan time —
all 11 confirmed on line 2 of their respective files, alongside `redaction_retention_policy.md`
also on line 2 and `keep_or_deprecate_decision.md` already `historical`). The 12th doc,
`redaction_retention_policy.md`, keeps `status: active` unchanged (its §2-§7 + partial §9 content
backs the live `tools/write_path_guard.py` module and the live `PreToolUse:Bash` secret-scan hook)
and instead receives an additive scoped-status note inserted between its intro paragraph and its
`## 1. Purpose` heading — a considered rejection of a physical file split, per the investigation's
precedent-absence and regression-risk reasoning. The plan closes with registry regeneration,
knowledge-index rebuild, frontmatter validation, and re-running the one regression-sensitive test
file unmodified to confirm the new note disturbed nothing it asserts.

## Steps

### Step 1 — Flip `status: active` → `status: historical` on the 11 confirmed-historical docs
**Files:**
- `docs/engine/contracts/knowledge_gateway_mcp/phase1_baseline_comparison.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase3_pilot_acceptance_measurement.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_direct_tool_comparison.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_warm_direct_tool_comparison.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase4_workflow_recommendation.md`
- `docs/engine/contracts/knowledge_gateway_mcp/phase5_repeated_demand_measurement.md`
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/cache_migration_plan.md`
- `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
- `docs/engine/contracts/knowledge_gateway_mcp/audit_phase0_5.md`

**Change:** In each file, edit line 2 of the frontmatter block from `status: active` to `status:
historical`. No other line in any of these files changes. Confirmed live at Plan time (`grep -n
"^status:" docs/engine/contracts/knowledge_gateway_mcp/*.md`) that all 11 files currently carry
`status: active` on line 2 — the edit target is exact and unambiguous per file, no fuzzy matching
needed. `historical` is an already-valid enum member of `STATUS_VALUES = {"authoritative",
"active", "historical", "archive"}` (`tools/validate_frontmatter.py:44`) — no schema/tooling change
required to accept the new value.

Rationale per investigation.md (do not re-derive, this is settled): the 8 phase/measurement docs
are point-in-time records against a now-archived gateway (`tools/archive/knowledge_gateway_mcp.py`)
with no live consumer; `cache_migration_plan.md` and `evidence_cache_identity_contract.md` are
Phase-0 design contracts for archived modules
(`tools/knowledge_gateway_cache.py`/`_router.py`/`_packet_assembly.py`); `audit_phase0_5.md` is a
consolidated audit whose own trailing postscripts already point readers to the already-`historical`
`keep_or_deprecate_decision.md` as the current record.

**Do NOT touch:** Any other frontmatter field (`layer`, `authority`, `audience`, `tags`) in any of
these 11 files. Do NOT touch `keep_or_deprecate_decision.md` (already `historical` — zero diff
expected). Do NOT touch `redaction_retention_policy.md` in this step (handled separately in Step
2). Do NOT touch any `.json` schema file in the same directory (no frontmatter, not
registry-indexed, explicitly out of scope). Do NOT physically move or delete any file — content
stays in place, only the `status:` value changes.

**Verify:** `git diff --stat docs/engine/contracts/knowledge_gateway_mcp/` shows exactly these 11
files with a 1-line change each. `python3 tools/generate_registry.py --check` (dry-run diff mode,
per test_plan.md's Anti-Drift Test Guards) shows exactly 11 `status` field diffs and zero unrelated
diffs.

---

### Step 2 — Add scoped-status note to `redaction_retention_policy.md` (status unchanged)
**Files:** `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`

**Change:** Do **not** touch line 2 (`status: active` stays exactly as-is — confirmed correct,
this is the one file in the 12 that is *not* flipped). Insert a new blockquote note as a distinct
paragraph immediately after the existing intro paragraph (which ends `...produced by
`TCK-20260814-KGMCP-CONTRACT-SCHEMAS` and `TCK-20260814-KGMCP-EVIDENCE-CACHE-IDENTITY`.` — read at
`redaction_retention_policy.md:9-16`) and before the `## 1. Purpose` heading (currently at
`redaction_retention_policy.md:18`). Concretely: after the blank line that currently separates the
intro paragraph from `## 1. Purpose`, insert the note text below, followed by another blank line,
then leave `## 1. Purpose` and everything after it completely untouched.

Draft note text (implementer may lightly copyedit but must preserve every fact and every named
section number):

```
> **Scope note (added by TCK-20260909-KGMCP-DOC-STATUS-SWEEP):** This document's frontmatter
> `status:` remains `active`, but its content is now mixed-currency following the archival of the
> Knowledge Gateway MCP gateway (`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`). **Still live and
> enforced today:** §2 Eligible Source Types / Allowlist, §3 Redaction Rules, §4 Secret-Scan
> Disclosure, §5 Payload Size Cap, §6 Redaction-Policy Version, §7 Never-Cache Enumeration, and —
> within §9 — only the `open_connection_with_limits()` paragraph (WAL mode, busy_timeout, chmod
> 0600). This subset is implemented today in `tools/write_path_guard.py`, the current source of
> truth for the live behavior, and §4's `scan_for_secrets()` is called directly by the live
> `PreToolUse:Bash` secret-scan hook (`.claude/settings.json`). **Historical, describing only the
> archived payload-caching feature:** §1's framing (future cached payload rows), §8 Token-Counting
> Method, the remainder of §9 (`check_db_size_within_limit()`, `execute_bounded_transaction()`,
> `acquire_write_guard()`/`release_write_guard()`), §10 Cache-GC Defaults, and §11 Ratification
> Status. These sections are retained for historical/audit context only and no longer describe
> currently-enforced behavior.
```

This is purely additive — no existing line in the file is deleted, reworded, or reordered.
Cross-checked against every substring `tests/docs/test_redaction_retention_policy_doc.py` asserts
(read in full at Plan time, `tests/docs/test_redaction_retention_policy_doc.py:1-191`): the test's
6 test functions only assert that specific substrings are *present* somewhere in the file (plain
`in text` checks, e.g. `"## 1. Purpose" in text`, `"not a production-complete secret scanner" in
text`, `"kgmcp_char_heuristic_v1" in text`, `"Ratified as drafted" in text`,
`"TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION" in text`, `"No changes were made to §2" in
text`); none of them assert an absence, an exact line count, a specific heading order, or a
specific occurrence count. The draft note above does not remove, reword, or duplicate-in-conflict
any of those asserted strings (it references section numbers like "§2" and "§9" in prose, not the
literal heading text `## 1. Purpose`, so it cannot be mistaken for a second copy of a required
heading). Because the note is inserted before `## 1. Purpose` and after the existing intro
paragraph, every required heading/phrase from `## 1. Purpose` onward stays exactly where it was,
byte-for-byte.

**Do NOT touch:** Line 2 `status:` value (must stay `active`). Do NOT touch `## 1. Purpose` through
`## 11.` (or later) — no heading text, no required phrase, no code-cross-checked value
(`MAX_PAYLOAD_BYTES`, `kgmcp_char_heuristic_v1`, ratification ticket ID, etc.) may be edited,
reworded, or removed. Do NOT perform a physical file split (investigation explicitly evaluated and
rejected this — no precedent in the repo for a per-section status, and it would force a nontrivial,
regression-risking rewrite of `tests/docs/test_redaction_retention_policy_doc.py`). Do NOT edit
`tools/write_path_guard.py` or any other code file as part of "fixing" this doc — this ticket makes
zero code changes.

**Verify:** `tests/docs/test_redaction_retention_policy_doc.py` (all 6 tests) still passes
unmodified (see Step 6). `git diff docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
shows only an insertion (no deleted/changed lines) and confirms line 2 is unchanged.

---

### Step 3 — Regenerate `docs/REGISTRY.yaml`
**Files:** `docs/REGISTRY.yaml` (generated output); driven by `tools/generate_registry.py`

**Change:** Run `make docs-registry` (or the underlying `python3 tools/generate_registry.py`
regeneration command it wraps) after Steps 1-2 land. `tools/generate_registry.py`'s `collect_docs()`
walks `docs/**/*.md` and re-derives each entry's `status` field from live frontmatter — this is the
**only** writer of `docs/REGISTRY.yaml` in the repository (confirmed by investigation.md's Prior
Work section and by this ticket's own Related Code Areas listing only this one tool against the
registry; no other script or pipeline phase writes this file directly, so there is no concurrent-
writer/ordering hazard to resolve here — Finalize's own post-migration self-check, referenced in
CLAUDE.md's "After Work" section, calls this exact same regeneration path unconditionally, so
running it now and again at Finalize is idempotent, not a double-write conflict, since both calls
fully re-derive the file from current on-disk frontmatter rather than appending).

**Do NOT touch:** Any entry for a doc outside `docs/engine/contracts/knowledge_gateway_mcp/` — the
regeneration is a full-repo re-derive, so confirm no unrelated entries changed (see Step 3's
Verify).

**Verify:** Spot-check the regenerated `docs/REGISTRY.yaml` for at least 3 of the 11 flipped docs
(e.g. `phase1_baseline_comparison.md`, `cache_migration_plan.md`, `audit_phase0_5.md`) showing
`status: historical`, plus `redaction_retention_policy.md` still showing `status: active`. Run
`git diff --stat docs/REGISTRY.yaml` and confirm only KGMCP-related entries changed (no unrelated
doc's registry entry drifted) — this doubles as the test_plan.md Anti-Drift Test Guard requiring
`git diff --stat` to show no changes outside `docs/engine/contracts/knowledge_gateway_mcp/` and
`docs/REGISTRY.yaml` themselves.

---

### Step 4 — Rebuild the knowledge-search index
**Files:** none under version control directly touched by hand; driven by `make
knowledge-index-update`

**Change:** Run `make knowledge-index-update` so `search_docs`/the retrieval index picks up the 11
new `historical` statuses and stops ranking the retired docs as live guidance — this is the actual
user-visible symptom motivating the ticket (per the ticket's own Request Summary) and is AC #4
verbatim. This step has no other writers to coordinate with: it is a read-derive-rebuild of the
search index from on-disk doc content plus `docs/REGISTRY.yaml` (already regenerated in Step 3), it
does not mutate any source doc, and no other pipeline phase runs this command concurrently with a
Plan/Implement step.

**Do NOT touch:** Any doc content as a side effect of this step — it must be index-rebuild only.

**Verify:** Command exits 0. Per test_plan.md's Integration/retrieval note, `tests/tools/test_knowledge_search.py`
serves as the smoke check that the index-build machinery completed cleanly against the changed
files (see Step 7).

---

### Step 5 — Validate frontmatter on all 12 touched docs
**Files:** all 11 files from Step 1 plus `redaction_retention_policy.md` from Step 2 (12 total)

**Change:** Run, for each of the 12 files (or once over the whole directory, which also covers
`keep_or_deprecate_decision.md` and the excluded `.json` files as an extra collateral-damage
check):

```
python3 tools/validate_frontmatter.py docs/engine/contracts/knowledge_gateway_mcp/ --content-type doc
```

CLI signature confirmed live at Plan time via `python3 tools/validate_frontmatter.py --help`:
`usage: validate_frontmatter.py [-h] [--content-type {doc,ticket,artifact,archive}] path` — `path`
accepts either a single file or a directory, and `--content-type doc` is a valid enum member. This
is exactly the invocation named in the ticket's AC #5 and in test_plan.md's Anti-Drift Test Guards.
Running it over the whole directory (not just the 11 changed files) is the stronger form
recommended by test_plan.md, since it also confirms zero collateral frontmatter damage to
`redaction_retention_policy.md` (content changed, `status:` should not have) and to
`keep_or_deprecate_decision.md` (should show zero diff at all).

**Do NOT touch:** Nothing is mutated by this step — it is read-only validation.

**Verify:** Command exits 0 with no reported errors for all files in the directory.

---

### Step 6 — Re-run `tests/docs/test_redaction_retention_policy_doc.py` unmodified
**Files:** `tests/docs/test_redaction_retention_policy_doc.py` (read/run only — no edits)

**Change:** Run:

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/docs/test_redaction_retention_policy_doc.py -v
```

This is the primary regression guard named by both the ticket (AC #2's "not wrongly retired") and
test_plan.md ("the single highest-risk regression point in this ticket"). All 6 tests must pass
with zero modification to the test file itself — a passing run with an untouched test file is the
proof that Step 2's additive note did not disturb any required heading or phrase.

**Do NOT touch:** The test file itself. If any assertion fails, the fix is to correct the inserted
note in `redaction_retention_policy.md` (Step 2), never to loosen or remove the failing assertion —
per CLAUDE.md's Gate Integrity rule, a failing test here is a real signal to fix the doc, not an
obstacle to edit around.

**Verify:** `6 passed` (or however many tests currently exist in that file — confirmed 6 test
functions at Plan time by reading the file in full) in the pytest output.

---

### Step 7 — Run the remaining scoped regression suite from test_plan.md
**Files:** none changed; test-only

**Change:** Run the remaining two scoped commands test_plan.md names, to confirm the registry/
frontmatter-validation tooling and the live `write_path_guard.py` module are both unaffected:

```
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -v
/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest tests/tools/test_write_path_guard.py -v -m "not slow"
```

The `test_write_path_guard.py` run is specifically the guard against an implementer "fixing" the
doc by editing the code instead (test_plan.md's Anti-Drift Test Guards) — this ticket makes zero
`tools/` changes, so this file's full pass with zero code diff in `tools/write_path_guard.py`
confirms that boundary held.

**Do NOT touch:** `tools/write_path_guard.py` or `tools/generate_registry.py`/`tools/validate_frontmatter.py`
source — these are run against, not modified by, this ticket.

**Verify:** All tests pass in both commands.

## Scope Guards

Restated from the ticket's Out of Scope and investigation.md's Anti-Drift Hazards — none of the
following may be touched by this plan's execution:

- **Never flip `redaction_retention_policy.md`'s `status:` value.** It must stay `active` through
  every step. This is the single highest-risk drift pattern in this ticket (accidentally
  pattern-matching it into the same bulk edit as the other 11 files).
- **Never physically move or delete any of the 13 files** in
  `docs/engine/contracts/knowledge_gateway_mcp/` — they stay in place as historical record per the
  ticket's own Out of Scope.
- **Never touch anything in `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s own scope**: the
  hard-delete of `tools/archive/`, parity-entry finalization, or `norecursedirs` cleanup. That
  ticket remains independently blocked on its own 2-week monitoring window regardless of this
  ticket landing.
- **Never touch the `.json` schema files** in the same directory
  (`*.schema.json`, `provider_capabilities_*.json`) — no frontmatter, not registry-indexed, out of
  scope by the ticket's own text.
- **Never widen scope to `docs/engine/contracts/knowledge_gateway_mcp_contract.md`** (the sibling
  top-level wire-contract document one directory up) — explicitly outside this ticket's named
  Scope; flagged in investigation.md as a possible future ticket, not this one.
- **Never re-litigate the Option C deprecation decision** — settled per
  `keep_or_deprecate_decision.md` §4.
- **Never edit `tools/write_path_guard.py` or any other `src/`/`tools/` code** — this is a doc-only
  ticket; zero code changes are in scope.
- **Never physically split `redaction_retention_policy.md`** into a live file and a historical
  file — investigation.md explicitly evaluated and rejected this approach (no repo precedent for a
  per-section status, and it would force a risky rewrite of the regression-tested
  `tests/docs/test_redaction_retention_policy_doc.py`). Only the additive scoped note from Step 2
  is in scope.
- **Never loosen or edit `tests/docs/test_redaction_retention_policy_doc.py`'s assertions** to make
  Step 2's note "fit" — if the note conflicts with an assertion, fix the note, not the test.

## Dependency Map

Steps 1 and 2 are independent of each other (different files, no shared line ranges) and can be
done in either order or in parallel by the implementer. Step 3 (registry regeneration) depends on
Steps 1 and 2 both being complete, since it re-derives from all 12 files' current on-disk state.
Step 4 (index rebuild) depends on Step 3 being complete (it should reflect the regenerated
registry). Step 5 (frontmatter validation) can run any time after Steps 1-2, independent of Steps
3-4. Steps 6 and 7 (test re-runs) depend only on Step 2 (Step 6) and Steps 1-2 (Step 7,
confirming zero code drift) respectively, and can run before or after Steps 3-4.

Suggested execution order: Step 1 → Step 2 → Step 6 (fast feedback on the highest-risk change) →
Step 5 → Step 3 → Step 4 → Step 7 (final full confirmation).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Each of the 12 `status: active` docs individually assessed and either changed or explicitly justified as staying `active` | Step 1 (11 flipped to `historical`) + Step 2 (`redaction_retention_policy.md` justified and left `active`) | `git diff --stat` per-file review (Step 1/2 Verify); investigation.md's per-doc reasoning is the recorded justification |
| `redaction_retention_policy.md`'s still-live content not wrongly retired — resolved by split or scoped note, decision recorded | Step 2 | `tests/docs/test_redaction_retention_policy_doc.py` (Step 6) |
| `docs/REGISTRY.yaml` regenerated and reflects new statuses | Step 3 | Manual spot-check (Step 3 Verify) + `tests/tools/test_generate_registry.py` (Step 7) |
| `make knowledge-index-update` run so retrieval stops surfacing retired docs as live | Step 4 | Command exit code + `tests/tools/test_knowledge_search.py` smoke check (Step 7 scope note) |
| `python3 tools/validate_frontmatter.py <each changed doc> --content-type doc` passes | Step 5 | Command exit code (Step 5 Verify) + `tests/tools/test_validate_frontmatter.py` (Step 7) |

## Anti-Drift Notes

- The single highest-risk action in this entire plan is accidentally including
  `redaction_retention_policy.md` in the Step 1 bulk `status:` flip pattern, since it is
  alphabetically and structurally identical to the other 11 files being edited the same way in the
  same session. Step 1's file list explicitly excludes it; Step 2 explicitly calls out "do NOT
  touch line 2." Treat this as the one file that must be double-checked with `git diff` after Step
  1 completes, before moving to Step 2.
- `audit_phase0_5.md`'s flip to `historical` was a genuine judgment call, not a default — the
  investigation resolved it with specific reasoning (its own postscripts point to
  `keep_or_deprecate_decision.md` as current; "retains reference value" isn't a distinguishing
  reason vs. its 8 sibling phase docs). Do not re-open this question during implementation; it is
  settled.
- The scoped note added in Step 2 must remain purely additive. If, during implementation, it turns
  out inserting the note exactly where specified would somehow require touching an existing line
  (it should not, per the read file structure at Plan time), stop and flag rather than improvising
  a workaround that touches `## 1. Purpose` or later content.
- `docs/REGISTRY.yaml` is regenerated a second time, unconditionally, by Finalize's own
  post-migration self-check per CLAUDE.md's "After Work" section — Step 3's regeneration here is
  not redundant or conflicting with that; both fully re-derive the file from on-disk frontmatter,
  so running it twice in the same ticket's lifecycle is idempotent, not a double-write hazard.
- No `docs/parity_ledger/` entry needs updating — investigation.md confirmed all relevant
  KGMCP-arc entries (`INFRA-340`-`INFRA-359`) are already `status: verified` with no P0 among them,
  and a pure `status:` frontmatter sweep is not a behavior change requiring a new entry.

## Unresolved Questions

None. Every open question investigation.md flagged (the `audit_phase0_5.md` judgment call, the
`redaction_retention_policy.md` split-vs-note decision) was resolved with explicit reasoning in
that document and carried forward into this plan's steps without re-litigation, per the ticket's
own Assumptions/Open Questions section instructing exactly that ("decide it explicitly and record
the reasoning rather than defaulting either way" — done in investigation.md, not deferred to
Implement).
