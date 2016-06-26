from __future__ import absolute_import
import warnings

from scrapy.utils import signal as _signal
from scrapy.exceptions import ScrapyDeprecationWarning
from scrapy.dispatch.robustapply import robustApply
from scrapy.dispatch.utils import func_accepts_kwargs


class SignalManager(object):

    def __init__(self, sender=None):
        self.sender = sender
        self.signals = {}

    def connect(self, receiver, signal, **kwargs):
        """
        Connect a receiver function to a signal.

        The signal can be any object, although Scrapy comes with some
        predefined signals that are documented in the :ref:`topics-signals`
        section.

        :param receiver: the function to be connected
        :type receiver: callable

        :param signal: the signal to connect to
        :type signal: object
        """
        kwargs.setdefault('sender', self.sender)
        if not func_accepts_kwargs(receiver):
            warnings.warn("The use of handlers that don't accept "
                          "**kwargs has been deprecated, plese refer "
                          "to the Signals API documentation.",
                          ScrapyDeprecationWarning, stacklevel=2)
            self.signals[receiver.__repr__()] = \
                lambda sender, **kw: robustApply(receiver, sender, **kw)
            return signal.connect(self.signals[receiver.__repr__()],
                                  **kwargs)
        return signal.connect(receiver, **kwargs)

    def disconnect(self, receiver, signal, **kwargs):
        """
        Disconnect a receiver function from a signal. This has the
        opposite effect of the :meth:`connect` method, and the arguments
        are the same.
        """
        kwargs.setdefault('sender', self.sender)
        if not func_accepts_kwargs(receiver):
            return signal.disconnect(self.signals[receiver.__repr__()],
                                     **kwargs)
        return signal.disconnect(receiver, **kwargs)

    def send_catch_log(self, signal, **kwargs):
        """
        Send a signal, catch exceptions and log them.

        The keyword arguments are passed to the signal handlers (connected
        through the :meth:`connect` method).
        """
        kwargs.setdefault('sender', self.sender)
        return _signal.send_catch_log(signal, **kwargs)

    def send_catch_log_deferred(self, signal, **kwargs):
        """
        Like :meth:`send_catch_log` but supports returning `deferreds`_ from
        signal handlers.

        Returns a Deferred that gets fired once all signal handlers
        deferreds were fired. Send a signal, catch exceptions and log them.

        The keyword arguments are passed to the signal handlers (connected
        through the :meth:`connect` method).

        .. _deferreds:
        http://twistedmatrix.com/documents/current/core/howto/defer.html
        """
        kwargs.setdefault('sender', self.sender)
        return _signal.send_catch_log_deferred(signal, **kwargs)

    def disconnect_all(self, signal, **kwargs):
        """
        Disconnect all receivers from the given signal.

        :param signal: the signal to disconnect from
        :type signal: object
        """
        kwargs.setdefault('sender', self.sender)
        return _signal.disconnect_all(signal, **kwargs)
