import unittest
import gc

from scrapy.dispatch.weakref_backports import WeakMethod


class HasMethod():
    def method(self):
        pass


class WeakrefBackportsTest(unittest.TestCase):

    def test_weakmethod_creation(self):
        has_method_inst = HasMethod()
        self.assertIsInstance(WeakMethod(has_method_inst.method), WeakMethod)
        with self.assertRaises(TypeError):
            WeakMethod({})

    def test_weakref_weakmethod_eq(self):
        hasmethod = HasMethod()
        reference1 = WeakMethod(hasmethod.method)
        self.assertEqual(reference1, reference1)
        self.assertEqual(reference1, reference1)
        gc.collect()
        reference2 = WeakMethod(hasmethod.method)
        self.assertEqual(reference1, reference2)
        gc.collect()
        self.assertEqual(reference1, reference2)
        self.assertNotEqual(reference1, HasMethod.method)
