"""Independent exception classes for tools/agent_codex_pilot_guardrails/
(TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS).

One file for all of this package's exceptions, mirroring tools/agent_replay_codex/errors.py's
own stated convention.
"""


class PilotManifestValidationError(Exception):
    """Raised by the pilot-request loader on a missing file or a missing/empty human_owner or
    rollback_plan_summary field."""


class MissingHumanOwnerError(PilotManifestValidationError):
    """Raised when a pilot request's human_owner field is absent or empty/whitespace-only."""


class MissingRollbackPlanError(PilotManifestValidationError):
    """Raised when a pilot request's rollback_plan_summary field is absent or empty/whitespace-only."""


class ConcurrentProviderClaimError(Exception):
    """Raised when the same ticket_id is claimed, in-progress, by two different providers."""


class EnabledSurfaceExceedsEvidenceError(Exception):
    """Raised when a requested enabled hook-event or writer-function set is not a subset of the
    Phase-2/Phase-3-evidenced set."""


class PilotManifestDriftError(Exception):
    """Raised when the post-pilot baseline manifest shows a pre-existing monitoring line was
    rewritten, reordered, or deleted."""


class PilotSignoffNotGrantedError(Exception):
    """Raised when live pilot execution is attempted without CODEX_LIVE_PILOT_HUMAN_SIGNOFF=1."""


class PilotConfigToggleGuardError(Exception):
    """Raised when the config toggle mechanism is pointed at the real, committed
    .codex/config.toml."""


class PilotRollbackVerificationError(Exception):
    """Raised when the rollback-scope snapshot (agent-monitoring/*.jsonl + the pilot ticket file)
    does not match byte-for-byte across a rollback drill."""
