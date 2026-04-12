import inspect
import typing

class NoInit:
    pass

sig = inspect.signature(NoInit.__init__)
print(f"Parameters: {list(sig.parameters.keys())}")
for name, param in sig.parameters.items():
    print(f"Param: {name}, Kind: {param.kind}, Annotation: {param.annotation}")
