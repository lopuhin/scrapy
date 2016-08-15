"""Helper functions for working with signals"""

import logging

from twisted.internet.defer import maybeDeferred, DeferredList, Deferred
from twisted.python.failure import Failure

logger = logging.getLogger(__name__)


class _IgnoredException(Exception):
    pass


def send_catch_log(signal=None, sender=None, *arguments, **named):
    """Like pydispatcher.robust.sendRobust but it also logs errors and returns
    Failures instead of exceptions.
    """
    return signal.send_robust(sender=sender, **named)


def send_catch_log_deferred(signal=None, sender=None, *arguments, **named):
    """Like send_catch_log but supports returning deferreds on signal handlers.
    Returns a deferred that gets fired once all signal handlers deferreds were
    fired.
    """
    return signal.send_robust_deferred(sender=sender, **named)


def disconnect_all(signal, sender=None):
    """Disconnect all signal handlers. Useful for cleaning up after running
    tests
    """
    signal.disconnect_all(sender)
