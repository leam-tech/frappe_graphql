from graphql import GraphQLSchema, GraphQLResolveInfo

import frappe
from frappe.model.meta import is_single

from frappe_graphql import CursorPaginator

from .dataloaders import get_doctype_dataloader
from .utils import get_singular_doctype, get_plural_doctype


def setup_root_query_resolvers(schema: GraphQLSchema):
    """
    This will handle DocType Query at the root.

    Query {
        User(name: ID): User!
        Users(**args: CursorArgs): UserCountableConnection!
    }
    """

    for fieldname, field in schema.query_type.fields.items():
        dt = get_singular_doctype(fieldname)
        if dt:
            field.resolve = _get_doc_resolver
            continue

        dt = get_plural_doctype(fieldname)
        if dt:
            field.resolve = _doc_cursor_resolver


def _get_doc_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    dt = get_singular_doctype(info.field_name)
    if is_single(dt):
        kwargs["name"] = dt

    return get_doctype_dataloader(dt).load(kwargs["name"])


def _doc_cursor_resolver(obj, info: GraphQLResolveInfo, **kwargs):
    plural_doctype = get_plural_doctype(info.field_name)
    frappe.has_permission(doctype=plural_doctype, throw=True)

    return CursorPaginator(doctype=plural_doctype).resolve(obj, info, **kwargs)
