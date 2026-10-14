"""Whether a saved run was host-independent, and the refusal a tool that compares two runs applies (typed record, TCK-20261014-UNAUDITED-RUNS-...).

A run's manifest carries ``audit_mode`` and ``signals_zeroed`` (booleans; absent in older manifests). ``signals_zeroed`` is True when audit_mode, or a governor that
pins itself, fed the governors zeroed signals, so nothing the host's speed changed could reach what the run computed. A comparison of two runs that is not True
on both is a comparison of host speed as much as of the change.
"""
from __future__ import annotations

from typing import Iterable, List, Mapping, Optional


class NonAuditRunError(ValueError):
    """A run that is not host-independent was offered to a tool that compares runs."""


def run_is_host_independent(manifest: Mapping[str, object]) -> Optional[bool]:
    """True when the manifest records zeroed signals, False when it records live ones, None when it says nothing (an older manifest)."""
    value = manifest.get("signals_zeroed")
    return value if isinstance(value, bool) else None


def require_host_independent_runs(manifests: Mapping[str, Mapping[str, object]]) -> None:
    """Raise `NonAuditRunError` naming every run (id to manifest) that is not recorded as host-independent; an older manifest with no record counts as not recorded."""
    bad: List[str] = [run_id for run_id, m in manifests.items() if run_is_host_independent(m) is not True]
    if bad:
        raise NonAuditRunError(f"runs not recorded as host-independent (audit_mode or a pinned governor): {sorted(bad)}; a comparison of them measures host speed as well")
