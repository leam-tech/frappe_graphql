import frappe
from graphql import GraphQLResolveInfo


class IntrospectionDisabled(Exception):
    pass


def disable_introspection_queries(next_resolver, obj, info: GraphQLResolveInfo, **kwargs):
    # https://github.com/jstacoder/graphene-disable-introspection-middleware
    if is_introspection_disabled() and info.field_name.lower() in ['__schema', '__introspection']:
        raise IntrospectionDisabled("Introspection is disabled")

    return next_resolver(obj, info, **kwargs)


def is_introspection_disabled():
    return not frappe.local.conf.get("developer_mode") and \
        not frappe.local.conf.get("enable_introspection_in_production")
