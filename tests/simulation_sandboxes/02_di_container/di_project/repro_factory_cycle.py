from container import Container, CircularDependencyError
import unittest

class A:
    def __init__(self, b: 'B'):
        self.b = b

class B:
    def __init__(self, a: A):
        self.a = a

def test_factory_cycle():
    container = Container()
    # Factory for A depends on B (auto-wired), B depends on A
    container.register_factory(A, lambda: A(container.resolve(B)))
    
    try:
        container.resolve(A)
        print("FAIL: No CircularDependencyError raised for factory cycle")
    except CircularDependencyError:
        print("PASS: CircularDependencyError raised for factory cycle")
    except RecursionError:
        print("FAIL: RecursionError (Stack Overflow) instead of CircularDependencyError")

if __name__ == "__main__":
    test_factory_cycle()
