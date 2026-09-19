---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION
artifact_type: investigation
tags: [architecture, documentation, schema]
---

# Investigation notes — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION

Not a fresh investigation — the design question (feasibility, value, vocabulary) was already
settled by `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION` (child 1, done). This
file records the one real, unanticipated implementation finding.

## The orphan-system invariant is not fixture-testable the way the other 9 are, and that's
## structural, not a bug to route around

`registry.py::validate()`'s existing invariants are all pure functions of the `data` dict alone —
`layers` and `unaudited_depends_on_edges` are both self-contained top-level fields inside
`data` itself, so a minimal 2-3-mechanism synthetic fixture can exercise any ONE invariant in
isolation without needing to also satisfy every other one.

The new orphan-system invariant (10) cannot work this way by construction: its whole job is
"does this REGISTERED system have zero members ACROSS THE REAL, COMPLETE mechanism set" — a
property that requires an external reference (the real `registries/system_registry.jsonl`,
loaded fresh regardless of what `data` happens to be). Any synthetic fixture with fewer than the
full 93 real mechanisms will, by definition, leave most of the 7 real registered systems with
zero declared members in that fixture — not because anything is broken, but because the fixture
was never meant to be complete.

Confirmed directly, not assumed: adding the invariant caused exactly 18 pre-existing, previously-
green tests to fail, each for the identical reason — `"system 'combat' is registered ... but no
mechanism declares it"`, repeated once per one of the 7 real registered systems, for every
fixture that never mentions `systems:` at all.

**Fix**: `tests/unit/tools/conftest.py`'s own new autouse fixture patches
`registry._load_system_registry` to return an empty dict by default. An empty registered-systems
set makes both new invariants vacuously satisfied for any fixture that doesn't declare
`systems: []` — exactly the pre-existing tests' own situation, since none of them were ever
about systems membership in the first place. The 2 tests that validate the REAL, complete
registry (`test_real_registry_passes_validation`, `test_real_registry_unaudited_edges_all_resolve`)
restore the real lookup explicitly, via `monkeypatch.setattr` naming the real
`system_registry.load_registry` function, so they still exercise the genuine invariant against
genuine data.

This is not a workaround masking a design flaw — it is the correct behavior for an invariant
whose subject is "the real world," the same way `test_real_registry_passes_validation` already
existed as a separate, dedicated test for exactly the properties only the real, complete file can
prove, rather than trying to make every fixture-based test carry the full 93-mechanism weight.
