from typing import Any
from graphql import GraphQLObjectType, GraphQLResolveInfo

import frappe

from frappe_graphql import CursorPaginator
from .document_resolver import document_resolver
from .utils import get_singular_doctype, get_plural_doctype


def default_field_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):

    parent_type: GraphQLObjectType = info.parent_type
    if not isinstance(info.parent_type, GraphQLObjectType):
        frappe.throw("Invalid GraphQL")

    if parent_type.name == "Query":
        # This section is executed on root query type fields
        singular_doctype = get_singular_doctype(info.field_name)
        if singular_doctype:
            return frappe._dict(
                doctype=singular_doctype,
                name=kwargs.get("name")
            )

        plural_doctype = get_plural_doctype(info.field_name)
        if plural_doctype:
            frappe.has_permission(doctype=plural_doctype, throw=True)
            return CursorPaginator(doctype=plural_doctype).resolve(obj, info, **kwargs)

    if not isinstance(obj, dict):
        return None

    should_resolve_from_doc = obj.get("name") and (
        obj.get("doctype") or get_singular_doctype(parent_type.name))

    # check if requested field can be resolved
    # - default resolver for simple objects
    # - these form the resolvers for
    #   "SET_VALUE_TYPE", "SAVE_DOC_TYPE", "DELETE_DOC_TYPE" mutations
    if info.field_name in obj:
        value = obj.get(info.field_name)
        if isinstance(value, CursorPaginator):
            return value.resolve(obj, info, **kwargs)

        if not should_resolve_from_doc:
            return value

    if should_resolve_from_doc:
        # this section is executed for Fields on DocType object types.
        return document_resolver(
            obj=obj,
            info=info,
            **kwargs
        )

    return None
