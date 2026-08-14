---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan — TCK-20260809-COMBAT-ACTIONSTYLE-WIRING

## Mid-session design correction absorbed here (real, user-directed)
The user interrupted the original implementation ("I think one of the design is data-driven, you
not hard code every personality based on every race in the code, but define them in data, and
code read them") after the sibling `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION`'s own
bravery-bias table had already landed as a hardcoded Python dict. Rather than leave that ticket's
own shipped code half-migrated, both the bravery-bias table AND this ticket's own new
`action_style_thresholds` were moved together into one real data file,
`data/content/social/personality_bias.yaml`, with `compiler.py` reading it (cached, with an
in-code fallback matching the shipped data exactly, so a missing/malformed file never crashes
world compilation). Registered as a real, intentional non-catalog file
(`NON_CATALOG_FILES` in `src/content/repository.py`, and a `DESIGN_ONLY` entry in
`src/content/matrix.py`'s content usage matrix) rather than building a full
`CatalogRepository` content-family schema for what is fundamentally a small, flat tuning table —
proportionate to its actual size/shape.

## Implementation
- `get_action_style_for_bravery(bravery: float) -> int` (`src/worldbuilding/compiler.py`): reads
  `action_style_thresholds` from the same data-driven config, returns
  `ActionStyle.AGGRESSIVE`/`EVASIVE`/`BALANCED`.
- Wired into the existing `.combat(...)` builder call: `action_style=get_action_style_for_bravery
  (personality.bravery)` — uses the entity's own final, bias-applied bravery value (computed
  moments earlier in the same loop iteration), so `ActionStyle` and `bravery` stay consistent for
  the same entity.

## Explicitly not fixed (real, traced, disclosed)
- `tactical.py`'s own `AGGRESSIVE` range-bonus and `EVASIVE` reposition-stub sub-branches are dead
  code (local variable never read downstream) — a separate, real bug in that function's own
  control flow, independent of whether `action_style` is ever set. Fixing `tactical.py`'s own
  internal wiring is a distinct change from this ticket's own scope (get `ActionStyle` assigned to
  real entities at all) and risks scope creep into re-auditing every dormant sub-branch of a
  large, already-dense tactical decision function. Disclosed in docs and the ticket body rather
  than silently left unmentioned.

## Verification plan
- Direct unit tests: threshold boundaries, and a real synthetic-world compile confirming a
  high-bravery-biased faction's population skews `AGGRESSIVE` (not every entity the class
  default).
- Real live-world re-verification (same methodology as the sibling ticket): `dungeon_crawl`/
  `urban_political` post-fix `action_style` distributions, confirmed ordered/correlated with the
  sibling ticket's own bravery-bias findings.

## Acceptance-criteria map
| AC | How satisfied |
|---|---|
| investigation.md confirms real ActionStyle consumers and which are genuinely dead code | Done |
| Data-driven design correction absorbed for both this ticket and its sibling | Done |
| Real gap-closing work re-verified against real corpus data | Done |
| Scoped pytest passes | Done |
