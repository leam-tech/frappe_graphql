from graphql import GraphQLType, GraphQLResolveInfo

from frappe.model.meta import Meta

from .dataloaders import get_child_table_loader
from .utils import get_frappe_df_from_resolve_info


def setup_child_table_resolvers(meta: Meta, gql_type: GraphQLType):
    for df in meta.get_table_fields():
        if df.fieldname not in gql_type.fields:
            continue

        gql_field = gql_type.fields[df.fieldname]
        gql_field.resolve = _child_table_resolver


def _child_table_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    # If the obj already has a non None value, we can return it.
    # This happens when the resolver returns a full doc
    if obj.get(info.field_name) is not None:
        return obj.get(info.field_name)

    df = get_frappe_df_from_resolve_info(info)
    if not df:
        return []

    return get_child_table_loader(
        child_doctype=df.options,
        parent_doctype=df.parent,
        parentfield=df.fieldname
    ).load(obj.get("name"))
