---
status: active
layer: frontend
authority: P2
audience: designer
date: 2026-09-09
tags: [art, pixel-art, experiments, live-map, accessibility]
---

# Detailed Plan 07 — Manual Pixel-Art Experiment Execution

## Outcome and boundary

Run the disposable manual sessions defined by this plan, using
[visual-system planning](../../brainstorm/render-and-art/visual-system-planning.md) for visual constraints
and the [program review handoff](../../brainstorm/render-and-art/render-and-art-review-handoff.md) for
cross-epic context. Record which hypotheses deserve another drawing pass. This plan creates no art assets
now, selects no production style, and never gates G1–G5. A renderer charter may require native-scale
readability evidence, but must accept current or synthetic fixtures as alternatives and cannot require
completion of this art plan.

## Fixed test constraints

- Current map cell: 16 pixels; turn-based grid gameplay; one-cell character readability.
- Judge at native display scale, not only enlarged source scale.
- No hue-only, motion-only, hover-only or single-pixel critical distinction.
- Runtime/generated IDs receive no unique art by default.
- Quantity, cooldown, severity, duration and rarity do not create new base identities.
- Labels/HUD detail remain valid where exact map identity is unnecessary.

## Required stress set

| Family | Exact first identities/groups |
|---|---|
| Entities | Goblin Scout/Archer; Apprentice Mage/Arcane Mage/Moon Cult Sorcerer; Town Healer/Forest Druid; Spirit Guardian; Dragon Cult Champion; Cave Spider/Lizardfolk Scout |
| Items | Rusted Sword/Iron Sword/Steel Sword/Silvered Blade; Wooden Staff/Apprentice Staff; Warding Charm/Frost Focus; Crystal Shard/Frost Shard/Spirit Essence; Ember Axe/Venom Dagger; Spirit Lantern |
| Skills/conditions | Power Strike/Heavy Strike; CRUSH/SLASH/PIERCE wounds; Frozen/stunned |
| World/semantic | Spirit Wisp/ground loot; Mine/Dungeon Entrance; Investigate/Explore; Moon Cult/Arcane Circle; active/depleted resource node |

## Session sequence

| ID | Draw | Question | Minimum pass | May inform |
|---|---|---|---|---|
| `ART-W01` | Single-color silhouettes for entity groups and crowded row | Do body family, combat delivery and threat prominence work before color/detail? | Critical neighbors and body families read at one cell; Guardian is not resource/effect; spider is not humanoid | Body templates, landmark and equipment cues |
| `ART-W02` | Grayscale item groups | Do contour/motif distinguish family and decision-relevant identity? | Families read immediately; adjacent identities match after brief legend review without hue | Item templates, motifs, candidate size |
| `ART-W03` | Grayscale Power Strike/Heavy Strike with ready/cooldown states | Can one grammar preserve distinct skills and state? | Shared family and distinct action survive cooldown treatment | Physical-skill grammar and state framing |
| `ART-W04` | Hardest examples at 16×16, 24×24 and 32×32 | What smallest source/display candidate preserves prior distinctions? | Native display remains readable and leaves overlay room | Candidates carried into composition only |
| `ART-W05` | Crowded native-scale gameplay composition and status strip | Does attention order survive all representations/overlays? | Player, threats, objective/interactable, entities, loot, resources and background separate without pixel inspection | Draw order, overlay priority, HUD/map allocation |
| `ART-W06` | Color variants plus grayscale copies | Does color improve scan without carrying critical meaning alone? | Every critical distinction survives grayscale; simultaneous channels do not collide | Color-channel candidates for another test |
| `ART-W07` | Optional 2–4-frame idle for humanoid/non-humanoid/Guardian | Does motion add life without moving the cell or attention hierarchy? | Static identity survives; motion is anchored and nonessential | Whether further idle study is worthwhile |

Each session stops on failure or records a deliberate revision before later results are allowed to
constrain it. `ART-W07` starts only after a static candidate passes `ART-W05`.

## Size/composition rules

For map entities, every 16/24/32 source is composited into the current 16-pixel cell at zoom 1.0; record
overhang, cropping and overlay collision. Items/skills use 16, 24 and 32 CSS-pixel experiment boxes at 1:1
nearest-neighbor display plus a separate 16-pixel preview. These boxes are not production slot decisions.

The crowded scene includes focused player, Goblin Scout/Archer, one caster, Spirit Guardian, Spirit Wisp,
ground loot, active/depleted resource nodes, Mine/Dungeon Entrances, terrain, fog/memory, HP, selection,
objective and combat-target overlays. Include wound and incapacity family strips.

## Result handling

After each session record: date, artist/reviewer, identities, source/display sizes, native-scale context,
color condition, question, drawing, pass/fail/exploratory disposition, confusions, successes, allowed next
decision, rejected alternatives, still-unfrozen decisions and produced file paths.

A pass advances only the next drawing experiment. A fail revises/rejects that candidate. Exploratory or
missing-context results freeze nothing. Renderer teams may copy sanitized captures into a chartered
readability fixture, but pixel identity and renderer choice remain independent.

If a human later submits a manual revision for production consideration, it must use the
asset-management proposal's versioned `CandidateHandoffPackage`. The manual session is a producer only:
asset management independently copies and validates the exact source, hashes, bounded structure,
provenance and rights, and owns quarantine and adoption eligibility. Handoff is not adoption, publication
or activation. Manual records remain outside CAP-B by default unless its owner later approves and tests an
explicit producer-class/corpus-separation amendment.

## Decisions explicitly unfrozen

- Final sprite/icon resolution, palette and art style.
- Status/effect roster and subtype grammar.
- Full executable skill roster.
- Place representation, footprint and transformations.
- Faction-emblem breadth.
- Animation timing/frame count and production scope.
- Render tier, loading, atlas and composition architecture.
- Expanded equipment/paper-doll treatment.

## Cleanup and repository boundary

Keep working drawings outside production asset manifests unless a later reviewed asset ticket adopts them.
Disposable experiment files can be archived or removed after their result record identifies them. Do not
add runtime IDs, asset loaders, atlases, engine imports, gameplay data, or production UI dimensions through
this plan.

## Exit checklist per session

- [ ] Exact stress identities and current 16-pixel constraint were used.
- [ ] Native-scale and grayscale evidence exists.
- [ ] Pass/fail/exploratory criteria were applied.
- [ ] Only the listed next decision was informed.
- [ ] Production specifications remain unfrozen.
- [ ] Result record and file references are complete.
