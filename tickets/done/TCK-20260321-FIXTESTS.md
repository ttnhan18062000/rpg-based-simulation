# TCK-20260321-FIXTESTS

**Title:** Resolve Core Engine Test Regressions
**Status:** INPROGRESS

**Description:** 
The simulation test suite currently emits 14+ failures. The objective is to apply Test-Driven Development and Clean Code principles to systematically isolate the broken implementations, refactor the faults, and stabilize the integration suite to 100% green.

**Scope:**
- Investigate and execute `pytest --lf`.
- Refactor the failing system modules.
- Ensure the fixes do not break other systems.
- Use clean code principles (SOLID, DRY) for the refactoring.

**Acceptance Criteria:**
- `pytest tests/ -v` completes with 0 failures, 0 errors.
- Code conforms to clean architectural constraints.
