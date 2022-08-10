from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe

from .utils import get_singular_doctype


def setup_link_field_resolvers(schema: GraphQLSchema):
    """
    This will set up Link fields on DocTypes to resolve target docs
    """
    for type_name, gql_type in schema.type_map.items():
        dt = get_singular_doctype(type_name)
        if not dt:
            continue

        meta = frappe.get_meta(dt)
        for df in meta.get_link_fields() + meta.get_dynamic_link_fields():
            if df.fieldname not in gql_type.fields:
                continue
            gql_type.fields[df.fieldname].resolve = None

            _name_df = f"{df.fieldname}__name"
            if _name_df not in gql_type.fields:
                continue

            gql_type.fields[_name_df].resolve = _resolve_link_name_field


def setup_dynamic_link_field_resolvers(schema: GraphQLSchema):
    """
    This will set up Link fields on DocTypes to resolve target docs
    """
    pass


def _resolve_link_field(obj, info: GraphQLResolveInfo, **kwargs):
    pass


def _resolve_link_name_field(obj, info: GraphQLResolveInfo, **kwargs):
    df = info.field_name.split("__name")[0]
    return obj.get(df)
