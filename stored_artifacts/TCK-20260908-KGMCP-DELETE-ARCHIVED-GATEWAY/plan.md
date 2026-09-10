---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY
artifact_type: plan
tags: [ai, mcp, governance]
---

# Implementation Plan — TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY

## Summary

This ticket executes M2 steps 3-4 of the Knowledge Gateway MCP deprecation: hard-delete the 11
files under `tools/archive/` and the 15 files under `tests/archive/` (not 20 — the ticket's own
body text overstates the test-file count; `investigation.md`'s "Current Behavior" section
verified the real, current 15-file list via direct `ls`), remove the now-dead `"archive"`
`norecursedirs` entry from `pyproject.toml`, update two live tests that assert facts the delete
falsifies, update the 21 parity ledger entries the predecessor annotated, and update 3 planning/
contract docs to close out the milestone. The approach is a strict ordered sequence: verify zero
live call sites one final time, delete files, fix the fallout (tests, config, ledger, docs),
verify green. No behavior in `src/` changes; this is tooling/governance cleanup only. The
parity-ledger status question (what value replaces `verified` when a P1/P2 entry's sole cited
evidence is permanently deleted) is resolved below via a direct precedent already in the same
file (`INFRA-010`, `docs/parity_ledger/infrastructure.yaml:98-111`): `status: unsupported`, not
`missing` — see Step 8.

## Steps

### Step 1 — Final pre-delete zero-call-site re-verification

**Files:** none (verification only, no edits)
**Change:** Re-run, one more time, immediately before any delete in this session:
```
grep -rln "knowledge_gateway" tools/ src/ tests/ .claude/ docs/ --include="*.py" --include="*.md" --include="*.sh" --include="*.json" | grep -v '^tools/archive/\|^tests/archive/'
```
Compare the result against `investigation.md`'s "Confirmed zero remaining live call sites"
section and the ticket's own "Early Closure Decision" evidence block — every hit must be one of
the already-enumerated doc-prose/comment/test-name references (`tools/retrieval_cache.py`,
`tools/write_path_guard.py`, `tools/gate_checks/test_scope_coverage_static.py`,
`tools/agent-monitoring/kgmcp_baseline_runner.py`, `tools/agent-monitoring/generate_retro.py`,
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, `tests/tools/test_mcp_json_registration.py`'s
test function name). Zero *new* live call sites is the pass condition. If a new, previously
unseen hit appears, stop — do not delete — and escalate per the ticket's own Out of Scope rule
("if the window surfaces a real, live, undiscovered consumer... escalate instead").
**Do NOT touch:** any file — this step is read-only.
**Verify:** Manual diff of grep output against `investigation.md`'s enumerated list; no automated
test corresponds to this step.

### Step 2 — Hard-delete `tools/archive/` (11 files + `__pycache__/`)

**Files:**
- `tools/archive/knowledge_gateway_cache.py`
- `tools/archive/knowledge_gateway_mcp.py`
- `tools/archive/knowledge_gateway_packet_assembly.py`
- `tools/archive/knowledge_gateway_redaction.py`
- `tools/archive/knowledge_gateway_router.py`
- `tools/archive/start_knowledge_gateway_mcp.sh`
- `tools/archive/kgmcp_phase1_gateway_runner.py`
- `tools/archive/kgmcp_phase2_gateway_runner.py`
- `tools/archive/kgmcp_phase3_gateway_runner.py`
- `tools/archive/kgmcp_phase4_direct_tool_comparison_runner.py`
- `tools/archive/kgmcp_phase4_warm_direct_tool_comparison_runner.py`
- `tools/archive/__pycache__/` (directory, if present)

**Change:** `git rm tools/archive/knowledge_gateway_cache.py tools/archive/knowledge_gateway_mcp.py tools/archive/knowledge_gateway_packet_assembly.py tools/archive/knowledge_gateway_redaction.py tools/archive/knowledge_gateway_router.py tools/archive/start_knowledge_gateway_mcp.sh tools/archive/kgmcp_phase1_gateway_runner.py tools/archive/kgmcp_phase2_gateway_runner.py tools/archive/kgmcp_phase3_gateway_runner.py tools/archive/kgmcp_phase4_direct_tool_comparison_runner.py tools/archive/kgmcp_phase4_warm_direct_tool_comparison_runner.py`, then `rm -rf tools/archive/__pycache__` and, once the directory is empty, confirm `tools/archive/` itself has nothing left (do not `mkdir`/recreate it — leave it absent, matching how `tests/archive/` is also fully removed in Step 3). File count and identity confirmed by direct `ls -la tools/archive/` in `investigation.md`'s "Current Behavior" section (11 files total, matches the ticket's own "6 + 5" framing).
**Do NOT touch:** `tools/write_path_guard.py` (the extracted, still-live module — the ticket's own Out of Scope forbids any change to it or its consumers) and `tools/retrieval_cache.py`.
**Verify:** `git status --short tools/archive/` shows nothing (directory gone); `find tools/archive -type f 2>/dev/null | wc -l` returns nothing/0.

### Step 3 — Hard-delete `tests/archive/` (15 files)

**Files:**
- `tests/archive/test_kgmcp_baseline_corpus_dedup_coverage.py`
- `tests/archive/test_kgmcp_measurement_baseline.py`
- `tests/archive/test_kgmcp_phase1_baseline_comparison.py`
- `tests/archive/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/archive/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tests/archive/test_kgmcp_phase4_direct_tool_comparison.py`
- `tests/archive/test_kgmcp_phase4_warm_direct_tool_comparison.py`
- `tests/archive/test_kgmcp_phase5_repeated_demand_measurement.py`
- `tests/archive/test_knowledge_gateway_cache.py`
- `tests/archive/test_knowledge_gateway_contract_schemas.py`
- `tests/archive/test_knowledge_gateway_failure_semantics.py`
- `tests/archive/test_knowledge_gateway_mcp.py`
- `tests/archive/test_knowledge_gateway_packet_assembly.py`
- `tests/archive/test_knowledge_gateway_redaction.py`
- `tests/archive/test_knowledge_gateway_router.py`

**Change:** `git rm` all 15 files listed above (exact list per `investigation.md`'s direct `ls -la
tests/archive/` read, cross-checked against `stored_artifacts/TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE/plan.md`
Step 8's own 15-file list — they are the same 15 files; the 5 phase-runner test files were
already part of that original list, only content-edited later by
`TCK-20260909-HOTFIX-KGMCP-ORPHANED-PHASE-RUNNERS`, not newly added). This is the ticket's single
most important correction to its own scope text: the ticket's Related Code Areas says "20 files
under `tests/archive/`" — that count is wrong; the real, verified count is 15. Do not go looking
for 5 additional files that do not exist. Confirm `tools/archive/__pycache__`-equivalent for
tests (`tests/archive/__pycache__/`) is also removed if present.
**Do NOT touch:** `tests/tools/test_write_path_guard.py`, `tests/tools/test_retrieval_cache.py`,
`tests/docs/test_redaction_retention_policy_doc.py`, `tests/docs/test_phase4_direct_tool_comparison_doc.py`,
`tests/docs/test_phase4_workflow_recommendation_doc.py`, `tests/docs/test_phase5_repeated_demand_measurement_doc.py`
— all confirmed live and independent, and the last 3 are explicitly named in `investigation.md`'s
Anti-Drift Hazards as "must not be swept into this ticket's delete either."
**Verify:** `find tests/archive -type f -name '*.py' 2>/dev/null | wc -l` returns nothing/0;
`pytest tests/docs/test_phase4_direct_tool_comparison_doc.py tests/docs/test_phase4_workflow_recommendation_doc.py tests/docs/test_phase5_repeated_demand_measurement_doc.py -v --co`
still collects all 3 files (per `test_plan.md`'s "No accidental `tests/docs/` sweep guard").

### Step 4 — Remove the dead `"archive"` entry from `pyproject.toml`'s `norecursedirs`

**Files:** `pyproject.toml` (L52-62, `[tool.pytest.ini_options]` block)
**Change:** Read directly at `pyproject.toml:54-62` — current list is:
```toml
norecursedirs = [
    "reviews",
    "scratch",
    "stored_artifacts",
    ".venv",
    ".git",
    "node_modules",
    "__pycache__",
    "archive",
]
```
Remove exactly the `"archive",` line (leave every other entry, ordering, and the rest of
`[tool.pytest.ini_options]` — currently just `pythonpath = ["."]` — untouched). This is safe once
Steps 2-3 land: `investigation.md` confirmed via `find` that the only other directories literally
named `archive` (`docs/archive/`, `docs/plans/archive/`, `scripts/archive/`) hold zero
`test_*.py`/`*_test.py` files, so none of them need this exclusion for correctness.
**Do NOT touch:** `markers` or any other `[tool.pytest.ini_options]` key; do not remove
`"stored_artifacts"` or any other `norecursedirs` entry.
**Verify:** `git diff pyproject.toml` shows exactly one line removed and nothing else (per
`test_plan.md`'s "pyproject.toml scoped-edit guard"); `pytest tests/tools/test_ci_workflow_test_coverage.py -v` (after Step 5's companion test update) passes.

### Step 5 — Update `tests/tools/test_knowledge_gateway_archival.py`

**Files:** `tests/tools/test_knowledge_gateway_archival.py` (currently 39 lines, read in full)
**Change:** The file currently defines 3 tests over `_ARCHIVED_FILENAMES` (the same 6 source
files deleted in Step 2):
- `test_gateway_modules_archived_not_present_at_old_paths()` (L23-26) — asserts absence at the
  original `tools/` paths. **Stays valid unmodified** — still true after this ticket's delete.
- `test_gateway_modules_exist_at_archive_location()` (L29-32) — asserts each of
  `_ARCHIVED_FILENAMES` exists under `tools/archive/`. **This becomes false** after Step 2 and
  must be replaced. Rewrite it to assert absence from `tools/archive/` instead, e.g.:
  ```python
  def test_gateway_modules_no_longer_exist_at_archive_location():
      for filename in _ARCHIVED_FILENAMES:
          archived_path = _ARCHIVE_DIR / filename
          assert not archived_path.exists(), f"expected {archived_path} to be hard-deleted, not archived"
  ```
  Combined with the unmodified `test_gateway_modules_archived_not_present_at_old_paths()`, this
  proves the gateway package no longer exists anywhere in the repo (neither old path nor archive).
- `test_write_path_guard_exists_and_is_not_archived()` (L35-38) — **stays valid unmodified**
  (unaffected by this ticket; confirmed in `test_plan.md`'s regression surface list).
Also update the module docstring (L1-4), which currently describes "each module has a mirror
file under `tools/archive/`" — that framing is now stale; reword to state the gateway package no
longer exists anywhere (old path or archive), only its extracted `write_path_guard.py` remainder
survives.
**Do NOT touch:** the `_ARCHIVED_FILENAMES` list contents (still the correct 6-filename list to
assert absence of) or `test_write_path_guard_exists_and_is_not_archived()`'s body.
**Verify:** `pytest tests/tools/test_knowledge_gateway_archival.py -v` — all 3 tests pass post-delete.

### Step 6 — Update `tests/tools/test_ci_workflow_test_coverage.py` (L432-485 region only)

**Files:** `tests/tools/test_ci_workflow_test_coverage.py`
**Change:** Two real-repo-state tests in this region break on Steps 3-4's changes (both directly
read, confirmed at the cited line numbers):
- `test_pytest_norecursedirs_reads_real_pyproject_toml()` (L432-435): currently
  `assert "archive" in norecursedirs`. After Step 4, invert this to
  `assert "archive" not in norecursedirs` (proving the dead entry is genuinely gone, not just
  silently untested) — leave `assert "stored_artifacts" in norecursedirs` (L435) unchanged, it is
  unaffected by this ticket.
- `test_check_against_real_repo_state_recognizes_tests_archive_as_norecursedirs_excluded()`
  (L480-485): calls `check_ci_workflow_test_coverage(_REAL_WORKFLOW_PATH, _REPO_ROOT)` and indexes
  `by_condition["ci_test_dir_covered:tests/archive"]`. Once `tests/archive/` no longer exists as a
  directory (Step 3) and its checker no longer has anything to enumerate there, this key is most
  likely never produced, so the dict lookup raises `KeyError` rather than a clean assertion
  failure. **Delete this test function entirely** (its subject directory no longer exists — there
  is nothing left for it to assert) rather than attempting to rewrite it against a directory that
  is gone. Do not leave a test indexing a key that may not exist.
Leave the surrounding comment block (L422-429) explaining why this region exists — it remains
accurate historical context (`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`'s archival is what
prompted these tests originally) — optionally append one sentence noting
`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` completed the cleanup these tests were tracking.
**Do NOT touch:** `test_directory_is_excluded_from_pytest_collection_matches_any_path_segment()`
(L442-445) or `test_fixture_norecursedirs_excluded_directory_passes_instead_of_failing()`
(L452-477) — both use synthetic fixture data (`{"archive", "scratch"}`, `{"orphan"}`), not the
real repo state, and stay valid regardless of this ticket's delete (per `test_plan.md`'s explicit
"stay valid and must NOT be touched" note). Do not touch
`test_pytest_norecursedirs_returns_empty_set_for_missing_file()` (L438-439) either.
**Verify:** `pytest tests/tools/test_ci_workflow_test_coverage.py -v` passes in full.

### Step 7 — Full scoped regression run

**Files:** none (verification only)
**Change:** Run the ticket's own required AC gate:
```
pytest tests/tools/ tests/docs/ -v
```
This must pass in full — it is the ticket's own literal AC ("`tools/write_path_guard.py` and
`tools/retrieval_cache.py` remain fully functional, confirmed via `pytest tests/tools/ tests/docs/ -v` passing in full"). If anything outside Steps 2-6's scope breaks, stop and investigate
before proceeding to the doc/ledger steps below — do not paper over an unrelated failure.
**Do NOT touch:** do not run unscoped `pytest tests/` (forbidden by CLAUDE.md's Testing Rule and
`test_plan.md`'s "Never" list).
**Verify:** exit code 0, full pass count reported.

### Step 8 — Update the 21 `docs/parity_ledger/infrastructure.yaml` entries via `tools/parity_ledger_writer.py`

**Files:** `docs/parity_ledger/infrastructure.yaml` (entries INFRA-334, 335, 336, 337, 338, 339,
342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 354, 355, 356, 357)
**Change:** `docs/parity_ledger/schema.json`'s `status` enum (read directly) is exactly
`["verified", "divergent", "missing", "unsupported", "legacy_verified"]`. `verified`/`divergent`
require non-null `v2_evidence`+`test_path`; `divergent` additionally requires
`divergence_note`; neither `missing` nor `unsupported` requires any of those fields to be
non-null. This resolves the investigation's open question: **`docs/parity_ledger/infrastructure.yaml:98-111`
(`INFRA-010`) is a direct, already-existing precedent for exactly this situation** — a whole
subsystem (RabbitMQ) was removed entirely by a prior ticket
(`TCK-20260817-DEAD-INFRA-REMOVAL-EPIC`), and the entry was moved from `verified` to
**`status: unsupported`**, with `v2_evidence` rewritten to explain the removal and cite the
removal ticket, `test_path: null`, and `divergence_note` stating the removal and that the
behavior "is inapplicable, not verified." Use `unsupported`, not `missing`, for this ticket's
entries too — `missing` in this ledger (see `docs/parity_ledger/substrate.yaml:3360-3370`,
`SUB-325`/`SUB-326`) is used for behavior that was never implemented in V2 at all, which is not
this case (the underlying behavior may still be presumed correct; only its dedicated regression
test evidence is gone).

Per-entry disposition (based on `investigation.md`'s "Parity Ledger Overlap" table, itself a real
read of every entry's current `test_path`/`v2_evidence`, further verified in this planning pass by
extracting each of INFRA-342/343/345/346/349/355's full `test_path` field text directly):

**Rule A — sole/primary evidence permanently deleted → `status: unsupported`** (18 entries:
INFRA-334, 335, 336, 337, 338, 339, 343, 344, 347, 348, 349, 350, 351, 352, 354, 355, 356, 357).
For each: set `status: unsupported`, `test_path: null`, rewrite `v2_evidence` to state the cited
test file(s) were hard-deleted by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` (name this ticket)
and no longer exist anywhere in the repo (archived or otherwise), and set/append `divergence_note`
stating the behavior is presumed still correct in `src/`/`tools/write_path_guard.py` where
applicable but its dedicated regression-locking test evidence no longer exists — mirroring
`INFRA-010`'s exact `divergence_note` phrasing pattern ("`<subsystem>` removed entirely by
`<ticket>`; `<behavior>` is inapplicable, not verified.").
  - **Note on INFRA-343 specifically — Architecture-Review Round 2 finding, fixed here.**
    Originally (Round 1 submission) misclassified in the "No-change" bucket below alongside
    INFRA-342, on the assumption both entries already cite a live successor. Independently
    re-verified directly against `docs/parity_ledger/infrastructure.yaml:9468-9583`: INFRA-343's
    core claim is "real cache read/write wiring into the live Knowledge Gateway MCP gateway" —
    `compute_lookup_identity()`, `perform_cache_lookup()`/`perform_cache_write()`, and
    specifically the `_run_knowledge_context()`/`_run_knowledge_status()` MCP-tool integration
    hooks. Its `v2_evidence`/`test_path` cite `tools/archive/knowledge_gateway_cache.py` and
    `tools/archive/knowledge_gateway_mcp.py` (both hard-deleted by Step 2) plus
    `tests/archive/test_knowledge_gateway_{cache,mcp,failure_semantics,redaction}.py` (hard-deleted
    by Step 3) as the PRIMARY evidence. The only surviving live citation —
    `tests/tools/test_retrieval_cache.py::TestProviderResultCache`/`TestMigration003`/
    `TestProviderResultCacheStats` — tests `retrieval_cache.py`'s own Level-1 provider-result-cache
    functions, not the actual gateway-orchestration hooks the entry's `text` claims. Unlike
    INFRA-342 (whose claimed symbols were genuinely relocated to live `tools/write_path_guard.py`
    by the predecessor), no live successor of INFRA-343's MCP-wiring code exists anywhere — that
    orchestration logic lived only in `tools/archive/knowledge_gateway_mcp.py` and is being
    permanently deleted, not relocated. INFRA-343 therefore moves to Rule A, joining INFRA-349 and
    INFRA-355 below as a case with a partially-live `test_path` whose surviving citation does not
    actually prove the entry's core claim.
  - Note on INFRA-349 and INFRA-355 specifically: both have a *mixed* `test_path` today (part
    live, part deleted), but their entry `text`'s core claim is not directly proven by the
    surviving live citation alone: INFRA-349's claim is that the Level 2 cache is "wired
    genuinely live into the production `knowledge_context` call path" — the surviving
    `tests/tools/test_retrieval_cache.py::TestMigration004`/`TestContextPacketCache`/
    `TestContextPacketCacheStats` citations test the cache module's own read/write functions in
    isolation, not the actual `knowledge_context` MCP tool integration; the deleted
    `tests/archive/test_knowledge_gateway_mcp.py` AC1-AC7 tests (e.g.
    `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`) were the
    direct end-to-end wiring proof. INFRA-355's claim is about a completed measurement
    ("Measures, honestly, whether real repeated/semantically-equivalent question demand
    exists..."); its surviving citation (`tests/docs/test_phase5_repeated_demand_measurement_doc.py`)
    is a doc-parity guard, not a re-verification of the measurement itself, which lived in the
    now-deleted `tests/archive/test_kgmcp_phase5_repeated_demand_measurement.py`. Both therefore
    fall to Rule A despite having a partially-live `test_path` today.

**Rule B — mixed `test_path` where the surviving live citation directly proves the entry's core
textual claim → stays `status: verified`, trim `test_path`/`v2_evidence` to drop only the
dead-file citation, AND correct the now-stale `divergence_note`** (2 entries: INFRA-345,
INFRA-346). **Architecture-Review Round 1 finding, fixed here**: both entries' current
`divergence_note` reads "Archived 2026-09-07 by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`;
code now lives at `tools/archive/<same filename>`, tests at `tests/archive/<same filename>`"
(confirmed present verbatim at both entries by direct read at `docs/parity_ledger/infrastructure.yaml`)
— this becomes false the moment Steps 2-3 hard-delete those files. Round 1's original submission
omitted this fix for INFRA-345/346 even though the disposition otherwise mirrors it; fixed here.
(Note: INFRA-342's own `divergence_note` field is separately confirmed `null` — it has no such
stale text to fix, and its own small wording correction lives in `test_path` instead, see the
"No-change" bucket below; INFRA-343 no longer belongs in a "stays verified" bucket at all — see
Rule A above, Architecture-Review Round 2 finding.) Update INFRA-345/346's `divergence_note`:
replace "code now lives at `tools/archive/<same filename>`..." with wording stating the archived
file was hard-deleted by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` and no longer exists
anywhere in the repo, while the entry's surviving live citation (named per-entry below) is what
now backs the `status: verified` value going forward.
  - **INFRA-345** (claim: Level 1 payload size cap recalibrated to 65536 bytes): its `test_path`
    today cites `tests/tools/test_knowledge_gateway_redaction.py::TestSizeCap` (dead — file
    deleted in Step 3) plus `tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant`
    (live, confirmed at `tests/docs/test_redaction_retention_policy_doc.py`, per `test_plan.md`'s
    regression list — imports `tools.write_path_guard as kgr` already). That surviving test
    directly cross-checks the same numeric claim (65536) against the live module constant,
    confirmed present at `tools/write_path_guard.py:57`
    (`MAX_PAYLOAD_BYTES: int = 65536  # §5, redaction_retention_policy.md:121 — recalibrated`).
    Trim `test_path` to just that surviving citation; update `v2_evidence`'s stale
    `tools/knowledge_gateway_redaction.py:68`/`:185-190` citation to point at
    `tools/write_path_guard.py:57` and `:174-178` (`check_size_cap()`, both confirmed present by
    direct read) instead; keep `status: verified`.
  - **INFRA-346** (claim: "Level 2 assembled context-packet cache schema/migration added"): its
    `test_path` cites `tests/tools/test_retrieval_cache.py::TestLevel2Migrations` (live, 13 tests
    directly covering schema/migration existence and idempotency — the entry's core claim) plus
    `tests/tools/test_knowledge_gateway_redaction.py::TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`
    (dead — file deleted in Step 3, and a secondary/incidental assertion, not the core
    schema/migration claim). Trim `test_path` to just the live `TestLevel2Migrations` citation;
    keep `status: verified`; `v2_evidence` needs no further change beyond removing any stale
    citation of the deleted file if present in that field too (read the entry directly at write
    time to confirm).

**No-change (already correctly handled by the predecessor, wording-only tweak) — stays
`status: verified`** (1 entry: INFRA-342 only — INFRA-343 moved to Rule A above per
Architecture-Review Round 2). INFRA-342 already has `v2_evidence` fully rewritten by the
predecessor ticket to cite the live `tools/write_path_guard.py` as primary evidence (not
`tools/archive/` at all) — no `status` change needed. `divergence_note` is already `null` (no
stale text there to fix). The one wording fix lives in `test_path` (confirmed by direct read at
`docs/parity_ledger/infrastructure.yaml:9432-9434`): it currently reads "...now archived at
`tests/archive/test_knowledge_gateway_redaction.py`, excluded from default collection..." — update
"now archived at" to "previously archived, now deleted by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`,
formerly at" (or equally precise phrasing) so the citation stops implying the file still exists at
that path. A wording-only correction to `test_path`, not a structural rewrite, and not touching
`v2_evidence`/`divergence_note` at all.

**Mechanics of the write** — never a raw `Edit` on this ~9500-line file. For each of the 21
entries: read the current full entry from `docs/parity_ledger/infrastructure.yaml` (needed
because `write_entry()` upserts a *complete* entry dict by `id`, not a partial patch — confirmed
at `tools/parity_ledger_writer.py:90-112`), construct the modified full dict per the disposition
above, then:
```
python3 -c "import sys; sys.path.insert(0,'tools'); from parity_ledger_writer import write_entry; import json; print(json.dumps(write_entry('infrastructure.yaml', <entry_dict>)))"
```
one call per entry (or batch them in a small script that loops the same `write_entry` call across
all 21 dicts — `write_entry` itself has no native batch form, only per-entry upsert). Immediately
after the last write, issue a **separate, visible** Bash call:
```
python3 tools/parity_index.py build
```
(required for `generate_retro.py`'s `parity_write_safety` metric per `parity_ledger_writer.py`'s
own docstring — the in-process rebuild inside `write_entry()` is invisible to that metric).
**Do NOT touch:** any entry outside the 21 named above; do not touch `divergence_note`/`status`
formatting of surrounding entries; do not use raw `Edit`/`Write` on the YAML file directly at any
point.
**Verify:** `git diff docs/parity_ledger/infrastructure.yaml` shows only field-level changes to
exactly these 21 entries (per `test_plan.md`'s "Parity ledger single-writer-path guard"); for each
of the 18 Rule-A entries (including INFRA-343, moved here per Architecture-Review Round 2),
`status: unsupported` and `test_path: null`; for INFRA-345/346, `status: verified` with a trimmed
`test_path` and a corrected `divergence_note`; for INFRA-342 only, `status: verified` unchanged
structurally (a `test_path` wording-only fix, no `status`/`v2_evidence`/`divergence_note` change).

### Step 9 — Update `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md` §1

**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/standalone_items.md`
**Change:** Read directly at L21-80 (§1, "Remove/archive knowledge-gateway"). Milestones 3-4 are
stated at L71-73 as future/pending ("**Monitor for 2 weeks**...", "**Delete** only after the
monitoring window confirms no renewed calls.") and the status-update block at L28-29 describes
milestones 3-4 as "a separate, explicitly filed follow-on once 1-2 land — not silently deferred,"
without recording that this ticket executed them (with an early-closure substitution for the
calendar wait, not a full 2-week elapse). Add a dated status note (matching the existing
"**Status update (2026-09-07)**" pattern at L23) directly under the L21 heading or after L33,
stating: milestones 3-4 executed by `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` on 2026-09-10,
via the ticket's own documented Early Closure Decision (repo-visible zero-call-site
re-verification substituted for the remaining ~12 days of calendar wait, per direct user
instruction) rather than the full elapsed 2-week window; all `tools/archive/`/`tests/archive/`
files hard-deleted, `norecursedirs`'s `"archive"` entry removed. Item 1 (§1) is now fully closed —
no work remains under this heading.
**Do NOT touch:** §2, §3, §4 of this same doc (unrelated standalone items) or the "Revised during
the 2026-09-04..." historical block (L34-54) — leave as-written historical context, per the doc's
own stated convention ("The rest of this section is left as-written below for historical
context... superseded by this status update where it conflicts").
**Verify:** no automated test covers this doc; manual read-back confirms the closure note is
present and accurate. If `docs/` files are modified, `make knowledge-index-update` must be run at
Finalize per CLAUDE.md's After Work rule (not part of this step's own verification, but must not
be skipped later).

### Step 10 — Update `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md` (item 6 / Governance-readiness condition 4)

**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`
**Change:** Read directly at L285-299 (the Governance-readiness gate's 4 conditions) — condition
4 (L296-299) currently reads: "`knowledge-gateway` (item 6) archived with **zero renewed calls**
observed over 2 weeks — item 6 was re-ratified to deprecate on 2026-09-07... and archival
(`TCK-20260907-KGMCP-DEPRECATION-EPIC` M2 steps 1-2) is in progress; this condition's 2-week
monitoring window (M2 steps 3-4) starts once archival lands, tracked as a separate follow-on."
This still describes M2 steps 3-4 as a pending follow-on. Update this condition's text to state
it is now satisfied: `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` executed M2 steps 3-4 on
2026-09-10 via the documented Early Closure Decision (not a full 2-week elapsed-time observation),
zero renewed calls confirmed, gateway files hard-deleted. Also check L118-120 (the item 6
inventory row referenced as "UNBLOCKED 2026-09-07") for any similar stale in-progress framing of
milestones 3-4 and update if present (read that region directly before editing — the
investigation flagged this file as "not read," so confirm the exact wording live rather than
assuming L118-120's content from this plan alone).
**Do NOT touch:** any other Governance-readiness condition (1, 2, 3) or any other roadmap item
unrelated to item 6/knowledge-gateway.
**Verify:** no automated test covers this doc; manual read-back confirms condition 4's text no
longer describes M2 steps 3-4 as in-progress/pending.

### Step 11 — Update `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` (scoped additive correction)

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`
**Change:** This doc was deliberately kept `status: active` by
`TCK-20260909-KGMCP-DOC-STATUS-SWEEP` because it mixes still-live content (backing
`tools/write_path_guard.py`) with historical content describing the archived gateway. It contains
at least 8 direct citations of now-fully-deleted archive-path files (confirmed present at L89,
L157, L222, L336, L361, plus others per `investigation.md`'s count) stating or implying those
files currently exist at `tools/archive/...`/`tests/archive/...`. Follow the exact precedent
`TCK-20260909-KGMCP-DOC-STATUS-SWEEP` already established for this same file: a targeted,
additive correction per citation site (e.g. append "— hard-deleted by
`TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`, no longer present anywhere in the repo" immediately
after each citation), not a full rewrite and not a `status: historical` flip (the latter is
explicitly out of scope per this ticket's own Out of Scope section, which reserves the full
`docs/engine/contracts/knowledge_gateway_mcp/` directory sweep as a separate future ticket).
**Do NOT touch:** this doc's `status: active` frontmatter value, or any content unrelated to the
archive-path citations; do not perform the wider directory-level `status: historical` sweep.
**Verify:** no automated test covers this doc's prose directly, but
`tests/docs/test_redaction_retention_policy_doc.py::test_payload_size_cap_doc_matches_live_module_constant`
(already in the regression surface, Step 7) must still pass — confirming this step's edits did
not disturb the doc's still-live, still-tested §5 payload-cap content.

### Step 12 — Final full verification

**Files:** none (verification only)
**Change:** Re-run the ticket's own AC gate in full: `pytest tests/tools/ tests/docs/ -v`. Also
re-run the anti-drift guards from `test_plan.md`:
```
git diff --stat tools/write_path_guard.py tools/retrieval_cache.py    # must be empty
git diff --stat tools/agent-monitoring/generate_retro.py tools/agent-monitoring/kgmcp_baseline_runner.py tools/agent-monitoring/kgmcp_baseline_corpus.py dashboard-frontend/    # must be empty
find tests/archive -type f -name '*.py' 2>/dev/null | wc -l    # must be 0/nothing
find tools/archive -type f 2>/dev/null | wc -l    # must be 0/nothing
git diff pyproject.toml    # exactly one line removed
```
Confirm every Acceptance Criterion in the ticket maps to a completed step (see Acceptance
Criteria Map below).
**Do NOT touch:** nothing new — this is a read-only confirmation step.
**Verify:** all commands above return the stated expected results; full `pytest tests/tools/
tests/docs/ -v` exit code 0.

## Scope Guards

- Do not touch `tools/write_path_guard.py` or `tools/retrieval_cache.py`, or edit either's tests
  beyond what Steps 5-6 require to keep them passing (they require zero edits — both are
  confirmed independent).
- Do not delete or modify `tests/docs/test_phase4_direct_tool_comparison_doc.py`,
  `tests/docs/test_phase4_workflow_recommendation_doc.py`, or
  `tests/docs/test_phase5_repeated_demand_measurement_doc.py`.
- Do not touch `tools/agent-monitoring/kgmcp_baseline_runner.py`,
  `tools/agent-monitoring/kgmcp_baseline_corpus.py`, `tools/agent-monitoring/generate_retro.py`,
  or `dashboard-frontend/`.
- Do not perform a raw multi-line `Edit`/`Write` on `docs/parity_ledger/infrastructure.yaml` —
  `tools/parity_ledger_writer.py`'s `write_entry()` only.
- Do not widen the `pyproject.toml` edit beyond the single `"archive"` `norecursedirs` line.
- Do not re-open the `docs/engine/contracts/knowledge_gateway_mcp/` directory-wide `status:
  historical` sweep, and do not flip `redaction_retention_policy.md`'s own `status: active`
  frontmatter.
- Do not re-litigate the Option C re-ratification decision (`keep_or_deprecate_decision.md` §4).
- Do not un-archive anything — if Step 1's re-verification finds a new live call site, stop and
  escalate rather than proceeding with the delete.
- Do not touch `.mcp.json` (already correctly deregistered; re-run
  `tests/tools/test_mcp_json_registration.py` only as a regression guard, do not edit the file).

## Dependency Map

- Step 1 gates Steps 2-3 (do not delete before the final re-verification passes clean).
- Steps 2 and 3 are independent of each other but both must complete before Step 4 (the
  `norecursedirs` removal is only safe once `tests/archive/` is actually gone) and before Step 7
  (full regression run needs the final file state).
- Step 4 depends on Steps 2-3 (norecursedirs removal reasoning assumes `tests/archive/` no longer
  holds test files).
- Step 5 depends on Step 2 (assertions reference the 6 deleted `tools/archive/` files).
- Step 6 depends on Steps 3-4 (assertions reference `tests/archive/`'s existence and
  `norecursedirs`'s content).
- Step 7 depends on Steps 2-6 all being complete — it is the integration checkpoint before moving
  to docs/ledger work.
- Step 8 (parity ledger) is independent of Steps 9-11 (docs) and could run in parallel with them,
  but both should follow Step 7's green regression run as a sanity gate.
= Steps 9, 10, and 11 are mutually independent (three different docs).
- Step 12 depends on all prior steps.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Superseded 2026-09-10 (monitoring window substitution) | N/A — already satisfied by the ticket's own Early Closure Decision section, re-confirmed by Step 1 | Manual grep diff (Step 1) |
| Fresh repo-wide sweep confirms zero live call sites | Step 1 | Manual grep comparison against investigation.md |
| 6 `tools/archive/knowledge_gateway_*`/shell file hard-deleted | Step 2 | `find tools/archive -type f \| wc -l` == 0 |
| 15 `tests/archive/` test files hard-deleted | Step 3 | `find tests/archive -type f -name '*.py' \| wc -l` == 0 |
| 5 `kgmcp_phase*_runner.py` + 5 sibling test files hard-deleted | Steps 2, 3 | same as above (included in the 11/15 counts) |
| `norecursedirs` no longer carries a dead `"archive"` entry | Step 4 | `git diff pyproject.toml`; `pytest tests/tools/test_ci_workflow_test_coverage.py -v` (Step 6) |
| `write_path_guard.py`/`retrieval_cache.py` remain functional, `pytest tests/tools/ tests/docs/ -v` passes | Steps 5, 6, 7, 12 | `pytest tests/tools/ tests/docs/ -v` |
| 21 `docs/parity_ledger/infrastructure.yaml` entries updated via `tools/parity_ledger_writer.py` | Step 8 | `git diff docs/parity_ledger/infrastructure.yaml` scoped to exactly 21 entries; `write_entry()`'s own schema validation |

## Review Round 1 (Architecture Review, 2026-09-10)

**Verdict on first submission: NEEDS_CHANGES.** Finding: Step 8's Rule B disposition for
INFRA-345/INFRA-346 updated `test_path`/`v2_evidence` but omitted correcting their own stale
`divergence_note` text ("code now lives at `tools/archive/<same filename>`..."). Independently
re-verified directly against `docs/parity_ledger/infrastructure.yaml`'s real content before
accepting the finding (both entries' `divergence_note` fields confirmed to read exactly the stale
pattern cited). Fixed above in Rule B's own text — see the "Architecture-Review Round 1 finding,
fixed here" note inline. All other aspects of the plan (file lists, the `unsupported` status
choice and its `INFRA-010` precedent, the INFRA-345/346 "stays verified" exception's own
reasoning) were confirmed sound by this same review round and required no change.

## Review Round 2 (Architecture Review, 2026-09-10)

**Verdict on second submission: NEEDS_CHANGES.** Finding: INFRA-343 was misclassified in the
"No-change / stays verified" bucket alongside INFRA-342. Independently re-verified directly
against `docs/parity_ledger/infrastructure.yaml:9468-9583`: INFRA-343's core claim (real cache
read/write wiring into the live Knowledge Gateway MCP gateway — `compute_lookup_identity()`,
`perform_cache_lookup()`/`perform_cache_write()`, and specifically the
`_run_knowledge_context()`/`_run_knowledge_status()` MCP-tool integration hooks) is backed
primarily by `tools/archive/knowledge_gateway_cache.py` and `tools/archive/knowledge_gateway_mcp.py`
(both hard-deleted by Step 2) plus 4 `tests/archive/test_knowledge_gateway_*.py` files (hard-deleted
by Step 3). The only surviving live citation
(`tests/tools/test_retrieval_cache.py::TestProviderResultCache`/`TestMigration003`/
`TestProviderResultCacheStats`) tests unrelated Level-1 provider-result-cache functions, not the
gateway-orchestration hooks the entry's `text` actually claims — unlike INFRA-342, whose claimed
symbols genuinely relocated to live `tools/write_path_guard.py`, INFRA-343's MCP-wiring code has no
live successor anywhere; it is being permanently deleted, not relocated. Fixed above: INFRA-343
moved from the "No-change" bucket to Rule A (18 entries total now, `status: unsupported`,
`test_path: null`), joining the same failure mode already correctly identified for INFRA-349 and
INFRA-355 (a partially-live `test_path` whose surviving citation does not actually prove the
entry's core claim). Also corrected, while fixing this: the "No-change" bucket's own wording-fix
location — re-verified directly that INFRA-342's `divergence_note` field is `null` (not stale text
as Round 1's fix language had implied by analogy), and that its actual wording fix lives in
`test_path` instead ("now archived at tests/archive/..." → reflecting the file is now deleted, not
archived). All other aspects re-confirmed sound by this round (durable-state/API-boundary N/A,
`unsupported`-vs-`missing` choice, remaining Rule A/B entry lists, scope guards, Out-of-Scope
consistency).

## Review Round 3 (Architecture Review, 2026-09-10)

**Verdict on third submission: APPROVED.** A fresh, independent re-review (not trusting Round 2's
own "fixed" framing) re-verified the INFRA-343 reclassification and the INFRA-342 wording-fix
location directly against the real `docs/parity_ledger/infrastructure.yaml` content, and
reconciled the entry count: 18 Rule-A + 2 Rule-B (INFRA-345/346) + 1 no-change (INFRA-342) = 21,
matching the ticket's own 21-entry list with no duplicates or omissions. No further changes
required — durable-state/API-boundary rules N/A (no `src/` change), the `unsupported` status
choice and `INFRA-010` precedent confirmed sound, no regressions found across the two prior edit
rounds (file lists, live-test updates, scope guards, dependency map, AC map all internally
consistent). Plan is APPROVED as of this round; Implement proceeded on this verdict.

## Anti-Drift Notes

- The ticket's own body text says "20 files" under `tests/archive/`; the real, verified count is
  15 (investigation.md's central correction). Do not let this resurface during implementation —
  the delete list in Step 3 is the authoritative 15-file list.
- Two live tests not named anywhere in the ticket's Related Code Areas
  (`tests/tools/test_knowledge_gateway_archival.py`,
  `tests/tools/test_ci_workflow_test_coverage.py`) will break on delete and are covered by Steps
  5-6 — do not skip these because the ticket itself doesn't name them.
- The parity-ledger status question is resolved as `unsupported` (not `missing`) via direct
  precedent (`INFRA-010`) already in the same YAML shard — do not re-derive this from first
  principles or guess a different enum value at implementation time.
- Only 2 of the 21 entries (INFRA-345, INFRA-346) stay `verified` with a trimmed `test_path`
  rather than moving to `unsupported`, because their surviving live citation directly proves the
  entry's core textual claim. Only 1 entry (INFRA-342) stays `verified` fully unchanged
  structurally. The other 18 (including INFRA-343 — moved here by Architecture-Review Round 2,
  not investigation.md's own original grouping) move to `unsupported`. Do not blanket-convert
  entries to `unsupported` without checking the "does the surviving live citation actually prove
  the core textual claim" distinction first for each — a partially-live `test_path` is not by
  itself sufficient to stay `verified` (this refines, and partially departs from, investigation.md's
  own blanket "the other 19"/"INFRA-342/343 both stay verified" framing — the refinement is based
  on this planning pass's own direct read of each entry's `test_path`/`text` fields, cited above,
  further corrected by two rounds of architecture review).
- `write_entry()` requires a **complete** entry dict per call (upsert by `id`), not a partial
  patch — always read the current full entry before constructing the replacement dict.
- The parity index rebuild (`python3 tools/parity_index.py build`) must be issued as its own
  visible Bash call after the last `write_entry()` call, even though `write_entry()` already
  rebuilds it in-process — required for the `parity_write_safety` retro metric to see it.
- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`'s correction must
  stay additive/scoped (per its own established precedent from `TCK-20260909-KGMCP-DOC-STATUS-SWEEP`)
  — resist the temptation to do a fuller rewrite or status flip while already in the file.
- If any `docs/` files are modified (Steps 9-11 certainly qualify), `make knowledge-index-update`
  must run at Finalize per CLAUDE.md's After Work rule — not verified by any step above, must not
  be forgotten at ticket close.

## Deviations (Implement phase, 2026-09-10)

Two adjacent-test dependencies on the deleted files were found during implementation that neither
this plan.md nor investigation.md anticipated (beyond the two already-named in Steps 5-6). Both
are the same class of foreseeable casualty as those two (a live test outside the delete list
asserting a fact the delete falsifies), not a live functional/behavioral dependency on the archived
gateway — so both were fixed directly as part of Implement, per the same reasoning Steps 5-6
already establish, rather than escalated as a new live-consumer discovery under the ticket's
Out-of-Scope "un-archive and escalate" clause (that clause is about a genuine undiscovered
*functional* consumer of gateway behavior, not a test-fixture path reference).

1. **`tests/tools/test_evidence_cache_identity_contract.py`** (found during Step 1's
   re-verification sweep, before any delete): `test_new_schema_file_parses_and_has_own_schema_version`
   read `_SIBLING_SCHEMA_TEST = tests/archive/test_knowledge_gateway_contract_schemas.py` via
   `.read_text()` to assert that sibling file's fixed schema-file list was never extended to
   include the new evidence-kinds schema. Since that sibling file is one of the 15 hard-deleted by
   Step 3, `.read_text()` would raise `FileNotFoundError`. Fixed by removing the now-moot
   sibling-cross-check assertion (and the now-unused `_SIBLING_SCHEMA_TEST` constant and its
   docstring reference), keeping the still-valid `schema_version`/`$schema`/`title` assertions in
   the same test function.
2. **`tests/tools/test_parity_ledger_writer.py::TestInfra352DocumentsChangedPathsIntegrationDecision`**
   (found during Step 12's final verification run, after Step 8's parity-ledger writes): a
   content-lock test asserted INFRA-352's ledger entry stays `status == "verified"` with a
   truthy `test_path` — both of which Step 8's own Rule A disposition for INFRA-352 (sole test
   citation hard-deleted, no live successor) correctly changed to `unsupported`/`null`. The plan's
   own Rule A classification of INFRA-352 was not wrong; this pre-existing content-lock test
   (written by an earlier ticket, `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT`) simply did not
   anticipate the later full gateway deletion. Fixed by updating only the two now-stale
   assertions (`status`/`test_path`) to match the new reality, leaving the `text`/
  `support_boundary` content-lock assertions — the test's actual regression-guard purpose —
   unchanged, and adding a docstring note explaining the update.

Neither fix required any change to this plan's own 12 ordered steps, scope guards, or the Rule A/B
entry classifications in Step 8 — both are corrections to test files this plan did not name,
required to keep the ticket's own `pytest tests/tools/ tests/docs/ -v` AC gate honest rather than
silently red.
