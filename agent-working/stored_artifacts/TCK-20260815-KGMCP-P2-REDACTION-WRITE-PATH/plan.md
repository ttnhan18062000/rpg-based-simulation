---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH
artifact_type: plan
tags: [ai, mcp, security]
---

# Implementation Plan — TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH

## Summary

Add one new module, `tools/knowledge_gateway_redaction.py`, implementing
`redaction_retention_policy.md` §2–§10 as real, pure, directly-testable functions: a §2 allowlist
check, §3 redaction + hashing, the §4 4-pattern secret-scan baseline (shipped verbatim, not
hardened), a §5 8 KB size-cap check, a §6 `redaction_policy_version` stamp folded into a single
`evaluate_write_candidate()` orchestrator that returns a `WriteDecision` dataclass, six independent
§7 never-cache category checks, §9 SQLite operational-limits helpers (WAL/busy-timeout/file-mode/
size-ceiling/bounded-transaction/in-process stampede guard), and six §10 GC-eligibility predicate
functions plus the identity-contract's `SYMBOL`/`FILE` never-flag rule. Nothing in this module opens
`knowledge-index/retrieval_cache.db` at its real path, issues an `INSERT`/`UPDATE` against
`retrieval_provider_result_cache_rows`, or is imported by any of the three live-gateway files — this
ticket ships functions the next ticket (`CACHE-READ-WRITE-WIRING`) calls, never a live write path.
Two gaps investigation.md flagged for Plan to resolve are resolved below (Design Decisions DD2 and
DD3) rather than left open.

## Design Decisions

### DD1 — New module path: `tools/knowledge_gateway_redaction.py`

Follows the `knowledge_gateway_*` naming precedent already used by the three live-gateway files
(`tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`,
`tools/knowledge_gateway_mcp.py`) and matches test_plan.md's own suggested name
(`staging_artifacts/TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH/test_plan.md:55-57`). Test file:
`tests/tools/test_knowledge_gateway_redaction.py`. Confirmed available (no existing file at either
path): `tools/knowledge_gateway_redaction.py` and `tests/tools/test_knowledge_gateway_redaction.py`
do not appear in investigation.md's read of `tools/` or `tests/tools/`, and this ticket's own
Related Code Areas lists only "New: a redaction/write-path module under `tools/` (path decided by
this ticket's own Plan phase)" — no prior ticket claimed this path.

### DD2 — `redaction_policy_version` stays in-memory only; no schema/migration work in this ticket (resolves investigation.md Risk 2)

**Decision: option (b).** `evaluate_write_candidate()`'s returned `WriteDecision.redaction_policy_version`
field is a real, stamped in-memory value (satisfying AC4 verbatim: "a real, stamped value distinct
from the other 3 version axes"). No `ALTER TABLE`/new migration function is added to
`tools/retrieval_cache.py` by this ticket, and no `redaction_policy_version` column is added to
`retrieval_provider_result_cache_rows`. Durable persistence of this value into an actual row is
explicitly deferred to `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`.

**Reasoning, grounded in direct reads, not inference:**
- `LEVEL1_CACHE_COLUMNS` (`tools/retrieval_cache.py:104-128`) and the live
  `migration_001_add_level1_tables()` `CREATE TABLE` statement (`tools/retrieval_cache.py:198-248`,
  both read directly) contain exactly 21 columns; `redaction_policy_version` is not among them —
  confirmed, not assumed.
- `cache_migration_plan.md:111-115` (read directly): **"No `ALTER TABLE ADD COLUMN` is required by
  this ticket's own scope. Both migrations above add wholly new tables... If a future ticket needs to
  widen an existing populated table's shape, that migration must be designed separately at that
  time."** This is the frozen migration design's own explicit statement that neither `migration_001`
  nor `migration_002` pre-authorizes a column-add, and that widening the table is a **separately
  designed**, later decision — not something this ticket (whose Scope is "write-path code," not
  schema/migrations, and whose own dependency ticket is the now-closed, schema-only
  `CACHE-SCHEMA-MIGRATIONS`) should absorb as an incidental part of "real, tested logic."
- This ticket's own Anti-Drift Hazard (`investigation.md:281-286`) and Out-of-Scope /
  never-INSERT/UPDATE guard (`investigation.md:273-277`) both already forbid this ticket from
  performing any real `INSERT`/`UPDATE` against `retrieval_provider_result_cache_rows`. A column
  this ticket itself will never write a row into (because it does no INSERT/UPDATE at all) has no
  functional reason to exist yet — adding it now would be dead schema until child 3 lands, achieving
  nothing AC4 doesn't already get from the in-memory stamp.
- `tools/retrieval_events.py::emit_retrieval_event()` (`tools/retrieval_events.py:91-135`, esp.
  `:133`) is the direct, already-shipped precedent for "stamp a distinct version constant onto an
  in-memory record before/at persistence, without that stamp requiring the *emitting* module to own
  the persistence layer's schema" — `retrieval_event_schema_version` is stamped into the dict
  `emit_retrieval_event()` builds; the schema of `agent-monitoring/events.jsonl` (a JSONL file, not a
  fixed-column SQL table) tolerates new keys without a migration. `WriteDecision` follows the same
  shape: a real stamped field on a real returned object, with the durable sink's schema evolution
  handled by whichever ticket owns the durable sink.

**No ticket text or field name in this plan contradicts AC4's wording** — "a real, stamped value
distinct from the other 3 version axes" does not say "column"; the ticket's Scope bullet ("Implement
`redaction_policy_version` (§6) as a real, stamped **column** value on every write") uses the word
"column" once, but that bullet must be read against the ticket's own Out-of-Scope framing directly
above it ("This ticket builds pure, directly-testable functions; the next ticket calls them from the
real code path") and the Anti-Drift Hazard explicitly warning against "silently" adding this column
(`investigation.md:281-286`, which itself anticipates exactly this tension and requires "a
deliberate, documented decision," not a silent resolution either way). This plan resolves that
textual tension by treating "column value" as describing the *value's eventual destination*
(a future column child 3 adds), not a mandate for this ticket to create that column today.

**Flagged for Architecture Review confirmation.** This is a schema-boundary judgment call, not a
mechanical fact. Architecture Review should confirm this reading of AC4 against the ticket's own
Scope-bullet wording before Implement proceeds; if Review disagrees, the fallback is Step 7 gaining a
`migration_003_add_redaction_policy_version_column` addition (a genuinely new, not-frozen-plan
migration ordinal) — a materially different, larger change than this plan currently scopes, so a
Review override here should trigger a plan revision, not a silent Implement-time addition.

### DD3 — Security-pass precondition: resolved for this ticket, explicitly NOT resolved for child 3

investigation.md's Risk 1 (`investigation.md:208-229`) already determined, citing
`redaction_retention_policy.md` §4 and §11 verbatim ("must be reviewed and expanded by a
security-focused pass **before Phase 2 payload caching goes live**"), that this ticket's own shipping
is not blocked: this ticket wires nothing into a live request path, so caching does not "go live" as
a result of this ticket landing. **This plan ships the disclosed 4-pattern baseline exactly as
documented in §4 (`redaction_retention_policy.md:81-86`), unmodified, unexpanded, unhardened.**

**This resolution does not transfer to `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`.** That
ticket is the one that wires these functions into the real gateway request path and begins actually
serving/writing cache rows during live operation — the precise point at which §4/§11's "before Phase
2 payload caching goes live" language becomes operative. Child 3's own Investigate phase MUST
re-ask this question independently, citing §4/§11's exact wording itself, rather than importing this
ticket's resolution by reference. This plan does not pre-answer that question for child 3 in either
direction — recorded here only so it is not silently assumed resolved when child 3's Investigate
phase starts.

### DD4 — `test_sqlite_defaults_not_silently_implemented`'s scope confirmed: the new module is unconstrained by it

Read directly: `tests/docs/test_redaction_retention_policy_doc.py:24` hard-codes
`_RETRIEVAL_CACHE_PY = Path(__file__).parent.parent.parent / "tools" / "retrieval_cache.py"` — a
single literal path, no glob, no directory walk. `test_sqlite_defaults_not_silently_implemented`
(`tests/docs/test_redaction_retention_policy_doc.py:107-125`) reads only `_RETRIEVAL_CACHE_PY`'s
text/AST (`"PRAGMA" not in source"`, `"busy_timeout" not in source"`, `"os.chmod"`/`"chmod" not in
source"`, `"os" not in imported_modules"` via `ast.Import`/`ast.ImportFrom` only). **Confirmed: this
constrains `tools/retrieval_cache.py` only.** `tools/knowledge_gateway_redaction.py` (this ticket's
new module) may freely use `PRAGMA`, `busy_timeout`, `.chmod(...)`, and any import it needs — this
test cannot see it and is not weakened by its existence. Step 8 below implements §9 there
specifically because it must live in the new module, never in `tools/retrieval_cache.py` (which
Step 8's own guard test re-confirms stays untouched).

Practical note: this plan's §9 helpers use `Path.chmod(0o600)` (pathlib, not `os.chmod`), so the new
module never needs `import os` at all — not that it would matter, since the ban does not reach this
file either way.

### DD5 — Non-collapse rule: `WriteDecision` and `CacheRowSnapshot` field names checked against `evidence_cache_identity_contract.md` §1/§2

Read directly: §1's lookup-identity fields (`evidence_cache_identity_contract.md:40-45`) are
`normalized_intent`, `resolved_entity_ids`, `filters`, `budget_class`, `routing_policy_version`,
`repo_branch_scope`. §2's validity-identity fields (`evidence_cache_identity_contract.md:84-88`) are
`evidence_fingerprints`, `validated_negative_scopes`, `adapter_version_at_validation`,
`working_tree_overlap`, `provider_generation_at_validation`. Every field name this plan introduces
below (`verdict`, `rejection_category`, `redacted_payload`, `redacted_hash`, `unredacted_hash`,
`redaction_policy_version`, `source_type`, `cache_key`, plus the `CacheRowSnapshot` fields in Step 9)
is checked pairwise against both lists: zero collisions. None of this ticket's dataclasses claim to
*be* a lookup-identity or validity-identity structure — both are single-purpose, redaction-specific
shapes, so the Non-collapse rule (§3, `evidence_cache_identity_contract.md:100-121`) is not implicated
by construction, not merely by naming luck.

### DD6 — Never-cache §7 categories: 2 of 6 reuse the §4 secret-scan function; documented, not silent

`SECRETS_OR_CREDENTIALS` and `TOKENS` (2 of the 6 §7 categories,
`redaction_retention_policy.md:129-136`) are detected via the same `scan_for_secrets()` function Step
4 builds for §4 — the AWS-key/API-key/PEM-header matches satisfy "secrets and credentials," the
Bearer-token match satisfies "tokens." This is a deliberate fold, not a silent gap: per test_plan.md's
own explicit allowance (`test_plan.md:129-133`, "if the implementation folds token-rejection entirely
into §4's secret-scan, this test should assert that explicitly and document the fold as a real design
decision, not silently skip the category"), Step 6's test for these two categories asserts the fold
directly (calls `scan_for_secrets()` and asserts the never-cache category function reports the same
verdict) rather than inventing a second, redundant pattern set. The remaining 4 categories
(`RAW_ENVIRONMENT_VALUES`, `UNREDACTED_SENSITIVE_TOOL_OUTPUT`, `ARBITRARY_CONFIG_FILE_CONTENTS`,
`UNRESTRICTED_RAW_PROMPTS`) get genuinely independent detection logic — see Step 6.

### DD7 — GC-eligibility snapshot type is Plan-invented, not a 1:1 mirror of `LEVEL1_CACHE_COLUMNS` — a real gap flagged, not silently papered over

`LEVEL1_CACHE_COLUMNS` (`tools/retrieval_cache.py:104-128`, read directly, all 21 names enumerated)
has **no `cache_status` column** — `cache_status` exists only on the three legacy marker-only tables
(e.g. `retrieval_query_cache_rows.cache_status`, `tools/retrieval_cache.py:167`). test_plan.md's
`test_gc_eligibility_flags_failed_incomplete_write` (`test_plan.md:177`) nonetheless requires a
"failed/incomplete write ... only a non-terminal `cache_status`" check. Since this ticket ships no
read/write function against `retrieval_provider_result_cache_rows` at all (Out of Scope), there is no
real row shape to check eligibility against yet. **Resolution:** Step 9 defines a Plan-invented
`CacheRowSnapshot` dataclass — a convenience shape for this ticket's own pure-function testing,
explicitly documented in its own docstring as NOT a claim that the real table has a `cache_status`
column. **Flagged, not resolved, for child 3:** `CACHE-READ-WRITE-WIRING`'s own Plan phase must decide
how "failed/incomplete write" is actually represented against the real 21-column row shape (e.g. a
row simply never gets committed on a failed write, making per-row "incomplete" detection moot; or a
future column is added) — this plan does not silently invent that answer for child 3, and Step 9's
docstring says so explicitly so it cannot be mistaken for a real column claim later.

### DD8 — Per-key stampede guard: in-process lock, not a DB sentinel row

§9's own policy text (`redaction_retention_policy.md:215`) explicitly offers either mechanism ("an
`INSERT OR IGNORE` sentinel row **or** an in-process lock keyed by the write's primary key") and
frames both as acceptable, "policy, not implementation." This plan chooses the in-process lock
(`threading.Lock` per cache key, non-blocking `acquire`) because: (a) it requires zero new SQL table
or `INSERT` statement, keeping this step's guard-test (`test_sqlite_limits_functions_not_added_to_
tools_retrieval_cache_py` and the ticket's own "never real INSERT/UPDATE against
`retrieval_provider_result_cache_rows`" guard) trivially satisfied with no ambiguity; (b) it matches
this ticket's "pure, directly-testable functions" framing better than a DB-backed guard would.
**Documented limitation:** this guard is in-process only — it does not coordinate across separate OS
processes or machines. If child 3's real deployment runs multiple worker processes writing
concurrently, a DB-sentinel-row guard may be needed instead; that is child 3's call to make against
its own real concurrency model, not pre-decided here.

### DD9 — WAL-mode is a persistent, file-level SQLite setting; this ticket's own tests never touch the real `CACHE_DB_PATH`, but child 3 must decide the cross-module effect deliberately

**Enumeration of other writers to the shared resource** (`tools/retrieval_cache.py:59`'s
`CACHE_DB_PATH = Path("knowledge-index/retrieval_cache.db")`, the same on-disk SQLite file Step 8's
§9 helpers are capable of opening): `tools/retrieval_cache.py::_get_connection()`
(`tools/retrieval_cache.py:135-144`) is the sole existing opener, called from 8 sites (`check_index_cache`,
`write_index_cache`, `check_query_cache`, `write_query_cache`, `check_packet_cache`,
`write_packet_cache`, `prune`, `cmd_stats`) — confirmed by direct read, none of which set
`PRAGMA journal_mode=WAL`. `PRAGMA journal_mode=WAL` is a **database-file-level** setting in SQLite
(persisted in the file header), unlike `PRAGMA busy_timeout` (connection-scoped only, no persistence
effect). **Consequence this plan must not create by accident:** if Step 8's `open_connection_with_limits()`
were ever called against the real `CACHE_DB_PATH`, WAL mode would persist and silently change the
journal mode observed by every subsequent `tools/retrieval_cache.py::_get_connection()` call against
that same file too — a real behavioral effect on a file this ticket's own Out-of-Scope says it must
not touch the *code* of, achieved without editing a single line of `tools/retrieval_cache.py`.

**This plan avoids that entirely for this ticket:** Step 8's functions take a caller-supplied
`db_path: Path` parameter with no default tied to `tools.retrieval_cache.CACHE_DB_PATH`, this ticket's
own module never imports `CACHE_DB_PATH`, and every new test in Step 8/Step 10 opens only
`tmp_path`-scoped throwaway files (mirroring `tests/tools/test_retrieval_cache.py`'s own
`_isolated_cache_db` fixture pattern). **Flagged for child 3:** when `CACHE-READ-WRITE-WIRING` wires
these §9 helpers against the real `CACHE_DB_PATH` for the first time, its own Plan phase must decide
and document — as a deliberate choice, not an inherited side effect — whether enabling WAL mode
file-wide is acceptable (it is very likely a strict reliability improvement for concurrent readers,
but it is still a cross-module effect on `tools/retrieval_cache.py`'s existing connections that
deserves an explicit sentence in that ticket's own investigation, not silent inheritance from this
one).

## Steps

### Step 1 — Module skeleton, constants, and the non-production-complete disclosure

**Files:** `tools/knowledge_gateway_redaction.py` (new)

**Change:** Create the module with a docstring modeled on `tools/retrieval_events.py:1-21`'s
"what this is / what this is not" convention, citing `redaction_retention_policy.md` §2–§10 by
section number and stating verbatim, in the module docstring or immediately above `_SECRET_SCAN_PATTERNS`
(Step 4), that the secret-scan baseline is "a documented starting point, not a production-complete
secret scanner ... must be reviewed and expanded by a security-focused pass before Phase 2 payload
caching goes live" (quoting `redaction_retention_policy.md:88-91` in spirit, per this ticket's own
Scope bullet 3 instruction not to drop that disclosure). Add module-level constants only (no logic
yet):

```python
redaction_policy_version: int = 1  # 4th distinct version axis — see §6, DD nothing aliases this.

SOURCE_TYPE_CONTEXT_SEARCH = "context_search"  # Plan-invented literal; §2 names the provider by
SOURCE_TYPE_GRAPHIFY = "graphify"              # module path, not a wire-string — no contract-literal exists.
ALLOWED_SOURCE_TYPES: frozenset[str] = frozenset({SOURCE_TYPE_CONTEXT_SEARCH, SOURCE_TYPE_GRAPHIFY})

LOCAL_USER_PLACEHOLDER = "<local-user>"   # §3, redaction_retention_policy.md:57
LOCAL_PATH_PLACEHOLDER = "<local-path>"   # §3, redaction_retention_policy.md:60

MAX_PAYLOAD_BYTES: int = 8192             # §5, redaction_retention_policy.md:96

SQLITE_MAX_DB_SIZE_BYTES: int = 256 * 1024 * 1024   # §9 table, redaction_retention_policy.md:208
SQLITE_BUSY_TIMEOUT_MS: int = 5000                  # §9 table, redaction_retention_policy.md:213
SQLITE_FILE_MODE: int = 0o600                       # §9 table, redaction_retention_policy.md:210

ALLOW = "allow"
REJECT = "reject"
```

**Other writers to a shared resource:** none — this step adds only new names in a brand-new file;
nothing else in the repo defines `redaction_policy_version`, `ALLOWED_SOURCE_TYPES`, or any of the
other constants above (confirmed: `grep -rn "redaction_policy_version"` across `tools/` returns no
hits before this ticket, per investigation.md's own reading of the doc's future-tense §6 language).

**Do NOT touch:** `tools/retrieval_cache.py`, `tools/retrieval_events.py`, or any of the three
live-gateway files — this step only creates the new file.

**Verify:** `test_module_docstring_preserves_non_production_complete_disclosure` (this test can be
written and pass as soon as this step lands, before any function body exists).

### Step 2 — §2 Allowlist check

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add

```python
def check_allowlist(source_type: str) -> bool:
    """True iff source_type is one of the two §2-eligible provider source types. Any other value
    (raw filesystem read, live shell stdout, arbitrary tool-call payload) returns False —
    redaction_retention_policy.md §2 names no other eligible source until a future ticket adds one.
    """
    return source_type in ALLOWED_SOURCE_TYPES
```

**Do NOT touch:** do not add a third value to `ALLOWED_SOURCE_TYPES` "for completeness" — §2's
enumeration is exactly two provider types today (`redaction_retention_policy.md:39-46`).

**Verify:** `test_allowlist_accepts_context_search_source_type`,
`test_allowlist_accepts_graphify_source_type`, `test_allowlist_rejects_unlisted_source_type`.

### Step 3 — §3 Redaction rules and content hashing

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add a local `_hash_text()` helper and `redact_content()`. The hashing helper
intentionally re-implements, rather than imports, the same one-line SHA-256 shape
`tools/retrieval_cache.py::_hash_text()` already uses (`tools/retrieval_cache.py:267-268`,
`hashlib.sha256(text.encode("utf-8")).hexdigest()`) — that function is private (leading underscore)
and internal to a module this ticket must not import from for a live-gateway-adjacent concern (see
Scope Guards), so this plan duplicates the one-line algorithm rather than reaching into
`retrieval_cache.py`'s private surface:

```python
def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_content(text: str, *, repo_root: Path | None = None) -> str:
    """Strips local usernames and machine-specific absolute paths per §3, replacing each with a
    fixed placeholder — or, for a path under repo_root, rewriting it to its repo-relative form.
    Must run before any hashing. Illustrative regex shapes below; implementer may adjust exact
    syntax provided the placeholder/rewrite behavior the tests below assert is preserved.
    """
    # e.g. r"(/home/|/Users/|C:\\Users\\)[^/\\\s]+" -> LOCAL_USER_PLACEHOLDER (keep any trailing
    # path segments after the username intact).
    # Then: any remaining absolute path not resolvable under repo_root -> LOCAL_PATH_PLACEHOLDER;
    # an absolute path that IS under repo_root -> rewritten relative to repo_root.
    ...
```

Two hash accessors, both required by AC2, are added alongside: a private `_hash_text` reused for
both call sites, and no function ever returns an *unredacted* hash from a public entry point (Step 7
enforces this at the `WriteDecision` boundary — `redact_content()` itself only returns text, not a
hash, so the ordering guarantee lives in Step 7's orchestrator, not here).

**Do NOT touch:** `tools/retrieval_cache.py::_hash_text`/`_normalize_query`/`_hash_filters`
(`tools/retrieval_cache.py:267-276`) — read-only citation for the algorithm shape, never imported,
never edited.

**Verify:** `test_redaction_replaces_local_username_in_home_path`,
`test_redaction_replaces_machine_specific_absolute_path`,
`test_redacted_hash_differs_from_unredacted_hash_for_same_input`,
`test_redaction_runs_before_hashing_order_is_enforced` (the last two exercise `_hash_text` directly
against pre/post-`redact_content()` output, confirming the two differ for input that changes under
redaction).

### Step 4 — §4 Secret-scan baseline (verbatim 4 patterns)

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add the 4 regexes exactly as documented (`redaction_retention_policy.md:83-86`, quoted
verbatim — no hardening, no 5th pattern, per this ticket's Out-of-Scope and Anti-Drift Hazard):

```python
_SECRET_SCAN_PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "generic_api_key_assignment": re.compile(
        r"(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE
    ),
    "pem_private_key_header": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{20,}"),
}


def scan_for_secrets(text: str) -> str | None:
    """Returns the matching pattern's key (e.g. "aws_access_key_id") on the first match, else None.
    Any non-None result means the caller must REJECT the write outright — never redact-and-store
    (§4, redaction_retention_policy.md:91-92). This baseline is a documented starting point, not a
    production-complete secret scanner — see Step 1's module-level disclosure and DD3/DD6.
    """
    for name, pattern in _SECRET_SCAN_PATTERNS.items():
        if pattern.search(text):
            return name
    return None
```

**Do NOT touch:** do not add a 5th pattern, do not widen any of the 4 regexes beyond what's quoted
above (explicit Out of Scope and Anti-Drift Hazard).

**Verify:** `test_secret_scan_detects_aws_style_access_key_id`,
`test_secret_scan_rejects_write_on_aws_key_match`,
`test_secret_scan_detects_generic_api_key_assignment`,
`test_secret_scan_rejects_write_on_api_key_match`,
`test_secret_scan_detects_pem_private_key_header`,
`test_secret_scan_rejects_write_on_pem_header_match`,
`test_secret_scan_detects_bearer_token`,
`test_secret_scan_rejects_write_on_bearer_token_match`,
`test_secret_scan_clean_content_is_not_rejected`.
(`test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store` is verified at Step 7,
once the orchestrator ordering exists.)

### Step 5 — §5 Payload size cap

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:**

```python
def check_size_cap(redacted_payload: str) -> bool:
    """True iff the UTF-8-encoded redacted payload is <= MAX_PAYLOAD_BYTES (8192). Must be called
    on already-redacted text only (§5: "measured on the UTF-8-encoded redacted payload" —
    redaction_retention_policy.md:96). Never truncates; callers must reject outright on False.
    """
    return len(redacted_payload.encode("utf-8")) <= MAX_PAYLOAD_BYTES
```

**Do NOT touch:** do not add a truncation code path anywhere in this module — §5 explicitly forbids
silent truncation.

**Verify:** `test_payload_under_cap_is_accepted`, `test_payload_exactly_at_cap_is_accepted`,
`test_payload_over_cap_is_rejected_not_truncated`,
`test_size_cap_measured_on_redacted_not_raw_payload` (construct raw input that's over-cap only
before redaction, e.g. many long local-path occurrences that shrink to `LOCAL_PATH_PLACEHOLDER`
after Step 3's `redact_content()`, then confirm `check_size_cap()` is called on the post-redaction
string and passes).

### Step 6 — §7 Never-cache enumeration (6 independent categories)

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add category name constants and one dispatcher returning the set of violated
categories (never a single boolean — AC1 requires "not a single catch-all"):

```python
CATEGORY_SECRETS_OR_CREDENTIALS = "secrets_or_credentials"
CATEGORY_TOKENS = "tokens"
CATEGORY_RAW_ENVIRONMENT_VALUES = "raw_environment_values"
CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT = "unredacted_sensitive_tool_output"
CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS = "arbitrary_config_file_contents"
CATEGORY_UNRESTRICTED_RAW_PROMPTS = "unrestricted_raw_prompts"

_ENV_VALUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,}=\S+", re.MULTILINE)  # shell/env assignment shape
_CONFIG_LINE_PATTERN = re.compile(r"^[\w.\-]+\s*[:=]\s*.+$", re.MULTILINE)  # generic key: value / key=value line


def check_never_cache_categories(
    *, content: str, redacted_content: str, is_raw_prompt: bool = False
) -> frozenset[str]:
    """Returns the set of §7 categories this content violates, independently of one another (DD6):
    - secrets_or_credentials / tokens: reuse scan_for_secrets() on `content` (any match -> both or
      one of these, per which pattern matched — secrets_or_credentials for the 3 credential-shaped
      patterns, tokens for bearer_token).
    - raw_environment_values: _ENV_VALUE_PATTERN match on `content`.
    - unredacted_sensitive_tool_output: defense-in-depth re-scan — True if `redacted_content` still
      contains a raw home-directory or absolute-path pattern redact_content() was supposed to strip
      (i.e. redaction did not fully do its job), per §3's own placeholder guarantee.
    - arbitrary_config_file_contents: 3+ lines in `content` matching _CONFIG_LINE_PATTERN.
    - unrestricted_raw_prompts: `is_raw_prompt` passed True by the caller (i.e. the caller is
      offering the full unprocessed prompt text itself, as opposed to a normalized/hashed query
      form — redaction_retention_policy.md:136).
    """
    ...
```

**Do NOT touch:** do not collapse this into a single `is_cacheable(text) -> bool` — AC1 and
`test_never_cache_categories_are_independently_enforced` both require each category to be its own,
separately-attributable check result.

**Verify:** `test_never_cache_rejects_secrets_or_credentials`, `test_never_cache_rejects_tokens`,
`test_never_cache_rejects_raw_environment_values`,
`test_never_cache_rejects_unredacted_sensitive_tool_output`,
`test_never_cache_rejects_arbitrary_config_file_contents`,
`test_never_cache_rejects_unrestricted_raw_prompts`,
`test_never_cache_categories_are_independently_enforced`.

### Step 7 — §6 `redaction_policy_version` stamping + `WriteDecision`/`evaluate_write_candidate()` orchestrator

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add the return dataclass and the single pipeline entry point tying Steps 2–6 together in
the fixed order: allowlist → redact → secret-scan (short-circuits) → size-cap → never-cache →
stamp+hash → ALLOW.

```python
@dataclass(frozen=True)
class WriteDecision:
    verdict: str                      # ALLOW or REJECT
    rejection_category: str | None    # e.g. "not_allowlisted", "aws_access_key_id",
                                       # "oversized_payload", or a CATEGORY_* constant; None on ALLOW
    redacted_payload: str | None      # present only on ALLOW; never the unredacted text
    redacted_hash: str | None         # present only on ALLOW; the unredacted hash is never exposed
    redaction_policy_version: int     # stamped on every decision, ALLOW and REJECT alike


def evaluate_write_candidate(
    *, source_type: str, raw_content: str, is_raw_prompt: bool = False
) -> WriteDecision:
    if not check_allowlist(source_type):
        return WriteDecision(REJECT, "not_allowlisted", None, None, redaction_policy_version)

    redacted = redact_content(raw_content)

    secret_match = scan_for_secrets(redacted)
    if secret_match is not None:
        return WriteDecision(REJECT, secret_match, None, None, redaction_policy_version)

    if not check_size_cap(redacted):
        return WriteDecision(REJECT, "oversized_payload", None, None, redaction_policy_version)

    violated = check_never_cache_categories(
        content=raw_content, redacted_content=redacted, is_raw_prompt=is_raw_prompt
    )
    if violated:
        return WriteDecision(REJECT, sorted(violated)[0], None, None, redaction_policy_version)

    return WriteDecision(
        ALLOW, None, redacted, _hash_text(redacted), redaction_policy_version
    )
```

Note `_hash_text(raw_content)` (the *unredacted* hash) is never computed or stored anywhere in this
function — satisfying `test_only_redacted_hash_is_ever_returned_for_persistence` by construction, not
by a separate filter step.

**Other writers to a shared resource:** none — `WriteDecision` is a transient, in-memory return value;
this step performs no I/O and touches no file, table, or counter any other code path writes to.

**Do NOT touch:** do not add an `unredacted_hash` field to `WriteDecision` even for debugging
convenience — AC2 requires the unredacted hash never be exposed from a write-path decision function.

**Verify:** `test_redaction_policy_version_is_stamped_on_every_write_decision`,
`test_redaction_policy_version_distinct_from_retrieval_version` (mirrors
`tests/tools/test_retrieval_events.py::TestFieldShapeConstant::test_schema_version_constant_distinct_from_cache_key_version_constant`,
`tests/tools/test_retrieval_events.py:78-84` — assert value/name-absence against `rc.RETRIEVAL_VERSION`,
`rc.retrieval_cache_schema_version`, and `re_mod.retrieval_event_schema_version`, all 3),
`test_only_redacted_hash_is_ever_returned_for_persistence`,
`test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store`.

### Step 8 — §9 SQLite operational limits

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:**

```python
def open_connection_with_limits(db_path: Path) -> sqlite3.Connection:
    """Opens db_path (creating parent dirs if needed), applies PRAGMA journal_mode=WAL and
    PRAGMA busy_timeout=5000 on the connection, and chmods the file to 0600 immediately after
    creation if this call is the one that created it (never re-chmods a pre-existing file, so an
    operator's own permission choice on an existing file is not silently overwritten on reconnect).
    Caller-supplied db_path only — never defaults to tools.retrieval_cache.CACHE_DB_PATH (DD9).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    created_now = not db_path.exists()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    if created_now:
        db_path.chmod(SQLITE_FILE_MODE)
    return conn


def check_db_size_within_limit(db_path: Path) -> bool:
    return not db_path.exists() or db_path.stat().st_size < SQLITE_MAX_DB_SIZE_BYTES


def execute_bounded_transaction(conn: sqlite3.Connection, statements: list[tuple[str, tuple]]) -> None:
    """Executes each (sql, params) pair then commits exactly once — never leaves an open
    transaction across calls. Generic: contains no literal INSERT/UPDATE text of its own; callers
    supply statements. This ticket calls it with zero real statements in its own tests/production
    use — it exists as the reusable primitive child 3 wires real writes through.
    """
    for sql, params in statements:
        conn.execute(sql, params)
    conn.commit()


_write_locks: dict[str, threading.Lock] = {}
_write_locks_guard = threading.Lock()


def acquire_write_guard(cache_key: str) -> bool:
    """Non-blocking, in-process only (DD8) — not multi-process safe. True if this caller may
    proceed; False if another in-process caller already holds the guard for cache_key.
    """
    with _write_locks_guard:
        lock = _write_locks.setdefault(cache_key, threading.Lock())
    return lock.acquire(blocking=False)


def release_write_guard(cache_key: str) -> None:
    with _write_locks_guard:
        lock = _write_locks.get(cache_key)
    if lock is not None and lock.locked():
        lock.release()
```

**Other writers to a shared resource:** see DD9 in full — `tools/retrieval_cache.py::_get_connection()`
is the only other opener of any SQLite file this module is *capable* of pointing at, but this ticket's
own tests and any production call site (there are none yet — Out of Scope) never pass
`tools.retrieval_cache.CACHE_DB_PATH` to `open_connection_with_limits()`; only `tmp_path`-scoped test
files are used. `_write_locks`/`_write_locks_guard` are new, module-private, in-process state — no
other module reads or writes them.

**Do NOT touch:** `tools/retrieval_cache.py` (DD4 — zero `PRAGMA`/`busy_timeout`/`chmod` there);
do not give `open_connection_with_limits()` a default `db_path` value pointing at
`tools.retrieval_cache.CACHE_DB_PATH`.

**Verify:** `test_wal_mode_pragma_applied_on_connection_open`,
`test_busy_timeout_pragma_set_to_5000ms`, `test_file_permissions_set_to_0600_after_creation`,
`test_max_db_size_check_flags_oversized_database`,
`test_write_path_wraps_statements_in_single_bounded_transaction`,
`test_per_key_stampede_guard_prevents_concurrent_duplicate_write`,
`test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py` (this last one, plus a full
re-run of `test_sqlite_defaults_not_silently_implemented`, is the direct regression guard for DD4).

### Step 9 — §10 Cache-GC eligibility predicates

**Files:** `tools/knowledge_gateway_redaction.py`

**Change:** Add the Plan-invented `CacheRowSnapshot` (documented per DD7 as a testing convenience,
not a claim about the real table's columns) and 6 independent eligibility predicates plus the
identity-contract never-flag rule:

```python
@dataclass(frozen=True)
class CacheRowSnapshot:
    """Plan-invented convenience shape for this ticket's own pure-function GC-eligibility testing
    (DD7) — NOT a 1:1 mirror of LEVEL1_CACHE_COLUMNS (tools/retrieval_cache.py:104-128), which has
    no cache_status column. CACHE-READ-WRITE-WIRING must decide how any field here that has no real
    column counterpart (cache_status, evidence_kind, only_change_is_provider_generation_bump) maps
    onto the real 21-column row shape when it wires real read/write logic; this ticket's GC checks
    are validated only against this synthetic snapshot.
    """
    repo_branch_scope: str
    provider_generation: str
    hit_count: int
    created_at: float
    last_hit_at: float | None
    cache_status: str | None            # Plan-invented; see docstring above
    evidence_kind: str | None            # e.g. "SYMBOL" / "FILE" — see evidence_identity_kinds.schema.json
    only_change_is_provider_generation_bump: bool = False


def gc_eligible_expired_exact_query_result(snapshot: CacheRowSnapshot, *, now: float, max_age_seconds: float) -> bool: ...
def gc_eligible_deleted_branch_packet(snapshot: CacheRowSnapshot, *, branch_exists: bool) -> bool: ...
def gc_eligible_obsolete_provider_version_row(snapshot: CacheRowSnapshot, *, current_provider_generation: str) -> bool: ...
def gc_eligible_low_use_regenerable_packet(snapshot: CacheRowSnapshot, *, low_use_threshold: int) -> bool: ...
def gc_eligible_stale_row_superseded_by_refresh(snapshot: CacheRowSnapshot, *, superseded: bool) -> bool: ...
def gc_eligible_failed_incomplete_write(snapshot: CacheRowSnapshot) -> bool: ...


def gc_eligibility_never_flags_protected_evidence(snapshot: CacheRowSnapshot) -> bool:
    """True (never-flag) iff snapshot.evidence_kind is SYMBOL/FILE and
    only_change_is_provider_generation_bump is True — enforces
    evidence_cache_identity_contract.md §4's fallback rule (quoted at
    redaction_retention_policy.md:244-246): such a row must never be evicted on a bare
    PROVIDER_GENERATION bump alone. Callers must consult this before honoring any of the 6
    predicates above.
    """
    ...
```

`prune()` (`tools/retrieval_cache.py:502-529`, confirmed by direct read never called from any
`check_*`/`write_*` function today) is never called, imported, or invoked from this module — these
are pure predicates/reporters only.

**Other writers to a shared resource:** none — `CacheRowSnapshot` is a synthetic, in-memory-only test
fixture type; nothing else in the repo constructs, reads, or persists it.

**Do NOT touch:** `tools/retrieval_cache.py::prune()` — no call added anywhere in this module (§10's
explicit "does not change `prune()`'s current manual-only status").

**Verify:** `test_gc_eligibility_flags_expired_exact_query_result`,
`test_gc_eligibility_flags_packet_for_deleted_branch`,
`test_gc_eligibility_flags_obsolete_provider_version_row`,
`test_gc_eligibility_flags_low_use_regenerable_packet`,
`test_gc_eligibility_flags_stale_row_superseded_by_refresh`,
`test_gc_eligibility_flags_failed_incomplete_write`,
`test_gc_eligibility_never_flags_symbol_or_file_backed_evidence_on_bare_generation_bump`,
`test_prune_remains_the_only_eviction_call_site`.

### Step 10 — Whole-module architecture guards + full regression pass

**Files:** `tests/tools/test_knowledge_gateway_redaction.py` (new — collects every test named in
Steps 1–9, following `tests/tools/test_retrieval_cache.py`'s per-concern test-class layout), plus
running (not editing) the regression surface named in test_plan.md.

**Change:** Add the module-wide static guards:
- An AST-based test (mirroring `tests/tools/test_context_packet_assembler.py::TestWorkflowIsolationGuards::test_assembler_does_not_import_contextpacket_from_retrieval_cache`,
  `tests/tools/test_context_packet_assembler.py:419-432`) asserting
  `tools/knowledge_gateway_redaction.py` never imports from `tools/knowledge_gateway_router.py`,
  `tools/knowledge_gateway_packet_assembly.py`, or `tools/knowledge_gateway_mcp.py`.
- An AST/substring-based test asserting the module's source never contains the literal text
  `"INSERT INTO retrieval_provider_result_cache_rows"` or
  `"UPDATE retrieval_provider_result_cache_rows"`.
- Re-run (unmodified) `tests/docs/test_redaction_retention_policy_doc.py`,
  `tests/tools/test_kgmcp_measurement_baseline.py::test_no_live_gateway_code_or_search_mcp_edits_introduced`,
  `tests/tools/test_retrieval_events.py::TestFieldShapeConstant`,
  `tests/agent_codex_posttool_adapter/test_redaction.py`,
  `tests/tools/test_retrieval_cache.py` (all classes), and the 4 live-gateway integration test files
  named in test_plan.md's Regression Surface — all must pass unmodified, confirming zero drift.

**Do NOT touch:** any existing test file's assertions — this step only adds new tests and runs
existing ones.

**Verify:** the two Scoped Pytest Commands in test_plan.md, both run in full.

## Scope Guards

- No `PRAGMA`, `busy_timeout`, `.chmod(...)`, or `import os` anywhere in `tools/retrieval_cache.py`
  (DD4; hard-enforced by `test_sqlite_defaults_not_silently_implemented`).
- No `ALTER TABLE`/new migration function added to `tools/retrieval_cache.py`, and no
  `redaction_policy_version` column added to `retrieval_provider_result_cache_rows` (DD2 — decided
  in-memory-only for this ticket, flagged for Architecture Review confirmation).
- No expansion, hardening, or 5th pattern added to the §4 secret-scan baseline beyond the 4 quoted
  regexes (Step 4; explicit Out of Scope and Anti-Drift Hazard).
- No real `INSERT`/`UPDATE` against `retrieval_provider_result_cache_rows` anywhere in this module —
  `execute_bounded_transaction()` is generic and carries no literal SQL of its own; the GC-eligibility
  functions operate only on the synthetic `CacheRowSnapshot`, never a real row.
- No edit to `tools/knowledge_gateway_router.py`, `tools/knowledge_gateway_packet_assembly.py`, or
  `tools/knowledge_gateway_mcp.py` — not read, not imported, not opened by any step (Step 10's guard
  test enforces the import half of this mechanically).
- No default `db_path` in `open_connection_with_limits()` (or any other §9 helper) pointing at
  `tools.retrieval_cache.CACHE_DB_PATH` — every call site in this ticket's own tests/production use
  supplies a `tmp_path`-scoped path (DD9).
- No edit to `docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`,
  `cache_migration_plan.md`, or `evidence_cache_identity_contract.md` as part of Implement — tense
  corrections (§6/§9's future-tense language) are this ticket's later Document-Update phase's job,
  mirroring the §8 precedent (`redaction_retention_policy.md:179-185`), not a Plan/Implement step.
- No field name in `WriteDecision` or `CacheRowSnapshot` reused from
  `evidence_cache_identity_contract.md` §1 (`normalized_intent`, `resolved_entity_ids`, `filters`,
  `budget_class`, `routing_policy_version`, `repo_branch_scope`) or §2 (`evidence_fingerprints`,
  `validated_negative_scopes`, `adapter_version_at_validation`, `working_tree_overlap`,
  `provider_generation_at_validation`) for an unrelated redaction/GC-specific concept, or vice versa
  (DD5 — verified zero collisions).
- No `unredacted_hash` field or equivalent exposed from `WriteDecision` or any public function
  (AC2's "only the redacted hash is ever returned" requirement).
- No automatic GC wiring — the 6 `gc_eligible_*` functions and
  `gc_eligibility_never_flags_protected_evidence` are pure predicates only; none calls `DELETE` or
  `tools/retrieval_cache.py::prune()`.
- No `CLAUDE.md`, `.claude/agents/*.md`, or `.claude/skills/*.md` edits.
- No new `docs/parity_ledger/` entry written by Implement — deferred to this ticket's own later
  Parity phase (see "Docs and Parity — Deferred" below), following the sibling ticket's own precedent.

## Dependency Map

- Step 1 (constants/skeleton) has no dependency; must land first — every other step references its
  constants.
- Steps 2, 3, 4, 5 are independent of each other once Step 1 lands (allowlist, redaction, secret-scan,
  size-cap are four separate concerns with no cross-calls among themselves).
- Step 6 depends on Step 4 (`check_never_cache_categories` calls `scan_for_secrets()` per DD6) and on
  Step 3 (`redacted_content` parameter).
- Step 7 depends on Steps 2, 3, 4, 5, 6 all existing — it is the orchestrator wiring them together in
  a fixed order.
- Step 8 depends only on Step 1's constants (`SQLITE_BUSY_TIMEOUT_MS`, `SQLITE_FILE_MODE`,
  `SQLITE_MAX_DB_SIZE_BYTES`) — independent of Steps 2–7.
- Step 9 depends only on Step 1 (no shared code with Steps 2–8) — independent, can be implemented in
  parallel with Steps 2–8 if desired.
- Step 10 depends on all of Steps 1–9 existing (it is the whole-module guard pass and full regression
  run) — must be last.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — allowlist/redaction/secret-scan/size-cap/never-cache are real, independently testable functions, not documentation, not a single monolithic check | Steps 2, 3, 4, 5, 6 | `test_allowlist_*`, `test_redaction_*`, `test_secret_scan_*`, `test_payload_*`, `test_never_cache_*` (esp. `test_never_cache_categories_are_independently_enforced`) |
| AC2 — each of the 4 secret-scan patterns has a detection test AND a rejection (not redact-and-store) test; redacted-content hash differs from unredacted-content hash for the same input; only the redacted hash is ever returned for persistence | Steps 3, 4, 7 | `test_secret_scan_detects_*` / `test_secret_scan_rejects_write_on_*_match` (4 pairs), `test_redacted_hash_differs_from_unredacted_hash_for_same_input`, `test_only_redacted_hash_is_ever_returned_for_persistence` |
| AC3 — 8 KB size cap rejects (not truncates) an oversized payload | Step 5 | `test_payload_over_cap_is_rejected_not_truncated`, `test_size_cap_measured_on_redacted_not_raw_payload` |
| AC4 — `redaction_policy_version` is a real, stamped value distinct from the other 3 version axes | Step 1 (constant), Step 7 (stamped onto `WriteDecision`) | `test_redaction_policy_version_is_stamped_on_every_write_decision`, `test_redaction_policy_version_distinct_from_retrieval_version` |
| AC5 — this ticket's own investigation honestly re-confirms (or updates) whether the security-pass precondition blocks this ticket's own shipping | Already satisfied by investigation.md's Risk 1 (`investigation.md:208-229`); restated and its scope boundary sharpened here in DD3 | No pytest — satisfied by investigation.md's own text plus this plan's DD3, both citing `redaction_retention_policy.md` §4/§11 verbatim; Review-phase check is a documentation read, not a test run |

## Docs and Parity — Deferred (for later phases, not Implement)

- **Document-Update phase:** `redaction_retention_policy.md` §6's "stamped onto any future
  payload-bearing cache row" (future tense) and §9's "not implemented ... deferred to a future
  ticket" both need the same tense correction §8 already received
  (`redaction_retention_policy.md:179-185`, the precedent to mirror) — cite
  `tools/knowledge_gateway_redaction.py`'s real function names/line numbers once Implement lands.
  `docs/plans/knowledge-gateway-mcp-proposal.md` §20's "Store actual bounded normalized results"
  bullet gets annotated Done, per the epic's own convention.
- **Parity phase:** a new `docs/parity_ledger/infrastructure.yaml` entry (next ID after `INFRA-341`)
  covering this ticket's new module — allowlist/redaction/secret-scan/size-cap/`redaction_policy_version`
  stamping/§9 SQLite-limits/§10 GC-eligibility functions — following `INFRA-341`'s own shape (P1
  priority, `proof_type: regression`, real `test_path`s into
  `tests/tools/test_knowledge_gateway_redaction.py`). No edit to `INFRA-341` itself is needed — its
  own `support_boundary` text already correctly attributes this exact scope to this ticket by name.

## Anti-Drift Notes

- **DD2 is the single most consequential decision in this plan** — no `redaction_policy_version`
  column is added to `retrieval_provider_result_cache_rows` by this ticket, and this plan flags that
  decision explicitly for Architecture Review rather than treating it as settled by this plan alone.
  An implementer must not "helpfully" add the column, even via a new `migration_003_*` function,
  without Review's sign-off — that would silently expand this ticket's scope back into
  schema/migration territory the ticket's own title and Out-of-Scope explicitly disclaim.
- **DD3's boundary is fragile to restate incorrectly.** Do not write, in any doc or code comment
  produced by this ticket, a sentence implying the security-pass precondition is "resolved" in any
  general sense — it is resolved only for *this ticket's own* non-live shipping. Any comment near the
  secret-scan patterns should say so explicitly (Step 1/Step 4's docstrings already do).
- **Do not import `tools/retrieval_cache.py::_hash_text`/`_normalize_query`/`_hash_filters`** even
  though they're the obvious existing precedent — they are private (underscore-prefixed) to that
  module; Step 3 duplicates the one-line SHA-256 shape instead of reaching into another module's
  private surface, consistent with this ticket's Out-of-Scope isolation from the live-gateway/cache
  module's internals.
- **`open_connection_with_limits()` must never gain a default `db_path` argument that resolves to
  `tools.retrieval_cache.CACHE_DB_PATH`.** DD9 is the explicit reasoning: WAL mode is file-persistent,
  and pointing this ticket's own helper at the real cache file — even just in a test — would produce
  an observable side effect on `tools/retrieval_cache.py`'s existing connections without a single
  line of that file being edited. This is exactly the kind of instruction-following slip ("obviously
  this DB path helper should default to the real cache path") that must not happen here.
  `CACHE-READ-WRITE-WIRING` makes that connection deliberately, later, with its own investigation
  saying so.
- **`CacheRowSnapshot`'s `cache_status`/`evidence_kind`/`only_change_is_provider_generation_bump`
  fields are Plan-invented testing conveniences, not real columns** (DD7) — do not let this synthetic
  type's field names leak into any doc or comment as if they described
  `retrieval_provider_result_cache_rows`'s actual schema; `LEVEL1_CACHE_COLUMNS`
  (`tools/retrieval_cache.py:104-128`) remains the sole authoritative column list for that table.
- **Do not fold all 6 §7 never-cache categories into `scan_for_secrets()`** — only 2 of 6
  (`secrets_or_credentials`, `tokens`) are documented as folded (DD6); the other 4 need their own,
  separately-testable detection logic per AC1's "not a catch-all" requirement.

## Deviations (recorded during Implement)

- **Step 3's `redact_content()` home-path regex consumes the entire trailing path, not just the
  username segment.** Step 3's illustrative regex comment said to replace only the
  `/home/<user>` (or `C:\Users\<user>`) segment with `LOCAL_USER_PLACEHOLDER` while "keeping any
  trailing path segments after the username intact" (e.g. `/home/alice/project/file.py` ->
  `<local-user>/project/file.py`). The implemented `_HOME_PATH_PATTERN` instead matches the whole
  contiguous non-whitespace run starting at the home prefix (`/home/alice/project/file.py` ->
  `<local-user>`), consuming the trailing segments too. Reason: running a second, generic
  absolute-path pass (`_ABS_PATH_PATTERN`, needed for the separate "machine-specific absolute
  path" rule) over text that still had raw trailing path segments left behind by a narrower
  username-only substitution would re-match those leftover segments as their own "absolute path"
  and mis-redact them a second time (e.g. turning `<local-user>/project/file.py` into
  `<local-user><local-path>`, destroying the placeholder distinction the tests need). Full
  consumption avoids that double-processing conflict entirely. Plan.md Step 3 explicitly
  authorized this class of adjustment: "implementer may adjust exact syntax provided the
  placeholder/rewrite behavior the tests below assert is preserved" — the placeholder/rewrite
  *behavior* (real username never appears in output; a placeholder is substituted; a
  repo-root-relative path is rewritten instead of placeholdered) is preserved; only the exact
  span consumed by the username-specific regex changed. No AC or test_plan.md-mandated test
  required trailing-segment preservation specifically, so this is a syntax adjustment within the
  plan's own stated latitude, not a scope change — recorded here per CLAUDE.md's "never silently
  deviate" rule.
