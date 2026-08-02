"""Independent exception classes for tools/agent_codex_posttool_adapter/
(TCK-20260730-CODEX-POSTTOOL-ADAPTER).

One file for all of this package's exceptions, mirroring tools/agent_replay_codex/errors.py's
and tools/agent_codex_pilot_guardrails/errors.py's own stated one-file convention.
"""


class PayloadValidationError(Exception):
    """Raised when a raw stdin payload is not a dict, is missing a required field, or has a
    `tool_input` that is not itself a dict."""


class HookEventNotEvidencedError(Exception):
    """Raised when a payload's `hook_event_name` is not a member of
    tools.agent_codex_pilot_guardrails.enabled_surface.EVIDENCED_HOOK_EVENTS."""


class IdentityValidationError(Exception):
    """Raised when `provider` is not exactly `"codex"`, `ticket_id` does not match
    `TICKET_ID_PATTERN`, or `execution_id` does not match the expected shape for that
    `ticket_id`."""


class LiveAppendNotGrantedError(Exception):
    """Raised when an append is attempted without CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1."""


class ActivationFragmentGuardError(Exception):
    """Raised when the proposed activation fragment's scratch-target guard is pointed at the
    real, committed .codex/config.toml."""
