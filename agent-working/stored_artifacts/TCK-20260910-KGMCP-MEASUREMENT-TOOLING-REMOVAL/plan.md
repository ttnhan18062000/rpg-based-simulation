---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL
artifact_type: plan
tags: [agent-monitoring, mcp]
---

# Implementation Plan — TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL

## Summary

This is a pure-deletion/cleanup ticket: remove 3 orphaned KGMCP measurement modules under
`tools/agent-monitoring/`, remove the exact 7 fixtures that fall with them (keeping the 2 fixtures
with live `tests/docs/` consumers), add 2 architecture-guard tests to lock the outcome, fix a
now-stale comment citation in `tools/write_path_guard.py`, and update the 2 docs
(`docs/agent-monitoring/README.md`, `docs/parity_ledger/infrastructure.yaml`'s `INFRA-334`) that
independently describe the deleted modules as present. The investigation already re-derived and
confirmed every classification (module consumer set, fixture 7/2 split, doc/parity impact) — this
plan does not re-investigate, only sequences the mechanical execution with a final re-verification
step first, since the ticket's own stated risk is trusting a stale classification.

**Resolved judgment call:** the `tools/write_path_guard.py:61` comment fix is **included** in this
plan (Step 5). The investigation flagged it as "defensible either way" but recommended inclusion as
a same-session follow-through of this ticket's own fixture deletion (this ticket is the only one
whose action makes the comment's citation stale, per investigation.md's Scope Determination
discussion). Deciding here per the planner's mandate to resolve rather than defer resolvable
judgment calls: **include it**. It is comment-only, zero-behavior-change, and leaving a citation to
a file this same ticket deletes would be an immediate, avoidable inconsistency.

## Steps

### Step 1 — Final pre-delete consumer re-verification
**Files:** none changed; read-only grep/verification step.
**Change:** Immediately before any deletion, re-run the consumer grep from investigation.md to
guard against drift between investigation and implementation (another concurrent session could
have added a new consumer in the interim — see CLAUDE.md's shared-worktree hazard). Run, from repo
root:
```
grep -rn "kgmcp_baseline_corpus\|kgmcp_baseline_runner\|kgmcp_phase5_repeated_demand_measurement_runner" tools/ tests/ .claude/ Makefile 2>/dev/null | grep -v "^tools/agent-monitoring/kgmcp_baseline_corpus.py:\|^tools/agent-monitoring/kgmcp_baseline_runner.py:\|^tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py:"
grep -rln "kgmcp_phase1_baseline_comparison_results.json\|kgmcp_phase2_baseline_recomparison_results.json\|kgmcp_phase3_pilot_acceptance_measurement_results.json\|kgmcp_phase4_warm_direct_tool_comparison_results.json\|kgmcp_measurement_baseline_corpus_results.json\|kgmcp_phase5_events_investigate_snapshot.json\|kgmcp_phase5_working_log_snapshot.json" tools/ tests/ 2>/dev/null
```
Expected result: zero hits for the first command (modules have no live `.py`/`.claude`/`Makefile`
consumer outside themselves), zero `.py` hits for the second (the 7 fixtures have no code
consumer — doc/ticket/parity-ledger text hits are expected and fine, confirmed already in
investigation.md's fixture table). If either command surfaces a new hit not already accounted for
in investigation.md, **stop and re-flag** rather than proceeding — do not silently delete.
**Do NOT touch:** nothing is modified in this step.
**Verify:** No test to run; this is a go/no-go gate for Steps 2-3. Confirmed clean before
proceeding (per investigation.md, expected outcome).

### Step 2 — Delete the 3 orphaned modules
**Files:**
- `tools/agent-monitoring/kgmcp_baseline_corpus.py` (delete)
- `tools/agent-monitoring/kgmcp_baseline_runner.py` (delete)
- `tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py` (delete)
**Change:** `git rm tools/agent-monitoring/kgmcp_baseline_corpus.py
tools/agent-monitoring/kgmcp_baseline_runner.py
tools/agent-monitoring/kgmcp_phase5_repeated_demand_measurement_runner.py`. These are confirmed
zero-consumer (investigation.md "The 3 modules" section; re-confirmed Step 1) — no other writer or
reader touches these files, so there is no ordering/race concern for this deletion itself.
**Do NOT touch:** any other file under `tools/agent-monitoring/` — in particular do not touch
`tools/agent-monitoring/search_mcp.py` (imported by the deleted `kgmcp_baseline_runner.py`, but it
has other live callers and must survive) or `tools/agent-monitoring/registry_query.py` (imported by
the deleted phase5 runner, same reasoning).
**Verify:** Step 1's zero-consumer grep result is the proof this doesn't break anything;
`pytest tests/tools/test_write_path_guard.py tests/tools/test_knowledge_gateway_archival.py -v`
still passes (these do not import the deleted modules).

### Step 3 — Delete the 7 orphaned fixtures
**Files (all under `tests/tools/fixtures/`, all delete):**
- `kgmcp_phase1_baseline_comparison_results.json`
- `kgmcp_phase2_baseline_recomparison_results.json`
- `kgmcp_phase3_pilot_acceptance_measurement_results.json`
- `kgmcp_phase4_warm_direct_tool_comparison_results.json`
- `kgmcp_measurement_baseline_corpus_results.json`
- `kgmcp_phase5_events_investigate_snapshot.json`
- `kgmcp_phase5_working_log_snapshot.json`
**Change:** `git rm` each of the 7 files above. Investigation.md's fixture table (re-verified
independently of the ticket's own classification) confirms: 4 are outright orphaned (only
ticket/stored_artifacts/historical-doc text references them, no `.py` consumer), 3 are read only by
the 2 runner modules just deleted in Step 2 (`kgmcp_measurement_baseline_corpus_results.json`
written by `kgmcp_baseline_runner.py`:56-58; `kgmcp_phase5_events_investigate_snapshot.json` and
`kgmcp_phase5_working_log_snapshot.json` read by
`kgmcp_phase5_repeated_demand_measurement_runner.py`:71-76). No other writer or reader touches
these 7 paths.
**Do NOT touch — explicit exclusion, this is the ticket's stated primary risk:**
`kgmcp_phase4_direct_tool_comparison_results.json` and
`kgmcp_phase5_repeated_demand_measurement_results.json` must NOT be deleted. Both are read directly
via `json.loads()` by live tests (`tests/docs/test_phase4_direct_tool_comparison_doc.py`:22-23 and
`tests/docs/test_phase5_repeated_demand_measurement_doc.py`:26-31 respectively), confirmed to
import no runner module. Before running `git rm`, list the 7 target filenames and diff them against
the 9-fixture family to confirm these 2 are not in the delete list.
**Verify:**
`pytest tests/docs/test_phase4_direct_tool_comparison_doc.py
tests/docs/test_phase5_repeated_demand_measurement_doc.py -v` passes unmodified (this is the
anti-regression check per test_plan.md — both read their fixture directly, so a wrong deletion
fails immediately with `FileNotFoundError`).

### Step 4 — Add the 2 architecture-guard tests
**Files:** `tests/tools/test_knowledge_gateway_archival.py` (extend with 2 new test functions and
2 new module-level name lists — do NOT add to the existing `_ARCHIVED_FILENAMES` list, which per
that file's own docstring (lines 1-6, read confirmed) is specifically the gateway-package set from
`TCK-20260907`/`TCK-20260908`; conflating it with the separate measurement-tooling family would
misdocument what the list represents).
**Change:** Following the existing file's pattern (`_TOOLS_DIR`/`_ARCHIVE_DIR` path constants
already defined at lines 12-13; `test_gateway_modules_archived_not_present_at_old_paths` at
lines 25-28 as the model to mirror), add:
```python
_MEASUREMENT_TOOLING_FILENAMES = [
    "kgmcp_baseline_corpus.py",
    "kgmcp_baseline_runner.py",
    "kgmcp_phase5_repeated_demand_measurement_runner.py",
]

_REMOVED_MEASUREMENT_FIXTURES = [
    "kgmcp_phase1_baseline_comparison_results.json",
    "kgmcp_phase2_baseline_recomparison_results.json",
    "kgmcp_phase3_pilot_acceptance_measurement_results.json",
    "kgmcp_phase4_warm_direct_tool_comparison_results.json",
    "kgmcp_measurement_baseline_corpus_results.json",
    "kgmcp_phase5_events_investigate_snapshot.json",
    "kgmcp_phase5_working_log_snapshot.json",
]

_RETAINED_MEASUREMENT_FIXTURES = [
    "kgmcp_phase4_direct_tool_comparison_results.json",
    "kgmcp_phase5_repeated_demand_measurement_results.json",
]


def test_kgmcp_measurement_modules_no_longer_exist():
    for filename in _MEASUREMENT_TOOLING_FILENAMES:
        path = _TOOLS_DIR / "agent-monitoring" / filename
        assert not path.exists(), f"expected {path} to no longer exist (removed measurement tooling)"


def test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present():
    fixtures_dir = _REPO_ROOT / "tests" / "tools" / "fixtures"
    for filename in _REMOVED_MEASUREMENT_FIXTURES:
        path = fixtures_dir / filename
        assert not path.exists(), f"expected {path} to no longer exist (removed measurement fixture)"
    for filename in _RETAINED_MEASUREMENT_FIXTURES:
        path = fixtures_dir / filename
        assert path.exists(), f"expected {path} to still exist (live tests/docs/ consumer)"
```
`_REPO_ROOT` is already defined at line 11 of this file — reuse it, do not redefine.
This matches test_plan.md's "New Tests Required" section verbatim (test names
`test_kgmcp_measurement_modules_no_longer_exist` and
`test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present`), which explicitly names this file
as the chosen location (not a new standalone file) — record this choice in the ticket's
Implementation Notes at close.
**Do NOT touch:** the 3 existing test functions in this file (lines 25-40) or `_ARCHIVED_FILENAMES`
(lines 15-22) — those are `TCK-20260908`'s regression guard for the gateway package, unrelated to
this ticket's measurement-tooling family.
**Verify:** `pytest tests/tools/test_knowledge_gateway_archival.py -v` — all 5 tests (3 existing +
2 new) pass. Must run this step only after Steps 2 and 3 are complete (the new tests assert
non-existence/existence of files those steps delete).

### Step 5 — Fix the stale comment citation in `tools/write_path_guard.py`
**Files:** `tools/write_path_guard.py` (comment-only edit at line 61, read and confirmed at
`tools/write_path_guard.py:57-63`).
**Change:** The `MAX_PAYLOAD_BYTES` constant's trailing comment (lines 57-63) currently cites
`tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json` (line 61) as the source of
the observed `~10,612-30,548 bytes` range. Step 3 deletes that fixture. Repoint the citation to
`docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md` (confirmed
`status: historical` at that file's line 2, and confirmed to carry the identical figures at its own
lines 56 (`~10,612`) and 62 (`~30,548`) — read and verified directly, not inferred). Change line 61
from:
```
                                           # tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json),
```
to:
```
                                           # docs/engine/contracts/knowledge_gateway_mcp/phase2_baseline_recomparison.md:56,62),
```
No other line in the 57-63 comment block changes — the `MAX_PAYLOAD_BYTES = 65536` value and every
other word of the comment stay exactly as-is.
**Other writers to this resource:** `MAX_PAYLOAD_BYTES` is read by `check_size_cap()` in the same
module (per investigation.md, confirmed "uses only the live `MAX_PAYLOAD_BYTES` integer, never the
fixture") and cross-checked against doc text by
`tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant`
(confirmed by investigation.md to check only the constant value against doc text, never the
comment or the fixture path). No other module writes to this constant or this comment block — this
is a single-writer, comment-only edit with no concurrent-write or ordering concern.
**Do NOT touch:** `MAX_PAYLOAD_BYTES`'s value (`65536`) or any line of `check_size_cap()`'s logic
elsewhere in this module. A `git diff` on this file after this step must show only the one
`#`-prefixed line changed.
**Verify:** `pytest tests/tools/test_write_path_guard.py
tests/docs/test_redaction_retention_policy_doc.py -v` passes unmodified — both tests check the
constant/doc text, neither reads the comment, so this confirms the edit stayed comment-only.

### Step 6 — Update `docs/agent-monitoring/README.md`
**Files:** `docs/agent-monitoring/README.md` (the "## Knowledge Gateway MCP Phase 0 Measurement
Baseline" section, confirmed at lines 61-74 by direct read).
**Change:** This section presently describes `kgmcp_baseline_corpus.py` and
`kgmcp_baseline_runner.py` as present, current tooling with live file citations (lines 63-69), plus
a reference to the now-deleted `kgmcp_measurement_baseline_corpus_results.json` fixture (line 68).
Replace the section body with a one-line historical note (keep the heading so any external link
anchors to this section still resolve), e.g.:
```
## Knowledge Gateway MCP Phase 0 Measurement Baseline (one-time, separate from both cadences)

Removed by TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL — the corpus module, its runner, and the
fixture it produced no longer exist. See
`docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` (status: historical)
for the retained historical record of what this baseline measured.
```
Preserve the separate "2026-08-14" sub-note that follows this section (lines 76+ per the read
excerpt) unchanged — it describes `search_count`/`raw_investigation_count` relocating into
`generate_retro.py`, which is unrelated to this ticket's deletions and still accurate.
**Other writers to this resource:** This README is a hand-maintained doc, not machine-generated —
no other tool or pipeline phase writes to it. `docs/REGISTRY.yaml` indexes it by frontmatter but
does not rewrite its body. No concurrent-write concern.
**Do NOT touch:** any other section of this README (the `search_count`/`raw_investigation_count`
cadence description at lines 55-59, or anything above/below the target section) — this is a
targeted single-section edit.
**Verify:** `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py -v`
passes (confirms the edit didn't introduce a frontmatter or registry-shape violation). No dedicated
content test exists for this README's body text (confirmed no consumer test in investigation.md);
the guard here is doc-registry validity, not content assertion.

### Step 7 — Update `INFRA-334`'s `v2_evidence` via `parity_ledger_writer.py`
**Files:** `docs/parity_ledger/infrastructure.yaml` (entry `id: INFRA-334`, confirmed full text at
lines 8839-8867 by direct read) — edited only through
`tools/parity_ledger_writer.py::write_entry(shard_filename, entry, ledger_dir=None, db_path=None)`
(signature confirmed at `tools/parity_ledger_writer.py:90` by direct read; it validates via
`validate_entry()`, upserts by `id` into the shard, and rebuilds the derived parity index — never
edit this YAML with a raw `Edit` tool call).
**Change:** `INFRA-334`'s current `v2_evidence` field (confirmed verbatim by read) ends: "The other
source this entry's v2_evidence originally cited,
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, remains live and untouched by either ticket --
only this entry's own dedicated regression test is gone." This becomes false once Step 2 deletes
that file. Call `write_entry()` with the same `id: INFRA-334`, same `text`, same `status:
unsupported`, same `priority: P2`, same `legacy_evidence: null`, same `proof_type: regression`,
same `test_path: null`, same `divergence_note`, same `support_boundary` — only `v2_evidence`
changes, to state both the dedicated test (already gone, per existing text) and the corpus module
(now also gone, this ticket) are deleted, e.g.: "The dedicated regression evidence this entry cited
-- tests/tools/test_kgmcp_measurement_baseline.py -- was hard-deleted by
TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY ... and no longer exists anywhere in the repo. The other
source this entry's v2_evidence originally cited,
tools/agent-monitoring/kgmcp_baseline_corpus.py, was itself deleted by
TCK-20260910-KGMCP-MEASUREMENT-TOOLING-REMOVAL -- no evidence for this entry survives anywhere in
the repo." Do not change `status` (stays `unsupported`) or `test_path` (stays `null`) — this is a
P2, non-P0 entry, no passing `test_path` gate applies (confirmed by investigation.md's Parity
Ledger Overlap section).
**Other writers to this resource:** `docs/parity_ledger/infrastructure.yaml` is written by
`parity_ledger_writer.py::write_entry()` (this step) and, per repo convention, by the
`parity-updater` agent role during other tickets' Parity phase — no other ticket's work is active
on this same entry concurrently (investigation.md's Parity Ledger Overlap section confirms
`INFRA-339`, `INFRA-344`, `INFRA-350`, `INFRA-354`, `INFRA-355`, `INFRA-345` all need no update from
this ticket, so this step touches exactly one entry, `INFRA-334`, with no other in-flight writer to
it). `docs/REGISTRY.yaml` regeneration (Finalize phase) reads this file but does not write to it.
**Do NOT touch:** any other entry in `infrastructure.yaml` (`INFRA-339`, `INFRA-344`, `INFRA-350`,
`INFRA-354`, `INFRA-355`, `INFRA-345` all confirmed by investigation.md to need no change) — call
`write_entry()` once, for `INFRA-334` only.
**Verify:** the parity-ledger schema/build step inside `write_entry()` itself (raises on
`validate_entry()` failure); additionally run whatever parity-ledger schema test exists under
`tests/tools/` (test_plan.md references `tests/tools/test_parity_ledger_writer.py` "if present, or
equivalent" — run `pytest tests/tools/ -k "parity" -v` to catch whichever name is actually current).

### Step 8 — Final verification sweep
**Files:** none changed; verification only.
**Change:** Run the full scoped test set from test_plan.md's "Scoped Pytest Commands" section:
```
pytest tests/tools/test_write_path_guard.py tests/tools/test_knowledge_gateway_archival.py -v
pytest tests/docs/test_phase4_direct_tool_comparison_doc.py tests/docs/test_phase5_repeated_demand_measurement_doc.py tests/docs/test_redaction_retention_policy_doc.py -v
pytest tests/tools/ -k "registry or frontmatter or parity" -v
```
Additionally confirm via `git status`/`git diff --stat` that exactly 3 modules + 7 fixtures were
removed, exactly 1 test file was extended, exactly 2 docs were edited, and
`tools/write_path_guard.py` shows only a 1-line comment diff — matching this plan's scope exactly,
nothing extra.
**Do NOT touch:** run only the scoped commands above — never `pytest tests/` per this repo's
Testing Rule (test_plan.md reiterates this explicitly).
**Verify:** all of the above pass; this is the acceptance-criteria closing gate.

## Scope Guards

- Never delete `kgmcp_phase4_direct_tool_comparison_results.json` or
  `kgmcp_phase5_repeated_demand_measurement_results.json` — both have live `tests/docs/` consumers
  (`test_phase4_direct_tool_comparison_doc.py`, `test_phase5_repeated_demand_measurement_doc.py`)
  confirmed by direct read; deleting either breaks a passing test immediately.
- Never touch `MAX_PAYLOAD_BYTES`'s value or `check_size_cap()`'s logic in
  `tools/write_path_guard.py` — Step 5 is a single-line comment citation change only.
- Never re-open `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`'s already-settled `status: historical`
  adjudication for `docs/engine/contracts/knowledge_gateway_mcp/*.md` — those docs and
  `docs/plans/knowledge-gateway-mcp-proposal.md` are explicitly out of scope, leave their
  stale-but-historical citations as-is.
- Never touch `tools/retrieval_cache.py` or any retro/dashboard access-log code — that is
  `TCK-20260910-RETRIEVAL-CACHE-ACCESS-LOG-CHAIN-REMOVAL`'s separate scope.
- Never touch `tests/tools/test_knowledge_gateway_archival.py`'s existing 3 test functions or
  `_ARCHIVED_FILENAMES` list — those are `TCK-20260908`'s gateway-package regression guard, extend
  the file (Step 4) without modifying them.
- Never edit `docs/parity_ledger/infrastructure.yaml` with a raw `Edit`/`Write` tool call — only
  via `tools/parity_ledger_writer.py::write_entry()` (Step 7).
- Never touch `INFRA-339`, `INFRA-344`, `INFRA-350`, `INFRA-354`, `INFRA-355`, or `INFRA-345` in
  `infrastructure.yaml` — only `INFRA-334` needs an update per investigation.md.
- Never run `pytest tests/` unscoped.

## Dependency Map

- Step 1 (re-verification) must run before Steps 2 and 3 — it is the go/no-go gate.
- Step 2 (delete modules) and Step 3 (delete fixtures) are independent of each other but both
  depend on Step 1. Order between them does not matter (no fixture is deleted because a module was
  deleted first, or vice versa — both deletions are independently justified).
- Step 4 (new architecture-guard tests) depends on Steps 2 and 3 being complete — the new tests
  assert non-existence of files those steps delete and existence of files they retain; running
  Step 4 before Steps 2/3 would make the new tests fail against pre-deletion state.
- Step 5 (write_path_guard.py comment fix) depends on Step 3 specifically (it repoints a citation
  away from a fixture Step 3 deletes) but is otherwise independent of Steps 2, 4, 6, 7.
- Step 6 (README update) and Step 7 (parity-ledger update) both depend on Step 2 (they describe the
  corpus module as deleted) but are independent of each other and of Steps 3, 4, 5.
- Step 8 (final verification) depends on all prior steps being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| The three runner/corpus modules are removed, with no remaining import or invocation anywhere (`tools/`, `tests/`, `.claude/`, `Makefile`). | Step 1 (re-verify no consumer), Step 2 (delete) | Step 1's grep sweep; `pytest tests/tools/test_write_path_guard.py tests/tools/test_knowledge_gateway_archival.py -v` (Step 2); `test_kgmcp_measurement_modules_no_longer_exist` (Step 4) |
| Exactly seven fixtures are removed and the two named in Out of Scope are still present. | Step 3 (delete 7), Step 4 (guard test) | `test_orphaned_kgmcp_fixtures_removed_retained_fixtures_present` (Step 4) |
| `tests/docs/test_phase5_repeated_demand_measurement_doc.py` and the other `tests/docs/` fixture consumers still pass. | Step 3 | `pytest tests/docs/test_phase4_direct_tool_comparison_doc.py tests/docs/test_phase5_repeated_demand_measurement_doc.py tests/docs/test_redaction_retention_policy_doc.py -v` (Step 3 and Step 8) |
| Full `tests/tools/` and `tests/docs/` lanes pass (scoped per Testing Rule, not the whole suite). | All steps | Step 8's full scoped command set |

## Anti-Drift Notes

- The 7/2 fixture split is the ticket's own stated primary risk ("the split between 'orphaned,'
  'falls with the runners,' and 'keep' is the whole risk in this ticket") — Step 1's
  re-verification and Step 3's explicit diff-against-target-list check both exist specifically to
  guard this; do not shortcut either.
- `docs/agent-monitoring/README.md` and `INFRA-334` were not in the ticket's own Related Docs list
  — they were found independently by investigation.md. Both are required by this plan (Steps 6-7)
  even though the ticket body doesn't name them; this is expected per the investigation's own
  "independent re-derivation" mandate, not scope creep.
- The `write_path_guard.py:61` fix (Step 5) was an open judgment call in investigation.md; this
  plan resolves it as **included**, per the rationale in the Summary above. If a reviewer disagrees
  with this resolution, it is a single self-contained step that can be dropped without affecting
  any other step's correctness.
- No P0 parity entries are involved anywhere in this ticket's scope (confirmed by investigation.md)
  — no `test_path`-must-pass gate applies to Step 7's `INFRA-334` edit.
- This ticket touches no `src/` file and no Mechanics Bible chapter or `docs/engine/` contract
  applies — confirmed by investigation.md's "Mechanics / Engine Constraints: None" finding.
