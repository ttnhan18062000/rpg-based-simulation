---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS
artifact_type: test_plan
tags: [observability, documentation, economy]
---

# Test Plan — TCK-20260812-EVENT-TYPE-COVERAGE-SOURCE-COLUMN-STALENESS

This is a doc-only chore (per ticket Out of Scope: "no change to the actual event-derivation
code"). There is no code path to unit-test — the deliverable is prose/table accuracy. This plan is
built around spot-check commands that verify the corrected `source` values against real source
code, plus the mandatory frontmatter/format gates, not `pytest`.

## Regression Surface

No `src/` files change, so no existing test suite is at risk of regressing. The only regression
surface is **doc-format machine parsing**:

- `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` — parses this ticket's
  own `investigation.md` "Docs Requiring Update" bullets (already written above in the required
  `- \`path\`: reason` format) — verify it still parses after any Plan-phase edits to this file.
- `tools/validate_frontmatter.py` — must accept the frontmatter block on
  `event_type_coverage.md` (existing `status: authoritative` / `layer: simulation` / `authority: P1`
  / `audience: developer` / `last_verified: <date>` block, §1-8). Run: `python3
  tools/validate_frontmatter.py docs/simulation_quality/event_type_coverage.md` — **this is the
  ONLY file to pass to this tool.** Corrected during Review: the tool accepts exactly one
  positional path (no multi-file support — a multi-file invocation fails immediately with
  `unrecognized arguments`), and confirmed by direct execution to correctly FAIL (exit 1, "missing
  frontmatter block") against `entity.yaml` and every `docs/parity_ledger/*.yaml` file, since none
  of those carry a `---`-delimited frontmatter block by design — a pre-existing structural fact,
  not something this ticket's edits affect. Never invoke this tool against those 5 files, and never
  "fix" a FAIL against them by adding a frontmatter block they don't structurally need.
- If any `docs/parity_ledger/*.yaml` file is touched: the file must remain valid YAML and
  conform to the parity-ledger schema. The real validation entrypoint is `python3
  tools/parity_index.py build` (rebuilds `parity-index/parity.db` from all `docs/parity_ledger/
  *.yaml` files — a schema/structural parse failure on any entry, including the ones this ticket
  touches, surfaces as a build error). Run this after Steps 13-14 land, in addition to the plain
  `yaml.safe_load` parse check each of those steps already specifies.

## New Tests Required

None — this ticket adds no code, so there is no unit/integration/architecture-guard test to write
per the "New Tests Required" convention. Verification is spot-check-based (below), which stands in
for test coverage on a prose-accuracy ticket, per this ticket's own framing.

## Spot-Check Commands (verification, not pytest)

Run each after Implement edits `event_type_coverage.md`. Every command below should return output
consistent with the corrected `source` value — a mismatch means the doc edit is wrong, not that
code needs to change.

**1. Confirm no stale `event_extractor` rows remain for the 70 migrated §1.1 event types** (spot
sample across all 7 shaper groups — not exhaustive, exhaustive re-derivation was already done in
investigation.md):
```bash
for et in hero_death_unrecorded combat_initiated route_selected self_model_updated \
          shop_transaction gold_sink_fired alliance_proposed diplomatic_transition \
          xp_granted progression_plateau_detected demographic_mortality calamity_spawned \
          node_recharged faction_extinct social_memory_created contract_completed \
          commitment_abandoned rejection_cascade_tick conservation_law_verified; do
  echo "=== $et ==="
  grep -n "| \`$et\`" docs/simulation_quality/event_type_coverage.md
done
```
Expect: every line's `source` cell reads `event_shapers (<ClassName>)` (or `event_shapers
(run_shadow_shapers)` for `conservation_law_verified`), never bare `event_extractor` or
`CombatDamageEvent`.

**2. Confirm each named shaper class actually still emits that event_type in current source**
(guards against a doc fix that names a class the code no longer uses, e.g. if a future refactor
moves an event again — this is the check that would have caught the original staleness):
```bash
grep -n 'event_type="hero_death_unrecorded"' src/observability/event_shapers.py   # expect: inside CombatShaper's line range
grep -n 'event_type="node_recharged"' src/observability/event_shapers.py          # expect: inside DeferredInstrumentationShaper, NOT WorldDynamicsShaper
grep -n 'event_type="conservation_law_verified"' src/observability/event_shapers.py  # expect: inside run_shadow_shapers(), not any class
```

**3. Confirm the 4 gating flags are still all default `"ON"`** (if this regressed, the doc's
"live-by-default" framing for the whole ticket would be wrong — re-verify the premise, don't just
trust the investigation):
```bash
grep -n '"ENABLE_PUSH_EVENT_SHAPERS"' src/engine/kernel.py src/observability/event_extractor.py
grep -n '"ENABLE_PUSH_EVENT_SHAPERS_PHASE2"\|"ENABLE_PUSH_EVENT_SHAPERS_QUEST"\|"ENABLE_PUSH_EVENT_SHAPERS_AGENCY"' src/observability/event_shapers.py
```
Expect: every read defaults `"ON"`.

**4. Confirm `resource_harvested`/`item_crafted` were NOT re-touched/re-broken** (these were
already correct going in — this ticket must not regress them):
```bash
grep -n '`resource_harvested`\|`item_crafted`' docs/simulation_quality/event_type_coverage.md
```
Expect: both still read `event_shapers (EconomyShaper)`, byte-identical to before this ticket
(diff the two lines against `git show HEAD -- docs/simulation_quality/event_type_coverage.md` pre-
ticket if in doubt).

**5. Confirm §3.x "resolved by" corrections (if Plan decides to apply them) match §1.1's
corrected value for the same event_type** (no re-divergence within the same doc):
```bash
python3 - <<'PY'
import re
text = open("docs/simulation_quality/event_type_coverage.md").read()
# crude spot pairs — extend as needed for whichever events Plan actually edits in §3
pairs = ["decision_divergence_detected", "lead_certainty_updated", "skill_unlocked",
         "alliance_proposed", "social_memory_created", "ecology_cycle_completed"]
for et in pairs:
    rows = re.findall(rf".*`{et}`.*", text)
    print(et, "->", len(rows), "mentions")
    for r in rows:
        print("   ", r.strip()[:140])
PY
```
Manually confirm every printed mention names the same shaper/class for a given event_type.

**6. Confirm `docs/event_ledger/entity.yaml` (if edited in-scope) is internally consistent** —
`ENTITY-003`/`ENTITY-007` `evidence` fields should name the corrected shaper, matching the parallel
correction in `event_type_coverage.md`:
```bash
grep -n -A2 "id: ENTITY-003\|id: ENTITY-007" docs/event_ledger/entity.yaml
```

**7. `last_verified` frontmatter bump**:
```bash
head -10 docs/simulation_quality/event_type_coverage.md | grep last_verified
```
Expect: date matches this ticket's completion date, not the stale `2026-07-04`.

**8. Full-file diff sanity check** — confirm the diff touches only `source`/`resolved by`
column values, the `notes` clarifications called out in investigation.md, and the frontmatter
date, not any numeric `calibration_hits` value, scorer name, or classification
(`scored`/`unscored_intentional`/etc.) — those are out of scope and must be byte-identical
before/after:
```bash
git diff -- docs/simulation_quality/event_type_coverage.md | grep -E '^[+-]' | grep -v '^\(+++\|---\)' | grep -oE '\| `[a-z_]+` \| [a-zA-Z_() ]+ \|' 
```
Eyeball the output: only the middle (`source`) field should change per line, `event_type` and
column structure unchanged.

## Anti-Drift Test Guards

- **No `src/` diff.** `git diff --stat` after Implement must show 0 files under `src/`. This is
  the single most important guard on a "doc-only, no behavior change" ticket — run it as a hard
  gate, not a spot-check:
  ```bash
  git diff --stat HEAD | grep -E '^\s*src/' && echo "FAIL: src/ touched on a doc-only ticket" || echo "OK: no src/ changes"
  ```
- **No `calibration_hits` value changes.** A doc-only ticket must not "helpfully" update hit
  counts it didn't re-run — that would be an undisclosed, unverified claim. Diff every
  `calibration_hits` column value and confirm 0 changed.
- **No parity ledger `status` field flips.** This ticket corrects `v2_evidence`/`text` prose only;
  no entry's `status: verified` should change to anything else, and no new `P0` entry should be
  added without a real `test_path` (none of the entries in scope are `P0`, confirmed in
  investigation.md — if Plan finds one that is, escalate rather than silently adding a `test_path`
  that wasn't actually run).
