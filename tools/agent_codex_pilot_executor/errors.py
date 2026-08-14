"""Gate-specific errors for the scratch-only pilot executor."""


class PilotExecutorError(Exception):
    """Base class for executor refusals and failed simulations."""


class ScratchContainmentError(PilotExecutorError):
    """An injected scratch path is unsafe or escapes the scratch root."""


class PreflightRefusedError(PilotExecutorError):
    """A request, identity, or evidenced-surface gate refused execution."""

    def __init__(self, reason: str, message: str | None = None):
        super().__init__(message or reason)
        self.reason = reason


class ClaimRefusedError(PilotExecutorError):
    """A claim is active, malformed, unrecognized, or not owned by the caller."""


class LifecycleProofError(PilotExecutorError):
    """The declared scratch lifecycle could not be written or proven."""
