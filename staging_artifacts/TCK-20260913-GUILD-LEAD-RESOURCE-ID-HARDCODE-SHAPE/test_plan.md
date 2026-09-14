# Test Plan — TCK-20260913-GUILD-LEAD-RESOURCE-ID-HARDCODE-SHAPE

**Blocked, same reason as plan.md.** If Option 3 (or any option) is chosen, the ticket's own
acceptance criteria already names the minimum required coverage: a real test that fails loudly if
the referenced resource kind(s) stop matching the real content catalog — not a test that mocks a
matching node, since that's exactly the class of test that let the original `"iron"` vs.
`"iron_vein"` mismatch survive undetected. Filled in once a direction is picked.
