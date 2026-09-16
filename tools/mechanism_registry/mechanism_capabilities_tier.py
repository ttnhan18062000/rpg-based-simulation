#!/usr/bin/env python3
"""
Declares the single `(state, verified) -> tier` mapping for simulation_capabilities.html's 3-tier
plain-language field (`live` / `built` / `planned`), so it is never reimplemented per card.

TCK-20260915-ARTIFACT-STATE-CONVERGENCE (scope item 3, AC #4). A `state`-only mapping was tried and
rejected before writing this: `camp`'s own case proves it wrong in both directions --
`state: done` alone would suggest `tier: live` (false: camp has never been observed doing anything),
while capabilities' own pre-existing (buggy) `tier: planned` for camp is ALSO wrong the other way
(`planned` means "not yet built", and camp's own CampState code is real and wired). Only
`(state, verified.verdict)` together produces the correct answer: `done` + `verified.verdict ==
"contradicted"` -> `built` ("exists, correctly, but has never fired").

Per peer review, `partial -> live` is deliberately the mapping's weakest link (partial means partly
working; `live` asserts players experience it) -- rather than a general per-state override escape
hatch, only `partial` mechanisms may be overridden, via PARTIAL_TIER_OVERRIDES, and only with a
recorded, non-empty reason (never silently). No override table exists for the other five states: if
one of those ever needs a per-card exception, that itself is a signal this mapping function is wrong
and should be revisited, not silently patched around.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

VALID_TIERS = frozenset({"live", "built", "planned"})

# mechanism_id -> (tier, reason). Every entry here MUST correspond to a mechanism whose registry
# `state` is "partial" -- enforced by a test, not just documented, since a `partial` mechanism can
# in principle change state later and silently leave a stale override behind.
PARTIAL_TIER_OVERRIDES: Dict[str, Tuple[str, str]] = {}


def compute_tier(state: str, verified: Optional[dict]) -> str:
    """The declared mapping, state + verified.verdict only -- no card-specific knowledge here.
    Per-card overrides (partial only) are applied by the caller via PARTIAL_TIER_OVERRIDES, not
    inside this function, so this function's own output is always traceable to (state, verdict)
    alone."""
    verdict = verified.get("verdict") if verified else None

    if state == "done":
        return "built" if verdict == "contradicted" else "live"
    if state in ("orphan", "gated", "skeleton"):
        return "built"
    if state == "partial":
        return "live"
    if state == "gap":
        return "planned"
    raise ValueError(f"compute_tier: unrecognized state {state!r}")


def resolve_tier(mechanism_id: str, state: str, verified: Optional[dict]) -> str:
    """compute_tier(), then apply the partial-only override table -- the single entry point the
    regenerator should call, so the override is never bypassed by calling compute_tier() directly
    on a partial mechanism."""
    default = compute_tier(state, verified)
    if mechanism_id in PARTIAL_TIER_OVERRIDES:
        if state != "partial":
            raise ValueError(
                f"PARTIAL_TIER_OVERRIDES has an entry for {mechanism_id!r} but its registry state "
                f"is {state!r}, not 'partial' -- override table has gone stale, fix or remove it"
            )
        override_tier, reason = PARTIAL_TIER_OVERRIDES[mechanism_id]
        if not reason or not reason.strip():
            raise ValueError(f"PARTIAL_TIER_OVERRIDES[{mechanism_id!r}] has an empty reason")
        return override_tier
    return default
