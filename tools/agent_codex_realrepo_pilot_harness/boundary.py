"""The narrow, injected future-invoker boundary.

This module deliberately has no command builder, CLI, or subprocess dependency.
The future transport must be injected and separately reviewed before a live pilot.
"""
from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .authority import _LivePilotAuthority
from .errors import RootAdmissionRefused
from .live_preflight import LivePreflightResult
from .preflight import PreflightResult


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _require_captured_preflight(preflight: object) -> PreflightResult:
    """Bind invocation to no-write evidence captured before this boundary."""
    if not isinstance(preflight, PreflightResult):
        raise PermissionError("captured no-write preflight is required before invoker construction")
    if preflight.root != preflight.context.repo_root.resolve():
        raise RootAdmissionRefused("captured preflight root is not bound to its context")
    if preflight.baseline_digest != preflight.policy.baseline_sha256:
        raise RootAdmissionRefused("captured preflight baseline is not bound to policy")
    return preflight


def _admit_live_root(preflight: object) -> Path:
    """Future-only real-root admission, sequenced after authority and preflight.

    Ordinary preflight intentionally refuses the canonical project root. A future,
    separately reviewed live preflight must supply equivalent immutable evidence
    before this private admission can be used.
    """
    if not isinstance(preflight, LivePreflightResult):
        raise PermissionError("captured live preflight is required before live invoker construction")
    result = preflight
    if result.root != result.context.repo_root.resolve():
        raise RootAdmissionRefused("captured live preflight root is not bound to its context")
    if result.baseline_digest != result.policy.baseline_sha256:
        raise RootAdmissionRefused("captured live preflight baseline is not bound to policy")
    if result.root != _PROJECT_ROOT.resolve():
        raise RootAdmissionRefused("live boundary requires the reviewed canonical project root")
    return result.root


def invoke_after_authority(
    authority: _LivePilotAuthority | None,
    preflight: PreflightResult | None,
    invoker: Callable[[Path], object],
) -> object:
    """Call a scratch-test invoker only after authority and no-write preflight.

    The public seam deliberately permits only an injected scratch-root invoker.
    It neither constructs commands nor starts processes.
    """
    if not isinstance(authority, _LivePilotAuthority):
        raise PermissionError("live pilot authority is required before invoker construction")
    result = _require_captured_preflight(preflight)
    return invoker(result.root)


def _invoke_live_after_authority(
    authority: _LivePilotAuthority | None,
    preflight: object,
    invoker: Callable[[Path], object],
) -> object:
    """Reserved future live seam; no caller or test in this ticket may use it."""
    if not isinstance(authority, _LivePilotAuthority):
        raise PermissionError("live pilot authority is required before invoker construction")
    return invoker(_admit_live_root(preflight))
