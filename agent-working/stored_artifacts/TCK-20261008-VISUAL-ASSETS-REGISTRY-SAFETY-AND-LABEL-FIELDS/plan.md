---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REGISTRY-SAFETY-AND-LABEL-FIELDS
artifact_type: plan
date: 2026-10-09
tags: [architecture, testing]
---

# Plan: safety class, structured fallback, label fields, verify rules (W02.7, W03.1, W06.3)

## Today (investigated)
62 registry keys (36 icon, 23 terrain, 3 border). `VisualKeyDefinition` has `key, family, description, variant_axes, optional, detail`. The 36 icon descriptions state class (35 identifying, 1 decorative: `icon.plate.location`) and a fallback as prose; terrain descriptions say "the colour fill is its fallback" (forest identifying per `fallback_safety.md`); the 3 border keys are decorative per `fallback_safety.md` (D19) but only in that doc. No field, no check (`m1_contract_register.md:121,127,160`).

## Schema (registry file, `schema_version` stays 1: new REQUIRED fields on every key, migrated in this ticket)
- `safety_class`: `decorative | identifying | critical`.
- `fallback`: `{kind, text, glyph}`; `kind` in `none | flat_fill | text | glyph_and_text`; `text` (what the text shows, e.g. "the building name"), `glyph` (the existing glyph by name, e.g. "lucide:Hammer") nullable.
- icon family only: `label_key` (= `label.<key>`, verified equal so it cannot drift) and `label` (default English, describes what the icon IS or does, for alt/aria text); a `decorative` key has neither (W3C: empty alt).
## Verify / load rules
- W02.7: every key declares class and fallback; `decorative` may use any kind; `identifying` needs kind != none; `critical` needs kind `text` or `glyph_and_text` with non-empty text (no critical key exists; the surface owner's review stays a process rule).
- kind consistency: `none` has no text/glyph; `flat_fill` and `text` need text; `glyph_and_text` needs both.
- W03.1: a non-empty `variant_axes` is rejected (D17: only the `detail` axis exists).
- W06.3: a `check_fallbacks` function usable at build, release and activation: every key of the release/registry has a structurally valid alternative (the artifact itself may be missing, which is what the fallback is for).
- Icon family: non-decorative keys must carry label_key and label.
## Migration
All 62 keys migrated from their prose (mechanical for the 36 icons and 3 borders; terrain = identifying + flat_fill + "the terrain name as hover text"). The description prose is kept (not deleted).
## Registry hash / fixtures
The registry hash moves. With child 1 no fixture guard rides it; the 8 inventory pins need no change unless they pin descriptions (checked by the test run). No new release candidate unless the owner asks.
## Register
Rows W02.7, W03.1, W06.3 re-derived to MET with evidence; M1 RESULT stays BLOCKED (M0 is INCONCLUSIVE, `m1_contract_register.md:38,44`): the register's own count changes to 58 MET / 4 GAP.
## Owner approval
The label list (36 icon keys; the plate carries none) goes to the owner by blocking question BEFORE any code or commit that contains it.

## Owner approval (blocking question, 2026-10-09), verbatim
Label list (35 icon keys, the plate carries none): "Approve the list as written".

## Deviations from the plan while building (disclosed)
- The record fields are OPTIONAL at the model level (so synthetic fixture keys and old records still parse) and REQUIRED by the registry loader for every non-fixture key; `variant_axes` is rejected for every key including fixtures. The plan said required fields; this keeps the record contract stable.
- `fallback_problems` (W06.3) is used by `assemble_release` AND `export_runtime` (activation time), both refusing with `fallback_missing`.
- The contract fixture `visual_keys.fixture.yaml` lost its axis (the loader now refuses axes); the JSON record fixture keeps it (model-level).
- `icon.marker.enemy_camp`: the registry prose was cut off at the 256-character limit ("today's emoji label (swords,"), so its structured fallback is `glyph: emoji label (swords)`, `text: the location name as hover text`, modelled on the other markers; an assumption, noted here.
- ADR row is D23 (D22 is reserved for child 4).

