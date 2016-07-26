import unittest

from scrapy.dispatch.utils.robustapply import robust_apply, function
from scrapy.dispatch.utils import func_accepts_kwargs

class Callable(object):
    def __call__(self):
        pass


class NotCallable(object):
    pass


def method(): pass


class CallableKwargs(object):
    def __call__(self, **kwargs):
        pass


def accepts_pos_arg(arg):
    pass


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

    def test_robust_apply_error(self):
        named = {'arg': 'arg'}
        args = ['test']
        with self.assertRaises(TypeError):
            robust_apply(accepts_pos_arg, *args, **named)

    def test_robust_apply_filter_args(self):
        named = {'arg': 'from_named', 'test': 'test'}

        def calledFunction(arg='from_sign'):
            self.assertEqual(arg, 'from_named')
        robust_apply(calledFunction, **named)


class func_accepts_kwargs_test(unittest.TestCase):

    def test_func_accepts_kwargs(self):
        def accept_kwargs(**kwargs):
            pass

        def no_kwargs():
            pass
        # To test the attribute error case
        someval = 0
        self.assertTrue(func_accepts_kwargs(accept_kwargs))
        with self.assertRaises(TypeError):
            func_accepts_kwargs(someval)
        self.assertTrue(func_accepts_kwargs(NotCallable))
        self.assertFalse(func_accepts_kwargs(Callable))
        self.assertTrue(func_accepts_kwargs(CallableKwargs))
