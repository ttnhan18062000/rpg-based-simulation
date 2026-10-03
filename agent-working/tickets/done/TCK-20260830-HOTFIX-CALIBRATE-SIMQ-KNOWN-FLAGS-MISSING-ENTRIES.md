---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES
phase: done
date: 2026-08-30
tags: [feature-flags, calibration]
---

# TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES

## Title
`tools/calibrate_simq.py`'s `_KNOWN_FLAGS` Allowlist Silently Drops Env-Var Overrides for
Undeclared Flags

## Status
DONE

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
Audit confirmed the finding pre-supplied by the orchestrator: `_KNOWN_FLAGS` was missing 6 of the
17 live flags in `FeatureFlagManager._flags` (`src/domains/optimization/feature_flags.py`), not
just `ENABLE_INFORMATION_INTENT_EXECUTION` named in the ticket title —
`ENABLE_MEMORY_UPDATE`, `ENABLE_INFORMATION_INTENT_EXECUTION`,
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2`, `ENABLE_GUILD_QUEST_GENERATION`,
`ENABLE_PUSH_EVENT_SHAPERS_QUEST`, `ENABLE_PUSH_EVENT_SHAPERS_AGENCY` were all missing.

Changes to `tools/calibrate_simq.py`'s `_run_engine()`:
1. `_KNOWN_FLAGS` now lists all 17 flags, ordered to mirror
   `FeatureFlagManager.__init__`'s own declaration order (visual diffability for future audits).
2. The stale duplicate-list comment above `_KNOWN_FLAGS` (which itself had drifted out of sync,
   per the ticket's own root-cause note) was rewritten to point at `_KNOWN_FLAGS` as the single
   source of truth instead of re-listing flag names.
3. Implemented the optional hardening: after the existing env-var override loop, a second pass
   scans `os.environ` for any `ENABLE_`-prefixed key not in `_KNOWN_FLAGS` and logs
   `logger.warning(...)` naming the exact env var. Warning-only — no change to exit-code/raise
   behavior. This makes a future `_KNOWN_FLAGS` drift self-diagnosing instead of silent.

Followed the ticket's explicit Out-of-Scope instruction: `_KNOWN_FLAGS` stays a static list, not
converted to a dynamic derivation from `FeatureFlagManager().get_all_flags()`. Noting that as a
legitimate follow-up idea for a future ticket (would eliminate this class of drift entirely, but
is a larger design change than this hotfix's scope), not implemented here.

## Test Summary
Added `TestKnownFlagsEnvVarOverrides` to `tests/simulation_quality/test_calibrate_simq.py`,
reusing the existing `_patch_kernel_with_hook` helper (no duplication) to capture
`kernel.state.feature_flags` post-construction:
- `test_information_intent_execution_env_override_takes_effect` — the flag named in the ticket
  title now actually applies (`FeatureMode.ON`).
- `test_push_event_shapers_agency_env_override_takes_effect` — a second, different newly-added
  flag also applies (`FeatureMode.SHADOW`), proving the fix isn't limited to one flag.
- `test_unrecognized_env_var_is_not_applied` — anti-drift: an unrecognized `ENABLE_*` var still
  does not silently apply.
- `test_unrecognized_enable_prefixed_env_var_logs_warning` — `caplog`-based, confirms the new
  hardening warning fires and names the exact unrecognized env var.

All 9 tests in the file (5 pre-existing + 4 new) pass:
`.venv/bin/python3 -m pytest tests/simulation_quality/test_calibrate_simq.py -v` → 9 passed.

## Files Changed
- `tools/calibrate_simq.py` — `_KNOWN_FLAGS` expanded 11→17 flags; stale duplicate-list comment
  rewritten; added unrecognized-`ENABLE_*`-env-var warning pass.
- `tests/simulation_quality/test_calibrate_simq.py` — added `TestKnownFlagsEnvVarOverrides` (4
  new tests) plus a `FeatureMode` import.
- `tickets/inprogress/TCK-20260830-HOTFIX-CALIBRATE-SIMQ-KNOWN-FLAGS-MISSING-ENTRIES.md` — this
  file (Status, Implementation Notes, Test Summary, Files Changed, Completion Summary).

## Completion Summary
Fixed `tools/calibrate_simq.py`'s `_KNOWN_FLAGS` allowlist, which silently dropped env-var
feature-flag overrides for 6 of 17 live flags (not just `ENABLE_INFORMATION_INTENT_EXECUTION`,
confirmed by direct audit against `FeatureFlagManager`'s registry). All 17 flags are now
recognized, the stale duplicate-list comment was replaced with a pointer to `_KNOWN_FLAGS` as the
single source of truth, and a warning-only hardening pass now flags any future unrecognized
`ENABLE_*` env var instead of silently ignoring it. Verified via a real `_run_engine()` trial run
capturing the constructed kernel's `state.feature_flags`, plus a caplog-based warning test; no
flag default values were changed and no exit-code/raise behavior was altered.
