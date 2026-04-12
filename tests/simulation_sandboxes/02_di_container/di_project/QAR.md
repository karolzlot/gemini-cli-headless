# QA Request: DI Container

## Objectives
Verify the implementation of the DI container in `di_project/container.py`.

## Validation Criteria
- **Functional Verification**:
    - Singleton registration returns the same instance.
    - Factory registration returns a new instance.
    - Recursive resolution correctly injects nested dependencies.
- **Safety**:
    - **Circular Dependency Detection**: Explicitly test for cycles (A -> B -> A) and verify that `CircularDependencyError` is raised.
- **Project Rituals** (from `GEMINI.md`):
    - Verify that a self-test script or unit tests are included.
    - Check for any recursive calls that might lack cycle detection.

## Risk Areas
- Recursive resolution depth and performance.
- Edge cases where a class depends on itself directly.
- Multi-threading safety (optional but preferred if simple).
