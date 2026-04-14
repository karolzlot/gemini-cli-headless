---
id: IRQ-20260414-01
recipient: Doer
implementing_actor: Doer
priority: high
---

# Task Overview
Fix circular dependency bugs in the DI container for factory-based registrations and flatten the project structure by moving core files to the root and removing nested directories.

# Scope of Work
- **Circular Dependency Fix**:
    - [ ] Update the `resolve` logic in `container.py` to add the type being resolved to the `resolving` tracking set *before* checking and executing factory functions.
    - [ ] Ensure that `A(factory) -> B(factory) -> A(factory)` correctly raises a circular dependency error instead of a `RecursionError`.
- **Project Flattening**:
    - [ ] Move `di_project/container.py` to the root directory (`C:\Users\chojn\projects\gemini-cli-headless\tests\simulation_sandboxes\02_di_container\di_project\container.py`).
    - [ ] Move `di_project/test_container.py` to the root directory (`C:\Users\chojn\projects\gemini-cli-headless\tests\simulation_sandboxes\02_di_container\di_project\test_container.py`).
    - [ ] Remove the now redundant `di_project/di_project` directory and its `__init__.py`.
    - [ ] Update imports in all files to reflect the flattened structure.

# Out of Scope
- [ ] Do not change the registration API or core logic of the container beyond the requested fix.
- [ ] Do not introduce new features or external dependencies.

# Architectural Constraints (Project Knowledge)
- [ ] Maintain consistent naming conventions for the `Container` class.
- [ ] Ensure the solution for circular dependency detection is robust and covers all resolution paths (singleton, factory, etc.).

# Definition of Done
- [ ] `Container` class is located in `container.py` at the root.
- [ ] Circular dependency check handles factory loops without recursion errors.
- [ ] All tests pass in the new flattened structure.
- [ ] Redundant `di_project/di_project` folder is deleted.
