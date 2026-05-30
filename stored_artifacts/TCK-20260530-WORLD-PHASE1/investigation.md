# Phase 1 Investigation Notes

We need to check:
1. What serialization library or pydantic versions/base settings are standard in the project? We saw Pydantic `BaseModel` being used in `src/worldbuilding/recipe.py`. Let's inspect `src/worldbuilding/schema.py` to match styles and config rules.
2. Where are schema versions handled?
3. How is parsing structured?
