
from container import Container, CircularDependencyError
import unittest

class SelfCircular:
    def __init__(self, s: 'SelfCircular'):
        pass

class TestQA(unittest.TestCase):
    def test_self_circular(self):
        container = Container()
        # Even without registration, auto-instantiation should detect cycle
        with self.assertRaises(CircularDependencyError):
            container.resolve(SelfCircular)

    def test_factory_multiple_calls(self):
        container = Container()
        count = 0
        def my_factory():
            nonlocal count
            count += 1
            return f"instance-{count}"
        
        container.register_factory(str, my_factory)
        
        val1 = container.resolve(str)
        val2 = container.resolve(str)
        
        self.assertEqual(val1, "instance-1")
        self.assertEqual(val2, "instance-2")
        self.assertEqual(count, 2)

    def test_unregistered_class_not_singleton(self):
        class Transient:
            pass
        
        container = Container()
        t1 = container.resolve(Transient)
        t2 = container.resolve(Transient)
        
        self.assertIsNot(t1, t2, "Unregistered classes should be transient by default")

if __name__ == "__main__":
    unittest.main()
