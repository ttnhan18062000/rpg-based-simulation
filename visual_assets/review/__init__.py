"""Review tooling for draft sets (`TCK-20261008-VISUAL-ASSETS-REVIEW-TOOLING-IN-STORE-CLI`): the sheet rule, the compliance table, the look-alike report, the blind-check helpers, the owner review folder.

A peer of `visual_assets.store` and `visual_assets.drawing`: it reads the drafts, the committed specs and the frontend's colour table, judges nothing by itself (a verdict on art is recorded by running a command, never asserted by a test) and writes
only to a directory it is given. It may import `store.config`, `store.pixels` and `drawing.technique.lint`; `store` and `drawing` never import it (`tests/visual_assets/test_boundaries.py`).
"""
