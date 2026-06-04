# Test Plan - Phase 24 Resolver layer claims and evidence fields

We will run the content unit tests to verify:
- Resolver-only families are correctly set to `RESOLVED_PARTIALLY`.
- New evidence fields exist and are validated.
- Validation checks for resolver fetching exist.

## Automated Tests

Run:
```bash
pytest tests/unit/content/
```
