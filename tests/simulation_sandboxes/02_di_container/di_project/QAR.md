# QA Request: DI Container

## Validation Criteria
- [ ] Container correctly resolves singletons (same instance returned).
- [ ] Container correctly resolves factories (new instance returned).
- [ ] Container resolves dependencies recursively.
- [ ] Container raises `CircularDependencyError` for direct cycles (A -> A).
- [ ] Container raises `CircularDependencyError` for indirect cycles (A -> B -> A).
- [ ] Container handles classes without custom `__init__` (inheriting from `object`).

## Risk Areas
- Infinite recursion in `resolve` without cycle detection.
- `inspect.signature` on `object.__init__` returning `*args` and `**kwargs`.

## Rituals (from Project Brain)
- [ ] QA MUST verify that the Doer included a self-test script or unit tests.
- [ ] QA MUST check for any recursive calls that might lack cycle detection.
- [ ] QA MUST always produce a `QRP.md` report.
- [ ] QA MUST verify that the container handles classes without a custom `__init__`.
