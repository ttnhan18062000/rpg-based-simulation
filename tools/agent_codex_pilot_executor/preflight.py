"""Deterministic no-write checks performed before a scratch claim exists."""
from __future__ import annotations

from tools.agent_codex_pilot_guardrails.enabled_surface import assert_enabled_surface_subset
from tools.agent_codex_pilot_guardrails.ticket_selection import select_pilot_candidate
from tools.agent_codex_posttool_adapter.identity import validate_identity

from .errors import PreflightRefusedError
from .models import PilotSimulationContext
from .paths import ScratchPaths, resolve_scratch_paths


def _reason_for(exc: Exception) -> str:
    """Keep the refusal boundary actionable without exposing an implementation trace."""
    name = type(exc).__name__
    if name == "PilotManifestValidationError":
        return "request_missing_or_malformed"
    if name == "MissingHumanOwnerError":
        return "request_missing_human_owner"
    if name == "MissingRollbackPlanError":
        return "request_missing_rollback_plan"
    if name == "IdentityValidationError":
        return "identity_invalid"
    if name == "EnabledSurfaceExceedsEvidenceError":
        return "surface_not_evidenced"
    if name == "ScratchContainmentError":
        return "scratch_path_unsafe"
    return "preflight_dependency_refused"


def preflight(context: PilotSimulationContext) -> ScratchPaths:
    """Return safe paths or refuse before baseline, claim, or monitoring writes."""
    try:
        paths = resolve_scratch_paths(
            scratch_root=context.scratch_root,
            ticket_id=context.ticket_id,
            execution_id=context.execution_id,
        )
        request = select_pilot_candidate(context.ticket_id, paths.request_dir)
        if request.ticket_id != context.ticket_id:
            raise PreflightRefusedError(
                "request_ticket_mismatch", "pilot request ticket_id does not match requested ticket"
            )
        validate_identity("codex", context.execution_id, context.ticket_id)
        assert_enabled_surface_subset(context.enabled_hook_events, context.enabled_writer_names)
    except PreflightRefusedError:
        raise
    except Exception as exc:
        raise PreflightRefusedError(_reason_for(exc), str(exc)) from exc
    return paths
