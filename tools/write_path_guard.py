"""tools/write_path_guard.py — Pure, directly-testable write-path enforcement functions for
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §2-§9: the §2
provider-source allowlist, §3 redaction + hashing, the §4 secret-scan baseline (10 patterns), the
§5 64 KiB payload size cap, §6 `redaction_policy_version` stamping via `WriteDecision`, the §7
never-cache enumeration (6 independent categories), and §9's `open_connection_with_limits()`
connection-tuning helper.

What this is: pure functions and dataclasses only, independent of any particular caller. This
module was extracted from `tools/knowledge_gateway_redaction.py` by
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` as a pure code-location move (no behavior change)
once the Knowledge Gateway MCP itself was archived (`TCK-20260907-KGMCP-DEPRECATION-EPIC` M2) —
these functions have real, live consumers outside the gateway package
(`tools/retrieval_cache.py`'s own connection-opening helpers; the planned
`governance_capability_policy_epic.md` M4 secret-exposure hook) and needed a stable home that
would not itself get archived alongside the gateway. `evaluate_write_candidate()` is the single
orchestrator tying the §2-§7 checks together in a fixed order and returning a `WriteDecision`,
independent of which caller — the archived gateway, `retrieval_cache.py`, or a future Bash hook —
is doing the writing.

The §9 `check_db_size_within_limit()`/`execute_bounded_transaction()` helpers, the write-guard
pair (`acquire_write_guard()`/`release_write_guard()`), and all of §10 (cache-GC eligibility
predicates) stayed behind in the archived `tools/archive/knowledge_gateway_redaction.py` — none of
those has a real consumer outside the now-archived gateway package.

Security-baseline disclosure (§4/§11, quoted verbatim, not paraphrased away): "This baseline
ruleset is a documented starting point, not a production-complete secret scanner. It is
explicitly NEW (not a reuse of any existing repository tooling) and explicitly
non-production-complete. It must be reviewed and expanded by a security-focused pass before
Phase 2 payload caching goes live."

Originally built for TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH as part of
`tools/knowledge_gateway_redaction.py`; the §4 pattern-set expansion (4 to 10 patterns) was added
by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own Security-Review pass. Extracted into this
standalone module by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# §1 — Constants
# ---------------------------------------------------------------------------

redaction_policy_version: int = 1  # 4th distinct version axis — see §6.

SOURCE_TYPE_CONTEXT_SEARCH = "context_search"  # Plan-invented literal; §2 names the provider by
SOURCE_TYPE_GRAPHIFY = "graphify"              # module path, not a wire-string — no contract-literal exists.
ALLOWED_SOURCE_TYPES: frozenset[str] = frozenset({SOURCE_TYPE_CONTEXT_SEARCH, SOURCE_TYPE_GRAPHIFY})

LOCAL_USER_PLACEHOLDER = "<local-user>"   # §3, redaction_retention_policy.md:57
LOCAL_PATH_PLACEHOLDER = "<local-path>"   # §3, redaction_retention_policy.md:60

MAX_PAYLOAD_BYTES: int = 65536            # §5, redaction_retention_policy.md:121 — recalibrated
                                           # by TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION
                                           # from the real 7-entry corpus's observed cold response
                                           # range (~10,612-30,548 bytes,
                                           # tests/tools/fixtures/kgmcp_phase2_baseline_recomparison_results.json),
                                           # ~2.15x the observed max, rounded to the nearest clean
                                           # power of two (64 KiB).

SQLITE_BUSY_TIMEOUT_MS: int = 5000                  # §9 table, redaction_retention_policy.md:213
SQLITE_FILE_MODE: int = 0o600                       # §9 table, redaction_retention_policy.md:210

ALLOW = "allow"
REJECT = "reject"


# ---------------------------------------------------------------------------
# §2 — Allowlist check
# ---------------------------------------------------------------------------

def check_allowlist(source_type: str) -> bool:
    """True iff source_type is one of the two §2-eligible provider source types. Any other value
    (raw filesystem read, live shell stdout, arbitrary tool-call payload) returns False —
    redaction_retention_policy.md §2 names no other eligible source until a future ticket adds one.
    """
    return source_type in ALLOWED_SOURCE_TYPES


# ---------------------------------------------------------------------------
# §3 — Redaction rules and content hashing
# ---------------------------------------------------------------------------

# Matches a home-directory prefix plus everything contiguous after it (up to whitespace/quote),
# so the entire local-user-specific path segment is replaced in one pass — avoids a second,
# generic absolute-path pass re-matching (and mis-redacting) whatever trailing text remains.
_HOME_PATH_PATTERN = re.compile(r"(?:/home/|/Users/|C:\\Users\\)[^\s'\"]+")

# Generic absolute-path shape (2+ "/segment" groups, or a Windows drive-letter path) for content
# that survived the home-path pass above — i.e. a machine-specific absolute path not rooted at a
# recognized home-directory prefix.
_ABS_PATH_PATTERN = re.compile(r"(?:/[\w.\-]+){2,}|[A-Za-z]:\\(?:[\w.\-]+\\)*[\w.\-]+")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_content(text: str, *, repo_root: Path | None = None) -> str:
    """Strips local usernames and machine-specific absolute paths per §3, replacing each with a
    fixed placeholder — or, for a path under repo_root, rewriting it to its repo-relative form.
    Must run before any hashing.
    """
    text = _HOME_PATH_PATTERN.sub(LOCAL_USER_PLACEHOLDER, text)

    def _replace_abs_path(match: re.Match[str]) -> str:
        raw_path = match.group(0)
        if repo_root is not None:
            try:
                relative = Path(raw_path).relative_to(repo_root)
                return str(relative)
            except ValueError:
                pass
        return LOCAL_PATH_PLACEHOLDER

    return _ABS_PATH_PATTERN.sub(_replace_abs_path, text)


# ---------------------------------------------------------------------------
# §4 — Secret-scan baseline (originally 4 patterns; expanded to 10 by
# TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING's own Security-Review pass — see module docstring)
# ---------------------------------------------------------------------------

_SECRET_SCAN_PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key_id": re.compile(r"AKIA[0-9A-Z]{16}"),
    "generic_api_key_assignment": re.compile(
        r"(api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE
    ),
    "pem_private_key_header": re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9\-_.]{20,}"),
    # --- Expanded set (Security-Review pass, TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING) ---
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9\-]+"),
    # Negative lookahead excludes the "sk-ant-" prefix so an Anthropic key is attributed only to
    # anthropic_api_key below, never double-matched (or mis-attributed) as an OpenAI key.
    "openai_api_key": re.compile(r"sk-(?!ant-)[A-Za-z0-9]{20,}"),
    "anthropic_api_key": re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
    "generic_password_or_secret_assignment": re.compile(
        r"(password|passwd|secret)\s*[:=]\s*['\"][^'\"]{6,}['\"]", re.IGNORECASE
    ),
    "basic_auth_in_url": re.compile(r"https?://[^\s:/@]+:[^\s:/@]+@"),
}


def scan_for_secrets(text: str) -> str | None:
    """Returns the matching pattern's key (e.g. "aws_access_key_id") on the first match, else None.
    Any non-None result means the caller must REJECT the write outright — never redact-and-store
    (§4, redaction_retention_policy.md:91-92).

    This baseline is a documented starting point, not a production-complete secret scanner. It is
    explicitly NEW and explicitly non-production-complete — it must be reviewed and expanded by a
    security-focused pass before Phase 2 payload caching goes live (§4/§11). See this module's own
    docstring for the full disclosure; do not present this baseline as more complete than that.

    Expanded from 4 to 10 patterns by `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING`'s own
    Security-Review pass (module docstring "Update" paragraph). Still not exhaustive: real
    credential formats not covered here are neither detected nor claimed to be.
    """
    for name, pattern in _SECRET_SCAN_PATTERNS.items():
        if pattern.search(text):
            return name
    return None


# ---------------------------------------------------------------------------
# §5 — Payload size cap
# ---------------------------------------------------------------------------

def check_size_cap(redacted_payload: str) -> bool:
    """True iff the UTF-8-encoded redacted payload is <= MAX_PAYLOAD_BYTES (65536). Must be called
    on already-redacted text only (§5: "measured on the UTF-8-encoded redacted payload" —
    redaction_retention_policy.md:121). Never truncates; callers must reject outright on False.
    """
    return len(redacted_payload.encode("utf-8")) <= MAX_PAYLOAD_BYTES


# ---------------------------------------------------------------------------
# §7 — Never-cache enumeration (6 independent categories)
# ---------------------------------------------------------------------------

CATEGORY_SECRETS_OR_CREDENTIALS = "secrets_or_credentials"
CATEGORY_TOKENS = "tokens"
CATEGORY_RAW_ENVIRONMENT_VALUES = "raw_environment_values"
CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT = "unredacted_sensitive_tool_output"
CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS = "arbitrary_config_file_contents"
CATEGORY_UNRESTRICTED_RAW_PROMPTS = "unrestricted_raw_prompts"

# scan_for_secrets() match names that are named-service *tokens* (map to CATEGORY_TOKENS below);
# every other non-None match name is a *credential* shape (maps to CATEGORY_SECRETS_OR_CREDENTIALS).
_TOKEN_SHAPED_SECRET_PATTERNS: frozenset[str] = frozenset(
    {"bearer_token", "github_token", "slack_token"}
)

_ENV_VALUE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,}=\S+", re.MULTILINE)  # shell/env assignment shape
_CONFIG_LINE_PATTERN = re.compile(r"^[\w.\-]+\s*[:=]\s*.+$", re.MULTILINE)  # generic key: value / key=value line
_ARBITRARY_CONFIG_MIN_LINES = 3


def check_never_cache_categories(
    *, content: str, redacted_content: str, is_raw_prompt: bool = False
) -> frozenset[str]:
    """Returns the set of §7 categories this content violates, independently of one another
    (plan.md DD6):
    - secrets_or_credentials / tokens: reuse scan_for_secrets() on `content` — the bearer_token/
      github_token/slack_token patterns (named-service *tokens*) map to tokens; the remaining
      credential-shaped patterns (AWS key, generic api-key, PEM header, OpenAI/Anthropic *API
      keys*, generic password/secret assignment, basic-auth-in-URL) map to secrets_or_credentials.
    - raw_environment_values: an env-var-assignment shape (`_ENV_VALUE_PATTERN`) in `content`.
    - unredacted_sensitive_tool_output: defense-in-depth re-scan — True if `redacted_content`
      still contains a raw home-directory or absolute-path pattern redact_content() was supposed
      to strip (i.e. redaction did not fully do its job), per §3's own placeholder guarantee.
    - arbitrary_config_file_contents: 3+ lines in `content` matching `_CONFIG_LINE_PATTERN`.
    - unrestricted_raw_prompts: `is_raw_prompt` passed True by the caller (i.e. the caller is
      offering the full unprocessed prompt text itself, as opposed to a normalized/hashed query
      form — redaction_retention_policy.md:136).
    """
    violated: set[str] = set()

    secret_match = scan_for_secrets(content)
    if secret_match in _TOKEN_SHAPED_SECRET_PATTERNS:
        violated.add(CATEGORY_TOKENS)
    elif secret_match is not None:
        violated.add(CATEGORY_SECRETS_OR_CREDENTIALS)

    if _ENV_VALUE_PATTERN.search(content):
        violated.add(CATEGORY_RAW_ENVIRONMENT_VALUES)

    if _HOME_PATH_PATTERN.search(redacted_content) or _ABS_PATH_PATTERN.search(redacted_content):
        violated.add(CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT)

    if len(_CONFIG_LINE_PATTERN.findall(content)) >= _ARBITRARY_CONFIG_MIN_LINES:
        violated.add(CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS)

    if is_raw_prompt:
        violated.add(CATEGORY_UNRESTRICTED_RAW_PROMPTS)

    return frozenset(violated)


# ---------------------------------------------------------------------------
# §6 — redaction_policy_version stamping + WriteDecision / evaluate_write_candidate() orchestrator
# ---------------------------------------------------------------------------

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
    """Fixed-order pipeline: allowlist -> redact -> secret-scan (short-circuits) -> size-cap ->
    never-cache -> stamp+hash -> ALLOW. `_hash_text(raw_content)` (the *unredacted* hash) is never
    computed or stored anywhere in this function — only the redacted-content hash is ever
    returned, satisfying §3's "only the redacted-content hash may ever be persisted."
    """
    if not check_allowlist(source_type):
        return WriteDecision(REJECT, "not_allowlisted", None, None, redaction_policy_version)

    redacted = redact_content(raw_content)

    # Scanned against raw_content, not redacted: a redaction placeholder can swallow an
    # adjacent secret with no separator (e.g. "/home/alice/AKIA..." -> "<local-user>AKIA..."
    # loses the boundary redact_content() relies on), so scanning post-redaction risks a
    # false negative here even though check_never_cache_categories() below re-scans
    # raw_content and would still catch it — this keeps the primary guarantee independent
    # of that second check and keeps rejection_category attribution accurate.
    secret_match = scan_for_secrets(raw_content)
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


# ---------------------------------------------------------------------------
# §9 — SQLite operational limits (connection-opening only; the rest of §9 stayed behind in the
# archived tools/archive/knowledge_gateway_redaction.py)
# ---------------------------------------------------------------------------

def open_connection_with_limits(db_path: Path) -> sqlite3.Connection:
    """Opens db_path (creating parent dirs if needed), applies PRAGMA journal_mode=WAL and
    PRAGMA busy_timeout=5000 on the connection, and chmods the file to 0600 immediately after
    creation if this call is the one that created it (never re-chmods a pre-existing file, so an
    operator's own permission choice on an existing file is not silently overwritten on reconnect).
    Caller-supplied db_path only — never defaults to tools.retrieval_cache.CACHE_DB_PATH (WAL mode
    is a file-persistent setting; pointing this at the real cache file would silently change the
    journal mode observed by tools/retrieval_cache.py's own existing connections).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    created_now = not db_path.exists()
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    if created_now:
        db_path.chmod(SQLITE_FILE_MODE)
    return conn
