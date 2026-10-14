---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER
artifact_type: test_plan
tags: [architecture, testing, hud]
---

# Test plan — TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER

- `test_review_sheets.py`: six images and a README and nothing else, canvases at least 1400 px wide; the same drafts give the same bytes; only the four proposed drafts are shown and the two declined ones are never candidates (README and commands); the README holds what each image shows, the recorded result, the findings and 4 review plus 4 adopt commands with --parent r0001 and the existing source ids; a planted extra draft appears in 01 and changes the image; a folder inside a repository is refused; the font covers every label character; canvas rectangles are exact and clipped; the vision rows are real colours; other sets generate, a set already adopted gets no commands, a set with no marker gets a note.
- Mutants A to E (mutant_proof.txt).
