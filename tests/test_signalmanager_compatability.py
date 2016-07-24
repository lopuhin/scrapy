import unittest
import gc

from scrapy.signalmanager import SignalManager
from scrapy.dispatch.utils import func_accepts_kwargs
from scrapy.signals import Signal


def receiver(**kwargs):
    pass


def receiver_no_kwargs():
    pass


class BackwardCompatabilityTest(unittest.TestCase):

    def setUp(self):
        self.signals = SignalManager()

    def tearDown(self):
        self.assertFalse(self.signals._patched_receivers)
        gc.collect()

    def test_signal_proxies(self):
        new_signal = object()
        self.signals.connect(receiver, new_signal)
        self.assertIsInstance(
            self.signals._signal_proxies[new_signal.__repr__()], Signal)

    def test_patched_receivers(self):
        new_signal = Signal()
        self.signals.connect(receiver_no_kwargs, new_signal)
        self.assertTrue(
            func_accepts_kwargs(
                self.signals._patched_receivers[receiver_no_kwargs.__repr__()]
            )
        )
        self.signals.disconnect(receiver_no_kwargs, new_signal)
