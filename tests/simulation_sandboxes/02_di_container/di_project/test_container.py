import unittest
from container import Container, CircularDependencyError

class BaseService:
    pass

class ServiceA(BaseService):
    def __init__(self):
        self.value = "A"

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

class ServiceC:
    def __init__(self, b: ServiceB):
        self.b = b

class CircularA:
    def __init__(self, b: 'CircularB'):
        self.b = b

class CircularB:
    def __init__(self, a: 'CircularA'):
        self.a = a

class ExplicitArgs:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class NoInit:
    pass

class TestContainer(unittest.TestCase):
    def test_singleton_registration(self):
        container = Container()
        container.register_singleton(ServiceA, ServiceA)
        
        instance1 = container.resolve(ServiceA)
        instance2 = container.resolve(ServiceA)
        
        self.assertIsInstance(instance1, ServiceA)
        self.assertIs(instance1, instance2)

    def test_factory_registration(self):
        container = Container()
        container.register_factory(ServiceA, lambda: ServiceA())
        
        instance1 = container.resolve(ServiceA)
        instance2 = container.resolve(ServiceA)
        
        self.assertIsInstance(instance1, ServiceA)
        self.assertIsNot(instance1, instance2)

    def test_recursive_resolution(self):
        container = Container()
        container.register_singleton(ServiceA, ServiceA)
        container.register_singleton(ServiceB, ServiceB)
        container.register_singleton(ServiceC, ServiceC)
        
        c = container.resolve(ServiceC)
        
        self.assertIsInstance(c, ServiceC)
        self.assertIsInstance(c.b, ServiceB)
        self.assertIsInstance(c.b.a, ServiceA)

    def test_circular_dependency(self):
        container = Container()
        container.register_singleton(CircularA, CircularA)
        container.register_singleton(CircularB, CircularB)
        
        with self.assertRaises(CircularDependencyError):
            container.resolve(CircularA)

    def test_auto_instantiation(self):
        container = Container()
        # ServiceA is not registered, but it's a class with no deps
        instance = container.resolve(ServiceA)
        self.assertIsInstance(instance, ServiceA)

    def test_no_init(self):
        container = Container()
        instance = container.resolve(NoInit)
        self.assertIsInstance(instance, NoInit)

    def test_explicit_args_kwargs(self):
        container = Container()
        instance = container.resolve(ExplicitArgs)
        self.assertIsInstance(instance, ExplicitArgs)
        self.assertEqual(instance.args, ())
        self.assertEqual(instance.kwargs, {})

if __name__ == "__main__":
    unittest.main()
