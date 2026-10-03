---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE
artifact_type: investigation
tags: [ai, mcp, governance]
---

# Investigation — TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE

## Current Behavior

### `tools/knowledge_gateway_redaction.py` (445 lines) — full symbol inventory

Self-contained: it imports nothing from any other `knowledge_gateway_*` module (confirmed by
direct read and by the module's own docstring, line 12-16). Every symbol below is a pure
function/dataclass/constant.

| Symbol | Real external consumer (outside gateway package + its own tests)? | Depends on (internal) |
|---|---|---|
| `check_allowlist()` (L88) | No direct external call, but a transitive dependency of `evaluate_write_candidate()` | — |
| `_hash_text()` (L111) | Transitive dep of `evaluate_write_candidate()` | — |
| `redact_content()` (L115), `_HOME_PATH_PATTERN`, `_ABS_PATH_PATTERN` | Transitive dep of `evaluate_write_candidate()` and `check_never_cache_categories()` | — |
| `scan_for_secrets()` (L161), `_SECRET_SCAN_PATTERNS` | **Yes** — `governance_capability_policy_epic.md` M4 (not yet built; "Reuse `scan_for_secrets(text) -> str \| None` as-is") | — |
| `check_size_cap()` (L185) | Transitive dep of `evaluate_write_candidate()` | — |
| `check_never_cache_categories()` (L215), `CATEGORY_*` (6 constants), `_TOKEN_SHAPED_SECRET_PATTERNS`, `_ENV_VALUE_PATTERN`, `_CONFIG_LINE_PATTERN`, `_ARBITRARY_CONFIG_MIN_LINES` | Transitive dep of `evaluate_write_candidate()` | `scan_for_secrets()`, `redact_content()`'s patterns |
| `WriteDecision` (L261, dataclass) | Transitive dep — `evaluate_write_candidate()`'s return type | — |
| `evaluate_write_candidate()` (L270) | **Ticket's own Acceptance Criteria names it as required.** Real code caller today is `tools/knowledge_gateway_cache.py::perform_cache_write()`/`perform_context_packet_cache_write()` — itself a gateway module being archived. `tools/retrieval_cache.py` references it **only in docstrings** (lines 1061, 1278), never calls it. `tools/agent-monitoring/kgmcp_phase2_gateway_runner.py` monkeypatches it as a measurement spy (one-time script, gateway-adjacent). | `check_allowlist()`, `redact_content()`, `scan_for_secrets()`, `check_size_cap()`, `check_never_cache_categories()`, `_hash_text()` — i.e. essentially the entire §2-§7 block |
| `open_connection_with_limits()` (L311) | **Yes, real, live code call** — `tools/retrieval_cache.py` lines 632, 1041, 1237 (`_get_access_log_connection()`, `_get_level1_connection()`, `_get_level2_connection()`) | `SQLITE_BUSY_TIMEOUT_MS`, `SQLITE_FILE_MODE` |
| `check_db_size_within_limit()` (L330) | No — only `tools/knowledge_gateway_cache.py` (archived) calls it | `SQLITE_MAX_DB_SIZE_BYTES` |
| `execute_bounded_transaction()` (L334) | No real caller anywhere except its own unit test; module's own docstring calls it unused-in-production ("zero real statements in its own tests/production use") | — |
| `acquire_write_guard()`/`release_write_guard()` (L349/L360) | No — only `tools/knowledge_gateway_cache.py` (archived) calls them | `_write_locks`, `_write_locks_guard` |
| `CacheRowSnapshot`, `gc_eligible_*` (6 predicates), `gc_eligibility_never_flags_protected_evidence()`, `CACHE_STATUS_WRITE_COMPLETE`, `_PROTECTED_EVIDENCE_KINDS` (§10) | No — never wired into any live path anywhere (module's own docstring: "no automatic cache-GC wiring") | — |

**Key finding not obvious from the ticket's own framing**: the ticket names 3 symbols
(`scan_for_secrets`, `open_connection_with_limits`, `evaluate_write_candidate`) as needing
extraction, but `evaluate_write_candidate()` transitively pulls in essentially the *entire*
§2-§7 block (allowlist, redaction, secret-scan, size-cap, never-cache-categories, and all their
private helper patterns/constants) — you cannot extract `evaluate_write_candidate()` alone without
also moving `check_allowlist`, `redact_content`, `check_size_cap`,
`check_never_cache_categories`, `_hash_text`, `WriteDecision`, and every constant/pattern those
depend on. Only §9's remaining two functions (`check_db_size_within_limit`,
`execute_bounded_transaction`), the write-guard pair (`acquire_write_guard`/`release_write_guard`),
and all of §10 (GC-eligibility predicates) have **zero** real consumer outside the gateway package
and can legitimately stay behind in the archived file.

### `tools/retrieval_cache.py` — the confirmed real consumer

`from tools import knowledge_gateway_redaction as _kgr_redaction` (line 53). Grepped every call
site (`grep -n "_kgr_redaction\."`): exactly 3, all `_kgr_redaction.open_connection_with_limits(CACHE_DB_PATH)` —
`_get_access_log_connection()` (L632), `_get_level1_connection()` (L1041), `_get_level2_connection()`
(L1237). `evaluate_write_candidate()` appears only in two docstrings (L1061, L1278) describing that
the *real* write path is orchestrated by `tools/knowledge_gateway_cache.py` (itself archived) — it
is never imported-and-called by `retrieval_cache.py`'s own code. This narrows, but does not
eliminate, the ticket's Acceptance Criteria requirement: `evaluate_write_candidate()` must still be
importable from the new location per the ticket text, even though `retrieval_cache.py` itself
doesn't literally call it today.

### Full-repo consumer sweep (`grep -rn "knowledge_gateway_redaction"` across `tools/`, `src/`, `tests/`, `.claude/`, `.mcp.json`)

Real, load-bearing external consumers found (i.e., outside the `tools/knowledge_gateway_*.py`
package and outside `tests/tools/test_knowledge_gateway_redaction.py`/
`tests/tools/test_knowledge_gateway_cache.py`):
1. `tools/retrieval_cache.py` (confirmed above).
2. `tests/docs/test_redaction_retention_policy_doc.py` — imports the module *directly* (not via
   the `tools` package: `sys.path.insert(0, str(_REPO_ROOT / "tools")); import
   knowledge_gateway_redaction as kgr`) at line 80, to assert `kgr.MAX_PAYLOAD_BYTES` is mentioned
   in `redaction_retention_policy.md` (`test_payload_size_cap_doc_matches_live_module_constant`).
   This is a real, currently-passing test outside `tests/tools/` that will break the moment the
   module is archived, unless updated to import from the new location. (It also defines an unused
   `_KNOWLEDGE_GATEWAY_REDACTION_PY` path constant, dead code, safe to drop.)
3. `governance_capability_policy_epic.md` M4 — not yet built, cites `scan_for_secrets()` (line 161)
   by file:line in its own "Related Code Areas" section (line 243). No other file in the repo
   currently imports `scan_for_secrets()` — confirmed via `grep -rn "scan_for_secrets"
   --include="*.py"` (only definition + its own tests + the doc citation above).

No other real external consumers exist. Everything else that references
`knowledge_gateway_redaction` is either: the gateway package's own internal files
(`knowledge_gateway_cache.py`), the gateway's own test suite, one-time measurement runner scripts
under `tools/agent-monitoring/kgmcp_*_runner.py` (see below), or `.claude/agents/test-scoper.md`'s
own prose (an illustrative example of "module with module-level constants", not a functional
dependency — remains accurate in spirit even after the file moves, since the underlying incident
it documents, `TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP`, is historical fact).

### `tools/knowledge_gateway_cache.py` — the real orchestrator of `evaluate_write_candidate()`

`from tools import knowledge_gateway_redaction as rk` (line 67). Calls `rk.acquire_write_guard()`,
`rk.check_db_size_within_limit()`, `rk.SOURCE_TYPE_CONTEXT_SEARCH`/`rk.SOURCE_TYPE_GRAPHIFY`,
`rk.evaluate_write_candidate()`, `rk.ALLOW`, `rk.release_write_guard()` (lines 350-399, 546-619).
This module is itself one of the four gateway modules being archived (`{mcp,router,
packet_assembly,cache}`), so its own dependency on the redaction module does not need to keep
working post-archival — but it confirms `evaluate_write_candidate()` is real, live-wired logic
today, not dead code.

### Gateway-adjacent measurement tooling under `tools/agent-monitoring/`

`kgmcp_baseline_runner.py`, `kgmcp_baseline_corpus.py`, `kgmcp_phase1_gateway_runner.py`,
`kgmcp_phase2_gateway_runner.py`, `kgmcp_phase3_gateway_runner.py`,
`kgmcp_phase4_direct_tool_comparison_runner.py`, `kgmcp_phase4_warm_direct_tool_comparison_runner.py`
are all explicitly self-described "one-time... never wired into the fast pytest loop" scripts that
`importlib.util.spec_from_file_location()`-load `tools/knowledge_gateway_mcp.py` by literal path,
or (`kgmcp_phase2_gateway_runner.py`, `kgmcp_phase3_gateway_runner.py`) `from tools import
knowledge_gateway_redaction as _kgr_redaction` directly, to measure the live gateway's
latency/token/cache behavior. `kgmcp_phase2_gateway_runner.py` additionally monkeypatches
`_kgr_redaction.evaluate_write_candidate` as a pass-through spy. **These are gateway-package-adjacent,
not independent monitoring tooling** — once the gateway modules are archived and deregistered from
`.mcp.json`, these scripts have no live subject to measure and their own literal-path
`importlib` loads would break if run. They are historical, already-run, one-time scripts (their
results are committed as fixtures under `tests/tools/fixtures/kgmcp_*.json`), so leaving them
in place unexecuted is low-risk, but they are honestly part of the same archival unit, not
something this ticket's Related Code Areas currently names.

By contrast, `tools/agent-monitoring/generate_retro.py` **is** independent, surviving monitoring
tooling: `grep -n "knowledge_gateway\|retrieval_cache" tools/agent-monitoring/generate_retro.py`
shows it does `from retrieval_cache import (...)` (never `knowledge_gateway_redaction` or any
other gateway module) and every other match is prose inside a docstring/comment describing how the
KGMCP hooks into `log_cache_access()` historically. It depends only on `retrieval_cache.py`, which
this ticket keeps working — `generate_retro.py` needs no code change.

## Mechanics / Engine Contracts Constraints

- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §2-§10 is the
  authoritative source the extracted functions must keep bit-identical: §2 allowlist, §3 redaction
  + hashing, §4 secret-scan (10 patterns), §5 64 KiB size cap, §6 `redaction_policy_version`
  stamping, §7 never-cache enumeration, §9 SQLite operational limits, §10 GC-eligibility
  predicates. Extraction must not change any of this behavior — it is a pure code-location move,
  confirmed safe because the module has zero external dependency on gateway internals (self-
  contained, per the module's own docstring and the graphify traversal above).
- `docs/observability/retrieval_retention_redaction_policy.md` is `retrieval_cache.py`'s own cited
  redaction-category-name authority (per its module docstring) — it cross-references
  `redaction_retention_policy.md` by path only, carries no direct code `file:line` citations, so it
  needs no change from this ticket.
- Authoritative Mechanics Rule (CLAUDE.md): "Documentation and source code must remain in 100%
  semantic parity. If logic changes, update the corresponding doc AND the parity ledger entry... in
  the same session." Archiving code that multiple `status: active` docs and 16+ `docs/parity_ledger/
  infrastructure.yaml` entries cite by exact `file:line` is exactly the kind of change this rule
  covers — see "Docs Requiring Update" and "Risks" below for the scope this actually implies.

## Docs Requiring Update

- `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`: cites
  `tools/knowledge_gateway_redaction.py::ALLOWED_SOURCE_TYPES` (line 57),
  `tools/knowledge_gateway_redaction.py:47`/`:225` (line 193-194), and states the functions live
  "in a separate new module, `tools/knowledge_gateway_redaction.py`" (line 307) — every one of
  these becomes a wrong path/line once this ticket moves the cited symbols to the new module and
  archives the rest. Must be updated to point at the new module for the symbols that move, and
  either note the remainder is archived or drop the stale line-number citations.
- `docs/parity_ledger/infrastructure.yaml`: at minimum INFRA-342 (`text: 'Redaction/allowlist
  write-path enforcement functions in tools/knowledge_gateway_redaction.py...'`, `v2_evidence:
  'tools/knowledge_gateway_redaction.py:59...'`) and INFRA-343 (cites
  `knowledge_gateway_redaction.evaluate_write_candidate()`/`.open_connection_with_limits()` by
  name) have `v2_evidence` pointing at file:line locations this ticket's own action moves or
  archives. Both are P1 `status: verified` — the rule requiring an update on behavior/location
  change applies regardless of P0-only test_path enforcement. See Risks below: this is one entry
  in a much larger cluster (16+ P1 entries, INFRA-335 through INFRA-357) whose full remediation is
  likely too large for this ticket alone — flagged, not silently narrowed.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`:
  its own "Related Code Areas" section (line 243) cites `tools/knowledge_gateway_redaction.py —
  source of scan_for_secrets() (line 161) for M4` — this becomes a stale pointer the moment
  `scan_for_secrets()` moves to the new module. Cheap, mechanical fix (one citation line), and a
  real future-implementer hazard if left stale (M4's own implementer would follow a broken path).
  This is not one of the 5 decision docs this ticket's Out of Scope excludes from editing
  (`keep_or_deprecate_decision.md`, `audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`,
  `roadmap.md`, `standalone_items.md`) — it is a distinct doc this ticket is free to touch for this
  narrow citation fix.

The following were considered and are **not** required to change for this ticket:

`docs/observability/retrieval_retention_redaction_policy.md` (path:
`docs/observability/retrieval_retention_redaction_policy.md`) does not need to change: it only
cross-references `redaction_retention_policy.md` by path, carries no `tools/knowledge_gateway_*`
file:line citations of its own to go stale.

The wider `docs/engine/contracts/knowledge_gateway_mcp/` directory (path:
`docs/engine/contracts/knowledge_gateway_mcp/`) — `evidence_cache_identity_contract.md`,
`cache_migration_plan.md`, `phase0` through `phase5` measurement docs
(`phase2_baseline_recomparison.md`, `phase3_pilot_acceptance_measurement.md`, etc.),
`knowledge_gateway_mcp_contract.md` and siblings — all carry `status: active` frontmatter and many
cite `tools/knowledge_gateway_*.py` file:line locations that will go stale once those files are
archived. This ticket does not attempt a full sweep of that directory: doing so (10+ files, each
needing individual review of which citations are load-bearing vs. historical-measurement-record)
is a materially larger unit of work than "extract 3 symbols + archive 5 files + deregister 1 MCP
entry + fix 2 agent frontmatter grants," and the ticket's own Scope section does not name this
directory. Flagged explicitly as a Risk (see below) rather than silently left unaddressed — the
clean, low-risk fix once M2 steps 3-4 (delete) land is a frontmatter `status: historical` sweep
over this directory, matching this repo's own `TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER`/
`TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS` precedent for docs whose subject matter has become
historical.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml` — 24 entries directly reference
`knowledge_gateway`/`retrieval_cache` (found via `text`/`test_path` scan): INFRA-295, 297 (P2,
retrieval_cache-only, stay valid — `retrieval_cache.py` itself is not archived), INFRA-335 through
INFRA-357 (P1, 16 entries — every one of these documents a piece of the now-to-be-archived gateway
package, `v2_evidence` citing exact `file:line` locations, `test_path` citing test files this
ticket's own step 6 requires moving/marking), INFRA-379, 382, 390, 410 (P2, `retrieval_cache.py`/
`post_tool_hook.py`/`settings_json_hooks_wiring` — unaffected, `retrieval_cache.py` keeps working).

None of the affected entries are P0 (all P1/P2), so the hard "P0 requires a passing test_path"
rule does not block this ticket. The softer rule still applies: entries whose `v2_evidence`/
`test_path` this ticket's own action makes stale should be updated in the same session per the
Authoritative Mechanics Rule. Given the cluster size (16 P1 entries), full remediation may be
better sized as this ticket updating INFRA-342/343 (the two entries directly about the extracted
symbols) plus a status/note pass across the rest (e.g. appending "archived — see
TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE" to each without re-deriving each citation), rather
than a full line-by-line `v2_evidence` rewrite for all 16 — a Plan-phase sizing decision, not
resolved here.

## Prior Work

- `TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY` (done) — wrote the original policy doc this
  module implements.
- `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` (done, `stored_artifacts/
  TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/investigation.md`) — built
  `knowledge_gateway_redaction.py` itself; useful precedent for the module's own internal
  boundaries (it deliberately duplicates `_hash_text()` rather than importing
  `tools/retrieval_cache.py`'s private helper, the opposite choice `knowledge_gateway_cache.py`
  later made for its own reuse of `retrieval_cache.py`'s `_normalize_query()`/`_hash_text()` — a
  precedent for "duplicate a tiny pure helper rather than reach into another module's private
  surface," relevant if the new extraction module ever needs to avoid a fresh dependency).
- `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` (done) — wired `evaluate_write_candidate()` into
  the real write path via `knowledge_gateway_cache.py`; source of INFRA-343.
- `TCK-20260818-KGMCP-TICKET-VERIFY-SCOPED-REGRESSION-GAP` (done) — the real incident behind
  `tools/gate_checks/test_scope_coverage_static.py`'s existence: a legitimate
  `tools/retrieval_cache.py` change broke two pre-existing `tests/tools/` tests that a scoped
  `pytest_command` missed. Directly relevant precedent: this ticket's own Test phase must scope
  its `pytest_command` to cover `tests/tools/` as a bare directory, not cherry-picked files (per
  this project's `feedback_hand_orchestration_gate_patterns` memory note).
- `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` (done) — source of the accidental
  `mcp__knowledge-gateway__*` grant on `done-checker`/`test-scoper`; its own
  `tests/tools/test_wave1_agent_tools_frontmatter.py` hard-pins the exact `tools:` string for both
  agents (see Test Plan — this test must be updated as part of this ticket, not just the two
  `.md` files).
- `TCK-20260616-DOCS-ARCHIVE-HISTORY-LEDGER`/`TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS` (done) —
  precedent for `status: historical`/`status: archive` frontmatter sweeps over doc directories
  whose subject matter has become historical; relevant to the wider
  `docs/engine/contracts/knowledge_gateway_mcp/` directory flagged above (not executed by this
  ticket).
- `scripts/archive/` (5 files, created by commit `bc3915c0`/`TCK-20260820-...PARITY-LEDGER-HYGIENE`
  lineage) — the only existing "archive a tool script, don't delete" precedent in this repo: flat
  `<parent>/archive/<same-filename>.py`, no subdirectory nesting, no `README`, no `__init__.py`
  (confirmed: not a Python package). No `tools/archive/` exists yet. Confirmed via
  `git log --oneline -- scripts/archive/` that these files had zero test coverage at archival time
  — this repo has **no existing precedent** for what happens to a moved file's *own test suite*,
  since `scripts/archive/`'s 5 files were never covered by any test. This ticket is the first real
  test of that question (see Risks).

## Risks and Open Questions

1. **Scope is larger than the ticket's own "extract 3 symbols, archive 5 files" framing suggests.**
   `evaluate_write_candidate()` alone drags in essentially the whole §2-§7 block (see Current
   Behavior table) — not a blocker, but Plan must account for moving ~15 symbols, not 3.
2. **No repo precedent for archiving a module whose own test suite is large and still relevant.**
   `scripts/archive/`'s 5 files had zero test coverage when archived. This ticket's gateway modules
   have ~15 dedicated test files (`test_knowledge_gateway_{mcp,router,packet_assembly,cache,
   redaction,failure_semantics,contract_schemas}.py`, 7 `test_kgmcp_phase*`/`test_kgmcp_baseline*`
   files, plus 3 `tests/docs/test_phase4_*_doc.py`/`test_phase5_*_doc.py` files) that directly
   `import` the modules being archived — several with hard `.mcp.json`-registration assertions
   (`test_knowledge_gateway_mcp.py::test_mcp_json_gains_exactly_one_new_server_entry`,
   `test_knowledge_gateway_packet_assembly.py`/`test_knowledge_gateway_router.py`/
   `test_knowledge_gateway_contract_schemas.py` all assert `.mcp.json` carries the
   `knowledge-gateway` entry). **These tests will fail as soon as the `.mcp.json` entry is removed
   and/or the modules are moved**, regardless of where the code lands, unless they are themselves
   moved/updated/marked. The ticket's own Acceptance Criteria ("Every test that legitimately
   covered the gateway package... still passes (moved/updated as needed, not silently deleted or
   skipped)") anticipates this but does not resolve *how* — `pyproject.toml`'s
   `[tool.pytest.ini_options] norecursedirs` does not currently exclude any `tests/archive/`-shaped
   path, so simply moving test files to a `tests/archive/` directory without also updating
   `norecursedirs` (or otherwise excluding them from default collection) would not stop them from
   being collected and failing. This is a genuine Plan-phase decision point, not resolved by this
   investigation — options include: (a) move gateway test files to `tests/archive/` AND add
   `tests/archive` to `norecursedirs` (mirrors the code archive exactly, requires a `pyproject.toml`
   edit — a config change, reviewable in diff, not silent); (b) mark them
   `@pytest.mark.skip(reason="...")` in place with a citation to this ticket; (c) delete them,
   which the ticket's own Acceptance Criteria explicitly forbids ("not silently deleted"). This
   investigation recommends (a) for consistency with the code-archive convention, but flags it as
   an open decision for Plan/Architecture Review, not a resolved fact.
3. **`tools/agent-monitoring/kgmcp_*_runner.py`/`kgmcp_baseline_corpus.py` (7 files) are not named
   in the ticket's Related Code Areas but are genuinely gateway-adjacent** — one-time measurement
   scripts that `importlib`-load or directly import the modules being archived. They still work
   today (they already ran once; their results are committed as fixtures) but would break if
   re-run after archival. Recommend leaving them in place (never re-run, historical record) rather
   than archiving — but flag this explicitly rather than silently deciding it, since they do
   directly import a to-be-archived module by literal path.
4. **The `docs/engine/contracts/knowledge_gateway_mcp/` directory (10+ `status: active` docs)
   goes stale** the moment the code archives, but a full sweep is out of this ticket's committed
   scope per its own Scope section — see "Docs Requiring Update" above.
5. **Parity ledger cluster (16 P1 entries, INFRA-335 through INFRA-357)** — same sizing tension as
   #4. None are P0, so this is not a hard blocker, but leaving all 16 with stale `v2_evidence`
   after this ticket lands is a real, visible gap for the next parity-ledger hygiene sweep to find.
6. **Usage-count reconciliation gap** (per ticket's own Assumptions): `standalone_items.md` §1's
   original text says "2 vs 2,138" calls; a direct grep at the time found "13 vs 3,212"; the final
   re-ratification (`keep_or_deprecate_decision.md` §4) used a third, independently re-verified
   figure "1 vs 3,375." All three show the same order-of-magnitude imbalance and the ratification
   already happened on the strongest (most-recently-verified) figure — not material to this
   ticket's own scope, noted for completeness only, per the ticket's own instruction not to
   silently ignore it.
7. **New module name/location is genuinely undecided** — confirmed via `search_docs`, `graphify
   query`, and direct reads of `standalone_items.md` §1, `governance_capability_policy_epic.md` M4,
   and `keep_or_deprecate_decision.md` §4: none prescribes a specific path, only "a location
   independent of the gateway module" / "somewhere stable that won't itself get archived alongside
   the gateway."

   **Recommendation: `tools/write_path_guard.py`.** Flat file directly under `tools/`, matching
   this repo's confirmed convention (no existing `tools/shared/`/`tools/security/` package
   convention; the "CLI/module ownership" precedent in
   `docs/plans/archive/agent_infrastructure/parity_ledger_sqlite_context/v1_decisions_phase0.md`
   explicitly favors "flat files directly under `tools/`, not a new package"). Name rationale: the
   module being extracted is, in its own current docstring's own words, "pure, directly-testable
   write-path enforcement functions" (`tools/knowledge_gateway_redaction.py` line 2) — `evaluate_
   write_candidate()`/`WriteDecision`/`open_connection_with_limits()` are all about validating and
   safely opening a connection for a *write path* into a cache, independent of which caller (the
   now-archived gateway, `retrieval_cache.py`, or the future Bash secret-exposure hook) is doing
   the writing. `write_path_guard` names that write-path-guarding concern directly and carries no
   "gateway" or "redaction"-only framing (redaction is only one of the module's several checks —
   allowlist, secret-scan, size-cap, never-cache-categories, and now connection-limits are equally
   part of it), so it reads as owned by the write-path concern itself, not by the gateway that
   happens to be its first (and soon-departing) caller.

## Anti-Drift Hazards

- **Do not silently narrow "extract `scan_for_secrets`/`open_connection_with_limits`/
  `evaluate_write_candidate`" to a literal 3-function file** — as shown above,
  `evaluate_write_candidate()` needs the transitive §2-§7 closure to actually function; a
  3-function-only extraction would ship a broken `evaluate_write_candidate()` that
  `NameError`s on `check_allowlist`/`redact_content`/etc.
- **`.mcp.json`'s `github` entry must be provably untouched** — several existing gateway tests
  (`test_knowledge_gateway_mcp.py::test_search_mcp_py_provably_untouched` and siblings) already
  encode a "frozen files" discipline; the same discipline applies here in reverse (only the
  `knowledge-gateway` key is removed, `knowledge-search`/`github` keys stay byte-identical).
- **`retrieval_cache.py`'s own architecture-guard tests** (`tests/docs/
  test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`) assert
  `PRAGMA journal_mode`/`PRAGMA busy_timeout`/`os.chmod`/`chmod` never appear directly in
  `tools/retrieval_cache.py`'s own source — i.e., the connection-tuning logic must stay exclusively
  behind the extracted `open_connection_with_limits()`, never get inlined into
  `retrieval_cache.py` as a side effect of "simplifying" the import.
- **`test_wave1_agent_tools_frontmatter.py`'s exact-list assertion** (`declared == expected`) means
  the two `.md` frontmatter edits and the Python test's own `_WAVE1_CANDIDATE_TOOLS` dict must be
  changed together, in the same commit — editing only the `.md` files leaves that test red.
- **Do not touch the 5 explicitly-excluded decision docs** (`keep_or_deprecate_decision.md`,
  `audit_phase0_5.md`, `knowledge-gateway-mcp-proposal.md`, `roadmap.md`, `standalone_items.md`)
  beyond what M1 already recorded — this ticket executes M2 steps 1-2, it does not re-document M1
  or pre-empt M2 steps 3-4.
- **Do not implement `governance_capability_policy_epic.md`'s M4 hook itself** — this ticket only
  makes `scan_for_secrets()` importable from a stable location; wiring it into a `PreToolUse` Bash
  hook is that epic's own scope.
