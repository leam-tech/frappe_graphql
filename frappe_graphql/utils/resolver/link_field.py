from graphql import GraphQLResolveInfo, GraphQLType, is_scalar_type

import frappe
from frappe.model.meta import Meta

from .dataloaders import get_doctype_dataloader
from .utils import get_frappe_df_from_resolve_info


def setup_link_field_resolvers(meta: Meta, gql_type: GraphQLType):
    """
    This will set up Link fields on DocTypes to resolve target docs
    """
    link_dfs = meta.get_link_fields() + meta.get_dynamic_link_fields() + \
        _get_default_field_links()

    for df in link_dfs:
        if df.fieldname not in gql_type.fields or is_scalar_type(
                gql_type.fields[df.fieldname].type):
            continue

        gql_field = gql_type.fields[df.fieldname]
        if df.fieldtype == "Link":
            gql_field.resolve = _resolve_link_field
        elif df.fieldtype == "Dynamic Link":
            gql_field.resolve = _resolve_dynamic_link_field
        else:
            continue

        _name_df = f"{df.fieldname}__name"
        if _name_df not in gql_type.fields:
            continue

        gql_type.fields[_name_df].resolve = _resolve_link_name_field


def _resolve_link_field(obj, info: GraphQLResolveInfo, **kwargs):
    df = get_frappe_df_from_resolve_info(info)
    if not df:
        return None

    dt = df.options
    dn = obj.get(info.field_name)

    if not (dt and dn):
        return None

    # Permission check is done within get_doctype_dataloader via get_list
    return get_doctype_dataloader(dt).load(dn)


def _resolve_dynamic_link_field(obj, info: GraphQLResolveInfo, **kwargs):
    df = get_frappe_df_from_resolve_info(info)
    if not df:
        return None

    dt = obj.get(df.options)
    if not dt:
        return None

    dn = obj.get(info.field_name)
    if not dn:
        return None

    # Permission check is done within get_doctype_dataloader via get_list
    return get_doctype_dataloader(dt).load(dn)


def _resolve_link_name_field(obj, info: GraphQLResolveInfo, **kwargs):
    df = info.field_name.split("__name")[0]
    return obj.get(df)


def _get_default_field_links():
    def _get_default_field_df(fieldname):
        df = frappe._dict(
            fieldname=fieldname,
            fieldtype="Data"
        )
        if fieldname in ("owner", "modified_by"):
            df.fieldtype = "Link"
            df.options = "User"

        if fieldname == "parent":
            df.fieldtype = "Dynamic Link"
            df.options = "parenttype"

        return df

    return [
        _get_default_field_df(x) for x in [
            "owner", "modified_by", "parent"
        ]
    ]
