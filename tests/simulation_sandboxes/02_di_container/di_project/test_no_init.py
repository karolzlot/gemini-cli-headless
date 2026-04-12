import unittest
from container import Container

class NoInit:
    pass

class ExplicitArgs:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

class TestNoInit(unittest.TestCase):
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
