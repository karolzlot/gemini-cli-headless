import unittest
from container import Container, CircularDependencyError

class DependencyA:
    pass

class DependencyB:
    def __init__(self, a: DependencyA):
        self.a = a

class DependencyC:
    def __init__(self, b: DependencyB):
        self.b = b

class CircularA:
    def __init__(self, b: 'CircularB'):
        self.b = b

class CircularB:
    def __init__(self, a: CircularA):
        self.a = a

class NoHint:
    def __init__(self, something):
        self.something = something

class TestContainer(unittest.TestCase):
    def setUp(self):
        self.container = Container()

    def test_singleton(self):
        instance = DependencyA()
        self.container.register_singleton(DependencyA, instance)
        resolved = self.container.resolve(DependencyA)
        self.assertIs(instance, resolved)

    def test_factory(self):
        self.container.register_factory(DependencyA, lambda: DependencyA())
        resolved1 = self.container.resolve(DependencyA)
        resolved2 = self.container.resolve(DependencyA)
        self.assertIsNot(resolved1, resolved2)
        self.assertIsInstance(resolved1, DependencyA)

    def test_auto_wire_nested(self):
        # Should resolve C -> B -> A
        c = self.container.resolve(DependencyC)
        self.assertIsInstance(c, DependencyC)
        self.assertIsInstance(c.b, DependencyB)
        self.assertIsInstance(c.b.a, DependencyA)

    def test_circular_dependency(self):
        with self.assertRaises(CircularDependencyError):
            self.container.resolve(CircularA)

    def test_missing_type_hint(self):
        with self.assertRaises(TypeError):
            self.container.resolve(NoHint)

    def test_singleton_used_in_auto_wire(self):
        a_instance = DependencyA()
        self.container.register_singleton(DependencyA, a_instance)
        b = self.container.resolve(DependencyB)
        self.assertIs(b.a, a_instance)

if __name__ == "__main__":
    unittest.main()
