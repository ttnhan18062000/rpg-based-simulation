"""Single future-pilot composition path; no caller-controlled transport surface."""
from __future__ import annotations

import os
from collections.abc import Callable

from tools.agent_codex_live_transport.invoker import invoke_live_transport
from tools.agent_codex_realrepo_pilot_harness.authority import issue_live_authority
from tools.agent_codex_realrepo_pilot_harness.live_preflight import _create_live_preflight
from tools.agent_codex_realrepo_pilot_harness.proofs import (
    assert_post_run_proof,
    capture_policy_baseline,
)

from .production_config import _create_production_config_capability


_TRANSIENT_CONFIG_PATH = ".codex/config.toml"


class PilotExecutionCleanupError(RuntimeError):
    """Makes a failed operation and failed rollback independently visible."""

    def __init__(self, primary_error: Exception, cleanup_error: Exception):
        self.primary_error = primary_error
        self.cleanup_error = cleanup_error
        super().__init__(
            f"pilot operation failed: {primary_error!r}; rollback verification also failed: "
            f"{cleanup_error!r}"
        )


def _restore_and_verify(capability: object, execution_id: str) -> None:
    capability.restore(execution_id)
    capability.verify_restored()


def _run_with_capability(
    authority: object,
    preflight: object,
    capability: object,
    transport: Callable[[object, object], object],
    capture_after: Callable[[object], dict[str, bytes]],
    prove: Callable[[object, dict[str, bytes], object], None],
) -> object:
    """Run the reviewed operation and always restore the captured config bytes."""
    try:
        capability.enable()
        outcome = transport(authority, preflight)
        capability.verify_enabled()
        prove(preflight, capture_after(preflight.root), outcome)
    except Exception as primary_error:
        try:
            _restore_and_verify(capability, preflight.context.execution_id)
        except Exception as cleanup_error:
            raise PilotExecutionCleanupError(primary_error, cleanup_error) from primary_error
        raise
    _restore_and_verify(capability, preflight.context.execution_id)
    return outcome


def execute_controlled_pilot(context: object) -> object:
    """Execute one future pilot only through its reviewed evidence and capability chain."""
    preflight = _create_live_preflight(context)
    if _TRANSIENT_CONFIG_PATH not in preflight.policy.allowed_paths:
        raise PermissionError("captured policy does not allow the transient pilot config path")
    authority = issue_live_authority(os.environ)
    capability = _create_production_config_capability(authority, preflight)
    return _run_with_capability(
        authority,
        preflight,
        capability,
        invoke_live_transport,
        lambda root: capture_policy_baseline(root, preflight.policy.path),
        lambda preflight, after, outcome: assert_post_run_proof(
            preflight,
            after,
            run_start_iso=outcome.started_at_iso,
            run_end_iso=outcome.ended_at_iso,
        ),
    )
