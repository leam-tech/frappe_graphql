# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import time


def profile_fn(fn):
    from graphql import GraphQLResolveInfo

    def _inner(*args, **kwargs):
        _v = fn.__name__
        if len(args) > 1 and isinstance(args[1], GraphQLResolveInfo):
            _v += f" df: {args[1].field_name}"

        t = time.perf_counter()
        v = fn(*args, **kwargs)
        print(_v, f"{(time.perf_counter() - t) * 1000}ms")
        return v

    return _inner


from .utils.cursor_pagination import CursorPaginator  # noqa
from .utils.loader import get_schema  # noqa
from .utils.exceptions import ERROR_CODED_EXCEPTIONS, GQLExecutionUserError, GQLExecutionUserErrorMultiple  # noqa
from .utils.roles import REQUIRE_ROLES  # noqa
from .utils.subscriptions import setup_subscription, get_consumers, notify_consumer, \
  notify_consumers, notify_all_consumers, subscription_keepalive, complete_subscription  # noqa

__version__ = '1.0.0'
