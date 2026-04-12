import typing
from typing import Any, Callable, Dict, Set, Type, TypeVar, Optional
import inspect

T = TypeVar("T")

class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected during resolution."""
    pass

class Container:
    def __init__(self) -> None:
        self._registry: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[..., Any]] = {}
        self._instances: Dict[Type, Any] = {}
        self._resolving: Set[Type] = set()

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """Registers a class as a singleton for a given interface."""
        self._registry[interface] = implementation
        # Clear cached instance if re-registering
        if interface in self._instances:
            del self._instances[interface]

    def register_factory(self, interface: Type[T], factory_func: Callable[..., T]) -> None:
        """Registers a factory function for a given interface."""
        self._factories[interface] = factory_func

    def resolve(self, interface: Type[T]) -> T:
        """Resolves an interface to its implementation, handling dependencies recursively."""
        if interface in self._resolving:
            raise CircularDependencyError(f"Circular dependency detected for {interface}")

        if interface in self._instances:
            return self._instances[interface]

        self._resolving.add(interface)
        try:
            instance = self._do_resolve(interface)
            
            # If it was registered as a singleton (in _registry but not _factories), cache it
            if interface in self._registry and interface not in self._factories:
                 self._instances[interface] = instance
                 
            return instance
        finally:
            self._resolving.remove(interface)

    def _do_resolve(self, interface: Type[T]) -> T:
        if interface in self._factories:
            return self._factories[interface]()

        if interface in self._registry:
            implementation = self._registry[interface]
            return self._instantiate(implementation)

        # If not registered, try to instantiate the interface itself if it's a class
        if inspect.isclass(interface):
            return self._instantiate(interface)

        raise ValueError(f"No registration for {interface} and it cannot be auto-instantiated.")

    def _instantiate(self, cls: Type[T]) -> T:
        try:
            type_hints = typing.get_type_hints(cls.__init__)
        except (TypeError, NameError, AttributeError):
            # Fallback for classes with no __init__ or if type hints can't be resolved
            type_hints = {}

        signature = inspect.signature(cls.__init__)
        kwargs = {}
        for name, param in signature.parameters.items():
            if name == 'self':
                continue
            
            # Use type_hints if available, otherwise fallback to param.annotation
            dependency_type = type_hints.get(name, param.annotation)

            if dependency_type is inspect.Parameter.empty:
                if param.default is not inspect.Parameter.empty:
                    continue
                # Ignore VAR_POSITIONAL and VAR_KEYWORD if no type hint/registration exists
                if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                    continue
                raise ValueError(f"Parameter '{name}' of {cls} lacks a type hint and has no default value.")
            
            kwargs[name] = self.resolve(dependency_type)
        
        return cls(**kwargs)
