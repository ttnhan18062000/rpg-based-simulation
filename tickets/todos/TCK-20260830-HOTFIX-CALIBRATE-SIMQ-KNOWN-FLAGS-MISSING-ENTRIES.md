---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES
phase: open
date: 2026-08-30
tags: [feature-flags, calibration]
---

# TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES

## Title
`tools/calibrate_simq.py`'s `_KNOWN_FLAGS` Allowlist Silently Drops Env-Var Overrides for
Undeclared Flags

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Filed from `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`'s investigation. That
ticket found `tools/calibrate_simq.py:243-250`'s `_KNOWN_FLAGS` allowlist is missing
`ENABLE_INFORMATION_INTENT_EXECUTION` — confirmed by direct read, the list only contains:

```python
_KNOWN_FLAGS = [
    "ENABLE_WORLD_CAPABILITY_LAYER", "ENABLE_SELF_MODEL_COGNITION",
    "ENABLE_ADVENTURE_ROUTING", "ENABLE_COMBAT_ENGAGEMENT",
    "ENABLE_BELIEF_ASSIMILATION", "ENABLE_PROGRESSION_EVOLUTION",
    "ENABLE_SOCIAL_COOPERATION", "ENABLE_WORLD_EMERGENCE",
    "ENABLE_LIFE_ARC_CAMPAIGNS", "ENABLE_ENHANCED_TRACE_EVENTS",
    "ENABLE_PUSH_EVENT_SHAPERS",
]
```

Setting `ENABLE_INFORMATION_INTENT_EXECUTION=ON` as an environment variable is silently ignored —
the loop at line 272 only reads `os.environ.get(flag, ...)` for names present in this list, so an
override for any flag not on it does nothing, with no warning or error. The filing ticket had to
work around this by using `--profile`-level YAML `feature_flags` instead (the only path that
actually works for this flag), but this is an easy trap for a future investigation to fall into
silently — a trial intended to be flag-ON could actually run flag-OFF with no indication anything
went wrong.

This is the second time in this same batch of flag-validation follow-ups that a
`calibrate_simq.py` override-mechanism gap surfaced (the module's own comment at lines 237-239
already lists most of the 5-flag review's flags plus a few others, but evidently wasn't kept in
sync with every flag actually reviewed under `TCK-20260824-ROLLOUT-FLAG-DECISIONS`).

## Scope
- Add `ENABLE_INFORMATION_INTENT_EXECUTION` to `_KNOWN_FLAGS`.
- Audit whether any other flag in `src/domains/optimization/feature_flags.py`'s live registry is
  also missing from `_KNOWN_FLAGS` (the filing ticket only checked this one flag) — add any
  found.
- Consider (implementer's judgment, not mandatory): should this silently-ignored-override failure
  mode itself be hardened, e.g. warn/error on an unrecognized `ENABLE_*`-prefixed env var instead
  of just skipping unknown names? This would make the next such gap self-diagnosing instead of
  silent. If judged out of proportion for a hotfix, note it as a follow-up idea instead of
  implementing it.

## Out of Scope
- Any actual flag default change.
- Broader `calibrate_simq.py` refactoring beyond this allowlist gap.

## Acceptance Criteria
- `ENABLE_INFORMATION_INTENT_EXECUTION=ON` (and any other flag found missing during the audit) is
  recognized by `tools/calibrate_simq.py`'s env-var override mechanism.
- A quick regression check (e.g. a real trial run with the env var set, or a targeted unit test on
  `_parse_flag_value`/the override-application loop) confirms the fix actually takes effect.

## Related Tickets
- TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION (filing ticket, disclosed this
  finding)
- TCK-20260824-ROLLOUT-FLAG-DECISIONS (original flag review this tool supports)

## Related Code Areas
- tools/calibrate_simq.py
- src/domains/optimization/feature_flags.py

## Assumptions / Open Questions
None yet — to be surfaced during the missing-flags audit.

## Implementation Notes
(Not yet implemented — filed and deferred, per session's "verify follow-up tickets, then SimQ" sequencing.)

## Test Summary
(Not yet implemented.)

## Files Changed
(Not yet implemented.)

## Completion Summary
(Not yet implemented.)
