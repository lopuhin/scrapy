from __future__ import absolute_import

import inspect

import six


def func_accepts_kwargs(func):
    if six.PY2:
        # Not all callables are inspectable with getargspec, so we'll
        # try a couple different ways.
        # First check if object is callable to make behaviour same as python3
        if not callable(func):
            raise TypeError('{!r} is not a callable object'.format(func))
        try:
            argspec = inspect.getargspec(func)
        except TypeError:
            try:
                argspec = inspect.getargspec(func.__call__)
            except (TypeError, AttributeError):
                # We fall back to assuming the callable does accept kwargs,
                # since we don't want to prevent registration of valid but
                # weird receivers.
                argspec = None
        return not argspec or argspec[2] is not None

    return any(
        p for p in inspect.signature(func).parameters.values()
        if p.kind == p.VAR_KEYWORD
    ) or any(
        p for p in inspect.signature(func.__call__).parameters.values()
        if p.kind == p.VAR_KEYWORD
    )
