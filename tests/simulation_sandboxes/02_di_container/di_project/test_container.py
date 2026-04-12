import unittest
from container import Container, CircularDependencyError, RegistrationError

class ServiceA:
    pass

class ServiceB:
    def __init__(self, a: ServiceA):
        self.a = a

class ServiceC:
    def __init__(self, b: ServiceB):
        self.b = b

class CircularA:
    def __init__(self, b):
        self.b = b

class CircularB:
    def __init__(self, a):
        self.a = a

class TestDIContainer(unittest.TestCase):
    def test_singleton_registration(self):
        container = Container()
        container.register_singleton(ServiceA)
        
        instance1 = container.resolve(ServiceA)
        instance2 = container.resolve(ServiceA)
        
        self.assertIs(instance1, instance2)

    def test_factory_registration(self):
        container = Container()
        container.register_factory(ServiceA, lambda c: ServiceA())
        
        instance1 = container.resolve(ServiceA)
        instance2 = container.resolve(ServiceA)
        
        self.assertIsInstance(instance1, ServiceA)
        self.assertIsNot(instance1, instance2)

    def test_recursive_resolution(self):
        container = Container()
        container.register_singleton(ServiceA)
        container.register_singleton(ServiceB)
        container.register_singleton(ServiceC)
        
        service_c = container.resolve(ServiceC)
        
        self.assertIsInstance(service_c, ServiceC)
        self.assertIsInstance(service_c.b, ServiceB)
        self.assertIsInstance(service_c.b.a, ServiceA)

    def test_circular_dependency_detection(self):
        container = Container()
        # Using factories to manually trigger the circularity through resolve calls
        container.register_factory(CircularA, lambda c: CircularA(c.resolve(CircularB)))
        container.register_factory(CircularB, lambda c: CircularB(c.resolve(CircularA)))
        
        with self.assertRaises(CircularDependencyError):
            container.resolve(CircularA)

    def test_unregistered_type_fails(self):
        container = Container()
        with self.assertRaises(RegistrationError):
            container.resolve(ServiceA)

    def test_missing_annotation_fails(self):
        class MissingAnno:
            def __init__(self, x):
                self.x = x
        
        container = Container()
        container.register_singleton(MissingAnno)
        with self.assertRaises(RegistrationError) as cm:
            container.resolve(MissingAnno)
        self.assertIn("missing type annotation", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
