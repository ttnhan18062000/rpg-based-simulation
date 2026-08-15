"""Doc-structure tests for the Knowledge Gateway MCP redaction/retention policy
(TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY).

Phase 0 is policy/documentation-only: no cache read/write path, secret scanner, SQLite operational
defaults, or GC implementation exists in `tools/` yet. These tests assert doc *structure*
(required section headings, required phrases present as distinct, individually matchable text) —
never runtime behavior — mirroring the static-assertion pattern
`tests/tools/test_knowledge_gateway_contract_schemas.py` uses for schema shape.
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_POLICY_DOC = (
    _REPO_ROOT
    / "docs"
    / "engine"
    / "contracts"
    / "knowledge_gateway_mcp"
    / "redaction_retention_policy.md"
)
_RETRIEVAL_CACHE_PY = _REPO_ROOT / "tools" / "retrieval_cache.py"


def _read_doc() -> str:
    return _POLICY_DOC.read_text()


# ---------------------------------------------------------------------------
# Step 1 — AC1/AC2: required sections, never-cache enumeration
# ---------------------------------------------------------------------------

def test_redaction_retention_policy_doc_exists_and_has_required_sections():
    assert _POLICY_DOC.exists(), f"missing required policy doc: {_POLICY_DOC}"
    text = _read_doc()

    required_headings = [
        "## 1. Purpose",
        "## 2. Eligible Source Types",
        "## 3. Redaction Rules",
        "## 4. Secret-Scan Disclosure",
        "## 5. Payload Size Cap",
        "## 6. Redaction-Policy Version",
        "## 7. Never-Cache Enumeration",
    ]
    for heading in required_headings:
        assert heading in text, f"missing required section heading: {heading}"

    never_cache_items = [
        "Secrets and credentials",
        "Tokens (API tokens",
        "Raw environment values",
        "Unredacted sensitive tool output",
        "Arbitrary configuration-file contents",
        "Unrestricted raw prompts",
    ]
    for item in never_cache_items:
        assert item in text, f"never-cache enumeration missing item: {item}"

    assert "not a production-complete secret scanner" in text
    assert "NEW" in text


# ---------------------------------------------------------------------------
# Step 2 — AC3: token-counting method
# ---------------------------------------------------------------------------

def test_token_counting_method_returns_integer_compatible_with_budget_schema():
    text = _read_doc()
    assert "kgmcp_char_heuristic_v1" in text
    assert "budget_tokens" in text
    assert "budget_requested" in text
    assert "budget_returned" in text
    assert "budget_class" in text
    assert "non-negative integer" in text
    # Originally asserted "No callable ships in tools/..." (present tense, AC7 as scoped by
    # TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY, which explicitly deferred the callable to a
    # future ticket). TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY implemented the real callable at
    # tools/knowledge_gateway_packet_assembly.py, so §8 now correctly speaks in the past tense —
    # this test asserts that updated, accurate wording instead.
    assert "No callable shipped in" in text or "no callable shipped in" in text.lower()


# ---------------------------------------------------------------------------
# Step 3 — AC4: SQLite operational limits, documented not implemented
# ---------------------------------------------------------------------------

def test_sqlite_operational_limits_are_documented():
    text = _read_doc()
    required_phrases = [
        "Maximum database size",
        "TTL/usage-based eviction",
        "File permissions",
        "WAL mode",
        "Bounded transactions",
        "Busy timeouts",
        "One-writer-safe migration discipline",
        "Per-key stampede guard",
    ]
    for phrase in required_phrases:
        assert phrase in text, f"SQLite operational limits missing: {phrase}"
    assert "not implemented in `tools/retrieval_cache.py` by this" in text


def test_sqlite_defaults_not_silently_implemented():
    """Anti-scope-creep guard: this ticket documents SQLite defaults but must never wire them
    into tools/retrieval_cache.py. Fails loudly if any drifting implementer adds PRAGMA/
    busy_timeout/chmod code to that module under cover of satisfying AC4.
    """
    source = _RETRIEVAL_CACHE_PY.read_text()
    assert "PRAGMA" not in source
    assert "busy_timeout" not in source
    assert "os.chmod" not in source
    assert "chmod" not in source

    tree = ast.parse(source)
    imported_modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)
    assert "os" not in imported_modules


# ---------------------------------------------------------------------------
# Step 4 — AC5: cache-GC defaults, deference to evidence-identity contract
# ---------------------------------------------------------------------------

def test_gc_policy_never_authorizes_evicting_evidence_the_identity_contract_protects():
    text = _read_doc()
    assert "Cache-GC Defaults" in text
    assert "PROVIDER_GENERATION" in text
    assert "SYMBOL" in text
    assert "FILE" in text
    assert "defers to, and never overrides" in text
    assert "current manual-only status" in text


# ---------------------------------------------------------------------------
# Step 6 — AC7: ratification status is recorded accurately
#
# Originally asserted the pre-ratification "drafted, not ratified" state (AC7 as scoped by
# TCK-20260814-KGMCP-REDACTION-RETENTION-POLICY). The repository owner ratified §24 item 1 on
# 2026-08-15 (TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION), so the doc's own §11 changed to
# reflect that — this test now asserts the ratified state instead, since the property under test
# ("the doc's ratification section accurately reflects the real, current ratification status") is
# unchanged; only the real status itself changed.
# ---------------------------------------------------------------------------

def test_policy_doc_explicitly_flags_ratification_status():
    text = _read_doc()
    assert "Ratified as drafted" in text
    assert "TCK-20260815-HOTFIX-KGMCP-PHASE0-RATIFICATION" in text
    assert "No changes were made to §2" in text
