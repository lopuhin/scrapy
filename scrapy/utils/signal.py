"""Helper functions for working with signals"""

import logging

from twisted.internet.defer import maybeDeferred, DeferredList, Deferred
from twisted.python.failure import Failure

from scrapy.utils.log import failure_to_exc_info

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
    def logerror(failure, recv):
        spider = named.get('spider', None)
        if dont_log is None or not isinstance(failure.value, dont_log):
            logger.error("Error caught on signal handler: %(receiver)s",
                         {'receiver': recv},
                         exc_info=failure_to_exc_info(failure),
                         extra={'spider': spider})
        return failure
    named['errfunc'] = logerror
    return signal.send_robust_deferred(sender=sender, **named)


def disconnect_all(signal=Anonymous, sender=Any):
    """Disconnect all signal handlers. Useful for cleaning up after running
    tests
    """
    for receiver in signal._live_receivers(sender=sender):
        signal.disconnect(receiver=receiver, sender=sender)
