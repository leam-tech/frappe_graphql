# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import frappe
from frappe.utils import cint
from .utils.cursor_pagination import CursorPaginator  # noqa
from .utils.loader import get_schema  # noqa
from .utils.exceptions import ERROR_CODED_EXCEPTIONS, GQLExecutionUserError, \
    GQLExecutionUserErrorMultiple  # noqa
from .utils.roles import REQUIRE_ROLES  # noqa
from .utils.subscriptions import setup_subscription, get_consumers, notify_consumer, \
    notify_consumers, notify_all_consumers, subscription_keepalive, complete_subscription  # noqa

__version__ = '1.0.0'

if not cint(frappe.get_conf().get("developer_mode")):
    from graphql.pyutils import did_you_mean
    did_you_mean.__globals__['MAX_LENGTH'] = 0
