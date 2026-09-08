"""Tests for tools/write_path_guard.py — the pure write-path enforcement functions for
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md` §2-§9 (connection
opening only), extracted from `tools/knowledge_gateway_redaction.py` by
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE` once the Knowledge Gateway MCP package that module
belonged to was archived.

Ported verbatim (as a behavior-parity regression guard) from
`tests/tools/test_knowledge_gateway_redaction.py` (now archived to
`tests/archive/test_knowledge_gateway_redaction.py`) — every fixture and assertion here targets
the exact same inputs/outputs that file exercised, confirming the move was pure code relocation
with no behavior change. §9's `check_db_size_within_limit()`/`execute_bounded_transaction()`, the
write-guard pair, and §10's GC-eligibility predicates stayed behind in the archived module and are
not re-tested here — see the archived test file for their own (now-historical) coverage.

No test in this file opens `knowledge-index/retrieval_cache.db` at its real path or issues a real
INSERT/UPDATE against `retrieval_provider_result_cache_rows`; every §9 test uses a tmp_path-scoped
throwaway SQLite file, mirroring tests/tools/test_retrieval_cache.py's own `_isolated_cache_db`
fixture pattern (never CACHE_DB_PATH itself).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools import write_path_guard as wpg  # noqa: E402
from tools import retrieval_cache as rc  # noqa: E402
from tools import retrieval_events as re_mod  # noqa: E402


# ---------------------------------------------------------------------------
# Module docstring disclosure — checked on scan_for_secrets()'s own docstring since this module's
# top docstring was rewritten (per plan.md Step 1) to describe the write-path-guard concern rather
# than repeat the gateway-specific framing; the disclosure text itself lives verbatim on the
# function whose docstring the original module-level assertion was really guarding.
# ---------------------------------------------------------------------------

class TestModuleDisclosure:
    def test_scan_for_secrets_docstring_preserves_non_production_complete_disclosure(self):
        normalized = " ".join(wpg.scan_for_secrets.__doc__.split())
        assert "not a production-complete secret scanner" in normalized
        assert "security-focused pass before Phase 2 payload caching goes live" in normalized


# ---------------------------------------------------------------------------
# §2 Allowlist
# ---------------------------------------------------------------------------

class TestAllowlist:
    def test_allowlist_accepts_context_search_source_type(self):
        assert wpg.check_allowlist(wpg.SOURCE_TYPE_CONTEXT_SEARCH) is True

    def test_allowlist_accepts_graphify_source_type(self):
        assert wpg.check_allowlist(wpg.SOURCE_TYPE_GRAPHIFY) is True

    def test_allowlist_rejects_unlisted_source_type(self):
        assert wpg.check_allowlist("raw_filesystem_read") is False
        assert wpg.check_allowlist("live_shell_stdout") is False
        assert wpg.check_allowlist("") is False


# ---------------------------------------------------------------------------
# §3 Redaction rules and hashing
# ---------------------------------------------------------------------------

class TestRedactionAndHashing:
    def test_redaction_replaces_local_username_in_home_path(self):
        unix_input = "Path is /home/alice/project/file.py for the build."
        unix_output = wpg.redact_content(unix_input)
        assert "alice" not in unix_output
        assert wpg.LOCAL_USER_PLACEHOLDER in unix_output

        windows_input = r"Path is C:\Users\alice\project\file.py for the build."
        windows_output = wpg.redact_content(windows_input)
        assert "alice" not in windows_output
        assert wpg.LOCAL_USER_PLACEHOLDER in windows_output

    def test_redaction_replaces_machine_specific_absolute_path(self):
        not_under_repo = wpg.redact_content(
            "Config found at /opt/secret-data/config.txt on disk.", repo_root=Path("/repo/project")
        )
        assert "/opt/secret-data/config.txt" not in not_under_repo
        assert wpg.LOCAL_PATH_PLACEHOLDER in not_under_repo

        under_repo = wpg.redact_content(
            "See /repo/project/src/foo.py for details.", repo_root=Path("/repo/project")
        )
        assert "/repo/project/src/foo.py" not in under_repo
        assert "src/foo.py" in under_repo
        assert wpg.LOCAL_PATH_PLACEHOLDER not in under_repo

    def test_redacted_hash_differs_from_unredacted_hash_for_same_input(self):
        raw = "Home dir: /home/bob/secret-notes.txt"
        redacted = wpg.redact_content(raw)
        assert redacted != raw
        assert wpg._hash_text(raw) != wpg._hash_text(redacted)

    def test_only_redacted_hash_is_ever_returned_for_persistence(self):
        raw_content = "Home dir: /home/bob/notes.txt has the build output."
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=raw_content
        )
        assert decision.verdict == wpg.ALLOW
        assert decision.redacted_hash == wpg._hash_text(wpg.redact_content(raw_content))
        assert decision.redacted_hash != wpg._hash_text(raw_content)

        field_names = {f.name for f in __import__("dataclasses").fields(wpg.WriteDecision)}
        assert "unredacted_hash" not in field_names

    def test_redaction_runs_before_hashing_order_is_enforced(self):
        raw_content = "See /home/carol/data/report.txt for the numbers."
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_GRAPHIFY, raw_content=raw_content
        )
        assert decision.verdict == wpg.ALLOW
        assert decision.redacted_hash == wpg._hash_text(wpg.redact_content(raw_content))
        assert decision.redacted_hash != wpg._hash_text(raw_content)


# ---------------------------------------------------------------------------
# §4 Secret-scan baseline
# ---------------------------------------------------------------------------

_AWS_KEY = "AKIAABCDEFGHIJKLMNOP"
_API_KEY_ASSIGNMENT = 'api_key = "abcdefghij1234567890"'
_PEM_HEADER = "-----BEGIN RSA PRIVATE KEY-----"
_BEARER_TOKEN = "Bearer a1b2c3d4e5f6g7h8i9j0KLMN"
_CLEAN_CONTENT = "This is a perfectly normal piece of retrieved documentation text."

_GITHUB_TOKEN_GHP = "ghp_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
_GITHUB_TOKEN_FINE_GRAINED = "github_pat_" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
_SLACK_TOKEN = "xoxb-fake-placeholder-example-token"  # obviously-fake shape, not a real credential
_OPENAI_KEY = "sk-" + "A1b2C3d4E5f6G7h8I9j0K1l2M3n4"
_ANTHROPIC_KEY = "sk-ant-" + "A1b2C3d4E5f6G7h8I9j0K1l2"
_PASSWORD_ASSIGNMENT = 'password = "supersecretvalue1"'
_BASIC_AUTH_URL = "https://alice:hunter2@internal.example.com/api"


class TestSecretScan:
    def test_secret_scan_detects_aws_style_access_key_id(self):
        assert wpg.scan_for_secrets(f"key = {_AWS_KEY}") == "aws_access_key_id"

    def test_secret_scan_rejects_write_on_aws_key_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=f"key = {_AWS_KEY}"
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "aws_access_key_id"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_generic_api_key_assignment(self):
        assert wpg.scan_for_secrets(_API_KEY_ASSIGNMENT) == "generic_api_key_assignment"

    def test_secret_scan_rejects_write_on_api_key_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_API_KEY_ASSIGNMENT
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "generic_api_key_assignment"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_pem_private_key_header(self):
        assert wpg.scan_for_secrets(_PEM_HEADER) == "pem_private_key_header"
        assert wpg.scan_for_secrets("-----BEGIN EC PRIVATE KEY-----") == "pem_private_key_header"
        assert (
            wpg.scan_for_secrets("-----BEGIN OPENSSH PRIVATE KEY-----") == "pem_private_key_header"
        )
        assert wpg.scan_for_secrets("-----BEGIN PRIVATE KEY-----") == "pem_private_key_header"

    def test_secret_scan_rejects_write_on_pem_header_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_PEM_HEADER
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "pem_private_key_header"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_bearer_token(self):
        assert wpg.scan_for_secrets(_BEARER_TOKEN) == "bearer_token"

    def test_secret_scan_rejects_write_on_bearer_token_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_BEARER_TOKEN
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "bearer_token"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_clean_content_is_not_rejected(self):
        assert wpg.scan_for_secrets(_CLEAN_CONTENT) is None
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_CLEAN_CONTENT
        )
        assert decision.verdict == wpg.ALLOW

    def test_secret_scan_match_short_circuits_before_size_cap_or_redaction_store(self):
        oversized_secret_content = f"key = {_AWS_KEY}\n" + ("x" * (wpg.MAX_PAYLOAD_BYTES + 1))
        assert len(oversized_secret_content.encode("utf-8")) > wpg.MAX_PAYLOAD_BYTES
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=oversized_secret_content
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "aws_access_key_id"

    def test_secret_scan_detects_github_token(self):
        assert wpg.scan_for_secrets(f"token = {_GITHUB_TOKEN_GHP}") == "github_token"
        assert wpg.scan_for_secrets(f"token = {_GITHUB_TOKEN_FINE_GRAINED}") == "github_token"

    def test_secret_scan_rejects_write_on_github_token_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=f"token = {_GITHUB_TOKEN_GHP}"
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "github_token"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_slack_token(self):
        assert wpg.scan_for_secrets(_SLACK_TOKEN) == "slack_token"

    def test_secret_scan_rejects_write_on_slack_token_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_SLACK_TOKEN
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "slack_token"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_openai_api_key(self):
        assert wpg.scan_for_secrets(_OPENAI_KEY) == "openai_api_key"

    def test_secret_scan_rejects_write_on_openai_api_key_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_OPENAI_KEY
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "openai_api_key"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_anthropic_api_key(self):
        assert wpg.scan_for_secrets(_ANTHROPIC_KEY) == "anthropic_api_key"

    def test_secret_scan_rejects_write_on_anthropic_api_key_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_ANTHROPIC_KEY
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "anthropic_api_key"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_openai_pattern_does_not_mismatch_an_anthropic_key(self):
        """An Anthropic key must be attributed exclusively to anthropic_api_key — never also
        matched (or mis-attributed) as openai_api_key, since both share the "sk-" prefix. The
        openai_api_key pattern's negative lookahead is what this test is really verifying.
        """
        assert wpg.scan_for_secrets(_ANTHROPIC_KEY) == "anthropic_api_key"
        assert wpg._SECRET_SCAN_PATTERNS["openai_api_key"].search(_ANTHROPIC_KEY) is None

    def test_anthropic_pattern_does_not_mismatch_an_openai_key(self):
        assert wpg.scan_for_secrets(_OPENAI_KEY) == "openai_api_key"
        assert wpg._SECRET_SCAN_PATTERNS["anthropic_api_key"].search(_OPENAI_KEY) is None

    def test_secret_scan_detects_generic_password_assignment(self):
        assert (
            wpg.scan_for_secrets(_PASSWORD_ASSIGNMENT) == "generic_password_or_secret_assignment"
        )
        assert (
            wpg.scan_for_secrets("passwd: 'anotherSecretValue'")
            == "generic_password_or_secret_assignment"
        )
        assert (
            wpg.scan_for_secrets('secret = "topsecretvalue123"')
            == "generic_password_or_secret_assignment"
        )

    def test_secret_scan_rejects_write_on_password_assignment_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_PASSWORD_ASSIGNMENT
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "generic_password_or_secret_assignment"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_secret_scan_detects_basic_auth_in_url(self):
        assert wpg.scan_for_secrets(_BASIC_AUTH_URL) == "basic_auth_in_url"

    def test_secret_scan_rejects_write_on_basic_auth_in_url_match(self):
        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_BASIC_AUTH_URL
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "basic_auth_in_url"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None


# ---------------------------------------------------------------------------
# §5 Payload size cap
# ---------------------------------------------------------------------------

class TestSizeCap:
    def test_max_payload_bytes_is_the_real_data_derived_value(self):
        """Regression guard (TCK-20260816-HOTFIX-KGMCP-CACHE-SIZE-CAP-RECALIBRATION): every other
        test in this class references wpg.MAX_PAYLOAD_BYTES symbolically, so a silent regression of
        the constant back to 8192 (or any other value) would pass every boundary test here
        undetected. This test pins the real, data-derived literal value."""
        assert wpg.MAX_PAYLOAD_BYTES == 65536

    def test_payload_under_cap_is_accepted(self):
        assert wpg.check_size_cap("a" * 8000) is True

    def test_payload_exactly_at_cap_is_accepted(self):
        assert wpg.check_size_cap("a" * wpg.MAX_PAYLOAD_BYTES) is True

    def test_payload_over_cap_is_rejected_not_truncated(self):
        assert wpg.check_size_cap("a" * (wpg.MAX_PAYLOAD_BYTES + 1)) is False

        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content="a" * (wpg.MAX_PAYLOAD_BYTES + 1)
        )
        assert decision.verdict == wpg.REJECT
        assert decision.rejection_category == "oversized_payload"
        assert decision.redacted_payload is None
        assert decision.redacted_hash is None

    def test_size_cap_measured_on_redacted_not_raw_payload(self):
        raw_content = "/home/someuser/very/long/path/segment/example/file.py " * 1300
        assert len(raw_content.encode("utf-8")) > wpg.MAX_PAYLOAD_BYTES

        redacted = wpg.redact_content(raw_content)
        assert wpg.check_size_cap(redacted) is True

        decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=raw_content
        )
        assert decision.verdict == wpg.ALLOW


# ---------------------------------------------------------------------------
# §7 Never-cache enumeration
# ---------------------------------------------------------------------------

_ENV_VALUE_CONTENT = "DATABASE_URL=postgres://localhost:5432/db"
_CONFIG_CONTENT = "timeout: 30\nretries: 5\ndebug: true"
_UNREDACTED_TOOL_OUTPUT_CONTENT = "Tool ran successfully with no issues."
_UNREDACTED_TOOL_OUTPUT_REDACTED = (
    "Tool ran successfully with no issues. Output logged to /home/otheruser/logs/output.txt"
)
_RAW_PROMPT_CONTENT = "Please summarize this document for me."


class TestNeverCacheCategories:
    def test_never_cache_rejects_secrets_or_credentials(self):
        violated = wpg.check_never_cache_categories(
            content=_AWS_KEY, redacted_content=_AWS_KEY
        )
        assert wpg.CATEGORY_SECRETS_OR_CREDENTIALS in violated

    def test_never_cache_rejects_tokens(self):
        violated = wpg.check_never_cache_categories(
            content=_BEARER_TOKEN, redacted_content=_BEARER_TOKEN
        )
        assert wpg.CATEGORY_TOKENS in violated
        # Documented fold (plan.md DD6): tokens are detected via the same scan_for_secrets()
        # function §4 builds, not a second independent pattern set.
        assert wpg.scan_for_secrets(_BEARER_TOKEN) == "bearer_token"

    def test_never_cache_rejects_named_service_tokens_as_tokens_category(self):
        """github_token/slack_token are named-service *tokens* (like bearer_token), not
        credentials — both must classify into CATEGORY_TOKENS, not CATEGORY_SECRETS_OR_CREDENTIALS.
        """
        for content in (_GITHUB_TOKEN_GHP, _SLACK_TOKEN):
            violated = wpg.check_never_cache_categories(content=content, redacted_content=content)
            assert violated == frozenset({wpg.CATEGORY_TOKENS}), (content, violated)

    def test_never_cache_rejects_named_service_api_keys_as_secrets_or_credentials_category(self):
        """openai_api_key/anthropic_api_key/generic_password_or_secret_assignment/
        basic_auth_in_url are credential shapes (like the pre-existing AWS/generic-api-key/PEM
        patterns), not named-service tokens — all four must classify into
        CATEGORY_SECRETS_OR_CREDENTIALS, not CATEGORY_TOKENS.
        """
        for content in (_OPENAI_KEY, _ANTHROPIC_KEY, _PASSWORD_ASSIGNMENT, _BASIC_AUTH_URL):
            violated = wpg.check_never_cache_categories(content=content, redacted_content=content)
            assert violated == frozenset({wpg.CATEGORY_SECRETS_OR_CREDENTIALS}), (content, violated)

    def test_never_cache_rejects_raw_environment_values(self):
        violated = wpg.check_never_cache_categories(
            content=_ENV_VALUE_CONTENT, redacted_content=_ENV_VALUE_CONTENT
        )
        assert wpg.CATEGORY_RAW_ENVIRONMENT_VALUES in violated

    def test_never_cache_rejects_unredacted_sensitive_tool_output(self):
        violated = wpg.check_never_cache_categories(
            content=_UNREDACTED_TOOL_OUTPUT_CONTENT,
            redacted_content=_UNREDACTED_TOOL_OUTPUT_REDACTED,
        )
        assert wpg.CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT in violated

    def test_never_cache_rejects_arbitrary_config_file_contents(self):
        violated = wpg.check_never_cache_categories(
            content=_CONFIG_CONTENT, redacted_content=_CONFIG_CONTENT
        )
        assert wpg.CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS in violated

    def test_never_cache_rejects_unrestricted_raw_prompts(self):
        violated = wpg.check_never_cache_categories(
            content=_RAW_PROMPT_CONTENT, redacted_content=_RAW_PROMPT_CONTENT, is_raw_prompt=True
        )
        assert wpg.CATEGORY_UNRESTRICTED_RAW_PROMPTS in violated

    def test_never_cache_categories_are_independently_enforced(self):
        cases = [
            (
                {"content": _AWS_KEY, "redacted_content": _AWS_KEY},
                wpg.CATEGORY_SECRETS_OR_CREDENTIALS,
            ),
            (
                {"content": _BEARER_TOKEN, "redacted_content": _BEARER_TOKEN},
                wpg.CATEGORY_TOKENS,
            ),
            (
                {"content": _ENV_VALUE_CONTENT, "redacted_content": _ENV_VALUE_CONTENT},
                wpg.CATEGORY_RAW_ENVIRONMENT_VALUES,
            ),
            (
                {
                    "content": _UNREDACTED_TOOL_OUTPUT_CONTENT,
                    "redacted_content": _UNREDACTED_TOOL_OUTPUT_REDACTED,
                },
                wpg.CATEGORY_UNREDACTED_SENSITIVE_TOOL_OUTPUT,
            ),
            (
                {"content": _CONFIG_CONTENT, "redacted_content": _CONFIG_CONTENT},
                wpg.CATEGORY_ARBITRARY_CONFIG_FILE_CONTENTS,
            ),
            (
                {
                    "content": _RAW_PROMPT_CONTENT,
                    "redacted_content": _RAW_PROMPT_CONTENT,
                    "is_raw_prompt": True,
                },
                wpg.CATEGORY_UNRESTRICTED_RAW_PROMPTS,
            ),
        ]
        for kwargs, expected_category in cases:
            violated = wpg.check_never_cache_categories(**kwargs)
            assert violated == frozenset({expected_category}), (
                f"expected exactly {{{expected_category}}}, got {violated} for {kwargs}"
            )


# ---------------------------------------------------------------------------
# §6 redaction_policy_version stamping
# ---------------------------------------------------------------------------

class TestRedactionPolicyVersion:
    def test_redaction_policy_version_is_stamped_on_every_write_decision(self):
        allow_decision = wpg.evaluate_write_candidate(
            source_type=wpg.SOURCE_TYPE_CONTEXT_SEARCH, raw_content=_CLEAN_CONTENT
        )
        assert allow_decision.redaction_policy_version == wpg.redaction_policy_version

        reject_decision = wpg.evaluate_write_candidate(
            source_type="raw_filesystem_read", raw_content=_CLEAN_CONTENT
        )
        assert reject_decision.redaction_policy_version == wpg.redaction_policy_version

    def test_redaction_policy_version_distinct_from_retrieval_version(self):
        assert wpg.redaction_policy_version == 1
        assert rc.RETRIEVAL_VERSION == 1
        # Bumped 2 -> 3 by TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD's
        # migration_005 (adds retrieval_cache_access_log); the value itself is not what this test
        # guards -- see the assertion below.
        assert rc.retrieval_cache_schema_version == 3
        assert re_mod.retrieval_event_schema_version == 1
        # Same value today is a coincidence, not a shared identity -- confirmed by them being
        # four entirely separate module-level names, never imported/aliased from one another.
        assert "redaction_policy_version" not in dir(rc)
        assert "redaction_policy_version" not in dir(re_mod)
        assert "RETRIEVAL_VERSION" not in dir(wpg)
        assert "retrieval_cache_schema_version" not in dir(wpg)
        assert "retrieval_event_schema_version" not in dir(wpg)


# ---------------------------------------------------------------------------
# §9 SQLite operational limits — open_connection_with_limits() only (the rest of §9 stayed behind
# in the archived tools/archive/knowledge_gateway_redaction.py)
# ---------------------------------------------------------------------------

class TestSqliteOperationalLimits:
    def test_wal_mode_pragma_applied_on_connection_open(self, tmp_path):
        conn = wpg.open_connection_with_limits(tmp_path / "wal.db")
        try:
            mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert mode.lower() == "wal"
        finally:
            conn.close()

    def test_busy_timeout_pragma_set_to_5000ms(self, tmp_path):
        conn = wpg.open_connection_with_limits(tmp_path / "timeout.db")
        try:
            value = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            assert value == wpg.SQLITE_BUSY_TIMEOUT_MS
        finally:
            conn.close()

    def test_file_permissions_set_to_0600_after_creation(self, tmp_path):
        db_path = tmp_path / "perm.db"
        conn = wpg.open_connection_with_limits(db_path)
        conn.close()
        assert oct(db_path.stat().st_mode)[-3:] == "600"

    def test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py(self):
        """Narrowed by TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING (DD3, Architecture
        Review-confirmed): migration_003_add_redaction_policy_version_column legitimately issues a
        real `PRAGMA table_info(...)` schema-introspection query for its ALTER TABLE idempotency
        check — a different PRAGMA than the §9 connection-tuning ones
        (journal_mode/busy_timeout/chmod) this guard exists to keep exclusively behind
        write_path_guard.open_connection_with_limits(). Only those connection-tuning forms stay
        banned.

        Narrowed again by TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS. Relocated from
        tests/tools/test_knowledge_gateway_redaction.py by
        TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE, since open_connection_with_limits() is what
        this guard exists to protect and that function moved to this module.
        """
        source = Path(rc.__file__).read_text(encoding="utf-8")
        assert "PRAGMA journal_mode" not in source
        assert "PRAGMA busy_timeout" not in source
        assert "busy_timeout" not in source
        assert "os.chmod" not in source
        assert "chmod" not in source


# ---------------------------------------------------------------------------
# Whole-module architecture guards
# ---------------------------------------------------------------------------

class TestWorkflowIsolationGuards:
    def test_no_insert_or_update_literal_sql_against_provider_result_cache_rows(self):
        source = Path(wpg.__file__).read_text(encoding="utf-8")
        assert "INSERT INTO retrieval_provider_result_cache_rows" not in source
        assert "UPDATE retrieval_provider_result_cache_rows" not in source
