from container import Container, CircularDependencyError
import sys

def test_factory_self_cycle():
    container = Container()
    # A factory that resolves itself
    container.register_factory(int, lambda: container.resolve(int))
    
    print("Testing factory self-cycle...")
    try:
        container.resolve(int)
    except CircularDependencyError:
        print("Caught CircularDependencyError (SUCCESS)")
    except RecursionError:
        print("Caught RecursionError (FAILURE - Should be CircularDependencyError)")
    except Exception as e:
        print(f"Caught unexpected exception: {type(e).__name__}: {e}")

class A:
    def __init__(self, b: 'B'):
        pass

class B:
    def __init__(self, a: 'A'):
        pass

def test_factory_complex_cycle():
    container = Container()
    # A depends on B (auto-wired), B factory depends on A
    container.register_factory(B, lambda: B(container.resolve(A)))
    
    print("\nTesting factory complex cycle (A -> B (factory) -> A)...")
    try:
        container.resolve(A)
    except CircularDependencyError:
        print("Caught CircularDependencyError (SUCCESS)")
    except RecursionError:
        print("Caught RecursionError (FAILURE - Should be CircularDependencyError)")
    except Exception as e:
        print(f"Caught unexpected exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_factory_self_cycle()
    test_factory_complex_cycle()
