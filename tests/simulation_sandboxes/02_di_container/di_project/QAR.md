---
id: QAR-20260414-01
recipient: QA
parent_request: IRQ.md
---

# Validation Strategy
Perform an exhaustive verification of the structural changes and bug fixes, specifically focusing on the prevention of recursion during dependency resolution and the integrity of the flattened project layout.

# Feature-Specific Validation Criteria
- [ ] **Structural Integrity**: Verify that `container.py` and `test_container.py` are in the project root and imports work correctly.
- [ ] **Circular Dependency Detection**: Confirm that a circular dependency involving factories (e.g., A -> B -> A) triggers a specific exception (or the project's standard error) and DOES NOT crash with a `RecursionError`.
- [ ] **Functional Parity**: Ensure that existing non-circular resolutions (singletons, simple factories) still work as expected.

# Specific Risk Areas
- [ ] **Import Paths**: Check if the flattening of the project broke any module imports or test discovery mechanisms.
- [ ] **State Management**: Ensure the `resolving` set is correctly cleaned up after resolution (even on failure) to prevent poisoning subsequent requests.

# Mandatory Rituals
- **Ritual**: QA MUST verify that the Doer included a self-test script or unit tests.
- **Ritual**: QA MUST check for any recursive calls that might lack cycle detection.
