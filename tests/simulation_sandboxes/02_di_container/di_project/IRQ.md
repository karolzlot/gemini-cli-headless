# Implementation Request: DI Container

## Goal
Implement a Dependency Injection (DI) container in `container.py` that supports singleton and factory registrations, recursive resolution, and circular dependency detection.

## Scope
- Create `di_project/container.py`.
- Define `Container` class.
- Support `register_singleton(interface, implementation)`.
- Support `register_factory(interface, factory_func)`.
- Support `resolve(interface)`.
- Raise `CircularDependencyError` when a cycle is detected.
- Implement recursive resolution (if an implementation requires other dependencies).

## Out of Scope
- External configuration files (YAML/JSON).
- Thread safety.
- Decorator-based injection.

## Technical Details
- Use Python's type hints.
- `CircularDependencyError` should be a custom exception.
- Ensure the container can instantiate classes that do not define their own `__init__` (i.e., they inherit `object.__init__` which has `*args` and `**kwargs`). The container should ignore these generic parameters if no registration exists for them.
