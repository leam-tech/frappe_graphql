from graphql import GraphQLType, GraphQLResolveInfo

from frappe.model.meta import Meta

from .dataloaders import get_child_table_loader
from .utils import get_frappe_df_from_resolve_info
from ..depth_limit_validator import is_introspection_key
from ..extract_requested_fields_resolver_info import get_fields
from ..get_path import path_key
from ..permissions import get_allowed_fieldnames_for_doctype


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

    key = path_key(info)
    valid_fields = info.context.get(key)

    if not info.context.get(key):
        valid_fields = _get_fields_child_table(info, df.options, df.parent)
        info.context[key] = valid_fields

    return get_child_table_loader(
        child_doctype=df.options,
        parent_doctype=df.parent,
        parentfield=df.fieldname,
        path=key,
        fields=valid_fields
    ).load(obj.get("name"))


def _get_fields_child_table(info: GraphQLResolveInfo, child_doctype: str, parent_doctype: str):
    selected_fields = {
        key.replace('__name', '')
        for key in get_fields(info).keys()
        if not is_introspection_key(key)
    }
    # we need to make sure parent and name is there
    selected_fields.update({"name", "parent"})
    fieldnames = set(get_allowed_fieldnames_for_doctype(
        doctype=child_doctype,
        parent_doctype=parent_doctype
    ))
    return list(set(list(selected_fields.intersection(fieldnames))))
