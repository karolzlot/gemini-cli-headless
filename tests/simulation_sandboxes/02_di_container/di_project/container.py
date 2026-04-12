import inspect
from typing import Type, TypeVar, Callable, Any, Dict, Set


T = TypeVar("T")


class DIError(Exception):
    """Base exception for DI container."""
    pass


class CircularDependencyError(DIError):
    """Raised when a circular dependency is detected."""
    pass


class RegistrationError(DIError):
    """Raised when a type is not registered."""
    pass


class Container:
    """
    A simple Dependency Injection container supporting singletons, factories,
    and recursive resolution with circular dependency detection.
    """
    def __init__(self):
        self._registry: Dict[Type, Callable[[Container], Any]] = {}
        self._singletons: Dict[Type, Any] = {}
        self._resolving_stack: Set[Type] = set()

    def register_singleton(self, cls: Type[T], implementation: Any = None) -> None:
        """
        Registers a class as a singleton.
        If implementation is a class, it will be instantiated on first resolve.
        If implementation is a callable (factory), it will be called once.
        """
        if implementation is None:
            implementation = cls

        def singleton_factory(c: "Container") -> T:
            if cls not in self._singletons:
                if isinstance(implementation, type):
                    # It's a class, try to instantiate it
                    self._singletons[cls] = self._instantiate(implementation)
                elif callable(implementation):
                    # It's a factory or already an instance provider
                    self._singletons[cls] = implementation(c)
                else:
                    # It's a pre-existing instance
                    self._singletons[cls] = implementation
            return self._singletons[cls]

        self._registry[cls] = singleton_factory

    def register_factory(self, cls: Type[T], factory: Callable[["Container"], T]) -> None:
        """Registers a factory function that returns a new instance every time."""
        self._registry[cls] = factory

    def resolve(self, cls: Type[T]) -> T:
        """Resolves the requested type, handling dependencies recursively."""
        if cls in self._resolving_stack:
            path = " -> ".join([str(t) for t in self._resolving_stack]) + f" -> {cls}"
            raise CircularDependencyError(f"Circular dependency detected: {path}")

        if cls not in self._registry:
            raise RegistrationError(f"Type {cls} is not registered in the container.")

        self._resolving_stack.add(cls)
        try:
            return self._registry[cls](self)
        finally:
            self._resolving_stack.remove(cls)

    def _instantiate(self, cls: Type[T]) -> T:
        """Helper to instantiate a class by resolving its __init__ arguments."""

        init_method = getattr(cls, "__init__", None)
        if init_method is None or init_method is object.__init__:
            return cls()

        sig = inspect.signature(init_method)
        params = {}
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            
            if param.annotation is inspect.Parameter.empty:
                raise RegistrationError(
                    f"Cannot resolve parameter '{name}' of {cls}: missing type annotation."
                )
            
            params[name] = self.resolve(param.annotation)
            
        return cls(**params)
