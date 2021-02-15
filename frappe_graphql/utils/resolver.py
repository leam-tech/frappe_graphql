from typing import Any
import frappe
from graphql import GraphQLObjectType, GraphQLResolveInfo


def default_doctype_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
    parent_type: GraphQLObjectType = info.parent_type
    if not isinstance(info.parent_type, GraphQLObjectType):
        frappe.throw("Invalid GraphQL")

    if parent_type.name == "Query" and info.path[0] is None:
        # root doctype query
        doctype = get_doctype(info.path[1])
        if not frappe.has_permission(doctype=doctype):
            return []
        filters = frappe._dict()
        if kwargs and len(kwargs.keys()):
            if "filters" in kwargs:
                filters = frappe.parse_json(kwargs.get("filters"))
            else:
                filters = kwargs
        return frappe.get_list(doctype, filters=filters)
    elif len(info.path) == 3:
        doctype = get_doctype(parent_type.name)
        if not frappe.has_permission(doctype=doctype):
            return []
        cached_doc = frappe.get_cached_doc(doctype, obj.name)
        return cached_doc.get(info.field_name)


def get_doctype(name):
    valid_doctypes = [x.name for x in frappe.get_all("DocType")]
    return [x for x in valid_doctypes if x.replace(" ", "") == name][0]
