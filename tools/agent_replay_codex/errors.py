"""Independent exception classes for tools/agent_replay_codex/ (TCK-20260721-CODEX-REPLAY-PARITY).

One file for all of this package's exceptions, not per-module — this package has no write-guard
of its own (unlike tools/agent_orchestration_codex_adapter/), so the two-file errors.py/generator
split that sibling package uses is unnecessary here.
"""


class EntryCriterionNotMetError(Exception):
    """Raised when MONITORING-WRITER-UNIFICATION's writer module is not importable/landed."""


class ConsentNotGrantedError(Exception):
    """Raised when a real Codex CLI invocation is attempted without CODEX_REPLAY_PARITY_LIVE_CONSENT=1."""


class ContainmentViolationError(Exception):
    """Raised when a pre/post snapshot diff detects an unexpected change to tickets/ or
    agent-monitoring/*.jsonl, or the committed .codex/config.toml changed."""


class CodexInvocationError(Exception):
    """Raised when the real `codex exec` subprocess exits non-zero or produces no parseable result."""
