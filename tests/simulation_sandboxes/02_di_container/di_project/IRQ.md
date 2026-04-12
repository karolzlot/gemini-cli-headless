# Implementation Request: DI Container

## Context
We need a simple but robust Dependency Injection (DI) container for the project.

## Requirements
- **Location**: `di_project/container.py`
- **Features**:
    - Support for **singleton** registration (return the same instance every time).
    - Support for **factory** registration (return a new instance every time).
    - **Recursive resolution**: Automatically resolve dependencies of a requested type if they are also registered.
    - **Circular Dependency Detection**: The container MUST detect if there's a cycle in dependencies and raise a `CircularDependencyError`.
- **API (Example)**:
    ```python
    container = Container()
    container.register_singleton(ServiceA, ServiceA)
    container.register_factory(ServiceB, lambda c: ServiceB(c.resolve(ServiceA)))
    service_b = container.resolve(ServiceB)
    ```

## Constraints
- Do not use external DI libraries.
- Ensure type hinting is used where appropriate.
- Follow PEP 8 standards.
