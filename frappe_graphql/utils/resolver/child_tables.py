from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe

from .dataloaders import get_child_table_loader
from .utils import get_singular_doctype


def setup_child_table_resolvers(schema: GraphQLSchema):
    for type_name, gql_type in schema.type_map.items():
        dt = get_singular_doctype(type_name)
        if not dt:
            continue

        meta = frappe.get_meta(dt)
        for df in meta.get_table_fields():
            if df.fieldname not in gql_type.fields:
                continue

            gql_field = gql_type.fields[df.fieldname]
            gql_field.frappe_docfield = df
            gql_field.resolve = _child_table_resolver


def _child_table_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    df = getattr(info.parent_type.fields[info.field_name], "frappe_docfield", None)
    if not df:
        return []

    return get_child_table_loader(
        child_doctype=df.options,
        parent_doctype=df.parent,
        parentfield=df.fieldname
    ).load(obj.get("name"))
