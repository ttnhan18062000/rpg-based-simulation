---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE
artifact_type: plan
tags: [ai, mcp, governance]
---

# Implementation Plan — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE

## Summary

Extract the full transitive-dependency closure of `evaluate_write_candidate()` — not just the 3
symbols the ticket names — out of `tools/knowledge_gateway_redaction.py` into a new,
gateway-independent module `tools/write_path_guard.py`; update every real consumer
(`tools/retrieval_cache.py`, `tests/docs/test_redaction_retention_policy_doc.py`); archive the
now-orphaned remainder of the gateway package (5 modules + 1 shell script) to `tools/archive/`,
flat, matching the `scripts/archive/` precedent; move the 15 gateway test files that would
otherwise fail collection to `tests/archive/` (3 further candidate files were found, Review round
1, to have no real dependency on anything archived — left in place, not moved) and exclude that
directory via `pyproject.toml`'s
`norecursedirs`; deregister `.mcp.json`'s `knowledge-gateway` entry; strip the accidental
`mcp__knowledge-gateway__*` grants from `done-checker.md`/`test-scoper.md` together with the
`test_wave1_agent_tools_frontmatter.py` dict update in the same step; fix the 3 doc citations this
move breaks (`redaction_retention_policy.md`, `governance_capability_policy_epic.md`, parity ledger
INFRA-342/343 only); and end by filing the M2 steps 3-4 follow-on ticket. All symbol moves are pure
code relocation — no behavior change — verified by a new byte-identical-output test.

## Steps

### Step 1 — Create `tools/write_path_guard.py` with the full transitive closure

**Files:** `tools/write_path_guard.py` (new)

**Change:** Create the new module and move the following symbols out of
`tools/knowledge_gateway_redaction.py` verbatim (pure relocation, no logic change). Confirmed by
direct read of `tools/knowledge_gateway_redaction.py` (445 lines, read in full during Plan):

- **Module-level constants** (L59-80): `redaction_policy_version` (L59), `SOURCE_TYPE_CONTEXT_SEARCH`/
  `SOURCE_TYPE_GRAPHIFY`/`ALLOWED_SOURCE_TYPES` (L61-63, feeds `check_allowlist()`),
  `LOCAL_USER_PLACEHOLDER`/`LOCAL_PATH_PLACEHOLDER` (L65-66, feeds `redact_content()`),
  `MAX_PAYLOAD_BYTES` (L68, feeds `check_size_cap()` — also the constant
  `tests/docs/test_redaction_retention_policy_doc.py` imports, see Step 4), `SQLITE_BUSY_TIMEOUT_MS`/
  `SQLITE_FILE_MODE` (L77-78, feed `open_connection_with_limits()` only), `ALLOW`/`REJECT` (L80).
  **`SQLITE_MAX_DB_SIZE_BYTES` (L76) does NOT move** — its only consumer,
  `check_db_size_within_limit()`, stays behind (see Step 2).
- `check_allowlist()` (L88-93)
- `_HOME_PATH_PATTERN`/`_ABS_PATH_PATTERN` (L103-108), `_hash_text()` (L111-112), `redact_content()`
  (L115-132)
- `_SECRET_SCAN_PATTERNS` (L140-158), `scan_for_secrets()` (L161-178)
- `check_size_cap()` (L185-190)
- `CATEGORY_SECRETS_OR_CREDENTIALS`/`CATEGORY_TOKENS`/`CATEGORY_RAW_ENVIRONMENT_VALUES`/
  `CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT`/`CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS`/
  `CATEGORY_UNRESTRICTED_RAW_PROMPTS` (L197-202), `_TOKEN_SHAPED_SECRET_PATTERNS` (L206-208),
  `_ENV_VALUE_PATTERN`/`_CONFIG_LINE_PATTERN`/`_ARBITRARY_CONFIG_MIN_LINES` (L210-212),
  `check_never_cache_categories()` (L215-253)
- `WriteDecision` (L260-267), `evaluate_write_candidate()` (L270-304)
- `open_connection_with_limits()` (L311-327)

Preserve every docstring, inline comment, and the fixed evaluation order inside
`evaluate_write_candidate()` (allowlist -> redact -> secret-scan -> size-cap -> never-cache ->
stamp+hash) byte-for-identical — this is a pure code-location move per the investigation's own
confirmation that the module has zero external dependency on gateway internals. Update only the
new module's top docstring to describe it as the write-path-guard concern shared by any caller
(not gateway-specific framing), matching the investigation's own naming rationale (Risk #7): "pure,
directly-testable write-path enforcement functions," independent of which caller — the archived
gateway, `retrieval_cache.py`, or the future `governance_capability_policy_epic.md` M4 hook — is
doing the writing.

**Do NOT touch:** `check_db_size_within_limit()`, `execute_bounded_transaction()`,
`acquire_write_guard()`/`release_write_guard()`/`_write_locks`/`_write_locks_guard`, or any of §10
(`CacheRowSnapshot`, the 6 `gc_eligible_*` predicates, `gc_eligibility_never_flags_protected_evidence()`,
`CACHE_STATUS_WRITE_COMPLETE`, `_PROTECTED_EVIDENCE_KINDS`) — confirmed via the investigation's
symbol-inventory table and my own read that none of these has a real consumer outside the gateway
package; they stay behind for archival in Step 2.

**Verify:** New test from Step 5 (`tests/tools/test_write_path_guard.py`) passes; module imports
cleanly with no `NameError` (would occur immediately if the transitive closure were incomplete —
this is the exact failure mode the investigation's Anti-Drift Hazard #1 warns against).

---

### Step 2 — Trim `tools/knowledge_gateway_redaction.py` to the archival-only remainder

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Remove every symbol moved in Step 1, leaving only: `SQLITE_MAX_DB_SIZE_BYTES` (L76),
`check_db_size_within_limit()` (L330-331), `execute_bounded_transaction()` (L334-342),
`_write_locks`/`_write_locks_guard`/`acquire_write_guard()`/`release_write_guard()` (L345-364), and
all of §10 (L367-445). Update the module's top docstring to state plainly that this file is the
pre-archival remainder of `tools/knowledge_gateway_redaction.py` — the load-bearing symbols moved
to `tools/write_path_guard.py` in `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` — since the next
step archives this file as-is and a future reader of `tools/archive/knowledge_gateway_redaction.py`
needs this pointer.

**Do NOT touch:** The internal logic of the remaining functions — this step only removes code, it
does not alter `check_db_size_within_limit()`/`execute_bounded_transaction()`/
`acquire_write_guard()`/`release_write_guard()`/§10 bodies.

**Verify:** `tests/tools/test_knowledge_gateway_redaction.py` (still at its original path at this
point in the sequence — moves in Step 8) still collects and its subset of tests covering the
remaining symbols (write-guard, GC-eligibility, `check_db_size_within_limit`,
`execute_bounded_transaction`) still passes; tests covering the now-removed symbols are expected to
fail at this exact point (their assertions target symbols no longer in this file) — this is
transient and resolved by Step 8 moving the whole test file to `tests/archive/` before Step 9
archives the source. Do not treat this step's test run as a final gate; it is the mid-sequence
verification step, superseded by Step 8/9's own verification.

---

### Step 3 — Update `tools/retrieval_cache.py`'s 3 call sites to import from the new module

**Files:** `tools/retrieval_cache.py`

**Change:** Confirmed by direct read (`grep -n "_kgr_redaction\|knowledge_gateway_redaction"
tools/retrieval_cache.py`): line 53 does `from tools import knowledge_gateway_redaction as
_kgr_redaction`, and exactly 3 call sites use it, all `_kgr_redaction.open_connection_with_limits
(CACHE_DB_PATH)` — `_get_access_log_connection()` (L632), `_get_level1_connection()` (L1041),
`_get_level2_connection()` (L1237). Change the import to
`from tools import write_path_guard as _write_path_guard` and the 3 call sites to
`_write_path_guard.open_connection_with_limits(CACHE_DB_PATH)`. Also update the 5 comment/docstring
mentions that name the old module by string (L627, L1036, L1061, L1229, L1278 — e.g. "opens
CACHE_DB_PATH via knowledge_gateway_redaction.open_connection_with_limits()" and "after
knowledge_gateway_redaction.evaluate_write_candidate() has already returned ALLOW") to say
`write_path_guard` instead — these are comments only (no behavior change) but left stale they would
mislead the next reader about where the real write-path logic now lives.

**Other writers to this file / this import surface:** `tools/retrieval_cache.py` line 53's import
statement has exactly one writer at any given time (this ticket, this step) — no other in-flight
ticket touches this line per `git log`/working-log cross-check at Plan time. The 3 call sites
(`_get_access_log_connection()`, `_get_level1_connection()`, `_get_level2_connection()`) are each
called from multiple places inside `retrieval_cache.py` itself (migrations, read/write helpers) but
none of those callers reference `_kgr_redaction`/`_write_path_guard` directly — only the 3
connection-opening functions do, so the blast radius of the rename is exactly those 3 call sites
plus the import line.

**Do NOT touch:** `tools/retrieval_cache.py`'s own SQLite logic — the investigation's Anti-Drift
Hazard #3 confirms `tests/docs/test_redaction_retention_policy_doc.py::
test_sqlite_defaults_not_silently_implemented` asserts `PRAGMA journal_mode`/`PRAGMA busy_timeout`/
`os.chmod`/`chmod` never appear directly in `tools/retrieval_cache.py`'s own source — this step must
not inline any of `open_connection_with_limits()`'s body into `retrieval_cache.py` as a
"simplification"; it must stay behind the imported function call.

**Verify:** `tests/tools/test_retrieval_cache.py` full suite passes (per test_plan.md, the bulk of
this suite doesn't touch `_kgr_redaction` directly; only the subset exercising
`open_connection_with_limits()` indirectly is affected, by import path only, not behavior); new
Step 6 architecture-guard test passes; re-run
`test_sqlite_defaults_not_silently_implemented` specifically to confirm the guard still holds.

---

### Step 4 — Update `tests/docs/test_redaction_retention_policy_doc.py`'s direct import

**Files:** `tests/docs/test_redaction_retention_policy_doc.py`

**Change:** Confirmed by direct read (L77-84):
```python
import sys
sys.path.insert(0, str(_REPO_ROOT / "tools"))
import knowledge_gateway_redaction as kgr
...
assert str(kgr.MAX_PAYLOAD_BYTES) in text, (...)
```
in `test_payload_size_cap_doc_matches_live_module_constant()`. Change `import
knowledge_gateway_redaction as kgr` to `import write_path_guard as kgr` (the `sys.path.insert`
targeting `tools/` stays valid since `write_path_guard.py` lives directly under `tools/`, same as
the old module did). Also drop the unused `_KNOWLEDGE_GATEWAY_REDACTION_PY` path constant the
investigation flagged as dead code in this same file, since it is being touched anyway.

**Other writers to this file:** None currently in-flight (single-owner test file, no concurrent
ticket references it in `working_log.csv`).

**Do NOT touch:** Any other assertion in this file — investigation confirms every other test in it
is a pure doc-structure check, unaffected by this ticket.

**Verify:** `pytest tests/docs/test_redaction_retention_policy_doc.py -v` passes in full.

---

### Step 5 — Add `tests/tools/test_write_path_guard.py` (behavior-parity guard)

**Files:** `tests/tools/test_write_path_guard.py` (new)

**Change:** Port the fixture set from `tests/tools/test_knowledge_gateway_redaction.py` (read at
Plan time to exist and cover: allowlist reject, each of the 10 `_SECRET_SCAN_PATTERNS` entries,
oversized payload, each of the 6 `CATEGORY_*` never-cache cases, and the ALLOW path) into a new
test module that imports `tools.write_path_guard` and asserts `evaluate_write_candidate()` produces
byte-identical `WriteDecision` output to the pre-extraction fixtures for the same inputs. Also add
a basic `open_connection_with_limits()` test (WAL mode set, busy_timeout set, file chmod 0600 on
first creation, not re-chmodded on reconnect) if the ported original didn't already isolate one
into its own test — verify against the original file's actual test names before assuming, since I
have not read that test file's full contents at Plan time (only confirmed its existence and general
scope from investigation.md and test_plan.md); the implementer must open it and port equivalently,
not invent new fixtures from scratch.

**Do NOT touch:** `tests/tools/test_knowledge_gateway_redaction.py` itself in this step — it still
exists at its original path until Step 8 moves it to `tests/archive/`; this step only adds a new,
separate file.

**Verify:** `pytest tests/tools/test_write_path_guard.py -v` passes; this is the direct AC1
regression guard test_plan.md calls for.

---

### Step 6 — Add architecture-guard test to `tests/tools/test_retrieval_cache.py`

**Files:** `tests/tools/test_retrieval_cache.py`

**Change:** Add `test_retrieval_cache_imports_open_connection_with_limits_from_new_location` (or
equivalent name) to the file's existing `TestStaticGuards`-style class (per test_plan.md's
guidance to match the module's own established static-guard pattern — implementer must locate that
existing class by reading the file first, not assume its exact name). Assert
`Path("tools/retrieval_cache.py").read_text()` does NOT contain the string `"from tools import
knowledge_gateway_redaction"` and DOES contain `"from tools import write_path_guard"` (or the
equivalent import form actually used in Step 3).

**Other writers to this file:** `tests/tools/test_retrieval_cache.py` is a large, actively-extended
suite (per test_plan.md, "the bulk of this suite... must still pass in full" — it is not owned
solely by this ticket long-term). This step only appends one new test method; it must not alter or
reorder any existing test in the file.

**Do NOT touch:** Any existing test in this file.

**Verify:** `pytest tests/tools/test_retrieval_cache.py -v` passes, including the new test. Direct
AC2 regression guard.

---

### Step 7 — Exclude `tests/archive/` from default pytest collection

**Files:** `pyproject.toml`

**Change:** Confirmed by direct read (L52-60):
```toml
[tool.pytest.ini_options]
pythonpath = ["."]
norecursedirs = [
    "reviews",
    "scratch",
    "stored_artifacts",
    ".venv",
    ".git",
    "node_modules",
    "__pycache__",
]
```
Add `"archive"` as a new entry to this list (matches the existing bare-basename style of every
other entry; pytest's `norecursedirs` matches directory basenames during collection recursion, not
full paths). Confirmed via `find . -type d -iname "*archive*"` that no directory named `archive`
currently sits inside any path pytest recurses into for test collection that should legitimately
keep being collected — `docs/archive`, `docs/plans/archive`, `scripts/archive` all pre-exist and
contain no test files, so this addition changes nothing about their current (non-)collection.

**Other writers to `pyproject.toml`:** This is a shared, single config file with entries for many
subsystems (markers list follows immediately after `norecursedirs`, confirmed by the same read).
This step only appends one entry to the `norecursedirs` list; do not touch `markers` or any other
`[tool.pytest.ini_options]` key.

**Do NOT touch:** The `markers` list or any other pyproject.toml section.

**Verify:** `pytest tests/archive/ -v --co` (collection-only) after Step 8 confirms files exist and
are individually collectable; `pytest tests/ -v --co 2>&1 | grep -c archive` from repo root shows
zero collected items under `tests/archive/` in a default run.

---

### Step 8 — Move the 15 gateway-dependent test files to `tests/archive/`

**Files:** 15 files from `tests/tools/` — moved via `git mv` to `tests/archive/` (flat, mirroring
the `tools/archive/` convention from Step 9, no subdirectory nesting):

Confirmed present via direct `ls` at Plan time, each independently confirmed (Review round 1) to
have a real dependency (direct import, `importlib.util.spec_from_file_location`, or literal `Path`
reference) on a module this ticket archives:
- `tests/tools/test_knowledge_gateway_cache.py`
- `tests/tools/test_knowledge_gateway_contract_schemas.py`
- `tests/tools/test_knowledge_gateway_failure_semantics.py`
- `tests/tools/test_knowledge_gateway_mcp.py`
- `tests/tools/test_knowledge_gateway_packet_assembly.py`
- `tests/tools/test_knowledge_gateway_redaction.py`
- `tests/tools/test_knowledge_gateway_router.py`
- `tests/tools/test_kgmcp_baseline_corpus_dedup_coverage.py`
- `tests/tools/test_kgmcp_measurement_baseline.py`
- `tests/tools/test_kgmcp_phase1_baseline_comparison.py`
- `tests/tools/test_kgmcp_phase2_baseline_recomparison.py`
- `tests/tools/test_kgmcp_phase3_pilot_acceptance_measurement.py`
- `tests/tools/test_kgmcp_phase4_direct_tool_comparison.py`
- `tests/tools/test_kgmcp_phase4_warm_direct_tool_comparison.py`
- `tests/tools/test_kgmcp_phase5_repeated_demand_measurement.py`

**Correction, Review round 1: 3 files removed from this list, left in place untouched.**
`tests/docs/test_phase4_direct_tool_comparison_doc.py`,
`tests/docs/test_phase4_workflow_recommendation_doc.py`, and
`tests/docs/test_phase5_repeated_demand_measurement_doc.py` were originally included here, but
architecture-reviewer found — and I independently re-verified via `grep -n "^import\|^from"` on
each file — that none of the three imports any `tools/knowledge_gateway_*` module or references
`.mcp.json`; their only match on "knowledge_gateway_mcp" is as a **doc path component**
(`docs/engine/contracts/knowledge_gateway_mcp/...`), which they read as plain doc files — a
directory this ticket's own Out of Scope explicitly excludes from any sweep (only
`redaction_retention_policy.md` inside it is touched, by Step 13). Moving these 3 would have
silently dropped live, currently-passing coverage from default collection under a mistaken
"would otherwise fail" premise — exactly what AC6 forbids. They stay at their current
`tests/docs/` paths, fully unmodified by this ticket.

**Decision (resolves investigation Risk #2): option (a) — move + `norecursedirs`, not
`@pytest.mark.skip`.** Rationale: (1) matches this repo's only existing "archive a tool, don't
delete" precedent (`scripts/archive/`, confirmed flat with no nesting); (2) a `norecursedirs`
exclusion is a visible, reviewable config diff (Step 7), unlike an in-place skip mark which leaves
15 files sitting in the live `tests/tools/` tree indefinitely looking like active,
maintained coverage when they are not; (3) it matches this ticket's own Step 9 code-archival
mechanism exactly, so a future reader finds both halves (code + its tests) in a parallel, obviously
paired location (`tools/archive/knowledge_gateway_redaction.py` /
`tests/archive/test_knowledge_gateway_redaction.py`) rather than code in one place and tests
skip-marked in another; (4) the ticket's own AC explicitly requires "not silently deleted or
skipped" — a `pytest.mark.skip` is closer to "skipped" in letter than a directory move is. Do not
edit the test files' own contents beyond what's needed for them to remain syntactically valid at
their new path (none expected — they use repo-root-relative imports/paths, not paths relative to
their own file location, per test_plan.md's confirmation that these do `from tools import ...` or
`importlib.util.spec_from_file_location(..., <literal path>)` — the latter's literal path argument
must be updated in Step 9 alongside the source move, see that step).

**This step must run BEFORE Step 9 (source archival)**, not after — sequencing this way means that
by the time the gateway source modules are archived, none of these 15 test files are still being
collected from their old location, so there is no window where `pytest tests/tools/` fails due to
missing imports.

**Other writers to these files:** None of the 15 have any other in-flight ticket referencing them
in `tickets/inprogress/` at Plan time (checked via the ticket's own Related Tickets list, which
names none of these specifically).

**Do NOT touch:** `tests/tools/test_evidence_cache_identity_contract.py` — confirmed by
investigation to import no gateway module directly (only reads doc/contract files and
`retrieval_cache.py` via `ast.parse()`), stays in place. `tests/docs/test_phase4_direct_tool_comparison_doc.py`,
`tests/docs/test_phase4_workflow_recommendation_doc.py`,
`tests/docs/test_phase5_repeated_demand_measurement_doc.py` — removed from this step per the
Review-round-1 correction above, also stay in place. Do not let this move sweep pull in any file
not on the 15-file list above (test_plan.md's own Anti-Drift Test Guard: "the new `tests/archive/`
directory should contain *only* the files this ticket moves there").

**Verify:** `pytest tests/archive/ -v --co` (after Step 7's `norecursedirs` edit) shows all 15 files
individually collectable; `pytest tests/tools/ tests/docs/ -v --co` shows zero collection errors,
none of the 15 moved filenames appear in the collected list, and all 3 of the correctly-retained
`tests/docs/test_phase{4,4,5}_*.py` files above DO still appear in the collected list (confirming
they were not accidentally moved).

---

### Step 9 — Archive the 5 gateway modules + shell script to `tools/archive/`

**Files:** `tools/knowledge_gateway_mcp.py`, `tools/knowledge_gateway_router.py`,
`tools/knowledge_gateway_packet_assembly.py`, `tools/knowledge_gateway_cache.py`,
`tools/knowledge_gateway_redaction.py` (the Step-2-trimmed remainder), `tools/
start_knowledge_gateway_mcp.sh` — moved via `git mv` to `tools/archive/`, flat (no subdirectory
nesting, no new `__init__.py`), matching `scripts/archive/`'s confirmed precedent (5 files, flat,
no package markers — verified via direct `ls scripts/archive/` at Plan time: `apply_traceability.py`,
`ledger_validator.py`, `remediate_checklist.py`, `report_coverage.py`, `validate_checklist.py`).

**Decision (resolves the prompt's explicit open question about `tools/knowledge_gateway_cache.py`):
leave its internal `from tools import knowledge_gateway_redaction as rk` import (L67, confirmed by
direct read) unmodified — do not rewrite it to point at the new `tools/archive/` path.** Rationale:
`knowledge_gateway_cache.py` is itself being archived in this same step, alongside
`knowledge_gateway_redaction.py`. Per the investigation's own confirmation, this module has zero
real consumer post-archival (its only caller, the gateway MCP server, is archived in the same
commit) and the repo's only precedent for archived code (`scripts/archive/`) treats archived files
as a frozen historical snapshot, not maintained/runnable code — none of those 5 files were kept
cross-import-consistent with each other either (they had zero test coverage, so nothing would have
caught it either way). Rewriting the import to `tools.archive.knowledge_gateway_redaction` would
require adding an `__init__.py` to make `tools/archive/` an importable package, which breaks the
flat-file, no-package precedent this ticket is explicitly matching. If this module is ever needed
live again, it will be un-archived as a deliberate, reviewed act (matching the M2 steps 3-4
follow-on's own "monitor, then delete" framing) — at which point its imports get fixed as part of
that act, not preemptively now.

**If the chosen archive location's tests need the literal `importlib.util.spec_from_file_location`
paths updated:** Step 8 moved the test files first; any test using
`importlib.util.spec_from_file_location("knowledge_gateway_mcp", "tools/knowledge_gateway_mcp.py")`
(or sibling modules) needs that literal path string updated to `tools/archive/
knowledge_gateway_mcp.py` inside the now-relocated test file, or the test will `FileNotFoundError`
if anyone runs it directly from `tests/archive/` post-archival. This is a mechanical find-and-fix
the implementer must do per-file while reading each of the 15 `tests/tools/test_knowledge_gateway_*
.py`/`test_kgmcp_*.py` files moved in Step 8 — confirm the exact set of files using this pattern by
grepping `spec_from_file_location` across the moved files before editing.

**Do NOT touch:** `tools/agent-monitoring/kgmcp_*_runner.py` (7 files) or
`tools/agent-monitoring/kgmcp_baseline_corpus.py` — see Step 12 for the explicit no-op decision on
these.

**Verify:** `tests/tools/test_gateway_modules_archived_not_present_at_old_paths` (new, see below)
confirms old paths (`tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`,
`tools/start_knowledge_gateway_mcp.sh`) no longer exist and the mirror files exist under
`tools/archive/`. Add this as a small new test in `tests/tools/test_knowledge_gateway_archival.py`
(new file) — direct AC3 regression guard.

---

### Step 10 — Deregister `.mcp.json`'s `knowledge-gateway` entry

**Files:** `.mcp.json`, `tests/tools/test_mcp_json_registration.py` (new)

**Change:** Confirmed by direct read of `.mcp.json` (23 lines) — it has exactly 3 top-level
`mcpServers` entries: `knowledge-search`, `knowledge-gateway`, `github`. Remove the entire
`"knowledge-gateway": {...}` block (the `command`/`args`/`env`/`description` object for
`tools/start_knowledge_gateway_mcp.sh`), leaving `knowledge-search` and `github` byte-identical to
their current form. Add a new small standalone test file
`tests/tools/test_mcp_json_registration.py` asserting `set(mcp_config["mcpServers"].keys()) ==
{"knowledge-search", "github"}` and that the `knowledge-search` entry's exact dict shape matches
what's confirmed above — this is the inverse of, and functional replacement for, the now-archived
`test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`'s
`knowledge_search_entry == {...}` byte-identity check (per test_plan.md's Anti-Drift Test Guard).

**Other writers to `.mcp.json`:** This is a small, rarely-changed 3-entry config file. No other
in-flight ticket touches it per `working_log.csv`/`tickets/inprogress/` cross-check at Plan time.
The `github` entry (Docker-based GitHub MCP server) and `knowledge-search` entry are both live,
actively-used MCP registrations outside this ticket's scope — confirmed untouched by diffing this
step's change against the read above.

**Do NOT touch:** The `knowledge-search` or `github` entries — investigation's Anti-Drift Hazard #2
explicitly requires these stay byte-identical (mirrors the existing gateway tests' own "frozen
files" discipline, applied in reverse).

**Verify:** `pytest tests/tools/test_mcp_json_registration.py -v` passes. Direct AC4 regression
guard.

---

### Step 11 — Remove the accidental grants from agent frontmatter AND the frontmatter test, together

**Files:** `.claude/agents/done-checker.md`, `.claude/agents/test-scoper.md`,
`tests/tools/test_wave1_agent_tools_frontmatter.py`

**Change:** Confirmed by direct read:
- `.claude/agents/done-checker.md` line 4's `tools:` frontmatter list currently includes
  `mcp__knowledge-gateway__knowledge_context, mcp__knowledge-gateway__knowledge_status` — remove
  both, leaving every other listed tool untouched.
- `.claude/agents/test-scoper.md` line 4's `tools:` frontmatter list currently includes
  `mcp__knowledge-gateway__knowledge_status` — remove it, leaving every other listed tool untouched
  (in particular, `test-scoper.md` does NOT currently grant `Edit` — confirmed by the read above;
  do not add it as a side effect of this edit, per test_plan.md's Anti-Drift Test Guard citing
  `test_wave1_candidate_scope_excludes_known_denied_tools`'s forbidden-pairs list, which includes
  `("test-scoper", "Edit")` at L58 of the test file).
- `tests/tools/test_wave1_agent_tools_frontmatter.py`'s `_WAVE1_CANDIDATE_TOOLS` dict (confirmed at
  L35-46) hard-pins these same two grants for `"done-checker"` and `"test-scoper"` — remove the two
  `mcp__knowledge-gateway__*` entries from each list in this dict in the exact same commit as the
  two `.md` edits above. This is investigation's own named Anti-Drift Hazard: "editing only the
  `.md` files leaves that test red."

**Other writers to `test_wave1_agent_tools_frontmatter.py`:** `_WAVE1_CANDIDATE_TOOLS` is a shared
dict covering every Wave 1 agent, not just these two (confirmed by the surrounding structure at
L35+ covering multiple agent names). This step edits only the `"done-checker"` and `"test-scoper"`
entries; no other agent's entry in this dict changes. The forbidden-pairs list at L58 (used by
`test_wave1_candidate_scope_excludes_known_denied_tools`) is a second, separate structure in the
same file — this step must not touch it (per the same Anti-Drift Test Guard).

**Do NOT touch:** Any other tool in either agent's frontmatter list; any other agent's entry in
`_WAVE1_CANDIDATE_TOOLS`; the forbidden-pairs list.

**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -v` passes for all
parametrized cases, in particular `test_wave1_agent_files_declare_tools_field[done-checker]` and
`[test-scoper]`. Direct AC5 regression guard.

---

### Step 12 — Explicit no-op: leave the 7 gateway-adjacent runner scripts unchanged

**Files:** None changed. Explicitly NOT touching: `tools/agent-monitoring/kgmcp_baseline_runner.py`,
`kgmcp_baseline_corpus.py`, `kgmcp_phase1_gateway_runner.py`, `kgmcp_phase2_gateway_runner.py`,
`kgmcp_phase3_gateway_runner.py`, `kgmcp_phase4_direct_tool_comparison_runner.py`,
`kgmcp_phase4_warm_direct_tool_comparison_runner.py`.

**Change:** None. This is a deliberate decision, not an oversight: per investigation Risk #3, these
7 files are one-time, already-run measurement scripts whose results are committed as fixtures under
`tests/tools/fixtures/kgmcp_*.json`. They `importlib`-load or directly import
`tools/knowledge_gateway_mcp.py`/`tools/knowledge_gateway_redaction.py` by literal path and would
break if re-run post-archival — but they are not wired into the fast pytest loop (confirmed by
investigation's own reading of their self-description) and nothing in this ticket's test plan
requires re-running them. Leaving them unexecuted, in place, as a historical record is lower-risk
than archiving them (which would be scope creep beyond this ticket's own Related Code Areas) or
attempting to fix their imports (which would require them to still function, contradicting their
own "one-time, never re-run" nature).

**Do NOT touch:** These 7 files, and `tools/agent-monitoring/generate_retro.py` (confirmed
independent — imports only `retrieval_cache.py`, never any gateway module).

**Verify:** `git diff --stat tools/agent-monitoring/` shows zero changes to any of the 7 files (or
to `generate_retro.py`) as part of this ticket's diff. `pytest tests/tools/test_generate_retro.py
-v` passes unmodified — test_plan.md's own anti-drift signal that adjacent
`tools/agent-monitoring/` files weren't accidentally touched.

---

### Step 13 — Fix the 3 stale doc citations

**Files:** `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`,
`docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`,
`docs/parity_ledger/infrastructure.yaml`

**Change:**
1. `redaction_retention_policy.md` — confirmed by direct read, 3 distinct citation spots:
   - L56 (`Neither tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES...`) → update to
     `tools/write_path_guard.py::ALLOWED_SOURCE_TYPES` (moved in Step 1).
   - L193-194 (`tools/knowledge_gateway_redaction.py:47` for `redaction_policy_version`, and
     `tools/knowledge_gateway_redaction.py:225` for `WriteDecision.redaction_policy_version`) →
     update both to point at `tools/write_path_guard.py` at whatever line each symbol lands at post-
     move (implementer must verify the actual new line number after Step 1 lands — do not guess or
     carry over the old numbers, since the new file's internal ordering may differ from a straight
     concatenation).
   - L304-308 (§9 "They are now implemented as real, tested logic in a separate new module,
     `tools/knowledge_gateway_redaction.py`... `open_connection_with_limits(db_path)` applies...")
     — **this spot needs a split, not a single find-replace**, because §9 as currently written
     describes both `open_connection_with_limits()` (moves to `tools/write_path_guard.py`, Step 1)
     AND `check_db_size_within_limit()`/`execute_bounded_transaction()` (stay behind in the
     archived `tools/archive/knowledge_gateway_redaction.py`, Step 2/9) in the same paragraph.
     Rewrite this paragraph to name `tools/write_path_guard.py` for `open_connection_with_limits()`
     specifically, and note `check_db_size_within_limit()`/`execute_bounded_transaction()` now live
     in the archived module (`tools/archive/knowledge_gateway_redaction.py`, no longer live code)
     since this ticket, `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`.
2. `governance_capability_policy_epic.md` L243 (`- tools/knowledge_gateway_redaction.py — source of
   scan_for_secrets() (line 161) for M4.`) → update the path to `tools/write_path_guard.py` and the
   line number to `scan_for_secrets()`'s actual post-move line (verify, don't guess, same as above).
   This is the one non-decision-doc citation fix explicitly allowed by the ticket's Out of Scope
   (which excludes the 5 named decision docs only, not this one).
3. `docs/parity_ledger/infrastructure.yaml` — **revised sizing, corrected during Review (see below):
   the original "2 fixed now / 14 deferred" split was drawn on "which entries are specifically about
   the extracted symbols," not on the actually-correct criterion (CLAUDE.md's Authoritative Mechanics
   Rule / this ticket's own action): does THIS ticket's own archival make the entry's `v2_evidence`/
   `test_path` claim factually wrong (code no longer live at the cited path)? A live re-scan against
   the real ledger file found this is true for 21 entries, not 2** — confirmed via a script checking
   every entry's `v2_evidence` for a citation of
   `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py`/
   `tools/start_knowledge_gateway_mcp.sh`, or a `test_path` citing a `test_knowledge_gateway_*`/
   `test_kgmcp_*` file (Step 8's 15-file move list is a strict subset of these test_path citations —
   the 3 files retained in Step 8's own correction never matched this pattern, so this parity-ledger
   scan and count are unaffected by that separate correction):
   `INFRA-334, 335, 336, 337, 338, 339, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 354,
   355, 356, 357` (**INFRA-334 added, Review round 2** — its own scan range originally started at
   335, missing this one; its `test_path` is `tests/tools/test_kgmcp_measurement_baseline.py`, item
   #9 on Step 8's move list, so it qualifies the same way as the rest even though its `v2_evidence`
   itself cites `tools/agent-monitoring/kgmcp_baseline_corpus.py` — a file Step 12 explicitly leaves
   in place, so only its `test_path` half is stale, not its `v2_evidence` half; still requires the
   same annotation treatment below). INFRA-340, 341, 353 in the same numeric range do NOT cite an
   archived path — left untouched; INFRA-295, 297, 379, 382, 390, 410, all P2 and about
   `retrieval_cache.py`/`post_tool_hook.py` only, also untouched, confirmed no archived-module
   citation.

   Two different fixes for two different reasons, both via `tools/parity_ledger_writer.py` (the
   sanctioned, schema-validating tool — never a raw `Edit` on this 10,000+ line shared YAML file, per
   this repo's own established full-file-rewrite corruption hazard):
   - **INFRA-342 and INFRA-343** (the 2 entries whose text is directly about the symbols this ticket
     moves — `check_allowlist`/`scan_for_secrets`/`check_size_cap`/`check_never_cache_categories`/
     `WriteDecision`/`evaluate_write_candidate`/`open_connection_with_limits`): a real `v2_evidence`
     rewrite pointing at the new `tools/write_path_guard.py` locations — these entries' own subject
     matter is what moved, so a full, accurate rewrite is warranted and cheap (2 entries).
   - **The other 19 entries** (INFRA-334 plus the 18 about the router/packet-assembly/mcp/cache
     modules and their own history — not directly about this ticket's own Step 1 extraction, but
     whose cited paths this ticket's Step 8/9 archival still makes stale): append a short, additive
     note to each entry's `divergence_note` field (currently `null` on all 19, confirmed via the
     same script) — `"Archived 2026-09-07 by TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE; code
     now lives at tools/archive/<same filename>, tests at tests/archive/<same filename>.
     v2_evidence/test_path below describe the pre-archival live state and are kept as historical
     record, not re-derived."` (for INFRA-334 specifically, the note should say only the test moved,
     since `kgmcp_baseline_corpus.py` itself was not archived — adjust the wording for that one
     entry rather than reusing the generic note verbatim) — never re-deriving or rewriting each
     entry's own `v2_evidence`/`test_path` content (a 21-entry full rewrite is exactly the scale
     investigation's own sizing concern correctly flagged as too large for this ticket), but making
     each entry honestly non-misleading about current reachability, which a silent skip would not.
     This must be a real `tools/parity_ledger_writer.py` call per entry (or its batch-update form if
     one exists — check the tool's own CLI help before assuming), not 19 individual raw-YAML edits.

   Do NOT touch the P2 entries (INFRA-295, 297, 379, 382, 390, 410) — confirmed no archived-module
   citation, genuinely unaffected.

**Other writers to `infrastructure.yaml`:** This is a large, actively-appended-to shared ledger file
— many other tickets add or update entries in it over time (16+ P1 entries in this cluster alone,
spanning at least 6 different source tickets per the file's own history). This step touches exactly
2 of its ~9500+ lines' worth of entries (INFRA-342, INFRA-343); any concurrent ticket appending a
new entry elsewhere in the file is unaffected as long as this step uses the sanctioned writer tool
(which operates on individual entries, not a full-file rewrite) rather than a raw multi-line Edit
that could collide with concurrent structure.

**Do NOT touch:** The 5 explicitly-excluded decision docs (`keep_or_deprecate_decision.md`,
`audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`, `roadmap.md`, `standalone_items.md`); the
wider `docs/engine/contracts/knowledge_gateway_mcp/` directory beyond
`redaction_retention_policy.md`; the other 14 P1 parity-ledger entries in the INFRA-335-357 cluster;
`docs/observability/retrieval_retention_redaction_policy.md` (confirmed by investigation to need no
change — it only cross-references by path, no file:line citations of its own).

**Verify:** No automated test currently enforces doc-citation freshness for these 3 spots (confirmed
by test_plan.md — the one optional doc-structure test it suggests,
`test_governance_capability_policy_epic_doc_cites_new_scan_for_secrets_location`, is marked
low-priority/optional). Verification here is manual: `grep -n "knowledge_gateway_redaction"
docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md
docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
after this step should show zero remaining stale references to symbols that moved (the archived-
module references for `check_db_size_within_limit`/`execute_bounded_transaction` staying in the
doc's §9, pointed at `tools/archive/knowledge_gateway_redaction.py`, are expected and correct).
If implementer time allows, add the optional test test_plan.md names; not required for AC
satisfaction (no AC references this doc-citation freshness directly — it's covered by the
Authoritative Mechanics Rule in CLAUDE.md, not a ticket AC).

---

### Step 14 — File the M2 steps 3-4 follow-on ticket

**Files:** `tickets/inprogress/TCK-<new-date>-KGMCP-DELETE-ARCHIVED-GATEWAY.md` (or similar name,
implementer/Finalize-phase choice) via the standard ticket-creation flow.

**Change:** Once Steps 1-13 land and this ticket closes, file a new ticket covering M2 steps 3-4
from `TCK-20260907-KGMCP-DEPRECATION-EPIC`: a 2-week zero-call monitoring window on the archived
`tools/archive/` modules (confirming nothing outside this repo's own visibility calls the archived
gateway), followed by hard-deleting `tools/archive/knowledge_gateway_{mcp,router,packet_assembly,
cache,redaction}.py`, `tools/archive/start_knowledge_gateway_mcp.sh`, and `tests/archive/`'s 15
gateway test files. This step happens at Finalize time (after this ticket's own archival is
confirmed landed and merged), not mid-Implement — do not attempt to pre-file it before Steps 1-13
are done, since its own scope depends on this ticket's actual archive-location choices (Step 8's
`tests/archive/`, Step 9's `tools/archive/`) being real and merged.

**Do NOT touch:** This ticket's own scope does not include the monitoring window or the delete
itself — only filing the follow-on ticket that will carry them out.

**Verify:** New ticket file exists in `tickets/inprogress/` with correct frontmatter (`layer: ai`,
appropriate `tags`), Related Tickets pointing back to this ticket and to
`TCK-20260907-KGMCP-DEPRECATION-EPIC`. Direct AC7 regression guard — the ticket's Definition of Done
is not complete without this.

## Scope Guards

Restated from the ticket's own Out of Scope and the investigation's Anti-Drift Hazards — the
implementer must not do any of the following as part of this ticket:

- Do not perform the 2-week zero-call monitoring window or the eventual hard-delete (M2 steps 3-4)
  — Step 14 only files the follow-on ticket that will carry them out later.
- Do not re-litigate or re-document the Option C re-ratification decision
  (`TCK-20260907-KGMCP-DEPRECATION-EPIC` M1, `keep_or_deprecate_decision.md` §4) — already settled.
- Do not implement `governance_capability_policy_epic.md`'s M4 hook itself (the Bash
  secret-exposure `PreToolUse` wiring) — this ticket only makes `scan_for_secrets()` importable
  from `tools/write_path_guard.py`; M4's own wiring is that epic's scope.
- Do not edit any of the 5 explicitly-excluded decision docs (`keep_or_deprecate_decision.md`,
  `audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`, `roadmap.md`, `standalone_items.md`)
  beyond what M1 already recorded.
- Do not attempt a full sweep of the wider `docs/engine/contracts/knowledge_gateway_mcp/` directory
  (10+ other `status: active` docs) — only `redaction_retention_policy.md`'s 3 specific citation
  spots are in scope (Step 13). Note the wider sweep as a future follow-on in the Completion
  Summary.
- Do not attempt a full `v2_evidence`/`test_path` rewrite of all 21 stale entries (INFRA-334,
  335-357 minus 340/341/353) — only INFRA-342/343 get a full rewrite (they're directly about the
  moved symbols); the other 19 (including INFRA-334, added Review round 2) get the lightweight
  additive `divergence_note` annotation only (Step 13, corrected during Review — see the plan's
  own notes above). Never touch the 3 non-stale entries in the INFRA-335-357 range (INFRA-340,
  341, 353) or the 6 unrelated P2 entries (INFRA-295, 297, 379, 382, 390, 410).
- Do not archive or modify the 7 `tools/agent-monitoring/kgmcp_*_runner.py`/
  `kgmcp_baseline_corpus.py` files (Step 12's explicit no-op) or `generate_retro.py`.
- Do not touch `.mcp.json`'s `knowledge-search` or `github` entries — must stay byte-identical.
- Do not widen the `done-checker.md`/`test-scoper.md` frontmatter edit beyond the exact
  `mcp__knowledge-gateway__*` grants named — do not add or remove any other tool (in particular,
  never add `Edit` to `test-scoper.md`).
- Do not let the `tests/archive/` move (Step 8) sweep in any file beyond the 15 explicitly listed
  — in particular, never move the 3 `tests/docs/test_phase{4,4,5}_*.py` files removed from this
  step's list in the Review-round-1 correction (they have no real dependency on anything archived).
- Do not inline `open_connection_with_limits()`'s SQLite-tuning logic directly into
  `tools/retrieval_cache.py` — it must stay behind the imported function call (Step 3's Anti-Drift
  guard).
- Do not split the `done-checker.md`/`test-scoper.md` frontmatter edits and the
  `test_wave1_agent_tools_frontmatter.py` dict update across separate commits/steps (Step 11) — they
  must land together.
- Do not rewrite `tools/archive/knowledge_gateway_cache.py`'s internal import of
  `knowledge_gateway_redaction` to point at the new archive path (Step 9's explicit decision) —
  leave it as a frozen historical snapshot.

## Dependency Map

- Step 2 depends on Step 1 (symbols must exist in the new module before being removed from the old
  one).
- Step 3 depends on Step 1 (new module must exist to import from).
- Step 4 depends on Step 1 (same reason, for `MAX_PAYLOAD_BYTES`).
- Step 5 depends on Step 1 (tests the new module).
- Step 6 depends on Step 3 (asserts the import-path change Step 3 makes).
- Step 8 depends on Step 7 (norecursedirs exclusion should land before/alongside the test move so
  collection state is never ambiguous mid-sequence).
- Step 9 depends on Step 2 (the trimmed remainder is what gets archived) and on Step 8 (test files
  must be out of the collected-test tree before their source dependency is archived, to avoid a
  transient broken-collection window).
- Step 10 is independent of Steps 1-9 (pure `.mcp.json` edit) but is sequenced after Step 9 for
  narrative flow (deregister after the code that backs the registration is archived).
- Step 11 is fully independent of Steps 1-10 (frontmatter-only change) and could run in parallel.
- Step 12 is a no-op, no dependency.
- Step 13 depends on Step 1 (needs the new module's real post-move line numbers) and Step 9 (needs
  to know the final archive path for the §9 split).
- Step 14 depends on all of Steps 1-13 being complete and merged.

Steps 1-2-3-4-5-6 form one connected chain (the extraction); Steps 7-8-9 form a second chain (the
archival); Steps 10, 11, 12 are independent leaves; Step 13 depends on both chains; Step 14 depends
on everything.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: `scan_for_secrets()`, `open_connection_with_limits()`, `evaluate_write_candidate()` (and the full transitive closure) importable from a new, stable, gateway-independent module | Step 1 | Step 5's `tests/tools/test_write_path_guard.py` |
| AC2: `tools/retrieval_cache.py` imports the relocated symbols from the new location, confirmed via a real test run showing zero regressions | Step 3 | Step 6's new architecture-guard test in `tests/tools/test_retrieval_cache.py`; full `tests/tools/test_retrieval_cache.py` suite |
| AC3: `tools/knowledge_gateway_{mcp,router,packet_assembly,cache,redaction}.py` and `tools/start_knowledge_gateway_mcp.sh` archived (moved, not deleted) to a clearly-named archive location | Steps 2, 9 | New `tests/tools/test_knowledge_gateway_archival.py` (Step 9) |
| AC4: `.mcp.json`'s Knowledge Gateway MCP registration removed | Step 10 | `tests/tools/test_mcp_json_registration.py` |
| AC5: `done-checker.md`/`test-scoper.md` no longer carry the accidental `mcp__knowledge-gateway__*` grant | Step 11 | `tests/tools/test_wave1_agent_tools_frontmatter.py` parametrized cases |
| AC6: every test that legitimately covered the gateway package or `retrieval_cache.py`'s shared-symbol dependency still passes (moved/updated, not silently deleted/skipped) | Steps 4, 5, 6, 7, 8, 9, 10, 11 | Full `pytest tests/tools/ -v`, `pytest tests/docs/test_redaction_retention_policy_doc.py -v`, `pytest tests/archive/ -v --co` |
| AC7: a follow-on ticket for M2 steps 3-4 is filed once archival lands | Step 14 | Presence of new ticket file, correct frontmatter/Related Tickets |

## Anti-Drift Notes

- `evaluate_write_candidate()` needs its full §2-§7 transitive closure (~19 symbols, not 3) —
  Step 1 enumerates every one by exact line number, confirmed by direct read; a 3-function-only
  extraction ships a broken `NameError`-raising module.
- `.mcp.json`'s `github`/`knowledge-search` entries must stay byte-identical — Step 10 confirms the
  exact current 3-entry structure by direct read before editing.
- `retrieval_cache.py`'s own architecture-guard test
  (`test_sqlite_defaults_not_silently_implemented`) must keep passing — Step 3 explicitly forbids
  inlining the connection-tuning logic.
- The `test_wave1_agent_tools_frontmatter.py` dict update and the two `.md` frontmatter edits must
  land in the same step/commit (Step 11) — confirmed by direct read of the dict's exact current
  contents (L35-46) and the forbidden-pairs list (L58) that must stay untouched.
- `tools/knowledge_gateway_cache.py`'s internal import of `knowledge_gateway_redaction` is
  deliberately left unfixed post-archival (Step 9) — this is a considered decision matching the
  `scripts/archive/` "frozen snapshot" precedent, not an oversight; do not "fix" it during Verify.
- Test-archival mechanism is decided: move to `tests/archive/` + `pyproject.toml` `norecursedirs`
  edit (Steps 7-8), not in-place `@pytest.mark.skip` — reasoning given in Step 8.
- The 7 `tools/agent-monitoring/kgmcp_*_runner.py`/`kgmcp_baseline_corpus.py` files and
  `generate_retro.py` are deliberately left untouched (Step 12) — confirmed independent
  (`generate_retro.py`) or one-time/already-run-with-fixtures-committed (the 7 runners).
  `generate_retro.py` imports only `retrieval_cache.py` (confirmed via investigation's own grep),
  never any gateway module — its test suite passing unmodified is the anti-drift signal per
  test_plan.md.
- `docs/parity_ledger/infrastructure.yaml` edits (Step 13) must go through
  `tools/parity_ledger_writer.py`, never a raw multi-line `Edit` on this ~9500+ line shared file —
  this repo's own documented corruption risk for full-file YAML rewrites via ad-hoc scripts/raw
  edits applies directly here.
- §9 of `redaction_retention_policy.md` currently describes both a moving function
  (`open_connection_with_limits`) and two staying functions
  (`check_db_size_within_limit`/`execute_bounded_transaction`) in one paragraph — Step 13 requires
  splitting this citation, not a single find-replace, or the doc will misattribute the staying
  functions to the new module.

## Correction (2026-09-07, pre-Review-verdict)

`agent-working-design` reviewed the plan's original "2 fixed now / 14 deferred" parity-ledger split
and flagged the criterion it was drawn on as wrong: it should be "does this ticket's own archival
make the entry's claim factually false," not "which entries are specifically about the extracted
symbols." Independently re-scanned the real `docs/parity_ledger/infrastructure.yaml` file against
that corrected criterion and found 20 stale entries in the INFRA-335-357 range, not 2 — Step 13
above is corrected accordingly (full rewrite for the 2 entries directly about the moved symbols,
lightweight `divergence_note` annotation for the other 18, per-entry, not a full rewrite of all 20).

## Review Round 1 (NEEDS_CHANGES, resolved)

architecture-reviewer independently confirmed every other claim in this plan against real source
(the full symbol/line inventory, `retrieval_cache.py`'s call sites, `.mcp.json`'s structure,
`pyproject.toml`'s `norecursedirs`, the frontmatter grants, the `scripts/archive/` precedent,
INFRA-342/343's locations) — all accurate. One required change: 3 of the originally-listed 18
`tests/docs/`/`tests/tools/` files in Step 8 (`test_phase4_direct_tool_comparison_doc.py`,
`test_phase4_workflow_recommendation_doc.py`, `test_phase5_repeated_demand_measurement_doc.py`)
have zero real dependency on anything this ticket touches — verified independently via
`grep -n "^import\|^from"` on each, confirming no import of any `tools/knowledge_gateway_*` module
and no `.mcp.json` reference; their only match on "knowledge_gateway_mcp" is as a doc-path
component they read as plain text. Moving them would have silently dropped live, passing coverage
under a false "would otherwise fail collection" premise. Step 8 corrected to a 15-file move list;
the 3 files stay in place, untouched. All references to "18 gateway test files" elsewhere in this
plan updated to 15 accordingly (the separate parity-ledger-entries count, an unrelated number, is
unaffected by this specific fix — see the Correction section above and Review Round 2 below for
its own further correction).

## Review Round 2 (NEEDS_CHANGES, resolved)

architecture-reviewer independently re-verified Round 1's fix (3 test files correctly retained) and
the pre-Review parity-ledger correction (20 stale entries) against real files — both held, with one
gap: the parity-ledger scan's `INFRA-335-357` range missed `INFRA-334`, whose `test_path`
(`tests/tools/test_kgmcp_measurement_baseline.py`) is item #9 on Step 8's move list, making it a
21st stale entry the same way the others are, even though its own `v2_evidence` (citing
`tools/agent-monitoring/kgmcp_baseline_corpus.py`, a file Step 12 leaves in place) is not itself
stale — only its `test_path` half is. Fixed: Step 13's fix list now includes `INFRA-334` in the
lightweight-annotation tier (19 entries total in that tier, not 18; 21 stale entries total, not 20),
with a note that its own annotation wording should reflect that only the test moved, not the
source file it documents.

## Unresolved Questions

None. Every open decision investigation.md flagged (test-archival mechanism, new module name/
location, runner-script disposition, whether `knowledge_gateway_cache.py`'s internal import needs
updating, parity-ledger sizing) is resolved above with stated reasoning, crediting the
investigation's own recommendation where one was given (Risk #2 → option (a); Risk #3 → leave in
place; Risk #7 → `tools/write_path_guard.py`). The one genuinely non-material item investigation
flagged for completeness only — the "2 vs 2,138" vs. "13 vs 3,212" vs. "1 vs 3,375" usage-count
reconciliation gap — requires no plan decision; it does not affect any step above, since the
re-ratification already happened on the strongest, independently-verified figure before this ticket
began.

## Deviations (found during Implement)

1. **Step 3's literal 5-line docstring-mention list was followed exactly, not expanded.** During
   implementation I initially also rewrote two additional `tools/knowledge_gateway_cache.py` path
   mentions inside `tools/retrieval_cache.py`'s own docstrings (describing the *orchestrator* of
   the write path, not the moved `open_connection_with_limits()`/`evaluate_write_candidate()`
   calls themselves) to say `tools/archive/knowledge_gateway_cache.py`. On review this went beyond
   the plan's own precisely-scoped 5-spot list (L627, L1036, L1061, L1229, L1278), so I reverted
   those two extra edits and left the `tools/knowledge_gateway_cache.py` mentions as originally
   written — matching the plan's own literal scope exactly, per the "do not re-expand anything a
   review round narrowed" instruction.

2. **Step 13's `redaction_retention_policy.md` fix touched a 4th spot beyond the plan's named 3.**
   The plan named exactly L56, L193-194, and L304-308. While fixing L193-194 (the
   `redaction_policy_version`/`WriteDecision.redaction_policy_version` line citations), I found an
   adjacent, directly-related test-path citation in the same paragraph
   (`tests/tools/test_knowledge_gateway_redaction.py`, describing "a dedicated test" for the
   version-distinctness claim) that the plan's 3-spot enumeration did not name but which becomes
   equally stale once that test file moves to `tests/archive/`. Updated it to
   `tests/tools/test_write_path_guard.py` (the real, still-collected home of that exact test,
   `TestRedactionPolicyVersion::test_redaction_policy_version_distinct_from_retrieval_version`) in
   the same edit, since leaving it stale would have been a known, spotted gap left unstated.

3. **Real, plan-level gap found: not all 15 archived test files are individually collectable via
   `pytest tests/archive/ --co`, contrary to Steps 7/8's own stated Verify bar.** 10 of 15 files
   (the ones using `importlib.util.spec_from_file_location` with a literal path) collect cleanly
   once their literal path constants are updated to `tools/archive/...` (done, per Step 9's own
   "mechanical find-and-fix" instruction). The other 5
   (`test_kgmcp_baseline_corpus_dedup_coverage.py`, `test_knowledge_gateway_cache.py`,
   `test_knowledge_gateway_mcp.py`, `test_knowledge_gateway_packet_assembly.py`,
   `test_knowledge_gateway_redaction.py`) fail collection outright with `ImportError`/
   `FileNotFoundError`, because their SUT modules either (a) use a plain `from tools import X`
   package-style import of a module that itself moved into `tools/archive/` (unreachable via plain
   package import without a `tools/archive/__init__.py`, which Step 9 explicitly declined to add),
   or (b) internally compute `_REPO_ROOT = Path(__file__).resolve().parent.parent`, which silently
   breaks (resolves one directory too shallow) once the module moves one directory level deeper
   from `tools/` to `tools/archive/`, cascading into a `FileNotFoundError` on the module's own
   schema-loading code (`tools/archive/knowledge_gateway_mcp.py`).

   I did not fix either failure mode, and consider this the correct call: fixing (a) would require
   exactly what Step 9's own reasoning explicitly rejected (an `__init__.py` package under
   `tools/archive/`, breaking the flat-file, no-package precedent this ticket matches from
   `scripts/archive/`); fixing (b) would mean actively maintaining the *internal* logic of a module
   Step 9 explicitly designates a frozen historical snapshot (the same category of "not maintained/
   runnable code" Step 9 already accepts for `knowledge_gateway_cache.py`'s own left-unfixed
   `knowledge_gateway_redaction` import — this is that same precedent applying to 4 more files, not
   a new decision). None of this affects any of the ticket's real Acceptance Criteria: AC6's actual
   regression guard is `tests/tools/`/`tests/docs/`'s default collection (2623 tests, zero
   collection errors, confirmed) plus `tests/archive/`'s exclusion from that default run (confirmed
   via `norecursedirs`) — none of the 7 ACs require every archived file to be individually
   collectable when run directly, only Steps 7/8's own internal Verify guidance implied that, and
   that guidance is now understood to hold only for the spec_from_file_location-based subset (10 of
   15), not universally.
