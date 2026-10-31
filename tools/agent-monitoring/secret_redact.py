"""Redact secret-shaped strings before they are written to a tool row or a transit bundle.

TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION. The repository is public and two writers copy free text into
committed files: `post_tool_hook.py` (the call description in a tool row) and `handover_transit.py` (handover notes,
drafts and memory files copied into the transit bundle). A token pasted into a command or a note would become a
published secret.

ONE shape list, not two: the shapes are `tools/write_path_guard.py::_SECRET_SCAN_PATTERNS`, the list the Bash secret-scan
hook already uses (`scan_for_secrets`). This module reuses those compiled patterns and only chooses which of them to
redact; it adds no pattern of its own. Chosen (`REDACTED_SHAPES`): AWS access key, PEM private-key header (redaction
extends to the end of its block), Bearer token, GitHub token, Slack token, `sk-` and `sk-ant-` keys, and credentials in
a URL. Left out on purpose: `generic_password_or_secret_assignment` (`password=` has too many harmless matches). Not
covered because the shared list does not have them: JWTs, and an `sk-` key whose first 20 characters include a hyphen
(`sk-proj-...`); widening the shared list is a separate decision.

Redaction happens on write only: rows and bundles already written are never rewritten. A shape is the visible form of a
credential, not proof of one, so a redaction can hide a harmless look-alike, which is the cheaper mistake.

Failure never leaks and never raises: `safe_redact_text` returns `[REDACTION_FAILED]` instead of the raw text if anything
goes wrong, and `redact_bytes` raises so the transit export can leave that one file out and say so in its manifest.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))  # appended: nothing in tools/ may shadow a module of this directory
import write_path_guard as _wpg  # noqa: E402

REDACTED_SHAPES: tuple[str, ...] = (
    "pem_private_key_header",
    "aws_access_key_id",
    "bearer_token",
    "github_token",
    "slack_token",
    "anthropic_api_key",  # before openai_api_key: its prefix is the more specific one
    "openai_api_key",
    "basic_auth_in_url",
    "generic_api_key_assignment",
)
REDACTION_FAILED = "[REDACTION_FAILED]"

_PATTERNS = {name: _wpg._SECRET_SCAN_PATTERNS[name] for name in REDACTED_SHAPES}  # KeyError at import = a renamed shape: loud
_PEM_BLOCK = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?(?:-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\Z)")
_BYTES = {
    name: re.compile(p.pattern.encode("ascii"), p.flags & ~re.UNICODE) for name, p in _PATTERNS.items()
}
_PEM_BLOCK_BYTES = re.compile(_PEM_BLOCK.pattern.encode("ascii"))


def marker(name: str) -> str:
    return f"[REDACTED:{name}]"


def redact_text(text: str) -> str:
    """`text` with every secret-shaped substring replaced by `[REDACTED:<shape>]`. Idempotent. May raise only on a
    non-string; callers that must not raise use `safe_redact_text`."""
    if not text:
        return text
    text = _PEM_BLOCK.sub(marker("pem_private_key_header"), text)  # the whole block, not just its header line
    for name, pattern in _PATTERNS.items():
        text = pattern.sub(marker(name), text)
    return text


def safe_redact_text(text) -> str:
    """Like `redact_text` but never raises and never returns the raw text on failure."""
    try:
        return redact_text(text)
    except Exception:  # noqa: BLE001 - a monitoring writer must not fail the workflow, and must not leak
        return REDACTION_FAILED if text else text


def count_text(text: str) -> int:
    """How many secret-shaped substrings `text` holds."""
    if not text:
        return 0
    return len(_PEM_BLOCK.findall(text)) + sum(len(p.findall(_PEM_BLOCK.sub("", text))) for p in _PATTERNS.values())


def redact_bytes(data: bytes) -> tuple[bytes, int]:
    """(redacted bytes, number of replacements). The shapes are ASCII, so other bytes pass through unchanged."""
    hits = 0

    def _sub(name):
        def inner(_m):
            nonlocal hits
            hits += 1
            return marker(name).encode("ascii")
        return inner

    data = _PEM_BLOCK_BYTES.sub(_sub("pem_private_key_header"), data)
    for name, pattern in _BYTES.items():
        data = pattern.sub(_sub(name), data)
    return data, hits
