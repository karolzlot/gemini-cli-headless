# Project Brain: DI Container
## QA Rituals & Testing
- Ritual: QA MUST verify that the Doer included a self-test script or unit tests.
- Ritual: QA MUST check for any recursive calls that might lack cycle detection.
- Ritual: QA MUST always produce a `QRP.md` report, even if the implementation is broken or tests fail.
- Ritual: QA MUST verify that the container handles classes without a custom `__init__` (which have `*args` and `**kwargs` in their signature).
