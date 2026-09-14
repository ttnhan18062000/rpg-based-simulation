# Plan — TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS

## Chosen fix
Seed `state.feature_flags` from `FeatureFlagManager().serialize()` once, inside `Kernel.__init__`,
merged so any pre-existing entry in `state.feature_flags` (profile YAML, env-var override,
test-constructed state) wins over the manager default:

```python
_manager_defaults = FeatureFlagManager().serialize()
_existing_flags = dict(getattr(self._state, "feature_flags", None) or {})
object.__setattr__(self._state, "feature_flags", {**_manager_defaults, **_existing_flags})
```

Placed immediately after the existing `_opt_profile`/`_force_full_scan` `object.__setattr__` block
in `src/engine/kernel.py`, following that block's own established pattern for stamping a derived
value onto the frozen `AuthoritativeState` at construction. Deliberately **not** wrapped in a
swallowing `try/except` (unlike the adjacent block) — `feature_flags` is a real, always-present
`AuthoritativeState` field; a failure here is a genuine bug that should surface, not join the
"looks live and isn't" pattern this fix closes.

## What this does NOT do
- Does not patch any of the 9 inner-gate fallback strings (`flags.get(FLAG, "OFF")`) — that was
  explicitly rejected in the ticket's own filing and the reasoning stands: editing both sides
  independently is the dual-mechanism shape being removed, not a fix for it.
- Does not touch `FeatureFlagManager`'s own construction inside `pipeline.py::refine()` — the
  19 flags routed purely through `run_phase()`'s own dispatch are unaffected either way, and this
  fix doesn't change that routing.
- Does not resolve `TCK-20260913-LEADSTATE-DETAIL-LOCATION-KIND-CONTRACT-MISMATCH` (next in this
  batch's strict order) even though this fix is what makes that bug fire in practice.

## Steps
1. Re-confirm the 1-of-9 divergence count against current `main` (done — see investigation.md;
   count holds, total manager-flag count corrected from 28 to 26 in passing).
2. Implement the seeding in `Kernel.__init__`.
3. Verify empirically against a real, unmodified corpus profile with no env var
   (`frontier_marches` via `tools.calibrate_simq._run_engine`) — the literal acceptance signal.
4. Write committed test coverage for the *mechanism*, not just the one flag's resulting value:
   - Every manager-default flag gets seeded into an empty `state.feature_flags`.
   - A pre-existing explicit override that disagrees with the manager default survives untouched.
   - Constructing a second `Kernel` from an already-seeded state doesn't double-seed or corrupt.
   - The real corpus-profile end-to-end acceptance signal, as a permanent regression test.
5. Run the guild/flag/feature-flag regression suites plus a broader `tests/unit/engine/` +
   `tests/integration/kernel/` + `tests/unit/domains/optimization/` sweep, since `Kernel.__init__`
   is a central, load-bearing construction path touched by every real run.
6. Update ticket body, close, record hand-orchestrated monitoring, commit.

## Explicitly deferred to later tickets in this batch (not this ticket's scope)
- Classifying each of the 9 flags sole-gate vs. redundant-gate, and whether the redundant inner
  checks should eventually be removed now that seeding makes them reachable — real design question,
  not required to close this propagation gap; left as an open question in Implementation Notes.
- Re-checking `TCK-20260824-ROLLOUT-FLAG-DECISIONS`'s 5 named `*-FLAG-VALIDATION` follow-ups against
  the 9-flag list — noted as still-open in Implementation Notes, not resolved here, since it's
  process/tracking work rather than part of the propagation fix itself.
