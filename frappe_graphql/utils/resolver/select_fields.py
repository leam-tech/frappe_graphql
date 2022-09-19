from graphql import GraphQLType, GraphQLResolveInfo, GraphQLNonNull, GraphQLEnumType

import frappe
from frappe.model.meta import Meta

from .translate import _translatable_resolver
from .utils import get_frappe_df_from_resolve_info


def setup_select_field_resolvers(meta: Meta, gql_type: GraphQLType):

    for df in meta.get_select_fields():

        if df.fieldname not in gql_type.fields:
            continue

        gql_field = gql_type.fields[df.fieldname]
        gql_field.resolve = _select_field_resolver


def _select_field_resolver(obj, info: GraphQLResolveInfo, **kwargs):

    df = get_frappe_df_from_resolve_info(info)
    return_type = info.return_type

    value = obj.get(info.field_name)
    if isinstance(return_type, GraphQLNonNull):
        return_type = return_type.of_type

    if isinstance(return_type, GraphQLEnumType):
        return frappe.scrub(value).upper()

    if df and df.translatable:
        return _translatable_resolver(obj, info, **kwargs)

    return obj.get(info.field_name)
