import unittest

from scrapy.dispatch.robustapply import robust_apply, function


class Callable(object):
    def __call__(self):
        pass


class NotCallable(object):
    pass


def method(): pass


class RobustApplyTest(unittest.TestCase):

    def test_function_callable(self):
        self.assertEqual(function(method)[0], method)

    def test_class_callable(self):
        self.assertEqual(function(Callable)[0], Callable.__call__)

    def test_not_callable(self):
        with self.assertRaises(ValueError):
            function(NotCallable)

    def test_robust_apply(self):
        named = {'arg1': 'test1', 'arg2': 'test2'}
        def calledFunction(arg1):
            self.assertEqual(arg1, 'test1')
        robust_apply(calledFunction, **named)
