# Test Plan — TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN

No new production tests — investigation-only ticket, per its own explicit Out of Scope ("Choosing
or building a fix"). The one-off instrumented 2000-tick measurement script used to gather the
empirical confirmation in investigation.md was throwaway (not committed) — its own findings are
recorded verbatim in the investigation, and are independently reproducible from the grep-based
code-path findings (Defect 1/2) alone, which don't depend on any particular run. Real test coverage
proving the fixed conjunction belongs to the follow-up ticket
(`TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`), once a fix direction is chosen there.
