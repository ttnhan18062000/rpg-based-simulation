"""Retrieval-event field-shape provider-parity check (TCK-20260729-RETRIEVAL-EVENT-PARITY-CHECK).

This is a structural/field-shape parity check only, not live cross-provider parity: it asserts
that a retrieval-event field-name set (e.g. tools/retrieval_events.py's RETRIEVAL_EVENT_FIELDS)
contains no provider-specific field name and no execution-identity field (execution_id, provider).
It never invokes a real Codex or Claude Code execution, never compares live outputs across
providers, and performs zero file I/O — it operates purely on an in-memory frozenset/iterable of
field names passed in by the caller.
"""
from __future__ import annotations

# Provider vocabulary anchored to docs/architecture/agent_orchestration_contract.md:137-143's
# execution_id format example ("claude-code-TCK-...-<ts>-<hex>") and its Provider-Adapter Boundary
# section, which names exactly these two adapters. A closed, documented set — not an open-ended
# heuristic. If a third provider adapter is added to the repo, update this constant too.
_KNOWN_PROVIDER_TOKENS: frozenset[str] = frozenset({"codex", "claude", "claude-code"})

_IDENTITY_FIELD_NAMES: frozenset[str] = frozenset({"execution_id", "provider"})


class ProviderFieldViolationError(Exception):
    """Raised when a retrieval-event field-shape set contains execution_id/provider, or a field
    name that literally equals, is prefixed by, or is suffixed by a known provider token
    (case-insensitive) — e.g. "codex_latency_ms" or "claude_cache_status"."""


def assert_no_provider_specific_fields(
    fields: frozenset[str],
    provider_tokens: frozenset[str] = _KNOWN_PROVIDER_TOKENS,
) -> None:
    """Raises ProviderFieldViolationError on the first offending field name found in `fields`.

    Checks two independent rules per field name:
    1. Unconditional identity-field rule: the name is exactly "execution_id" or "provider".
    2. Provider-token rule: the lowercased name equals, starts with "{token}_", or ends with
       "_{token}", for any token in `provider_tokens` (lowercased).
    """
    lowered_tokens = {token.lower() for token in provider_tokens}
    for name in fields:
        if name in _IDENTITY_FIELD_NAMES:
            raise ProviderFieldViolationError(
                f"{name!r} is an execution-identity field and must not appear in a "
                "retrieval-event field-shape set"
            )
        lowered_name = name.lower()
        for token in lowered_tokens:
            if (
                lowered_name == token
                or lowered_name.startswith(f"{token}_")
                or lowered_name.endswith(f"_{token}")
            ):
                raise ProviderFieldViolationError(
                    f"{name!r} names or prefixes/suffixes provider token {token!r} and must not "
                    "appear in a provider-neutral retrieval-event field-shape set"
                )
