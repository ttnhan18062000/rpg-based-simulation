"""Typed exceptions for tools/agent_codex_runtime_shadow/ (TCK-20260730-CODEX-RUNTIME-SHADOW).

One file for all of this package's exceptions, not per-module — mirrors
tools/agent_replay_codex/errors.py's precedent of a single package-owned exception hierarchy
rather than sharing exception types across packages.
"""


class UnsupportedTierError(Exception):
    """Raised when a ticket-shaped input's tier is not `standard`."""


class UnsupportedPhaseError(Exception):
    """Raised when a phase name outside {Scope, Investigate, Plan, Review} is present."""


class ContractVersionMismatchError(Exception):
    """Raised when an input's declared workflow_version does not match the real
    implement-ticket.yaml's workflow_version, or that file's own workflow_version is missing or
    not an int."""


class PhaseOrderViolationError(Exception):
    """Raised when phases arrive out of the declared supported order (not an in-order prefix of
    the supported matrix's phase list)."""


class RequiredGateMissingError(Exception):
    """Raised when the Review phase entry has no output.verdict."""


class RequiredArtifactMissingError(Exception):
    """Raised when a required artifact file is absent on disk for a completed phase."""


class ShadowMismatchError(Exception):
    """Raised when a shadow comparison finds an axis mismatch with no covering RATIFIED
    divergence. Carries the mismatched axis name(s) so callers/tests can assert on them."""
