# Test Plan: Phase 23 Content Reference Graph & Active Data Validation

## Automated Unit Tests

We will add the following test scenarios to `tests/unit/content/test_layered_catalog.py`:

1. **Reference Graph Construction**:
   - Parse a small repository containing active definitions.
   - Assert `ContentReferenceGraph` compiles correct nodes and directed edges.
   - Verify that deterministic nodes lookups and reverse adjacency lookups return the expected sets.

2. **Active Unused Archetype Validation**:
   - Construct a test setup with an active archetype record (`EXISTING-LOGIC` / `REDESIGNED-CORE`) that has no population recipe or legacy projection referencing it.
   - Run `CatalogValidator.validate()`.
   - Assert that an error/warning issue is generated detailing the archetype's ID and family.

3. **Active Unused Material Validation**:
   - Construct a test setup with an active material record that has no resource, item, or recipe referencing it.
   - Run `CatalogValidator.validate()`.
   - Assert that an error/warning issue is generated detailing the material's ID and family.

4. **Active Unused Module Validation**:
   - Construct a test setup with a module that has no composition referencing it.
   - Run validation and assert a warning is generated.

5. **Exempted Families Unused Scenario**:
   - Create a future-extension / additional record.
   - Run validation and assert no error/warning is generated.
