---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260915-ARTIFACT-STATE-CONVERGENCE
artifact_type: plan
tags: [architecture, documentation, schema]
---

# Plan — TCK-20260915-ARTIFACT-STATE-CONVERGENCE

Per investigation.md: 3 of 5 artifacts actually converge (atlas, capabilities, wiring-map — wiring
map already done); 2 stay independently assessed (taxonomy, scorecard), recorded with reasoning
rather than mechanically converged. Both peer flags (taxonomy independence, capabilities'
`(state, verified)` mapping function) are now **confirmed** — no steps below remain gated.

## Step 0 — Correct the epic's own scoping documents — done

`docs/plans/mechanism_registry_initiative.md` (Finding 1, Gap 2) and
`tickets/todos/mechanism-registry/TCK-20260915-EPIC-MECHANISM-REGISTRY.md` (Request Summary, Scope
item 4, Out of Scope, Related Code Areas) corrected from the false "five artifacts, 50 taxonomy
rows" framing to the verified 3-mechanism-domain + 2-different-axis framing, with the correction's
own cause (grepped guessed vocabulary instead of reading the file) recorded in place. Both files
re-validated with `validate_frontmatter.py` after editing.

## Step 1 — Atlas convergence (scope item 1, AC #1/#2/#6) — unblocked, proceed

**Peer's explicit constraint (the sharpest risk in this ticket, not a general caution): surgical
field replacement of `badge.cls` only, never card prose.** The atlas is a 3171-line artifact the
user reads directly; its value is concentrated in hand-written card descriptions accumulated across
69 revisions. `camp` was itself found in a description, not a badge — and
`TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT` exists specifically to re-read those
descriptions. A regenerator that emits whole cards from a template would silently destroy the input
to that audit before it runs — the cards would still exist, still be well-formed, just emptied of
whatever caveats nobody has read yet. This is the load-bearing test (test_plan.md #3a), not a nice-
to-have.

1. `tools/mechanism_atlas_regenerate.py` (new): reads `mechanisms.yaml` +
   `mechanism_atlas_card_mapping.py`, computes expected `badge.cls` per mapped card
   (`registry.state`, applying split/partial exceptions), and mutates **only the `cls` key inside
   each mapped card's `badges[i]` dict** — parse the JSON, walk to the exact `(section, index,
   badge_index)` path from the mapping table, set `cls`, re-serialize the whole structure unchanged
   otherwise. Every other key (`title`, `text` on the badge, `fromNote`, `desc`, `src`) is carried
   through byte-for-byte from the parsed input — never regenerated, never templated. Same in-place-
   JSON-rewrite technique as the wiring-map classDef tool, not a full HTML regeneration.
2. `--check` mode (mirrors T2/T3's generator convention): reports drift without writing, non-zero
   exit if any mapped card's badge disagrees with the registry.
3. Run `--check` first against the real committed atlas to find any pre-existing drift beyond
   `camp`/`succession`/`committed_intentions` before regenerating — do not assume those 3 are the
   only ones.
4. Apply the fix (regenerate for real), diff-review the result before committing — the split/
   partial cards are the highest-risk spot for a bad auto-edit.
5. Idea-level cards (68, not mechanism-mapped) are untouched — `all_mechanism_card_badge_positions()`
   only returns mapped positions, so the regenerator physically cannot touch them.

## Step 2 — Capabilities convergence (scope item 3, AC #4) — unblocked, both peer flags confirmed

1. Build `tools/mechanism_capabilities_card_mapping.py` (new), same reuse-not-rederive approach as
   the atlas mapping — but capabilities has no equivalent citation table to reuse (Foundation's own
   investigation only cited atlas cards), so this one is a fresh hand mapping, cross-verified
   programmatically the same way (positional coverage check, no duplicate keys, spot-check a sample
   against card text) rather than trusted blind. 99 cards vs. 75 mechanisms — expect a similar
   split/partial-coverage shape to the atlas's, confirm by reading section-by-section rather than
   assuming a 1:1.
2. Declare the `(state, verified) -> tier` mapping function in one place
   (`tools/mechanism_capabilities_tier.py` — single function, exported, importable by both the
   regenerator and its own test):
   ```
   done + verified.verdict != contradicted  -> live
   done + verified.verdict == contradicted  -> built
   orphan | gated | skeleton                -> built
   partial                                  -> live, unless overridden (see 3)
   gap                                      -> planned
   ```
3. **`partial` override table, per peer's explicit tightening** — not a general escape hatch: a
   dedicated `PARTIAL_TIER_OVERRIDES: Dict[mechanism_id, Tuple[tier, reason]]`, checked only for
   `state == "partial"` mechanisms, applied after the declared mapping. A test asserts every entry
   has a non-empty `reason` string. No equivalent override table for the other 5 states — if one of
   those turns out to need a per-card exception later, that is itself a signal the mapping function
   is wrong and should be revisited, not silently patched.
4. `tools/mechanism_capabilities_regenerate.py` (new): same surgical-field-only discipline as Step
   1 — mutate only `tier` and `tierLabel` per mapped card, every other key (`title`, `desc`) carried
   through byte-for-byte. `tierLabel` is the one field this ticket DOES hand-write new text for
   (camp's fix requires a real replacement label, not just a `cls`-style enum flip) — write it
   deliberately, once, reviewed before committing, not templated from the mapping. Fix camp's own
   `planned`/"Built, but confirmed not working" contradiction as the first proof case (new value:
   `tier: built`, `tierLabel` close to the existing "Paying for Information" card's phrasing
   pattern).
5. Run `--check` against the real file first to find pre-existing drift beyond camp, same
   discipline as Step 1.3.

## Step 3 — Wiring map (scope item 4) — already done, no code change

Reconfirmed directly (investigation.md Finding 5): `make mechanism-wiring-map-classdef-check`
already passes against the current registry. No further action; this scope item closes on the
existing T3-built target.

## Step 4 — Taxonomy (scope item 2, AC #3) — unblocked, peer confirmed independence

Peer independently re-verified (own re-count: 108 cards / 6 values, `na` dominant at 47, titles
confirmed as architecture patterns) and confirmed the "stays independent" disposition. No code
change to the taxonomy file itself. Record the conclusion and its evidence (the zero-overlap check
against all 13 currently orphan/gated mechanism ids) in this ticket's Completion Summary — already
partly done via the `docs/plans/mechanism_registry_initiative.md` Finding 1 correction (see
investigation.md). Check whether the taxonomy file has a "scope/relationship to other docs" note
area before assuming one exists or needs adding; if none exists, do not invent one — the correction
belongs in the plan doc and this ticket's own record, not a retrofitted note in a file this ticket
otherwise leaves untouched.

## Step 5 — Scorecard (scope item 5, AC #5) — unblocked, proceed

Record the "stays independent" conclusion (investigation.md Finding 6) in this ticket's Completion
Summary. No code change — already correctly independent, nothing to converge.

## Step 6 — Propagation test (AC #2) — three consumers, per peer's explicit correction

**Peer's explicit scope correction**: now that taxonomy/scorecard are confirmed independent, the
propagation proof covers exactly the three real consumers — atlas, capabilities, wiring map — "two
out of three passing would look like success," so all three must move together in one test, not
two of three asserted and the third assumed from T3's prior work.

New test (`tests/unit/tools/test_mechanism_artifact_convergence.py`): flip one mechanism's `state`
(and separately, `verified.verdict`) in an in-memory/fixture copy of the registry (not the real
committed file), then:
- regenerate the atlas fixture, assert its badge `cls` changed to match
- regenerate the capabilities fixture, assert its `tier` changed to match the declared function
- call `mechanism_wiring_map_classdef.compute_expected_classdef()` (reused, not reimplemented —
  already proven generically by T3's own `test_compute_expected_classdef_maps_states_correctly`)
  against the same fixture, assert its result also changed to match

All three assertions in the same test, against the same single fixture mutation — proving
convergence holds generally, not just for today's already-correct values, and that no consumer was
silently left out.

## Step 7 — Docs, tests, close

- Update `docs/plans/mechanism_registry_initiative.md` if it references this child ticket's scope.
- `make knowledge-index-update` (docs changed).
- Full scoped pytest run, `graphify-out/` genuinely moved aside and restored (standing discipline
  every ticket this epic).
- Close per the established T1-T3 sequence: move ticket + staging artifacts, since this is the
  epic's last child, also move the entire `tickets/todos/mechanism-registry/` folder to
  `tickets/done/mechanism-registry/` per the Workflow Rule (all children done).

## Acceptance-criteria map

| AC | Satisfied by |
|---|---|
| 1 (no artifact keeps an independent hand-maintained `state` copy) | Steps 1, 2 — atlas + capabilities regenerate from registry; taxonomy/scorecard are not `state` copies at all (Finding 3/6), so AC #1 doesn't apply to them |
| 2 (propagation proven) | Step 6 |
| 3 (taxonomy expresses orphan/gated) | Step 4 — pending peer; may resolve as "not applicable, different axis" with recorded evidence rather than literal vocabulary addition |
| 4 (capabilities mapping declared once, overridable) | Step 2.2/2.3 |
| 5 (scorecard decision recorded) | Step 5 |
| 6 (artifacts stay viewable standalone) | Steps 1/2 write directly into each file's existing embedded JSON — no separate build/toolchain step, matches the existing convention already used for `card-sections-data` |
