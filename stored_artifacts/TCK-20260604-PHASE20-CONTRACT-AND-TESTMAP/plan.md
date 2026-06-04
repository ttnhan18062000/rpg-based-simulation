# Implementation Plan: Phase 20 Content Usage Contract

## Proposed Changes

### Content Module

#### [NEW] [matrix.py](file:///home/vboxuser/Work/rpg-based-simulation/src/content/matrix.py)
- Define `ContentFamilySpec` model/dict representing the metadata of a content family.
- Declare `CONTENT_USAGE_MATRIX` containing specifications for all 35+ content families.
- Implement helper function to generate the markdown matrix report.

#### [NEW] [content_usage_matrix.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/mechanics/content_usage_matrix.md)
- Generated markdown file documenting the component family contract.

### Test Module

#### [NEW] [test_content_usage_matrix.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/unit/content/test_content_usage_matrix.py)
- Complete unit test suite verifying `ContentUsageMatrix` constraints, completeness, and state checks.

## Verification Plan
Run:
```bash
pytest tests/unit/content/test_content_usage_matrix.py
```
Check that `docs/mechanics/content_usage_matrix.md` is correctly generated and matches.
