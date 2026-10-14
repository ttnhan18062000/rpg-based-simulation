---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER
artifact_type: investigation
tags: [architecture, testing, hud]
---

# Investigation — TCK-20261008-VISUAL-ASSETS-REVIEW-SHEET-FOLDER

- Budget: the store's PNG decoder bounds decoded images at about 4 MB (a security bound, not an encoder limit); encoding with zlib and struct needs no dependency, and a 2000 x 3900 canvas is written in about 4 seconds for the whole folder. PIL is not in the venv and was not added.
- Bugs found by looking at the first images, each pinned by a test: the vision rows were black because `pilot_colour_vision.simulate` works in 0..1 (not 0..255); an eleven-icon group overflowed the canvas (the zoom now steps down to fit); the silhouette rows overflowed (cells wrap onto further lines); a draft the owner already adopted (icons-v2) must not get adopt commands (it prints ALREADY ADOPTED).
- Mutant C (the repo guard removed) wrote a stray folder into the repo before the test caught it; it was deleted and the guard restored: a reminder that the guard is what keeps review output out of git.
