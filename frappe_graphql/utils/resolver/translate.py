from graphql import GraphQLResolveInfo, GraphQLType

import frappe
from frappe.model.meta import Meta


def setup_translatable_resolvers(meta: Meta, gql_type: GraphQLType):
    for df_fieldname in meta.get_translatable_fields():
        if df_fieldname not in gql_type.fields:
            continue

        gql_field = gql_type.fields[df_fieldname]
        if gql_field.resolve:
            continue

        gql_field.resolve = _translatable_resolver


def _translatable_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    value = obj.get(info.field_name)
    if isinstance(value, str) and value:
        value = frappe._(value)

    return value
