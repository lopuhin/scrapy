import unittest
from scrapy.dispatch.utils import func_accepts_kwargs


def no_kwargs(*args):
    pass

def accepts_kwargs(**kwargs):
    pass


class DispatchUtilsTest(unittest.TestCase):

    def test_func_accepts_kwargs(self):
        self.assertTrue(func_accepts_kwargs(accepts_kwargs))
        self.assertFalse(func_accepts_kwargs(no_kwargs))
