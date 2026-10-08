---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261008-VISUAL-ASSETS-ICON-RECOGNISABILITY-CHECKS

- `test_icon_specs.py`: one complete consistent spec per registered icon key (36; 22 v2), the style guide holds the generated table verbatim, the process-rule steps are in order, missing key / missing field / clashing distractor are refused, weapon upright vs dagger diagonal.
- `test_icon_recognition.py`: neutral shuffled reproducible images, valid PNG of the four panels with a location glyph on the plate, seeded candidate lists (intended name once, distractors, none last), whole-word synonym scoring, choice scoring, evaluate and prompts name only files.
- `test_icon_lookalikes.py`: planted twin at another size and family found at 0 px, a different shape not close and neighbours ordered, a one-pixel near twin still close, deterministic over 36 icons, empty sprite.
- Mutants A to D (mutant_proof.txt). Evidence runs: the blind check and the look-alike report on all 36 (stored).
