import gc
import sys
import time
import unittest
import weakref
import logging

from twisted.python.failure import Failure

from scrapy.dispatch import Signal, receiver
from scrapy.dispatch.dispatcher import NO_RECEIVERS
import scrapy.settings.default_settings as default_settings
from scrapy.exceptions import DontCloseSpider

logging.basicConfig()


if sys.platform.startswith('java'):
    def garbage_collect():
        # Some JVM GCs will execute finalizers in a different thread, meaning
        # we need to wait for that to complete before we go on looking for the
        # effects of that.
        gc.collect()
        time.sleep(0.1)
elif hasattr(sys, "pypy_version_info"):
    def garbage_collect():
        # Collecting weakreferences can take two collections on PyPy.
        gc.collect()
        gc.collect()
else:
    def garbage_collect():
        gc.collect()


def receiver_1_arg(val, **kwargs):
    return val


class Callable(object):
    def __call__(self, val, **kwargs):
        return val

    def a(self, val, **kwargs):
        return val

a_signal = Signal(providing_args=["val"])
b_signal = Signal(providing_args=["val"])
c_signal = Signal(providing_args=["val"])
d_signal = Signal(providing_args=["val"], use_caching=True)
test_signal = Signal()

class DispatcherTests(unittest.TestCase):
    """Test suite for dispatcher (barely started)"""

    def assertTestIsClean(self, signal):
        """Assert that everything has been cleaned up automatically"""
        # Note that dead weakref cleanup happens as side effect of using
        # the signal's receivers through the signals API. So, first do a
        # call to an API method to force cleanup.
        self.assertFalse(signal.has_listeners())
        self.assertEqual(signal.receivers, [])

    def test_exact(self):
        a_signal.connect(receiver_1_arg, sender=self)
        expected = [(receiver_1_arg, "test")]
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, expected)
        a_signal.disconnect(receiver_1_arg, sender=self)
        self.assertTestIsClean(a_signal)

    def test_ignored_sender(self):
        a_signal.connect(receiver_1_arg)
        expected = [(receiver_1_arg, "test")]
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, expected)
        a_signal.disconnect(receiver_1_arg)
        self.assertTestIsClean(a_signal)

    def test_garbage_collected(self):
        a = Callable()
        a_signal.connect(a.a, sender=self)
        expected = []
        del a
        garbage_collect()
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(result, expected)
        self.assertTestIsClean(a_signal)

    def test_cached_garbaged_collected(self):
        """
        Make sure signal caching sender receivers don't prevent garbage
        collection of senders.
        """
        class sender:
            pass
        wref = weakref.ref(sender)
        d_signal.connect(receiver_1_arg)
        d_signal.send(sender, val='garbage')
        del sender
        garbage_collect()
        try:
            self.assertIsNone(wref())
        finally:
            # Disconnect after reference check since it flushes the tested cache.
            d_signal.disconnect(receiver_1_arg)

    def test_multiple_registration(self):
        a = Callable()
        a_signal.connect(a)
        a_signal.connect(a)
        a_signal.connect(a)
        a_signal.connect(a)
        a_signal.connect(a)
        a_signal.connect(a)
        result = a_signal.send(sender=self, val="test")
        self.assertEqual(len(result), 1)
        self.assertEqual(len(a_signal.receivers), 1)
        del a
        del result
        garbage_collect()
        self.assertTestIsClean(a_signal)

    def test_uid_registration(self):
        def uid_based_receiver_1(**kwargs):
            pass

        def uid_based_receiver_2(**kwargs):
            pass

        a_signal.connect(uid_based_receiver_1, dispatch_uid="uid")
        a_signal.connect(uid_based_receiver_2, dispatch_uid="uid")
        self.assertEqual(len(a_signal.receivers), 1)
        a_signal.disconnect(dispatch_uid="uid")
        self.assertTestIsClean(a_signal)

    def test_robust(self):
        """Test the send_robust() function"""
        def fails(val, **kwargs):
            raise ValueError('this')
        a_signal.connect(fails)
        result = a_signal.send_robust(sender=self, val="test")
        err = result[0][1]
        self.assertIsInstance(err, Failure)
        a_signal.disconnect(fails)
        self.assertTestIsClean(a_signal)

    def test_disconnection(self):
        receiver_1 = Callable()
        receiver_2 = Callable()
        receiver_3 = Callable()
        a_signal.connect(receiver_1)
        a_signal.connect(receiver_2)
        a_signal.connect(receiver_3)
        a_signal.disconnect(receiver_1)
        del receiver_2
        garbage_collect()
        a_signal.disconnect(receiver_3)
        self.assertTestIsClean(a_signal)

    def test_values_returned_by_disconnection(self):
        receiver_1 = Callable()
        receiver_2 = Callable()
        a_signal.connect(receiver_1)
        receiver_1_disconnected = a_signal.disconnect(receiver_1)
        receiver_2_disconnected = a_signal.disconnect(receiver_2)
        self.assertTrue(receiver_1_disconnected)
        self.assertFalse(receiver_2_disconnected)
        self.assertTestIsClean(a_signal)

    def test_has_listeners(self):
        self.assertFalse(a_signal.has_listeners())
        self.assertFalse(a_signal.has_listeners(sender=object()))
        receiver_1 = Callable()
        a_signal.connect(receiver_1)
        self.assertTrue(a_signal.has_listeners())
        self.assertTrue(a_signal.has_listeners(sender=object()))
        a_signal.disconnect(receiver_1)
        self.assertFalse(a_signal.has_listeners())
        self.assertFalse(a_signal.has_listeners(sender=object()))

    def test_debug_logging(self):
        default_log = default_settings.LOG_ENABLED
        default_settings.LOG_ENABLED = False
        def callback():
            pass
        try:
            test_signal.connect(callback, weak=False)
        except  ValueError:
            self.fail("Should not raise errors when logging is disabled.")
        finally:
            test_signal.disconnect(callback)
        default_settings.LOG_ENABLED = default_log
        # with self.assertRaises(ValueError):
        test_signal.connect(callback)
        test_signal.disconnect(callback)
        self.assertTestIsClean(test_signal)
        def raise_dont_log(sender, **kwargs):
            raise DontCloseSpider
        test_signal.connect(raise_dont_log)
        named = {'val': 'val', 'dont_log': DontCloseSpider}
        test_signal.send_robust(self, **named)
        test_signal.send_robust_deferred(self, **named)

    def test_no_receivers(self):
        test_signal = Signal()
        self.assertFalse(test_signal._live_receivers(sender=None))
        test_signal.send(sender=self)
        test_signal.send_robust(sender=self)
        test_signal.send_robust_deferred(sender=self)

    def test_live_receivers(self):
        test_signal = Signal(use_caching=True)
        self.assertFalse(test_signal._live_receivers(sender=self))
        def callback(sender, **kwargs):
            pass
        test_signal.receivers = NO_RECEIVERS
        self.assertFalse(test_signal._live_receivers(sender=self))
        test_signal.receivers = []
        test_signal.connect(callback, sender=self, weak=False)
        self.assertTrue(test_signal._live_receivers(sender=self))
        # Should be fetched from the cache
        self.assertTrue(test_signal._live_receivers(sender=self))
        test_signal.disconnect(callback, sender=self)
        gc.collect()
        test_signal = Signal(use_caching=False)
        test_signal.connect(Callable())
        def _clear_receivers(*args, **kwargs):
            pass
        # Simulate race condition where dead receivers are not cleared
        test_signal._clear_dead_receivers = _clear_receivers
        self.assertFalse(test_signal._live_receivers(sender=None))

    def test_deprecated_receivers(self):
        test_signal = Signal()
        self.assertFalse(test_signal._live_receivers(sender=self))
        def callback(arg1='test', arg2='test'):
            self.assertEqual(arg1, 'test1')
            self.assertEqual(arg2, 'test2')
        test_signal.connect(callback)
        named = {'arg1': 'test1', 'arg2': 'test2'}
        test_signal.send_robust(sender=self, **named)
        test_signal.send(sender=self, **named)
        test_signal.disconnect(callback)
        self.assertTestIsClean(test_signal)


    def test_clear_dead_receivers_race(self):
        a = Callable()
        test_signal.connect(a)
        test_signal.send(sender=self, val='test')
        del test_signal.receiver_accepts_kwargs[id(a)]
        del a
        gc.collect()
        test_signal.send(sender=self, val='test')
        self.assertTestIsClean(test_signal)

    def test_clear_dead_receivers(self):
        test_signal = Signal()
        a = Callable()
        test_signal.connect(a)
        del a
        gc.collect()
        test_signal.send_robust(sender=self, val='test')
        self.assertFalse(test_signal.receiver_accepts_kwargs)
        self.assertTestIsClean(test_signal)


class ReceiverTestCase(unittest.TestCase):
    """
    Test suite for receiver.
    """
    def test_receiver_single_signal(self):
        @receiver(a_signal)
        def f(val, **kwargs):
            self.state = val
        self.state = False
        a_signal.send(sender=self, val=True)
        self.assertTrue(self.state)

    def test_receiver_signal_list(self):
        @receiver([a_signal, b_signal, c_signal])
        def f(val, **kwargs):
            self.state.append(val)
        self.state = []
        a_signal.send(sender=self, val='a')
        c_signal.send(sender=self, val='c')
        b_signal.send(sender=self, val='b')
        self.assertIn('a', self.state)
        self.assertIn('b', self.state)
        self.assertIn('c', self.state)
