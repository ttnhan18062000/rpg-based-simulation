# Phase 5 Investigation Notes

We need to review `src/worldbuilding/repository.py` to see exactly how schemas are recognized, parsed, and loaded, and how we can support `worldcomposition.v1` seamlessly.
- We will find `schema_version` detection and repository loader routines in `src/worldbuilding/repository.py`.
