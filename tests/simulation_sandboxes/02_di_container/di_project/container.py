import inspect
from typing import Any, Callable, Dict, Set, Type, TypeVar, Optional

T = TypeVar("T")

class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected during resolution."""
    pass

class Container:
    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._resolving: Set[Type] = set()

    def register_singleton(self, cls: Type[T], instance: T) -> None:
        """Map a type to a specific instance."""
        self._singletons[cls] = instance

    def register_factory(self, cls: Type[T], factory_func: Callable[[], T]) -> None:
        """Map a type to a callable that produces an instance."""
        self._factories[cls] = factory_func

    def resolve(self, cls: Type[T]) -> T:
        """Resolve an instance of the requested type."""
        if not isinstance(cls, type):
            raise TypeError(f"Expected a type to resolve, got {type(cls).__name__}: {cls}")

        if cls in self._resolving:
            raise CircularDependencyError(f"Circular dependency detected while resolving {cls.__name__}")

        if cls in self._singletons:
            return self._singletons[cls]

        self._resolving.add(cls)
        try:
            if cls in self._factories:
                return self._factories[cls]()
            return self._auto_wire(cls)
        finally:
            self._resolving.remove(cls)

    def _auto_wire(self, cls: Type[T]) -> T:
        """Attempt to instantiate the class by resolving its constructor dependencies."""
        from typing import get_type_hints
        try:
            init = cls.__init__
        except AttributeError:
            return cls()

        if init is object.__init__:
            return cls()

        try:
            # get_type_hints is better at resolving forward references (strings)
            hints = get_type_hints(init)
        except Exception:
            # Fallback to empty hints if resolution fails
            hints = {}

        sig = inspect.signature(init)
        kwargs = {}
        
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            
            # Try to get the type from hints (resolved) or param.annotation (unresolved)
            dep_type = hints.get(name, param.annotation)
            
            if dep_type is inspect.Parameter.empty or isinstance(dep_type, str):
                if param.default is not inspect.Parameter.empty:
                    continue
                raise TypeError(f"Cannot auto-wire parameter '{name}' of {cls.__name__}: missing or unresolved type hint.")

            kwargs[name] = self.resolve(dep_type)

        return cls(**kwargs)
