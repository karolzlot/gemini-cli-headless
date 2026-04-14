from container import Container, CircularDependencyError
import unittest

class A:
    def __init__(self, b: 'B'):
        self.b = b

class B:
    def __init__(self, a: A):
        self.a = a

def test_factory_cycle():
    print("Testing factory -> auto-wire cycle...")
    container = Container()
    container.register_factory(A, lambda: A(container.resolve(B)))
    try:
        container.resolve(A)
        print("FAIL: No CircularDependencyError raised")
    except CircularDependencyError:
        print("PASS: CircularDependencyError raised")
    except RecursionError:
        print("FAIL: RecursionError")

def test_dual_factory_cycle():
    print("Testing dual factory cycle...")
    container = Container()
    container.register_factory(A, lambda: A(container.resolve(B)))
    container.register_factory(B, lambda: B(container.resolve(A)))
    try:
        container.resolve(A)
        print("FAIL: No CircularDependencyError raised")
    except CircularDependencyError:
        print("PASS: CircularDependencyError raised")
    except RecursionError:
        print("FAIL: RecursionError (Stack Overflow)")

if __name__ == "__main__":
    test_factory_cycle()
    test_dual_factory_cycle()
